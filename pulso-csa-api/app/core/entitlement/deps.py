# Re-export from PulsoCSA (core.entitlement.deps)
import sys
from pathlib import Path

_pulso = Path(__file__).resolve().parent.parent.parent / "PulsoCSA" / "Python"  # core/entitlement -> core -> app
if str(_pulso) not in sys.path:
    sys.path.insert(0, str(_pulso))
from core.entitlement.deps import (
    require_valid_access,
    get_current_user_entitlement,
    auth_and_entitlement,
)

__all__ = ["require_valid_access", "get_current_user_entitlement", "auth_and_entitlement"]
