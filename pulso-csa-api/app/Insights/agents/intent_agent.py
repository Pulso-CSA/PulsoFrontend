import os
from typing import Any, Dict, Optional

from app.core.ollama.ollama_client import get_ollama_client
from app.utils.log_manager import add_log

from Insights.prompts.intent_prompts import INTENT_SYSTEM_PROMPT, build_intent_user_prompt
from Insights.utils.json_extract import extract_json_object

SOURCE = "insights_intent_agent"


def _use_ollama() -> bool:
    return os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes")


def classify_intent_with_ollama(user_prompt: str) -> Optional[Dict[str, Any]]:
    """
    Chama Ollama (modelo de interpretação) e devolve dict parseado ou None se indisponível/ inválido.
    """
    if not _use_ollama():
        add_log("info", "Insights: USE_OLLAMA desligado — intent via Ollama ignorado", SOURCE)
        return None
    try:
        client = get_ollama_client()
        raw = client.generate_text(
            build_intent_user_prompt(user_prompt),
            system_prompt=INTENT_SYSTEM_PROMPT,
            use_fast_model=True,
            num_predict=256,
        )
    except Exception as e:
        add_log("error", f"Insights Ollama intent falhou: {type(e).__name__}", SOURCE)
        return None
    if not raw or raw.startswith("Erro"):
        add_log("warning", "Insights: resposta Ollama vazia ou erro textual", SOURCE)
        return None
    parsed = extract_json_object(raw)
    if not parsed:
        add_log("warning", "Insights: JSON de intent não extraído da resposta LLM", SOURCE)
    return parsed
