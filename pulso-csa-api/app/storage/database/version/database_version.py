#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Version Database❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import anyio
from typing import Optional, Dict, Any
from datetime import datetime
from app.storage.database.database_core import get_collection

# Collection para versões do app (Electron)
app_versions_collection = get_collection("app_versions")

# Índice por plataforma
try:
    app_versions_collection.create_index("platform", unique=True)
except Exception:
    pass

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Async wrappers❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


async def _run_sync(fn, *args, **kwargs):
    """Run blocking pymongo calls without blocking the event loop."""
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Version CRUD❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


async def get_version_by_platform(platform: str) -> Optional[Dict[str, Any]]:
    """Busca versão por plataforma (win, mac, linux)."""
    doc = await _run_sync(
        app_versions_collection.find_one,
        {"platform": platform},
    )
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id", ""))
    if "updatedAt" in doc and hasattr(doc["updatedAt"], "isoformat"):
        doc["updatedAt"] = doc["updatedAt"].isoformat()
    return doc


async def upsert_version(
    platform: str,
    min_client_version: str,
    latest_version: str,
    release_notes: Optional[str] = None,
    force_upgrade: bool = False,
    download_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Cria ou atualiza registro de versão para a plataforma."""
    now = datetime.utcnow()
    doc = {
        "platform": platform,
        "minClientVersion": min_client_version,
        "latestVersion": latest_version,
        "releaseNotes": release_notes,
        "forceUpgrade": force_upgrade,
        "downloadUrl": download_url,
        "updatedAt": now,
    }
    await _run_sync(
        app_versions_collection.update_one,
        {"platform": platform},
        {"$set": doc},
        upsert=True,
    )
    doc["updatedAt"] = now.isoformat()
    return doc
