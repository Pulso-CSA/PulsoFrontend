#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Correção de Código JavaScript/TypeScript/React❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import re
import time
from typing import Optional

CORRECT_JS_TIMEOUT_SEC = int(os.getenv("CORRECT_JS_TIMEOUT_SEC", "120"))
CORRECT_JS_RETRY_DELAY_SEC = float(os.getenv("CORRECT_JS_RETRY_DELAY_SEC", "2"))

try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client
from app.prompts.loader import load_prompt


def _strip_markdown(raw: str) -> str:
    """Remove blocos markdown da saída do LLM."""
    if not raw or not raw.strip():
        return raw
    text = raw.strip()
    m = re.search(r"```(?:javascript|js|typescript|ts|tsx|jsx|vue)?\s*([\s\S]*?)\s*```", text)
    if m:
        return m.group(1).strip()
    return text


def _strip_ollama_artifacts(text: str) -> str:
    """Remove tokens que Ollama/Qwen injeta na saída (ex: <|fim_middle|>)."""
    if not text:
        return text
    for token in ("<|fim_middle|>", "<|im_end|>", "<|end|>", "<|eot_id|>"):
        text = text.replace(token, "")
    text = re.sub(r"<\|[^|]*\|>", "", text)
    return text.strip()


def correct_file_js(
    file_path: str,
    existing_source: str,
    prompt: str,
    project_root: str,
    language: str = "javascript",
    framework: Optional[str] = None,
) -> str:
    """
    Corrige o conteúdo de um arquivo JavaScript/TypeScript/React via LLM.
    Usa os prompts em PulsoCSA/JavaScript/prompts/correct/.
    """
    try:
        system_prompt = load_prompt("correct/implementation_system", stack="javascript")
        user_template = load_prompt("correct/implementation_user", stack="javascript")
    except FileNotFoundError:
        return existing_source

    user_prompt = user_template.replace("{project_root}", project_root)
    user_prompt = user_prompt.replace("{target_file}", file_path)
    user_prompt = user_prompt.replace("{reason}", prompt[:500])
    user_prompt = user_prompt.replace("{content_description}", prompt[:800])
    user_prompt = user_prompt.replace("{existing_source}", existing_source[:6000])
    user_prompt = user_prompt.replace("{frozen_section}", "Preserve exports, component names, and public API.")

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    client = get_openai_client()
    raw = ""
    for attempt in range(3):
        try:
            raw = client.generate_text(
                full_prompt,
                system_prompt=None,
                use_fast_model=False,
                num_predict=2048,
                timeout_override=CORRECT_JS_TIMEOUT_SEC,
            )
            if raw and len(raw.strip()) >= 20:
                break
        except Exception:
            if attempt < 2:
                time.sleep(CORRECT_JS_RETRY_DELAY_SEC * (attempt + 1))
    if not raw or len(raw.strip()) < 20:
        return existing_source
    return _strip_ollama_artifacts(_strip_markdown(raw))
