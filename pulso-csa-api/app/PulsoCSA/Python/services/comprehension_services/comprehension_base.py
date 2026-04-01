#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Base – Cache, confirmação, force_execute❯━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import hashlib
import json
import os
import re
import time
import threading
from typing import Any, Dict, Optional, Tuple

# Confirmação implícita: "sim", "ok", "pode ser", emojis
CONFIRM_PATTERNS = [
    re.compile(r"^(sim|s|ok|oki|pode\s+ser|vai|bora|executa|faça|faca|yes|y)\s*$", re.IGNORECASE),
    re.compile(r"^(👍|✅|✓|vamos)\s*$"),
]
EXECUTE_SIGNAL_KEYWORDS = re.compile(
    r"\b(faça|faca|fazer|executar|execute|aplicar|aplique|implementar|implemente|rode|rodar)\b",
    re.IGNORECASE,
)

INTENT_CACHE_TTL_SEC = int(os.getenv("COMPREHENSION_INTENT_CACHE_TTL_SEC", "300"))
INTENT_CACHE_MAX_SIZE = 500
_intent_caches: Dict[str, Dict[str, Tuple[float, str, float]]] = {}  # namespace -> cache
_intent_cache_lock = threading.Lock()


def prompt_cache_key(prompt: str, usuario: str | None = None, namespace: str = "default") -> str:
    """Chave de cache: hash normalizado + usuario para isolamento multiusuário."""
    text = (prompt or "").strip().lower()[:1000]
    u = (usuario or "default").strip()
    return hashlib.sha256(f"{namespace}|{text}|{u}".encode("utf-8")).hexdigest()


def intent_cache_get(key: str, namespace: str = "default") -> Tuple[str, float] | None:
    with _intent_cache_lock:
        cache = _intent_caches.setdefault(namespace, {})
        now = time.time()
        if key not in cache:
            return None
        ts, intent, confidence = cache[key]
        if now - ts > INTENT_CACHE_TTL_SEC:
            del cache[key]
            return None
        return (intent, confidence)


def intent_cache_set(key: str, intent: str, confidence: float, namespace: str = "default") -> None:
    with _intent_cache_lock:
        cache = _intent_caches.setdefault(namespace, {})
        if len(cache) >= INTENT_CACHE_MAX_SIZE:
            by_ts = sorted(cache.items(), key=lambda x: x[1][0])
            for k, _ in by_ts[: INTENT_CACHE_MAX_SIZE // 2]:
                del cache[k]
        cache[key] = (time.time(), intent, confidence)


def detect_execute_signal(prompt: str) -> bool:
    """Detecta sinal de execução: verbo imperativo ou confirmação implícita."""
    if not prompt or not prompt.strip():
        return False
    text = prompt.strip()
    if EXECUTE_SIGNAL_KEYWORDS.search(text):
        return True
    for pat in CONFIRM_PATTERNS:
        if pat.search(text):
            return True
    return False


def parse_intent_json(raw: str) -> dict | None:
    raw = (raw or "").strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            raw = m.group(1)
    m = re.search(r"\{[^{}]*\"intent\"[^{}]*\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def build_module_decision(
    module: str,
    intent: str,
    target_endpoint: str | None,
    should_execute: bool,
    explanation: str,
    next_action: str,
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Retorna dict padronizado de decisão de roteamento."""
    out: Dict[str, Any] = {
        "module": module,
        "intent": intent,
        "target_endpoint": target_endpoint,
        "should_execute": should_execute,
        "explanation": explanation,
        "next_action": next_action,
    }
    if extra:
        out.update(extra)
    return out
