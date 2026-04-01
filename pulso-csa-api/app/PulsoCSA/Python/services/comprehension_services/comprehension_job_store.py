#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Jobs assíncronos – comprehension (evita timeout de proxy)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Armazena resultados de workflows longos disparados via ?async_mode=true.
O cliente recebe 202 + job_id e faz polling em GET .../jobs/{job_id}.
Nota: memória por processo — com vários workers, use sticky session ou um único worker.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, Optional


def _js_log(level: str, msg: str) -> None:
    try:
        from utils.log_manager import add_log
        add_log(level, msg, "comprehension_job_store")
    except Exception:
        try:
            from app.utils.log_manager import add_log
            add_log(level, msg, "comprehension_job_store")
        except Exception:
            pass

_MAX_JOBS = 2000
_TTL_SEC = 7200  # 2 h
_PRUNE_EVERY = 128


_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}
_prune_counter = 0


def _prune_locked() -> None:
    global _jobs
    now = time.time()
    if len(_jobs) <= _MAX_JOBS:
        stale = [jid for jid, j in _jobs.items() if now - j.get("created_at", 0) > _TTL_SEC]
        for jid in stale:
            _jobs.pop(jid, None)
        return
    # Por tamanho: remove os mais antigos primeiro
    ordered = sorted(_jobs.items(), key=lambda x: x[1].get("created_at", 0))
    while len(_jobs) > _MAX_JOBS and ordered:
        jid, _ = ordered.pop(0)
        _jobs.pop(jid, None)


def create_job(owner_sub: str, stack: str) -> str:
    """owner_sub: email ou id do utilizador autenticado. stack: 'python' | 'javascript'."""
    global _prune_counter
    job_id = str(uuid.uuid4())
    now = time.time()
    with _lock:
        _prune_counter += 1
        if _prune_counter >= _PRUNE_EVERY:
            _prune_counter = 0
            _prune_locked()
        _jobs[job_id] = {
            "status": "pending",
            "owner_sub": owner_sub,
            "stack": stack,
            "created_at": now,
            "updated_at": now,
            "response": None,
            "error": None,
        }
    own_h = (owner_sub or "")[:48] + ("…" if len(owner_sub or "") > 48 else "")
    _js_log("info", f"[job_store] create_job | job_id={job_id} | stack={stack} | owner={own_h!r} | n_jobs={len(_jobs)}")
    return job_id


def mark_running(job_id: str) -> None:
    now = time.time()
    with _lock:
        j = _jobs.get(job_id)
        if j:
            j["status"] = "running"
            j["updated_at"] = now
            _js_log("info", f"[job_store] mark_running | job_id={job_id} | stack={j.get('stack')}")
        else:
            _js_log("warning", f"[job_store] mark_running | job_id={job_id} | JOB_NOT_IN_STORE")


def mark_completed(job_id: str, response_dict: Dict[str, Any]) -> None:
    now = time.time()
    with _lock:
        j = _jobs.get(job_id)
        if j:
            j["status"] = "completed"
            j["response"] = response_dict
            j["error"] = None
            j["updated_at"] = now
            keys = list((response_dict or {}).keys())[:20]
            _js_log(
                "info",
                f"[job_store] mark_completed | job_id={job_id} | response_top_keys={keys} | "
                f"processing_time_ms={(response_dict or {}).get('processing_time_ms')}",
            )
        else:
            _js_log("warning", f"[job_store] mark_completed | job_id={job_id} | JOB_NOT_IN_STORE")


def mark_failed(job_id: str, code: str, message: str) -> None:
    now = time.time()
    with _lock:
        j = _jobs.get(job_id)
        if j:
            j["status"] = "failed"
            j["error"] = {"code": code, "message": message}
            j["response"] = None
            j["updated_at"] = now
            msg = (message or "")[:400]
            _js_log("error", f"[job_store] mark_failed | job_id={job_id} | code={code} | message={msg!r}")
        else:
            _js_log("warning", f"[job_store] mark_failed | job_id={job_id} | JOB_NOT_IN_STORE | code={code}")


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        j = _jobs.get(job_id)
        if not j:
            return None
        return dict(j)


def assert_job_owner(job_id: str, owner_sub: str) -> Optional[Dict[str, Any]]:
    """Retorna o job se existir e pertencer ao utilizador; senão None."""
    with _lock:
        j = _jobs.get(job_id)
        if not j:
            _js_log("info", f"[job_store] assert_job_owner | job_id={job_id} | result=NOT_FOUND | n_jobs={len(_jobs)}")
            return None
        if j.get("owner_sub") != owner_sub:
            _js_log(
                "info",
                f"[job_store] assert_job_owner | job_id={job_id} | result=OWNER_MISMATCH | "
                f"expected_owner={(owner_sub or '')[:32]!r}",
            )
            return None
        return dict(j)
