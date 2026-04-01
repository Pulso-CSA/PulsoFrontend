#━━━━━━━━━❮Dependências de Autenticação❯━━━━━━━━━
# Depends reutilizáveis para proteger rotas sensíveis.
from typing import Optional

from fastapi import Depends, HTTPException, Header

from utils.login import verify_jwt_token
from storage.database.login.database_login import get_user_by_email, is_token_blacklisted


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


async def verificar_token_opcional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Dependency para autenticação opcional.
    Retorna dict do usuário se autenticado, None caso contrário.
    """
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        if await is_token_blacklisted(token):
            return None
        token_data = verify_jwt_token(token)
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")
        if not email:
            return None
        user = await get_user_by_email(email)
        if not user:
            return None
        return {"_id": str(user.get("_id")), "email": user.get("email"), "name": user.get("name")}
    except Exception:
        return None


def extrair_usuario_de_token(user: dict = Depends(verificar_token)) -> str:
    """Extrai email do usuário autenticado para uso em serviços."""
    return user.get("email") or user.get("_id", "")
