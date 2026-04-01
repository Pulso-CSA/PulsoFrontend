#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Database❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import anyio
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime
from pymongo import DESCENDING
from app.storage.database.database_core import get_collection

profiles_collection = get_collection("profiles")


def _to_iso_date(val: Any) -> str:
    """Converte valor para ISO 8601 (YYYY-MM-DDTHH:mm:ss.sssZ) compatível com JavaScript Date."""
    if val is None:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if isinstance(val, datetime):
        ms = int(val.microsecond / 1000)
        return val.strftime(f"%Y-%m-%dT%H:%M:%S.{ms:03d}Z")
    if isinstance(val, (int, float)):
        try:
            return datetime.utcfromtimestamp(val).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except (ValueError, OSError):
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if isinstance(val, str) and val:
        if val.endswith("Z") or "+" in val[-6:] or "T" in val:
            return val
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")


# Criar índices
try:
    profiles_collection.create_index([("user_email", 1), ("created_at", -1)])
except Exception:
    pass

async def _run_sync(fn, *args, **kwargs):
    """Run blocking pymongo calls without blocking the event loop."""
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))

async def get_profiles_by_user_email(user_email: str) -> List[Dict[str, Any]]:
    """Busca todos os perfis de um usuário."""

    def _fetch():
        cursor = profiles_collection.find(
            {"user_email": user_email}
        ).sort("created_at", DESCENDING)
        return list(cursor)

    profiles = await _run_sync(_fetch)
    for profile in profiles:
        profile["id"] = str(profile["_id"])
        profile["created_at"] = _to_iso_date(profile.get("created_at") or profile.get("createdAt"))
        profile["updated_at"] = _to_iso_date(profile.get("updated_at") or profile.get("updatedAt"))
    return profiles

async def create_profile(user_email: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Cria um novo perfil."""
    now = datetime.utcnow()
    doc = {
        "user_email": user_email,
        "name": name,
        "description": description or "",
        "created_at": now,
        "updated_at": now
    }
    result = await _run_sync(profiles_collection.insert_one, doc)
    doc["id"] = str(result.inserted_id)
    doc["created_at"] = _to_iso_date(doc["created_at"])
    doc["updated_at"] = _to_iso_date(doc["updated_at"])
    return doc

async def get_profile_by_id(profile_id: str, user_email: str) -> Optional[Dict[str, Any]]:
    """Busca um perfil específico do usuário."""
    if not profile_id or not ObjectId.is_valid(profile_id):
        return None
    try:
        profile = await _run_sync(
            profiles_collection.find_one,
            {"_id": ObjectId(profile_id), "user_email": user_email}
        )
        if profile:
            profile["id"] = str(profile["_id"])
            profile["created_at"] = _to_iso_date(profile.get("created_at") or profile.get("createdAt"))
            profile["updated_at"] = _to_iso_date(profile.get("updated_at") or profile.get("updatedAt"))
        return profile
    except Exception:
        return None

async def update_profile(profile_id: str, user_email: str, name: str, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Atualiza um perfil."""
    if not profile_id or not ObjectId.is_valid(profile_id):
        return None
    try:
        update_data = {
            "$set": {
                "name": name,
                "description": description or "",
                "updated_at": datetime.utcnow()
            }
        }
        result = await _run_sync(
            profiles_collection.update_one,
            {"_id": ObjectId(profile_id), "user_email": user_email},
            update_data
        )
        if result.modified_count > 0:
            return await get_profile_by_id(profile_id, user_email)
        return None
    except Exception:
        return None

async def delete_profile(profile_id: str, user_email: str) -> bool:
    """Deleta um perfil."""
    if not profile_id or not ObjectId.is_valid(profile_id):
        return False
    try:
        result = await _run_sync(
            profiles_collection.delete_one,
            {"_id": ObjectId(profile_id), "user_email": user_email}
        )
        return result.deleted_count > 0
    except Exception:
        return False

async def count_profiles_by_user_email(user_email: str) -> int:
    """Conta quantos perfis um usuário tem."""
    count = await _run_sync(
        profiles_collection.count_documents,
        {"user_email": user_email}
    )
    return count

