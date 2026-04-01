# Re-export from PulsoCSA
import sys
from pathlib import Path

_pulso = Path(__file__).resolve().parent.parent / "PulsoCSA" / "Python"
if str(_pulso) not in sys.path:
    sys.path.insert(0, str(_pulso))
from utils.db_config_validation import validar_db_config

__all__ = ["validar_db_config"]
