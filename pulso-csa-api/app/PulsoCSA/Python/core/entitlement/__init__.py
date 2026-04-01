#━━━━━━━━━❮Entitlement – Planos, Isentos, Feature Gating❯━━━━━━━━━
from core.entitlement.config import (
    PAYMENT_EXEMPT_USERS,
    is_payment_exempt,
    PLAN_MAX_SERVICES,
    SERVICE_IDS,
)
from core.entitlement.service_entitlement import (
    get_user_entitlement,
    check_service_access,
    require_service,
)
from core.entitlement.deps import (
    auth_and_entitlement,
    get_current_user_entitlement,
)

__all__ = [
    "PAYMENT_EXEMPT_USERS",
    "is_payment_exempt",
    "PLAN_MAX_SERVICES",
    "get_user_entitlement",
    "check_service_access",
    "require_service",
    "auth_and_entitlement",
    "get_current_user_entitlement",
]
