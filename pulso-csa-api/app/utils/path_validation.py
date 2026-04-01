# Re-export from PulsoCSA
import sys
from pathlib import Path

_pulso = Path(__file__).resolve().parent.parent / "PulsoCSA" / "Python"
if str(_pulso) not in sys.path:
    sys.path.insert(0, str(_pulso))
from utils.path_validation import is_production, sanitize_root_path

__all__ = ["is_production", "sanitize_root_path"]
