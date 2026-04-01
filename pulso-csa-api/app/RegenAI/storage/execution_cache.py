from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from RegenAI.models.regen_report import RegenReport
from RegenAI.models.regen_request import RegenRequest
from RegenAI.models.regen_status import RegenStatus


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionCache:
    def __init__(self) -> None:
        self._status_map: Dict[str, RegenStatus] = {}
        self._log_map: Dict[str, List[Dict[str, Any]]] = {}
        self._report_map: Dict[str, RegenReport] = {}
        self._live_results_map: Dict[str, List[Dict[str, Any]]] = {}
        self._exception_questions_map: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = Lock()

    def create_execution(self, execution_id: str, req: RegenRequest) -> RegenStatus:
        status = RegenStatus(
            execution_id=execution_id,
            status="queued",
            objective=req.objective,
            scopes=req.scopes,
            max_rounds=req.max_rounds,
            started_at=_utc_now(),
            updated_at=_utc_now(),
        )
        with self._lock:
            self._status_map[execution_id] = status
            self._log_map[execution_id] = []
            self._live_results_map[execution_id] = []
            self._exception_questions_map[execution_id] = []
        return status

    def get_status(self, execution_id: str) -> Optional[RegenStatus]:
        with self._lock:
            return self._status_map.get(execution_id)

    def update_status(self, execution_id: str, **kwargs: Any) -> Optional[RegenStatus]:
        with self._lock:
            status = self._status_map.get(execution_id)
            if status is None:
                return None
            payload = status.model_dump()
            payload.update(kwargs)
            payload["updated_at"] = _utc_now()
            updated = RegenStatus(**payload)
            self._status_map[execution_id] = updated
            return updated

    def add_round(self, execution_id: str, round_data: Dict[str, Any]) -> None:
        with self._lock:
            status = self._status_map.get(execution_id)
            if status is None:
                return
            rounds = list(status.rounds)
            rounds.append(round_data)
            updated = status.model_copy(update={"rounds": rounds, "updated_at": _utc_now()})
            self._status_map[execution_id] = updated

    def append_log(self, execution_id: str, level: str, message: str, source: str = "regenai") -> None:
        entry = {
            "timestamp": _utc_now(),
            "level": level,
            "source": source,
            "message": message,
        }
        with self._lock:
            self._log_map.setdefault(execution_id, []).append(entry)

    def get_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._log_map.get(execution_id, []))

    def append_live_result(self, execution_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            self._live_results_map.setdefault(execution_id, []).append(result)

    def get_live_results(self, execution_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._live_results_map.get(execution_id, []))

    def add_exception_question(self, execution_id: str, item: Dict[str, Any]) -> None:
        with self._lock:
            entries = self._exception_questions_map.setdefault(execution_id, [])
            if any(
                (x.get("question") == item.get("question") and x.get("source_file") == item.get("source_file"))
                for x in entries
            ):
                return
            entries.append(item)

    def get_exception_questions(self, execution_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._exception_questions_map.get(execution_id, []))

    def set_report(self, execution_id: str, report: RegenReport) -> None:
        with self._lock:
            self._report_map[execution_id] = report

    def get_report(self, execution_id: str) -> Optional[RegenReport]:
        with self._lock:
            return self._report_map.get(execution_id)


execution_cache = ExecutionCache()

