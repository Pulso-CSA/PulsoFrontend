# Re-export from PulsoCSA (core.entitlement)
from app.core.entitlement.deps import require_valid_access, get_current_user_entitlement, auth_and_entitlement

__all__ = ["require_valid_access", "get_current_user_entitlement", "auth_and_entitlement"]
