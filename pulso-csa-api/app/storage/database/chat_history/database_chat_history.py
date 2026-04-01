#━━━━━━━━━❮Database Chat History❯━━━━━━━━━
"""Histórico de chats por tenant + módulo."""
import anyio
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.storage.database.database_core import get_collection

chat_history_collection = get_collection("chat_history")

try:
    chat_history_collection.create_index([("tenant_id", 1), ("service_id", 1), ("session_id", 1)])
    chat_history_collection.create_index([("tenant_id", 1), ("service_id", 1), ("timestamp", -1)])
except Exception:
    pass


async def _run_sync(fn, *args, **kwargs):
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))


async def save_chat_message(
    tenant_id: str,
    usuario_id: str,
    service_id: str,
    session_id: str,
    mensagem_user: str,
    mensagem_assistant: str,
    dataset_ref: Optional[str] = None,
    model_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """Salva uma mensagem no histórico de chat. Cada session_id = um chat isolado."""
    doc = {
        "tenant_id": tenant_id,
        "usuario_id": usuario_id,
        "service_id": service_id,
        "session_id": session_id,
        "timestamp": datetime.utcnow(),
        "mensagem_user": mensagem_user[:10000] if mensagem_user else "",
        "mensagem_assistant": mensagem_assistant[:10000] if mensagem_assistant else "",
    }
    if dataset_ref:
        doc["dataset_ref"] = dataset_ref[:2048]
    if model_ref:
        doc["model_ref"] = model_ref[:2048]

    def _insert():
        r = chat_history_collection.insert_one(doc)
        doc["_id"] = str(r.inserted_id)
        return doc

    return await _run_sync(_insert)


async def list_chat_history(
    tenant_id: str,
    service_id: str,
    session_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Lista histórico de chat por tenant + service. Opcionalmente por session_id."""
    query = {"tenant_id": tenant_id, "service_id": service_id}
    if session_id:
        query["session_id"] = session_id
    cursor = chat_history_collection.find(query).sort("timestamp", -1).limit(limit)
    docs = list(await _run_sync(lambda: list(cursor)))
    for d in docs:
        d["_id"] = str(d.get("_id", ""))
        if isinstance(d.get("timestamp"), datetime):
            d["timestamp"] = d["timestamp"].isoformat()
    return docs


async def list_sessions(
    tenant_id: str,
    service_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Lista chats (sessions) do tenant para o service. Cada session = um chat isolado."""
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "service_id": service_id}},
        {"$sort": {"timestamp": -1}},
        {
            "$group": {
                "_id": "$session_id",
                "last_timestamp": {"$first": "$timestamp"},
                "last_mensagem_user": {"$first": "$mensagem_user"},
                "dataset_ref": {"$first": "$dataset_ref"},
                "model_ref": {"$first": "$model_ref"},
            }
        },
        {"$sort": {"last_timestamp": -1}},
        {"$limit": limit},
        {
            "$project": {
                "session_id": "$_id",
                "last_timestamp": 1,
                "last_mensagem_user": 1,
                "dataset_ref": 1,
                "model_ref": 1,
                "_id": 0,
            }
        },
    ]

    def _agg():
        return list(chat_history_collection.aggregate(pipeline))

    result = await _run_sync(_agg)
    for r in result:
        if isinstance(r.get("last_timestamp"), datetime):
            r["last_timestamp"] = r["last_timestamp"].isoformat()
        if r.get("last_mensagem_user") and len(r["last_mensagem_user"]) > 80:
            r["last_mensagem_user"] = r["last_mensagem_user"][:77] + "..."
    return result
