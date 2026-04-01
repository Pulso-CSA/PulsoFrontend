#━━━━━━━━━❮Espelha add_log para ficheiro rotativo (só processo local)❯━━━━━━━━━
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

_bridge_installed = False


def install_local_file_logging(log_path: Optional[str] = None) -> None:
    global _bridge_installed
    path = log_path or os.getenv("PULSO_LOCAL_LOG_FILE", "").strip()
    if not path or _bridge_installed:
        return

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fh = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root = logging.getLogger("pulso_csa_local")
    root.setLevel(logging.INFO)
    root.addHandler(fh)

    import utils.log_manager as lm

    _orig = lm.add_log

    def _dup(level: str, message: str, source: str, request_id=None):
        _orig(level, message, source, request_id)
        line = f"[{source}] {message}"
        lvl = (level or "info").lower()
        if lvl == "error":
            root.error(line)
        elif lvl == "warning":
            root.warning(line)
        else:
            root.info(line)

    lm.add_log = _dup  # type: ignore[assignment]
    _bridge_installed = True
    root.info("pulso-csa-local file logging at %s", path)
