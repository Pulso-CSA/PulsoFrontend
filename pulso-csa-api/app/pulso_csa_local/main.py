#━━━━━━━━━❮Pulso CSA — API local (desktop)❯━━━━━━━━━
"""
Entrypoint dedicado: não importar app.main.
Executar: uvicorn app.pulso_csa_local.main:app --host 127.0.0.1 --port <porta>
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

API_DIR = Path(__file__).resolve().parent.parent.parent  # api/
APP_DIR = Path(__file__).resolve().parent.parent  # api/app/

sys.path.insert(0, str(API_DIR))
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR / "PulsoCSA" / "Python"))

ROOT_DIR = API_DIR.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.is_file():
    load_dotenv(ENV_PATH, override=True, encoding="utf-8")
else:
    load_dotenv(override=True, encoding="utf-8")

# Electron: chaves e flags em ficheiro gravável (userData), definido por PULSO_CSA_USER_ENV
_user_env = (os.getenv("PULSO_CSA_USER_ENV") or "").strip()
if _user_env:
    _p = Path(_user_env)
    if _p.is_file():
        load_dotenv(_p, override=True, encoding="utf-8")

os.environ.setdefault("PULSO_CSA_LOCAL", "1")

from app.pulso_csa_local.auth_cache import install_local_auth_cache
from app.pulso_csa_local.allowlist_middleware import AllowlistedRootPathsMiddleware
from app.pulso_csa_local.local_log_bridge import install_local_file_logging

install_local_auth_cache()
install_local_file_logging()

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.pulso.config import APP_NAME, APP_VERSION, APP_DESCRIPTION
from routers.comprehension_router import router as comprehension_router
from PulsoCSA.JavaScript.routers.comprehension_router import router as comprehension_js_router
from routers.preview_router.preview_router import router as preview_router

from utils.log_manager import add_log, set_request_id

MAX_BODY_SIZE_BYTES = int(os.getenv("MAX_BODY_SIZE_MB", "8")) * 1024 * 1024
AUTH_ME_MAX_BODY_BYTES = int(os.getenv("AUTH_ME_MAX_BODY_MB", "8")) * 1024 * 1024


def _effective_max_body_bytes(request: Request) -> int:
    if request.method == "PUT" and request.url.path.rstrip("/") == "/auth/me":
        return max(MAX_BODY_SIZE_BYTES, AUTH_ME_MAX_BODY_BYTES)
    return MAX_BODY_SIZE_BYTES


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


app = FastAPI(
    title=f"{APP_NAME} (CSA Local)",
    version=APP_VERSION,
    description=APP_DESCRIPTION + " — serviço local desktop",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def pulso_local_secret_middleware(request: Request, call_next):
    expected = (os.getenv("PULSO_LOCAL_SECRET") or "").strip()
    if expected:
        # Liveness: o Electron faz probe HTTP sem header; não exigir token aqui (só 127.0.0.1).
        p = request.url.path.rstrip("/") or "/"
        if request.method == "GET" and p == "/health":
            return await call_next(request)
        got = (request.headers.get("X-Pulso-Local-Token") or "").strip()
        if got != expected:
            return JSONResponse(
                status_code=403,
                content={"detail": "Token local inválido.", "code": "LOCAL_TOKEN_INVALID"},
            )
    return await call_next(request)


@app.middleware("http")
async def middleware_body_and_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        set_request_id(request_id)
    except Exception:
        pass

    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        limit = _effective_max_body_bytes(request)
        if content_length and int(content_length) > limit:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "Payload muito grande.",
                    "code": "PAYLOAD_TOO_LARGE",
                    "request_id": request_id,
                },
            )

    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    add_log(
        "info",
        f"RESP {request.method} {request.url.path} = {response.status_code} ({elapsed_ms:.0f}ms)",
        "pulso_csa_local",
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if response.status_code < 400:
        response.headers["X-Request-Id"] = request_id
    return response


@app.middleware("http")
async def llm_api_key_middleware(request: Request, call_next):
    from app.core.llm import set_request_api_key, clear_request_api_key

    key = request.headers.get("X-OpenAI-API-Key", "").strip()
    if key:
        set_request_api_key(key)
    try:
        return await call_next(request)
    finally:
        clear_request_api_key()


_cors_origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://[::1]:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AllowlistedRootPathsMiddleware)

app.include_router(comprehension_router)
app.include_router(comprehension_js_router)
app.include_router(preview_router)


@app.get("/health", tags=["Health"])
def health_liveness():
    return {"status": "ok", "service": "pulso-csa-local", "version": APP_VERSION}


@app.get("/health/ready", tags=["Health"])
async def health_readiness():
    try:
        from app.storage.database.database_core import get_client

        client = get_client()
        client.server_info()
        return {"status": "ok", "mongo": "connected"}
    except Exception as e:
        err_msg = str(e)[:100] if not _is_production() else "MongoDB indisponível"
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "mongo": "disconnected", "error": err_msg},
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    add_log("error", f"EXCEÇÃO LOCAL | path={request.url.path} | type={type(exc).__name__} | msg={exc}", "pulso_csa_local")
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if _is_production():
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno.", "code": "INTERNAL_ERROR", "request_id": request_id},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "code": "INTERNAL_ERROR", "request_id": request_id},
    )
