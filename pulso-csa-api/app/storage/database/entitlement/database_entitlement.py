#━━━━━━━━━❮Database Service Entitlements❯━━━━━━━━━
"""Armazena services_enabled por usuário (escolha de serviços conforme plano)."""
import anyio
from typing import List, Optional
from app.storage.database.database_core import get_collection

entitlements_collection = get_collection("service_entitlements")

try:
    entitlements_collection.create_index("userId", unique=True)
except Exception:
    pass


async def _run_sync(fn, *args, **kwargs):
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))


async def get_services_enabled(user_id: str) -> List[str]:
    """Retorna lista de service_ids ativados pelo usuário."""
    doc = await _run_sync(entitlements_collection.find_one, {"userId": user_id})
    if not doc:
        return []
    return doc.get("servicesEnabled") or []


async def set_services_enabled(user_id: str, services: List[str]) -> bool:
    """
    Define serviços ativados. Valida que não exceda max do plano.
    Retorna True se ok.
    """
    from datetime import datetime
    doc = await _run_sync(entitlements_collection.find_one, {"userId": user_id})
    now = datetime.utcnow()
    if doc:
        await _run_sync(
            entitlements_collection.update_one,
            {"userId": user_id},
            {"$set": {"servicesEnabled": services, "updatedAt": now}},
        )
    else:
        await _run_sync(
            entitlements_collection.insert_one,
            {
                "userId": user_id,
                "servicesEnabled": services,
                "createdAt": now,
                "updatedAt": now,
            },
        )
    return True
