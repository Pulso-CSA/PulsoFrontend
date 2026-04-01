import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING

from app.storage.database.database_core import get_collection, timestamp
from app.utils.log_manager import add_log

SOURCE = "insights_storage"


class InsightsRepository:
    """
    Persistência modular: sessões, prompts e artefatos gerados (insights/gráficos).
    Evolui para sharding/partições sem mudar a interface pública.
    """

    def __init__(self) -> None:
        self._indexes_ok = False

    def _ensure_indexes(self) -> None:
        if self._indexes_ok:
            return
        try:
            sess = get_collection("insights_sessions")
            pr = get_collection("insights_prompts")
            gen = get_collection("insights_generated")
            if hasattr(sess, "create_index"):
                sess.create_index([("tenant_id", ASCENDING), ("updated_at", DESCENDING)])
                sess.create_index("session_id")
            if hasattr(pr, "create_index"):
                pr.create_index([("session_id", ASCENDING), ("created_at", DESCENDING)])
                pr.create_index("tenant_id")
            if hasattr(gen, "create_index"):
                gen.create_index([("session_id", ASCENDING), ("created_at", DESCENDING)])
                gen.create_index("insight_id")
            self._indexes_ok = True
        except Exception as e:
            add_log("warning", f"Insights indexes: {type(e).__name__}", SOURCE)

    def create_session(self, tenant_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_indexes()
        session_id = uuid.uuid4().hex
        now = timestamp()
        doc = {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "title": title or "Sessão Insights",
            "created_at": now,
            "updated_at": now,
        }
        get_collection("insights_sessions").insert_one(doc)
        return doc

    def touch_session(self, session_id: str, tenant_id: str) -> None:
        self._ensure_indexes()
        get_collection("insights_sessions").update_one(
            {"session_id": session_id, "tenant_id": tenant_id},
            {"$set": {"updated_at": timestamp()}},
        )

    def get_session(self, session_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_indexes()
        return get_collection("insights_sessions").find_one({"session_id": session_id, "tenant_id": tenant_id})

    def list_sessions(self, tenant_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        self._ensure_indexes()
        cur = (
            get_collection("insights_sessions")
            .find({"tenant_id": tenant_id})
            .sort("updated_at", DESCENDING)
            .limit(limit)
        )
        return list(cur)

    def insert_prompt(
        self,
        *,
        tenant_id: str,
        session_id: str,
        prompt_text: str,
        id_requisicao: Optional[str],
        intent_snapshot: Dict[str, Any],
    ) -> str:
        self._ensure_indexes()
        pid = uuid.uuid4().hex
        doc = {
            "prompt_id": pid,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "prompt_text": prompt_text[:8000],
            "id_requisicao": id_requisicao,
            "intent_snapshot": intent_snapshot,
            "created_at": timestamp(),
        }
        get_collection("insights_prompts").insert_one(doc)
        self.touch_session(session_id, tenant_id)
        return pid

    def insert_insight_artifact(
        self,
        *,
        tenant_id: str,
        session_id: str,
        prompt_id: str,
        payload: Dict[str, Any],
    ) -> str:
        self._ensure_indexes()
        iid = str(payload.get("insight_id") or "").strip() or uuid.uuid4().hex
        doc = {
            "insight_id": iid,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "prompt_id": prompt_id,
            "chart_type": payload.get("chart_type"),
            "title": payload.get("title"),
            "payload": payload,
            "created_at": timestamp(),
        }
        get_collection("insights_generated").insert_one(doc)
        self.touch_session(session_id, tenant_id)
        return iid

    def list_prompts_for_session(self, session_id: str, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        self._ensure_indexes()
        cur = (
            get_collection("insights_prompts")
            .find({"session_id": session_id, "tenant_id": tenant_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return list(cur)

    def list_insights_for_session(self, session_id: str, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        self._ensure_indexes()
        cur = (
            get_collection("insights_generated")
            .find({"session_id": session_id, "tenant_id": tenant_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return list(cur)
