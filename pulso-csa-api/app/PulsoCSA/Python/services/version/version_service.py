#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Version Service❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import os
from typing import Optional
from models.version_models.version_models import VersionResponse, VersionUpdateRequest
# version está em api/app/storage/database/version/ (compartilhado)
try:
    from storage.database.version.database_version import get_version_by_platform, upsert_version
except ImportError:
    from app.storage.database.version.database_version import get_version_by_platform, upsert_version

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Config❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

USE_VERSION_DB = os.getenv("USE_VERSION_DB", "").strip().lower() in ("1", "true", "yes")
_VERSION_ADMIN_RAW = os.getenv("VERSION_ADMIN_EMAILS", "")
VERSION_ADMIN_EMAILS: frozenset[str] = frozenset(
    e.strip() for e in _VERSION_ADMIN_RAW.split(",") if e.strip()
)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Version Service❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


async def get_version_service(platform: str = "win") -> VersionResponse:
    """
    Retorna informações de versão do app Electron.
    Fonte: variáveis de ambiente ou MongoDB (se USE_VERSION_DB=true).
    """
    platform = (platform or "win").lower().strip()
    if platform not in ("win", "mac", "linux"):
        platform = "win"

    if USE_VERSION_DB:
        doc = await get_version_by_platform(platform)
        if doc:
            return VersionResponse(
                minClientVersion=doc.get("minClientVersion", "0.0.0"),
                latestVersion=doc.get("latestVersion", "1.0.0"),
                releaseNotes=doc.get("releaseNotes"),
                forceUpgrade=doc.get("forceUpgrade", False),
                downloadUrl=doc.get("downloadUrl"),
                platform=platform,
            )

    # Fallback: variáveis de ambiente
    min_ver = os.getenv("MIN_CLIENT_VERSION", "0.0.0")
    latest_ver = os.getenv("LATEST_VERSION", "1.0.0")
    release_notes = os.getenv("RELEASE_NOTES") or None
    force_upgrade = os.getenv("FORCE_UPGRADE", "").strip().lower() in ("1", "true", "yes")
    download_url = os.getenv("DOWNLOAD_URL") or None

    return VersionResponse(
        minClientVersion=min_ver,
        latestVersion=latest_ver,
        releaseNotes=release_notes,
        forceUpgrade=force_upgrade,
        downloadUrl=download_url,
        platform=platform,
    )


def is_version_admin(user: dict) -> bool:
    """Verifica se o usuário pode configurar versões (admin)."""
    if not user:
        return False
    email = (user.get("email") or "").strip()
    name = (user.get("name") or "").strip()
    return email in VERSION_ADMIN_EMAILS or name in VERSION_ADMIN_EMAILS


async def update_version_service(
    payload: VersionUpdateRequest,
    user: dict,
) -> VersionResponse:
    """
    Atualiza configuração de versão no MongoDB.
    Requer USE_VERSION_DB=true e usuário em VERSION_ADMIN_EMAILS.
    """
    platform = (payload.platform or "win").lower().strip()
    if platform not in ("win", "mac", "linux"):
        platform = "win"

    await upsert_version(
        platform=platform,
        min_client_version=payload.minClientVersion,
        latest_version=payload.latestVersion,
        release_notes=payload.releaseNotes,
        force_upgrade=payload.forceUpgrade,
        download_url=payload.downloadUrl,
    )

    return await get_version_service(platform=platform)
