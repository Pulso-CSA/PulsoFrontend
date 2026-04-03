#━━━━━━━━━❮Dependências de Autenticação❯━━━━━━━━━
# Depends reutilizáveis para proteger rotas sensíveis.
import os
from typing import Optional

from fastapi import Depends, HTTPException, Header

from utils.login import (
    decode_access_token_unverified_for_local_desktop,
    verify_jwt_token,
)
from storage.database.login.database_login import get_user_by_email, is_token_blacklisted


def _pulso_csa_local_mode() -> bool:
    return (os.getenv("PULSO_CSA_LOCAL") or "").strip().lower() in ("1", "true", "yes")


def _local_desktop_entitlement_grace() -> bool:
    """Definido pelo Electron ao arrancar uvicorn; desbloqueia CSA sem Mongo/chaves iguais à cloud."""
    return (os.getenv("PULSO_LOCAL_DESKTOP_ENTITLEMENT_GRACE") or "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _http_exc_is_expired_token(exc: HTTPException) -> bool:
    d = exc.detail
    s = d if isinstance(d, str) else str(d)
    return "expirad" in s.lower()


async def verificar_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency para autenticação obrigatória.
    Retorna dict com _id, email, name do usuário autenticado.
    Usar: Depends(verificar_token) na rota.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    try:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        try:
            token_bl = await is_token_blacklisted(token)
        except Exception:
            if not (_pulso_csa_local_mode() and _local_desktop_entitlement_grace()):
                raise
            token_bl = False
        if token_bl:
            raise HTTPException(status_code=401, detail="Token foi invalidado (logout)")
        try:
            token_data = verify_jwt_token(token)
        except HTTPException as e:
            if not _pulso_csa_local_mode() or _http_exc_is_expired_token(e):
                raise
            token_data = decode_access_token_unverified_for_local_desktop(token)
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        user = None
        try:
            user = await get_user_by_email(email)
        except Exception:
            user = None
        if user:
            return {"_id": str(user.get("_id")), "email": user.get("email"), "name": user.get("name")}
        if _pulso_csa_local_mode() and _local_desktop_entitlement_grace():
            data = token_data.get("data") or {}
            uid = data.get("id") or data.get("_id")
            uid_s = str(uid).strip() if uid is not None else ""
            if not uid_s:
                uid_s = email.strip().lower()
            return {
                "_id": uid_s,
                "email": email.strip().lower(),
                "name": (data.get("name") or "") or "",
            }
        raise HTTPException(status_code=401, detail="Sessão inválida. Faça login novamente.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


async def verificar_token_opcional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Dependency para autenticação opcional.
    Retorna dict do usuário se autenticado, None caso contrário.
    """
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        try:
            if await is_token_blacklisted(token):
                return None
        except Exception:
            if not (_pulso_csa_local_mode() and _local_desktop_entitlement_grace()):
                return None
        try:
            token_data = verify_jwt_token(token)
        except HTTPException as e:
            if not _pulso_csa_local_mode() or _http_exc_is_expired_token(e):
                return None
            try:
                token_data = decode_access_token_unverified_for_local_desktop(token)
            except HTTPException:
                return None
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")
        if not email:
            return None
        try:
            user = await get_user_by_email(email)
        except Exception:
            user = None
        if user:
            return {"_id": str(user.get("_id")), "email": user.get("email"), "name": user.get("name")}
        if _pulso_csa_local_mode() and _local_desktop_entitlement_grace():
            data = token_data.get("data") or {}
            uid = data.get("id") or data.get("_id")
            uid_s = str(uid).strip() if uid is not None else ""
            if not uid_s:
                uid_s = email.strip().lower()
            return {"_id": uid_s, "email": email.strip().lower(), "name": (data.get("name") or "") or ""}
        return None
    except Exception:
        return None


def extrair_usuario_de_token(user: dict = Depends(verificar_token)) -> str:
    """Extrai email do usuário autenticado para uso em serviços."""
    return user.get("email") or user.get("_id", "")
