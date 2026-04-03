#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Gerenciador de Logs da Aplicação❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import sys
import datetime
import threading
from contextvars import ContextVar
from typing import List, Dict, Optional

from utils.log_sanitizer import sanitizar_log

LOG_STORE: List[Dict] = []
LOG_STORE_LOCK = threading.Lock()
# Limite para multi-usuário: evita OOM com muitos requests (rotação: remove os mais antigos).
LOG_STORE_MAX_ENTRIES = int(os.getenv("LOG_STORE_MAX_ENTRIES", "10000"))

# ContextVar para request_id (definido pelo middleware)
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(request_id: str) -> None:
    """Define o request_id atual (chamado pelo middleware)."""
    _request_id_ctx.set(request_id)


def add_log(level: str, message: str, source: str, request_id: Optional[str] = None):
    """Adiciona um log à memória com timestamp e imprime no console. Inclui request_id quando disponível."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    rid = request_id or _request_id_ctx.get() or ""
    message_sanitized = sanitizar_log(str(message))
    log_msg = f"[request_id={rid}] {message_sanitized}" if rid else message_sanitized
    with LOG_STORE_LOCK:
        LOG_STORE.append({
            "timestamp": ts,
            "level": level.lower(),
            "message": message_sanitized,
            "source": source,
            "request_id": rid or None,
        })
        if len(LOG_STORE) > LOG_STORE_MAX_ENTRIES:
            del LOG_STORE[: LOG_STORE_MAX_ENTRIES // 2]
    level_tag = level.upper()[:5]
    line = f"[{ts}] [{level_tag}] [{source}] {log_msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        try:
            print(line.encode(enc, errors="replace").decode(enc, errors="replace"))
        except Exception:
            print(line.encode("ascii", errors="replace").decode("ascii"))


def get_logs(filter_level: str = None, filter_source: str = None) -> List[Dict]:
    """Retorna os logs armazenados, com filtro opcional por nível e/ou source. Thread-safe."""
    with LOG_STORE_LOCK:
        result = list(LOG_STORE)
    if filter_level and filter_level.lower() != "todos":
        result = [log for log in result if log["level"] == filter_level.lower()]
    if filter_source:
        result = [log for log in result if log["source"] == filter_source.lower()]
    return result


def clear_logs(source: str = None):
    """Limpa os logs da memória. Se source for informado, remove apenas logs daquele source. Thread-safe."""
    global LOG_STORE
    with LOG_STORE_LOCK:
        if source:
            LOG_STORE = [log for log in LOG_STORE if log["source"] != source.lower()]
        else:
            LOG_STORE.clear()
