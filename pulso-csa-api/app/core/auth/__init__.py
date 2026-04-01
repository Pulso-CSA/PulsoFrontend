# Re-export from PulsoCSA (core.auth)
import sys
from pathlib import Path

_pulso = Path(__file__).resolve().parent.parent.parent / "PulsoCSA" / "Python"
if str(_pulso) not in sys.path:
    sys.path.insert(0, str(_pulso))
from core.auth.auth_deps import verificar_token, verificar_token_opcional, extrair_usuario_de_token
from core.auth.auth_and_rate_limit import auth_and_rate_limit

__all__ = ["verificar_token", "verificar_token_opcional", "extrair_usuario_de_token", "auth_and_rate_limit"]
