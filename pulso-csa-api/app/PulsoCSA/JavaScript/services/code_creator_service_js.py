#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Geração de Código JS/TS/React via LLM❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import re
import time
from typing import Optional

CODEGEN_JS_TIMEOUT_SEC = int(os.getenv("CODEGEN_JS_TIMEOUT_SEC", "120"))
CODEGEN_JS_RETRY_DELAY_SEC = float(os.getenv("CODEGEN_JS_RETRY_DELAY_SEC", "2"))

try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client
from app.prompts.loader import load_prompt


def _strip_markdown_code(raw: str) -> str:
    """Remove blocos ```...``` da saída do LLM."""
    if not raw or not raw.strip():
        return raw or ""
    text = raw.strip()
    m = re.search(r"```(?:javascript|jsx|tsx|ts|js|vue)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    return text


def _strip_ollama_artifacts(text: str) -> str:
    """Remove tokens que Ollama/Qwen injeta na saída (ex: <|fim_middle|>)."""
    if not text:
        return text
    for token in ("<|fim_middle|>", "<|im_end|>", "<|end|>", "<|eot_id|>"):
        text = text.replace(token, "")
    # Qualquer <|...|> restante (padrão genérico)
    text = re.sub(r"<\|[^|]*\|>", "", text)
    return text.strip()


def _is_valid_app_content(content: str) -> bool:
    """
    Valida se o conteúdo define corretamente o componente App (evita tela preta por export default App sem definição).
    Rejeita saídas truncadas/corrompidas do LLM.
    """
    if not content or len(content.strip()) < 50:
        return False
    c = content.replace("\r", "")
    has_definition = (
        "function App" in c or "const App " in c or "const App=" in c
        or "export default function App" in c or "export default function app" in c.lower()
    )
    has_export = "export default" in c
    return bool(has_definition and has_export)


def _is_valid_index_content(content: str) -> bool:
    """Valida index.tsx/jsx — precisa montar o React no DOM."""
    if not content or len(content.strip()) < 40:
        return False
    c = content.replace("\r", "")
    return "createRoot" in c and ("getElementById" in c or "root" in c)


def _looks_like_prompt_echo(text: str) -> bool:
    """Rejeita saída que parece eco do prompt (texto em prosa, não código)."""
    if not text or len(text.strip()) < 20:
        return True
    head = text.strip()[:500].lower()
    # Frases típicas do prompt que o LLM ecoa em vez de gerar código
    bad_phrases = (
        "se quiser", "vale ressaltar", "lembre-se", "seu objetivo",
        "o output deve", "retorne somente", "gere apenas",
        "nunca inclua", "nunca utilize", "o uso de outras",
        "ferramentas de desenvolvimento", "stack moderna",
    )
    if any(p in head for p in bad_phrases):
        return True
    return False


def _is_valid_form_content(content: str) -> bool:
    """Valida *Form — rejeita stub vazio ou eco do prompt."""
    if not content or len(content.strip()) < 80:
        return False
    if _looks_like_prompt_echo(content):
        return False
    c = content.replace("\r", "")
    has_form = "<form" in c or "onSubmit" in c
    has_input = "<input" in c or "type=\"email\"" in c or "type=\"password\"" in c
    return bool(has_form or has_input)


def _is_valid_page_content(content: str) -> bool:
    """Valida *Page — rejeita stub vazio que perderia composição Page→Form."""
    if not content or len(content.strip()) < 60:
        return False
    c = content.replace("\r", "")
    has_import = "import " in c and ("from " in c or "from'" in c)
    has_component_usage = "<" in c and "/>" in c
    return bool(has_import and has_component_usage)


def _fix_auth_baseurl(content: str) -> str:
    """
    Garante fallback para API em formulários de login/auth.
    Se o código usa VITE_API_URL || '' (ou || ""), substitui pelo fallback
    para que o preview funcione mesmo sem .env.
    """
    if not content or "/auth/" not in content:
        return content
    fallback = "http://127.0.0.1:3001"
    # Padrões comuns que deixam baseUrl vazio
    for bad in (
        "VITE_API_URL || ''",
        "VITE_API_URL || \"\"",
        "VITE_API_URL||''",
        "VITE_API_URL||\"\"",
    ):
        if bad in content and fallback not in content:
            content = content.replace(bad, f"VITE_API_URL || '{fallback}'", 1)
    return content


def _is_valid_auth_service_content(content: str) -> bool:
    """Valida authService — rejeita stub vazio que perderia função login."""
    if not content or len(content.strip()) < 50:
        return False
    c = content.replace("\r", "")
    return "login" in c or "fetch" in c or "/auth/" in c


def generate_file_js(
    filename: str,
    refined_prompt: str,
    structure: str,
    file_context: str = "",
    backend: str = "{}",
    security: str = "{}",
    language: str = "javascript",
    framework: Optional[str] = None,
) -> str:
    """
    Gera o conteúdo de um arquivo JS/TS/React/Vue/Angular via LLM.
    Usa prompts de PulsoCSA/JavaScript/prompts/creation/.
    """
    try:
        system_prompt = load_prompt("creation/system", stack="javascript")
        template = load_prompt("creation/code_creation", stack="javascript")
    except FileNotFoundError:
        return ""

    prompt_text = template.replace("{filename}", filename)
    prompt_text = prompt_text.replace("{refined_prompt}", refined_prompt[:1500])
    prompt_text = prompt_text.replace("{structure}", structure[:2000])
    prompt_text = prompt_text.replace("{file_context}", file_context[:500])
    prompt_text = prompt_text.replace("{backend}", backend[:500])
    prompt_text = prompt_text.replace("{security}", security[:500])

    client = get_openai_client()
    raw = ""
    # Qwen 2.5 Coder (use_fast_model=False) é especializado em código; Mistral é para interpretação
    use_fast = os.getenv("CODEGEN_JS_USE_FAST_MODEL", "0").lower() in ("1", "true", "yes")
    for attempt in range(3):
        try:
            raw = client.generate_text(
                prompt_text,
                system_prompt=system_prompt,
                use_fast_model=use_fast,
                num_predict=1536,
                timeout_override=CODEGEN_JS_TIMEOUT_SEC,
            )
            if raw and len(raw.strip()) > 20:
                break
        except Exception:
            if attempt < 2:
                time.sleep(CODEGEN_JS_RETRY_DELAY_SEC * (attempt + 1))
    if not raw:
        return ""
    content = _strip_markdown_code(raw)
    content = _strip_ollama_artifacts(content)
    # Rejeitar eco do prompt (LLM devolveu instruções em vez de código)
    if _looks_like_prompt_echo(content):
        return ""
    # index.tsx/jsx: rejeitar saída inválida
    if filename and "index" in filename and ("tsx" in filename or "jsx" in filename):
        if not _is_valid_index_content(content):
            return ""
    # *Form.tsx: rejeitar stub vazio e corrigir baseUrl para auth
    if filename and "form" in filename.lower() and ("tsx" in filename or "jsx" in filename):
        if not _is_valid_form_content(content):
            return ""
        content = _fix_auth_baseurl(content)
    # *Page.tsx: rejeitar stub vazio (preserva Page→Form)
    if filename and "page" in filename.lower() and ("tsx" in filename or "jsx" in filename):
        if not _is_valid_page_content(content):
            return ""
    # authService: rejeitar stub vazio e corrigir baseUrl (preserva função login)
    if filename and "auth" in filename.lower() and "service" in filename.lower():
        if not _is_valid_auth_service_content(content):
            return ""
        content = _fix_auth_baseurl(content)
    # App.tsx/App.jsx: validar e corrigir
    if filename and "App" in filename and ("tsx" in filename or "jsx" in filename):
        if not _is_valid_app_content(content):
            # LLM retornou saída truncada/corrompida (ex: "export default App" sem definir App) → rejeitar
            return ""
        if "export default" not in content:
            content = "\n".join(line for line in content.split("\n") if "ReactDOM.render" not in line)
            content = content.rstrip()
            if not content.endswith("export default"):
                content = content.rstrip()
                if content and not content.endswith(";"):
                    content += "\n"
                content += "\nexport default App\n"
    return content
