#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Version Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import os
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException, Header
from services.version.version_service import (
    get_version_service,
    update_version_service,
    is_version_admin,
)
from models.version_models.version_models import VersionResponse, VersionUpdateRequest
from storage.database.login.database_login import get_user_by_email, is_token_blacklisted
from utils.login import verify_jwt_token

router = APIRouter(prefix="/version", tags=["Version"])


async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    try:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        if await is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token foi invalidado (logout)")
        token_data = verify_jwt_token(token)
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Sessão inválida. Faça login novamente.")
        return {"_id": str(user.get("_id")), "email": user.get("email"), "name": user.get("name")}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


async def require_version_admin(user: dict = Depends(get_current_user)):
    if not os.getenv("USE_VERSION_DB", "").strip().lower() in ("1", "true", "yes"):
        raise HTTPException(status_code=503, detail="Configuração de versão via API requer USE_VERSION_DB=true")
    if not is_version_admin(user):
        raise HTTPException(status_code=403, detail="Sem permissão. Configure VERSION_ADMIN_EMAILS.")
    return user

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Version Routes❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


@router.get("", response_model=VersionResponse)
async def get_version(
    platform: str = Query(default="win", description="Plataforma: win, mac, linux"),
):
    """
    Retorna informações de versão do app Electron (cliente).

    Usado pelo app Pulso (Electron) para:
    - Verificar versão mínima aceita (minClientVersion)
    - Obter última versão disponível (latestVersion)
    - Exibir notas da release
    - Forçar upgrade em caso de vulnerabilidades (forceUpgrade)

    **Não requer autenticação** — o app consulta antes do login.
    """
    return await get_version_service(platform=platform)


@router.put("", response_model=VersionResponse)
async def update_version(
    payload: VersionUpdateRequest,
    user: dict = Depends(require_version_admin),
):
    """Atualiza configuração de versão (admin). Requer USE_VERSION_DB=true e VERSION_ADMIN_EMAILS."""
    return await update_version_service(payload, user)
