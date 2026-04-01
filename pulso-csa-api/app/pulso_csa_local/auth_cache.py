#━━━━━━━━━❮Cache in-memory — auth local (desktop)❯━━━━━━━━━
"""
Envolve is_token_blacklisted e get_user_entitlement com TTL curto e modo degradado:
se Mongo falhar e existir entrada de cache válida, reutiliza.
"""
from __future__ import annotations

import hashlib
import os
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple

_CACHE_TTL = float(os.getenv("PULSO_LOCAL_AUTH_CACHE_TTL", "90"))

_bl: Dict[str, Tuple[float, bool]] = {}
_ent: Dict[str, Tuple[float, dict]] = {}
_lock = threading.Lock()


def _token_key(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _wrap_blacklist(orig: Callable):
    async def _inner(token: str) -> bool:
        key = _token_key(token)
        now = time.monotonic()
        with _lock:
            if key in _bl:
                ts, val = _bl[key]
                if now - ts < _CACHE_TTL:
                    return val
        try:
            val = await orig(token)
        except Exception:
            with _lock:
                if key in _bl:
                    return _bl[key][1]
            raise
        with _lock:
            _bl[key] = (now, val)
        return val

    return _inner


def _wrap_entitlement(orig: Callable):
    async def _inner(user_id: str, user: Optional[dict] = None) -> dict:
        uid = (user_id or "").strip() or "_empty"
        now = time.monotonic()
        with _lock:
            if uid in _ent:
                ts, val = _ent[uid]
                if now - ts < _CACHE_TTL:
                    return dict(val)
        try:
            val = await orig(user_id, user)
        except Exception:
            with _lock:
                if uid in _ent:
                    return dict(_ent[uid][1])
            raise
        with _lock:
            _ent[uid] = (now, dict(val))
        return dict(val)

    return _inner


def install_local_auth_cache() -> None:
    """
    Envolve blacklist e entitlement com TTL + degradado.
    Atualiza também os bindings em auth_deps / entitlement.deps (import antecipado).
    """
    import storage.database.login.database_login as dl
    import core.auth.auth_deps as ad
    import core.entitlement.service_entitlement as se
    import core.entitlement.deps as ed

    if not getattr(dl.is_token_blacklisted, "_pulso_local_cached", False):
        fn = dl.is_token_blacklisted
        w = _wrap_blacklist(fn)
        w._pulso_local_cached = True  # type: ignore[attr-defined]
        dl.is_token_blacklisted = w
        ad.is_token_blacklisted = w

    if not getattr(se.get_user_entitlement, "_pulso_local_cached", False):
        fn2 = se.get_user_entitlement
        w2 = _wrap_entitlement(fn2)
        w2._pulso_local_cached = True  # type: ignore[attr-defined]
        se.get_user_entitlement = w2
        ed.get_user_entitlement = w2
