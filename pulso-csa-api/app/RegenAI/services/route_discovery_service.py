import inspect
import re
from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.routing import APIRoute

from RegenAI.models.regen_request import RegenRequest, SCOPE_DIRECTORY_MAP

_STOP_WORDS = {
    "de",
    "do",
    "da",
    "dos",
    "das",
    "para",
    "com",
    "sem",
    "por",
    "que",
    "uma",
    "uns",
    "umas",
    "objetivo",
    "teste",
}


class RouteDiscoveryService:
    def discover(self, app: FastAPI, req: RegenRequest) -> List[Dict[str, str]]:
        methods_allowed = {m.upper() for m in req.include_methods}
        objective_terms = self._extract_terms(req.objective) | {t.lower() for t in req.include_keywords}
        scopes_allowed = set(req.scopes)

        ranked: List[Dict[str, str]] = []
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue

            if route.path.startswith("/regenai"):
                continue
            if route.path.startswith("/docs") or route.path.startswith("/openapi") or route.path.startswith("/redoc"):
                continue

            route_scope = self._detect_scope(route)
            if route_scope is None or route_scope not in scopes_allowed:
                continue

            methods = sorted((route.methods or {"GET"}) & methods_allowed)
            if not methods:
                continue

            score = self._score(route.path, route.name or "", objective_terms)
            for method in methods:
                ranked.append(
                    {
                        "path": route.path,
                        "method": method,
                        "name": route.name or "unknown",
                        "scope": route_scope,
                        "source_file": inspect.getsourcefile(route.endpoint) or "",
                        "score": str(score),
                    }
                )

        ranked.sort(key=lambda item: int(item["score"]), reverse=True)
        return ranked[: req.route_limit]

    @staticmethod
    def _extract_terms(text: str) -> set[str]:
        raw = re.findall(r"[a-zA-Z0-9_]{3,}", text.lower())
        return {term for term in raw if term not in _STOP_WORDS}

    @staticmethod
    def _score(path: str, name: str, terms: set[str]) -> int:
        haystack = f"{path} {name}".lower()
        if not terms:
            return 1
        return sum(1 for term in terms if term in haystack)

    @staticmethod
    def _detect_scope(route: APIRoute) -> Optional[str]:
        source_file = inspect.getsourcefile(route.endpoint)
        normalized_file = source_file.replace("\\", "/").lower() if source_file else ""
        for scope_name, directory in SCOPE_DIRECTORY_MAP.items():
            norm_dir = directory.replace("\\", "/").lower()
            if norm_dir in normalized_file:
                return scope_name

        endpoint_module = (getattr(route.endpoint, "__module__", "") or "").lower()
        if "cloudiac" in endpoint_module:
            return "CloudIAC"
        if "finops" in endpoint_module:
            return "FinOps"
        if "inteligenciadados" in endpoint_module:
            return "InteligenciaDados"
        if "pulsocsa.javascript" in endpoint_module:
            return "PulsoCSA/JavaScript"
        if "pulsocsa.python" in endpoint_module or endpoint_module.startswith("routers."):
            return "PulsoCSA/Python"
        return None

