# Re-export from PulsoCSA
import sys
from pathlib import Path

_pulso = Path(__file__).resolve().parent.parent / "PulsoCSA" / "Python"
if str(_pulso) not in sys.path:
    sys.path.insert(0, str(_pulso))
from utils.retreino_lock import obter_lock_retreino, liberar_lock_retreino

__all__ = ["obter_lock_retreino", "liberar_lock_retreino"]
