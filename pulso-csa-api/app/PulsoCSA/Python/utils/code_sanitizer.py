#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Sanitização de código gerado por LLM❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Módulo para limpar e extrair código válido da saída do LLM.
Remove eco, explicações, conteúdo de outros arquivos e artefatos.
"""
import re
from typing import List


# Padrões de eco/explicação (linhas a ignorar no início)
_ECHO_START_PATTERNS = (
    "tip:", "exemplo:", "relatório", "certifique-se", "seu objetivo é",
    "agora, a partir", "o código acima", "você pode modificar", "para api rest",
    "este é o conteúdo completo", "não repita", "gere o conteúdo",
    "podem estar erradas", "estão erradas as seguintes",
    "resumo da segurança", "resumo do backend", "estrutura do projeto",
    "contexto do arquivo", "contexto do arquivo:", "não inclua", "não adicione",
    "o programa deve conter", "responda apenas", "responda \"ok\"",
    "prompt feito", "recebo demais", "sua resposta vai ser",
    "regras gerais:", "formato da saída:", "neste código", "em seguida, usamos",
    "arquivo gerado", "arquivo gerado:",
    "pontos importante", "ponto importante", "importante para ponto de entrada",
    "retorne um json", "importe todos routers", "registre em app",
    "atenção ao respeitar", "não use markdown", "não retorne nada diferente",
    "o resultado deve conter", "nunca inclua texto explicativo",
    "nunca concatene código", "não use comentários", "obrigado!",
    "a seguir está a estrutura", "estrutura desejada para o arquivo",
    "retorne um ponto de entrada", "retorne como main.py",
)

# Padrões que indicam fim do código e início de explicação
_ECHO_END_PATTERNS = (
    "tip:", "exemplo:", "tip ", "exemplo ",
    "esse código segue", "você pode modificar", "o código acima é",
    "este é o conteúdo", "certifique-se de", "não repita",
    "podem estar erradas", "estão erradas as seguintes",
    "agora, a partir", "gere o conteúdo",
    "resumo da segurança", "estrutura do projeto", "contexto do arquivo",
    "neste código, criamos", "para evitar erros de segurança",
    "este se torna uma boa prática", "recomendo criar",
    "### definição", "### estrutura", "### atributos",
    "### arquivos:", "aqui, estou usando", "a classe user herda",
    "o método __init__ define", "armazena uma string",
)


def _get_target_basename(target_filename: str) -> str:
    """Retorna o nome base do arquivo alvo para comparação."""
    target_lower = target_filename.lower().replace("\\", "/")
    return target_lower.split("/")[-1] if "/" in target_lower else target_lower


def _is_other_file_marker(line: str, target_filename: str) -> bool:
    """True se a linha for marcador de outro arquivo (ex: # routes/login.py quando alvo é cadastro.py)."""
    s = line.strip()
    target_name = _get_target_basename(target_filename)
    # Comentário com path de arquivo (# config/settings.py, # models/user_model.py, etc.)
    if s.startswith("#"):
        s = s[1:].strip().lower().replace("\\", "/")
        if "/" in s or "\\" in s:
            parts = s.split("/") if "/" in s else s.split("\\")
            if parts:
                other_name = parts[-1].strip()
                if other_name and other_name != target_name:
                    return True
        for other in ("main.py", "requirements.txt", "settings.py", "user_model.py", "auth_router.py",
                      "calculator_router.py", "auth_service.py", "calculator_service.py", "test_auth.py", "test_calculator.py"):
            if s.startswith(other) and target_name != other:
                return True
        if "este é o conteúdo" in s or "não repita" in s:
            return True
    # Linha que é só nome de outro arquivo (ex: "# config/settings.py" ou "config/settings.py")
    s_lower = s.lower()
    for prefix in ("config/", "models/", "routers/", "services/", "tests/"):
        if s_lower.startswith(prefix) and target_name not in s_lower:
            return True
    # Bloco "### Arquivos:" ou "### Conteúdo:" — lista de outros arquivos
    if s.startswith("###") and ("arquivos" in s_lower or "conteúdo" in s_lower or "conteudo" in s_lower):
        return True
    # Separador "---" entre snippets de arquivos (corta aqui)
    if s == "---" or s.strip() == "---":
        return True
    # Lista numerada de outros arquivos: "1. **config/settings.py**", "2. models/..."
    if re.match(r"^\d+\.\s*(\*\*)?[\w/.-]+", s):
        for folder in ("config/", "models/", "routers/", "services/", "tests/"):
            if folder in s and target_name not in s:
                return True
    return False


def _is_same_file_marker(line: str, target_filename: str) -> bool:
    """True se a linha for marcador do próprio arquivo (ex: # routes/cadastro.py para cadastro.py)."""
    s = line.strip()
    if not s.startswith("#"):
        return False
    s = s[1:].strip().lower().replace("\\", "/")
    target_name = target_filename.lower().replace("\\", "/").split("/")[-1]
    if "routes/" in s:
        parts = s.split("/")
        if len(parts) >= 2:
            return parts[-1].strip() == target_name
    return s.strip() == target_name


def extract_single_file_content(raw: str, target_filename: str) -> str:
    """
    Extrai apenas o conteúdo do arquivo alvo.
    Corta quando detecta marcador de outro arquivo (# routes/xxx, # main.py, etc.).
    Ignora marcador do próprio arquivo na primeira linha.
    """
    if not raw or not raw.strip():
        return raw
    lines = raw.splitlines()
    result_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            result_lines.append(line)
            continue
        if _is_other_file_marker(line, target_filename):
            if result_lines:
                break
            continue  # Pula marcador de outro arquivo no início
        if _is_same_file_marker(line, target_filename) and not result_lines:
            continue
        result_lines.append(line)
    return "\n".join(result_lines).strip()


def _strip_leading_json_echo(lines: List[str]) -> List[str]:
    """Remove blocos iniciais que são eco de JSON (Resumo da segurança: {...})."""
    result = []
    in_json_block = False
    brace_depth = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            if not in_json_block:
                result.append(line)
            continue
        # Início de bloco JSON eco
        if ("resumo" in s.lower() and "{" in s) or ("estrutura" in s.lower() and "{" in s):
            in_json_block = True
            brace_depth = s.count("{") - s.count("}")
            continue
        if in_json_block:
            brace_depth += s.count("{") - s.count("}")
            if brace_depth <= 0:
                in_json_block = False
            continue
        result.append(line)
    return result


def strip_echo_and_explanations(text: str, target_filename: str = "") -> str:
    """
    Remove blocos de eco/explicação no início e no final.
    Mantém apenas o código Python/texto válido.
    """
    if not text or not text.strip():
        return text
    lines = _strip_leading_json_echo(text.splitlines())
    start_idx = 0
    target_base = _get_target_basename(target_filename) if target_filename else ""
    # Detectar e pular blocos de eco restantes (Resumo da segurança: {...}, Estrutura do projeto: {...})
    for i, line in enumerate(lines):
        s = line.strip().lower()
        if not s:
            continue
        # Eco de nome do arquivo: "auth_service.py" ou "user_model.py:"
        if target_base and (s == target_base or s == target_base + ":" or s.startswith(target_base + ":")):
            continue
        # Eco de prompt: linha que parece início de JSON ou instrução
        if (s.startswith("resumo ") or s.startswith("estrutura ") or s.startswith("contexto ")
            or s.startswith("regras gerais") or s.startswith("formato da saída")
            or s.startswith("arquivo gerado") or s.startswith("arquivo gerado:")
            or "vulnerabilidades_potenciais" in s or "recomendacoes" in s):
            continue
        if s.startswith("{") and ("vulnerabilidades" in s or "recomendacoes" in s or "checklist" in s):
            continue
        # Blocos ### Arquivos: ou ### Conteúdo: (lista de outros arquivos)
        if s.startswith("###") and ("arquivos" in s or "conteúdo" in s or "conteudo" in s):
            continue
        if (s.startswith("#━━") or s.startswith("import ") or s.startswith("from ") or
            s.startswith("def ") or s.startswith("class ") or s.startswith("@") or
            s.startswith("if __name__") or s.startswith("async def ")):
            start_idx = i
            break
        if any(p in s[:80] for p in _ECHO_START_PATTERNS):
            continue
        if "def " in s or "class " in s or "import " in s:
            start_idx = i
            break
        start_idx = i
        break

    trimmed = lines[start_idx:]
    end_idx = len(trimmed)
    for i, line in enumerate(trimmed):
        s = line.strip().lower()
        if not s:
            continue
        if any(p in s for p in _ECHO_END_PATTERNS):
            end_idx = i
            break
    return "\n".join(trimmed[:end_idx]).strip()


def remove_duplicate_definitions(text: str) -> str:
    """
    Remove definições duplicadas (mesma função/classe repetida).
    Corta no segundo "def X" ou "class X" já visto.
    """
    if not text or not text.strip():
        return text
    lines = text.splitlines()
    seen_defs = set()
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def "):
            name = stripped.split("(")[0].replace("def ", "").strip()
            if name in seen_defs:
                break
            seen_defs.add(name)
        elif stripped.startswith("class "):
            name = stripped.split("(")[0].replace("class ", "").split(":")[0].strip()
            if name in seen_defs:
                break
            seen_defs.add(name)
        result.append(line)
    return "\n".join(result).strip()


def strip_ollama_artifacts(text: str) -> str:
    """Remove tokens/artefatos que o Ollama injeta na saída."""
    if not text:
        return text
    t = text
    for artifact in ("<|fim_middle|>", "<|im_end|>", "<|end|>", "<|eot_id|>"):
        t = t.replace(artifact, "").strip()
    return t.strip()


def strip_code_fences(text: str) -> str:
    """Remove ```python e ``` de blocos gerados pela LLM."""
    if not text:
        return text
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
    if t.endswith("```"):
        t = t.rsplit("\n", 1)[0]
    return t.replace("```python", "").replace("```", "").strip()


def sanitize_requirements_txt(raw: str) -> str:
    """
    Extrai apenas linhas válidas de requirements.txt.
    Remove código Python, variáveis, atribuições e mantém só package specs.
    """
    if not raw or not raw.strip():
        return raw
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        # Ignora comentários longos
        if s.startswith("#") and len(s) > 80:
            continue
        # Remove linhas que são código Python (não package names como flask, fastapi)
        if any(x in s.lower() for x in (
            "def ", "class ", "if __name__", "print(", "from . import",
            "import ", "from ", " = ", "app.", "sessionmaker", "declarative_base",
            "optional", "field", "sessionlocal", "passwordbearer", "sessionmaker(",
            "oauth2", "getenv(", "os.getenv",
        )):
            continue
        # Rejeita atribuições Python ( = ) mas aceita package==1.0
        clean_pre = s.split("#")[0].strip()
        if " = " in clean_pre or clean_pre.startswith("="):
            continue
        # Linha válida: -r / -e / -- ou package[==versão]
        if s.startswith("-r ") or s.startswith("-e ") or s.startswith("--"):
            lines.append(s)
            continue
        clean = s.split("#")[0].strip()
        if clean and len(clean) < 80 and re.match(r"^[a-zA-Z0-9_.-]+([=<>!]+[\d.]*)?$", clean):
            lines.append(clean)
    return "\n".join(lines).strip()


def sanitize_generated_code(raw: str, target_filename: str) -> str:
    """
    Pipeline completo de sanitização.
    Aplica: fences → artifacts → single file → echo strip → duplicates.
    Para requirements.txt: sanitização específica.
    """
    if not raw or not raw.strip():
        return raw
    t = strip_code_fences(raw)
    t = strip_ollama_artifacts(t)
    fn_lower = target_filename.lower()
    if fn_lower == "requirements.txt":
        return sanitize_requirements_txt(t)
    t = extract_single_file_content(t, target_filename)
    t = strip_echo_and_explanations(t, target_filename)
    t = remove_duplicate_definitions(t)
    return t.strip()
