#━━━━━━━━━❮Middleware — root_path vs allowlist (desktop)❯━━━━━━━━━
from __future__ import annotations

import json
import os
from typing import Callable, List

from starlette.responses import JSONResponse

from utils.path_validation import is_path_under_base

TARGET_PATHS = frozenset({"/comprehension/run", "/comprehension-js/run", "/preview/start"})


def _load_allowed_roots(paths_file: str) -> List[str]:
    if not paths_file or not os.path.isfile(paths_file):
        return []
    try:
        raw = open(paths_file, encoding="utf-8").read().strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
        if isinstance(data, dict) and "roots" in data:
            return [str(x).strip() for x in data["roots"] if str(x).strip()]
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return []


def _norm_path(p: str) -> str:
    return os.path.normpath(os.path.abspath(os.path.expanduser((p or "").strip())))


def _root_allowed(root_path: str, allowed: List[str]) -> bool:
    if not root_path or not str(root_path).strip():
        return True
    resolved = _norm_path(str(root_path))
    for base in allowed:
        b = _norm_path(base)
        if is_path_under_base(resolved, b):
            return True
    return False


class AllowlistedRootPathsMiddleware:
    """ASGI: lê body JSON uma vez em POST alvo; valida root_path contra ficheiro allowlist."""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "").split("?", 1)[0]
        if method != "POST" or path not in TARGET_PATHS:
            await self.app(scope, receive, send)
            return

        if os.getenv("PULSO_LOCAL_RELAX_ROOT_ALLOWLIST", "").strip().lower() in ("1", "true", "yes"):
            await self.app(scope, receive, send)
            return

        paths_file = (os.getenv("PULSO_ALLOWED_ROOTS_FILE") or "").strip()
        allowed = _load_allowed_roots(paths_file) if paths_file else []

        body = b""
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.request":
                body += message.get("body", b"")
                more = message.get("more_body", False)

        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            data = {}

        root_path = data.get("root_path")
        rp_s = str(root_path).strip() if root_path is not None else ""

        if rp_s:
            if not allowed:
                resp = JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Lista de pastas autorizadas vazia. Escolha uma pasta no aplicativo ou defina PULSO_LOCAL_RELAX_ROOT_ALLOWLIST=1 em desenvolvimento.",
                        "code": "ROOT_ALLOWLIST_EMPTY",
                    },
                )
                await resp(scope, self._empty_receive, send)
                return
            if not _root_allowed(str(root_path), allowed):
                resp = JSONResponse(
                    status_code=403,
                    content={
                        "detail": "root_path não está na lista de pastas autorizadas (desktop).",
                        "code": "ROOT_PATH_NOT_ALLOWLISTED",
                    },
                )
                await resp(scope, self._empty_receive, send)
                return

        async def new_receive():
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, new_receive, send)

    async def _empty_receive(self):
        return {"type": "http.disconnect"}
