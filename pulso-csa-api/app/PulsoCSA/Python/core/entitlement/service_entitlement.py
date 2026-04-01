#━━━━━━━━━❮Service Entitlement – Validação de Acesso por Plano❯━━━━━━━━━
"""
Valida acesso a serviços conforme plano e usuários isentos.
"""
from typing import Optional

from fastapi import HTTPException

from core.entitlement.config import (
    is_payment_exempt,
    PLAN_MAX_SERVICES,
    SERVICE_IDS,
)
# database_subscription está em api/app/storage/database/subscription/ (compartilhado)
try:
    from storage.database.subscription.database_subscription import get_subscription_by_user_id
except ImportError:
    from app.storage.database.subscription.database_subscription import get_subscription_by_user_id


async def get_user_entitlement(user_id: str, user: Optional[dict] = None) -> dict:
    """
    Retorna entitlement do usuário: plano, max_services, services_enabled, is_exempt.
    Se isento, retorna max_services ilimitado e todos os serviços.
    """
    if user and is_payment_exempt(user):
        return {
            "tenant_id": user_id,
            "plano": "elite",
            "max_services": 999,
            "services_enabled": list(SERVICE_IDS),
            "is_exempt": True,
        }

    sub = await get_subscription_by_user_id(user_id)
    if not sub or sub.get("status") not in ("active", "trialing"):
        return {
            "tenant_id": user_id,
            "plano": None,
            "max_services": 0,
            "services_enabled": [],
            "is_exempt": False,
        }

    plan_id = (sub.get("planId") or "basic").lower()
    max_services = PLAN_MAX_SERVICES.get(plan_id, 1)

    # Busca services_enabled do banco (escolha do usuário)
    # entitlement está em api/app/storage/database/entitlement/ (compartilhado)
    try:
        from storage.database.entitlement.database_entitlement import get_services_enabled
    except ImportError:
        from app.storage.database.entitlement.database_entitlement import get_services_enabled
    services_enabled = await get_services_enabled(user_id)
    # Se não escolheu ainda: permite todos para paid users (UI de escolha é fase 2)
    if not services_enabled and max_services > 0:
        services_enabled = list(SERVICE_IDS)

    return {
        "tenant_id": user_id,
        "plano": plan_id,
        "max_services": max_services,
        "services_enabled": services_enabled,
        "is_exempt": False,
    }


def check_service_access(entitlement: dict, service_id: str) -> bool:
    """
    Verifica se o usuário tem acesso ao serviço.
    Isentos: sempre True.
    """
    if entitlement.get("is_exempt"):
        return True
    if entitlement.get("max_services", 0) <= 0:
        return False
    enabled = entitlement.get("services_enabled") or []
    return service_id in enabled


def require_service(entitlement: dict, service_id: str) -> None:
    """
    Levanta 403 se o usuário não tiver acesso ao serviço.
    """
    if not check_service_access(entitlement, service_id):
        max_s = entitlement.get("max_services", 0)
        enabled = entitlement.get("services_enabled") or []
        raise HTTPException(
            status_code=403,
            detail={
                "code": "SERVICE_NOT_ENTITLED",
                "message": f"Serviço '{service_id}' não está ativo no seu plano. "
                           f"Você tem {len(enabled)} de {max_s} serviços em uso.",
                "max_services": max_s,
                "services_enabled": enabled,
            },
        )
