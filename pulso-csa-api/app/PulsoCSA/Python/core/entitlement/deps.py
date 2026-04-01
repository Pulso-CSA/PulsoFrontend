#━━━━━━━━━❮Deps – Auth + Entitlement❯━━━━━━━━━
"""
Dependency que combina auth + rate limit + entitlement.
Usar em rotas que precisam validar plano/serviço.
"""
from fastapi import Depends, HTTPException

from core.auth.auth_and_rate_limit import auth_and_rate_limit
from core.entitlement.service_entitlement import (
    get_user_entitlement,
    require_service,
)


async def get_current_user_entitlement(
    user: dict = Depends(auth_and_rate_limit),
) -> dict:
    """
    Dependency: auth + rate limit + entitlement.
    Retorna dict com user + entitlement.
    """
    user_id = user.get("_id") or user.get("email") or ""
    entitlement = await get_user_entitlement(user_id, user)
    return {
        "user": user,
        "entitlement": entitlement,
    }


def auth_and_entitlement(service_id: str):
    """
    Factory: retorna dependency que exige auth + acesso ao service_id.
    Uso: Depends(auth_and_entitlement("finops"))
    """

    async def _dep(
        user: dict = Depends(auth_and_rate_limit),
    ) -> dict:
        user_id = user.get("_id") or user.get("email") or ""
        entitlement = await get_user_entitlement(user_id, user)
        require_service(entitlement, service_id)
        return {
            "user": user,
            "entitlement": entitlement,
        }

    return _dep


async def require_valid_access(user: dict = Depends(auth_and_rate_limit)) -> dict:
    """
    Exige: isento OU assinatura ativa.
    Retorna user. Levanta 403 se não tiver acesso.
    """
    user_id = user.get("_id") or user.get("email") or ""
    entitlement = await get_user_entitlement(user_id, user)
    if entitlement.get("is_exempt"):
        return user
    if entitlement.get("max_services", 0) > 0:
        return user
    raise HTTPException(
        status_code=403,
        detail={
            "code": "SUBSCRIPTION_REQUIRED",
            "message": "Assinatura ativa necessária. Faça upgrade do seu plano.",
        },
    )
