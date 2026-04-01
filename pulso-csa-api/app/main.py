#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

#━━━━━━━━━❮Adicionar módulos ao sys.path❯━━━━━━━━━
# Adiciona os módulos reorganizados ao path do Python
# __file__ está em api/app/main.py, então parent.parent é api/
API_DIR = Path(__file__).parent.parent.resolve()
APP_DIR = Path(__file__).parent.resolve()

# Adicionar api/ para que "app" seja um pacote válido (app.CloudIAC, app.PulsoCSA, etc.)
sys.path.insert(0, str(API_DIR))
# Adicionar api/app para arquivos compartilhados (storage, core, etc.)
sys.path.insert(0, str(APP_DIR))
# Depois adicionar os módulos (estão em api/app/, não em api/)
# Ordem: PulsoCSA primeiro (routers.analise_router, etc), depois CloudIAC, FinOps, InteligenciaDados
sys.path.insert(0, str(APP_DIR / "InteligenciaDados"))
sys.path.insert(0, str(APP_DIR / "FinOps"))
sys.path.insert(0, str(APP_DIR / "CloudIAC"))
sys.path.insert(0, str(APP_DIR / "PulsoCSA" / "Python"))

#━━━━━━━━━❮Env❯━━━━━━━━━
# Sobe 2 níveis até a raiz da PulsoAPI
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_PATH = os.path.join(ROOT_DIR, ".env")

# Carrega .env de múltiplos locais possíveis (UTF-8 para suportar ç, ã, etc.)
if os.path.isfile(ENV_PATH):
    load_dotenv(ENV_PATH, override=True, encoding="utf-8")
    print(f"✅ .env carregado de: {ENV_PATH}")
else:
    print(f"⚠️ .env não encontrado em: {ENV_PATH}")
    # Tenta carregar do diretório atual também
    load_dotenv(override=True, encoding="utf-8")

# Debug: variáveis sensíveis — apenas status "carregada" ou "não encontrada" (nunca o valor)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o3")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

def _env_ok(name: str, value: str) -> None:
    if value:
        print(f"  {name} carregada")
    else:
        print(f"  {name} não encontrada no .env")

print("Variáveis de ambiente (sem exibir valores):")
_env_ok("STRIPE_SECRET_KEY", STRIPE_SECRET_KEY)
_env_ok("STRIPE_WEBHOOK_SECRET", STRIPE_WEBHOOK_SECRET)
_env_ok("OPENAI_API_KEY", OPENAI_API_KEY)
_env_ok("OPENAI_MODEL", OPENAI_MODEL)
_env_ok("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
if os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes"):
    print("  USE_OLLAMA: ativo (Ollama — em Railway o interpretador padrão é o modelo leve salvo override em OLLAMA_MODEL_INTERPRETACAO)")


import time
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

#━━━━━━━━━❮Imports PulsoCSA❯━━━━━━━━━
from core.pulso.config import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    ALLOWED_ORIGINS,
    print_railway_env,
)

from routers.analise_router import governance_router, backend_router, infra_router
from routers.login_router.router_login import router as login_router
from routers.creation_routers import execution_router
from routers.deve_router import router as deve_router
from routers.tela_teste_router import router as tela_teste_router
from routers.spec_aliases_router import router as spec_aliases_router
from routers.deploy_router.deploy_router import router as deploy_router
from routers.venv_routers.venv_router import router as venv_router
from routers.preview_router.preview_router import router as preview_router
from routers.test_router.test_router import router as test_router
from routers.struc_anal.struc_anal_router import router as struc_anal_router
from routers.workflow.correct_workflow_router import router as correct_workflow_router
from routers.comprehension_router import router as comprehension_router
from PulsoCSA.JavaScript.routers.comprehension_router import router as comprehension_js_router

# ⭐ Code Plan (C2b)
from routers.correct_router.code_plan_router import router as code_plan_router

# ⭐ Code Writer (C3)
from routers.correct_router.code_writer_router import router as code_writer_router

# ⭐ Code Implementer (C4) — IMPORTANTE
from routers.correct_router.code_implementer_router import router as code_implementer_router

# Full Auto Workflow
from routers.workflow.full_auto_workflow_router import router as full_auto_workflow_router

# Pipeline (11–13.2): teste-automatizado, analise-retorno, correcao-erros, seguranca-pos
from routers.pipeline_router.pipeline_router import router as pipeline_router

from routers.chat_history_router import router as chat_history_router
from routers.profile_router.router_profile import router as profile_router
from routers.subscription_router.router_subscription import router as subscription_router
from routers.version_router.version_router import router as version_router

from utils.log_manager import add_log
from utils.rate_limit import check_rate_limit_ip

#━━━━━━━━━❮Imports CloudIAC❯━━━━━━━━━
from CloudIAC.routers.infra import router as infra_module_router

#━━━━━━━━━❮Imports FinOps❯━━━━━━━━━
from FinOps.routers.finops import router as finops_router
from FinOps.routers.reports_router import router as reports_router
from FinOps.routers.finance_router import finance_router

#━━━━━━━━━❮Imports InteligenciaDados❯━━━━━━━━━
# Imports explícitos (app.InteligenciaDados) pois routers.* conflita com PulsoCSA/CloudIAC/FinOps
from InteligenciaDados.routers.ID_routers.query_get_router import router as query_get_router
from InteligenciaDados.routers.ID_routers.captura_dados_router import router as captura_dados_router
from InteligenciaDados.routers.ID_routers.analise_dados_router import router as analise_dados_router
from InteligenciaDados.routers.ID_routers.tratamento_limpeza_router import router as tratamento_limpeza_router
from InteligenciaDados.routers.ID_routers.analise_estatistica_router import router as analise_estatistica_router
from InteligenciaDados.routers.ID_routers.modelos_ml_router import router as modelos_ml_router
from InteligenciaDados.routers.ID_routers.previsao_router import router as previsao_router
from InteligenciaDados.routers.ID_routers.id_chat_router import router as id_chat_router
from InteligenciaDados.routers.ID_routers.agendamento_retreino_router import router as agendamento_retreino_router
from InteligenciaDados.routers.ID_routers.insights_router import router as insights_router
from RegenAI.routers.regen_router import router as regen_router
from Insights.routers.insights_api_router import router as pulso_insights_router

#━━━━━━━━━❮Inicialização❯━━━━━━━━━

# Desabilita docs OpenAPI em produção (segurança)
_is_prod = (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)


#━━━━━━━━━❮DEBUG Railway❯━━━━━━━━━
# Chama apenas uma vez ao iniciar o servidor
print_railway_env("info")   # <-- adicionada

# Log MONGO_URI no startup (sem expor senha)
try:
    from app.storage.database.database_core import MONGO_URI
    _mongo_display = MONGO_URI[:80] + "..." if len(MONGO_URI or "") > 80 else (MONGO_URI or "(não definida)")
    print(f"[Startup] MONGO_URI={_mongo_display}")
except Exception as e:
    print(f"[Startup] MONGO_URI: não foi possível obter ({e})")

#━━━━━━━━━❮Key Ring (Chave Rotativa)❯━━━━━━━━━
@app.on_event("startup")
async def init_key_ring():
    """Inicializa KeyRing se KEY_SEED_WORDS configurado (chave rotativa + PQC)."""
    try:
        from utils.login import ROTATING_KEY_ENABLED
        if ROTATING_KEY_ENABLED:
            from app.PulsoCSA.Python.core.security import get_key_ring
            kr = get_key_ring()
            kr.get_current_key()  # força derivação no startup (e log DEBUG se KEY_RING_DEBUG=1)
            print("✅ KeyRing (chave rotativa HS384) inicializado")
    except Exception as e:
        print(f"⚠️ KeyRing: {e}")


#━━━━━━━━━❮Ollama Warmup (pré-carrega modelos)❯━━━━━━━
@app.on_event("startup")
async def ollama_warmup():
    """Pré-carrega os modelos Ollama efetivos (interpretação + execução) para reduzir a 1ª latência."""
    if os.getenv("USE_OLLAMA", "").strip().lower() not in ("1", "true", "yes"):
        return
    try:
        from ollama import Client
        from app.core.ollama.ollama_client import MODEL_EXECUCAO, MODEL_INTERPRETACAO

        host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        client = Client(host=host)
        seen: list[str] = []
        for model in (MODEL_INTERPRETACAO, MODEL_EXECUCAO):
            if not model or model in seen:
                continue
            seen.append(model)
            try:
                client.chat(model=model, messages=[{"role": "user", "content": "ok"}], options={"num_predict": 2})
                print(f"  Ollama warmup: {model}")
            except Exception:
                pass
    except ImportError:
        pass
    except Exception as e:
        print(f"  Ollama warmup: {type(e).__name__}")


#━━━━━━━━━❮Fix Governance Index (agendamento_id)❯━━━━━━━━━
# Remove índice agendamento_id da governance_layer se existir (foi criado por engano na coleção errada)
@app.on_event("startup")
async def fix_governance_agendamento_index():
    """Remove o índice agendamento_id da governance_layer (não pertence a essa coleção)."""
    try:
        from app.storage.database.database_core import get_collection
        coll = get_collection("governance")
        if hasattr(coll, "list_indexes"):
            for index in coll.list_indexes():
                if index.get("name") == "agendamento_id_1":
                    coll.drop_index("agendamento_id_1")
                    print("✅ Índice 'agendamento_id_1' removido da coleção 'governance_layer'")
                    break
    except Exception as e:
        print(f"⚠️ Aviso ao verificar índice governance: {e}")


#━━━━━━━━━❮Fix Profiles Index❯━━━━━━━━━
# Remove índice id_requisicao da coleção profiles se existir
@app.on_event("startup")
async def fix_profiles_index_on_startup():
    """Remove o índice id_requisicao da coleção profiles na inicialização."""
    try:
        from app.storage.database.profile.database_profile import profiles_collection
        indexes = list(profiles_collection.list_indexes())
        for index in indexes:
            index_key = index.get("key", {})
            if "id_requisicao" in index_key:
                try:
                    profiles_collection.drop_index(index["name"])
                    print(f"✅ Índice 'id_requisicao' removido da coleção 'profiles'")
                except Exception:
                    try:
                        profiles_collection.drop_index([("id_requisicao", 1)])
                        print(f"✅ Índice 'id_requisicao' removido da coleção 'profiles' (pelo campo)")
                    except Exception:
                        pass
    except Exception as e:
        # Não falha a inicialização se houver erro
        print(f"⚠️ Aviso ao verificar índice profiles: {e}")


#━━━━━━━━━❮Body size e Request ID (segurança e rastreio)❯━━━━━━━
MAX_BODY_SIZE_BYTES = int(os.getenv("MAX_BODY_SIZE_MB", "1")) * 1024 * 1024  # default 1 MB
# PUT /auth/me envia avatar em base64 (data URL); precisa de teto maior que o global.
AUTH_ME_MAX_BODY_BYTES = int(os.getenv("AUTH_ME_MAX_BODY_MB", "8")) * 1024 * 1024


def _effective_max_body_bytes(request: Request) -> int:
    if request.method == "PUT" and request.url.path.rstrip("/") == "/auth/me":
        return max(MAX_BODY_SIZE_BYTES, AUTH_ME_MAX_BODY_BYTES)
    return MAX_BODY_SIZE_BYTES


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Em produção não expõe stack trace nem detalhe da exceção (evita vazamento)."""
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    add_log("error", f"EXCEÇÃO GLOBAL | path={request.url.path} | type={type(exc).__name__} | msg={exc}", "main")
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if _is_production():
        add_log("error", f"Erro interno request_id={request_id} (detalhe não exposto).", "main")
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno.", "code": "INTERNAL_ERROR", "request_id": request_id},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "code": "INTERNAL_ERROR", "request_id": request_id},
    )


def _client_ip(request: Request) -> str:
    """IP do cliente (considera X-Forwarded-For em ambiente com proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


@app.middleware("http")
async def middleware_body_and_request_id(request: Request, call_next):
    """Rate limit por IP; limita tamanho do body; X-Request-Id para rastreio."""
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        from utils.log_manager import set_request_id
        set_request_id(request_id)
    except Exception:
        pass

    if request.url.path.startswith("/auth"):
        add_log("info", f"REQ {request.method} {request.url.path} | ip={_client_ip(request)} | request_id={request_id}", "middleware")

    allowed, _ = check_rate_limit_ip(_client_ip(request))
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Muitas requisições. Tente novamente em alguns minutos.",
                "code": "RATE_LIMIT_EXCEEDED",
                "request_id": request_id,
            },
        )

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
    add_log("info", f"RESP {request.method} {request.url.path} = {response.status_code} ({elapsed_ms:.0f}ms)", "middleware")
    # Headers de segurança (evita clickjacking, XSS, MIME sniffing)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if response.status_code < 400:
        response.headers["X-Request-Id"] = request_id
    return response


#━━━━━━━━━❮LLM API Key (BYOK – nunca armazenada em DB)❯━━━━━━━━━
@app.middleware("http")
async def llm_api_key_middleware(request: Request, call_next):
    """Extrai X-OpenAI-API-Key do header; define no contexto por request; limpa ao fim."""
    from app.core.llm import set_request_api_key, clear_request_api_key
    key = request.headers.get("X-OpenAI-API-Key", "").strip()
    if key:
        set_request_api_key(key)
    try:
        response = await call_next(request)
        return response
    finally:
        clear_request_api_key()


#━━━━━━━━━❮CORS❯━━━━━━━━━

# CORS: em dev permite localhost e null (Electron file://). Em prod usa ALLOWED_ORIGINS.
_is_prod = (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"
_cors_origins = (
    ALLOWED_ORIGINS
    if _is_prod
    else ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5173", "http://127.0.0.1:5173", "http://[::1]:8080", "http://[::1]:5173", "null"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=None if _is_prod else r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#━━━━━━━━━❮Rotas das Camadas❯━━━━━━━━━
#━━━━━━━━━❮Rotas❯━━━━━━━━━

app.include_router(login_router)
app.include_router(profile_router)
app.include_router(subscription_router)
app.include_router(deploy_router)
app.include_router(query_get_router)
app.include_router(captura_dados_router)
app.include_router(analise_dados_router)
app.include_router(tratamento_limpeza_router)
app.include_router(analise_estatistica_router)
app.include_router(modelos_ml_router)
app.include_router(previsao_router)
app.include_router(id_chat_router)
app.include_router(agendamento_retreino_router)
app.include_router(insights_router)
app.include_router(pulso_insights_router)
app.include_router(regen_router)
app.include_router(version_router, prefix="/api")

#━━━━━━━━━❮Desenvolvimento – Workflow completo (deve/run)❯━━━━━━━━━
app.include_router(deve_router)

#━━━━━━━━━❮Sistema de Compreensão – Entrada principal do workflow❯━━━━━━━━━
app.include_router(comprehension_router)

#━━━━━━━━━❮Sistema de Compreensão JavaScript – Entrada principal do workflow JS❯━━━━━━━━━
app.include_router(comprehension_js_router)

#━━━━━━━━━❮Aliases da spec (rotas no raiz: /input, /refinar, /validar, etc.)❯━━━━━━━━━
app.include_router(spec_aliases_router)

app.include_router(
    governance_router,
    tags=["Camada 1 - Governança"],
)
app.include_router(
    backend_router,
    prefix="/backend",
    tags=["Camada 2 – Backend"],
)
app.include_router(
    infra_router,
    prefix="/infra",
    tags=["Camada 2 – Infraestrutura"],
)
app.include_router(
    infra_module_router,
    prefix="/infra",
    tags=["Infra – Terraform"],
)

app.include_router(
    execution_router,
    prefix="/execution",
    tags=["Camada 3 – Execução"],
)
app.include_router(tela_teste_router)

app.include_router(
    venv_router,
    prefix="/venv",
    tags=["Venv Manager"],
)
app.include_router(
    preview_router,
    tags=["Preview (npm run dev / streamlit run)"],
)
app.include_router(
    test_router,
    tags=["Test (Venv + Docker)"],
)
app.include_router(
    struc_anal_router,
    tags=["Análise Estrutural"],
)
app.include_router(
    correct_workflow_router,
    tags=["Workflow – Correção Estrutural"],
)


#━━━━━━━━━❮Code Generation Stack (C2b, C3, C4)❯━━━━━━━━━

app.include_router(
    code_plan_router,
    tags=["Code Plan – Correção de Código"],
)
app.include_router(
    code_writer_router,
    tags=["Code Writer – Geração de Código"],
)
app.include_router(
    code_implementer_router,
    tags=["Code Implementer – Implementação Final"],
)


#━━━━━━━━━❮Full Auto Workflow❯━━━━━━━━━

app.include_router(
    full_auto_workflow_router,
    tags=["Workflow – Full Auto"],
)

#━━━━━━━━━❮Pipeline (11–13.2)❯━━━━━━━━━
app.include_router(pipeline_router)

#━━━━━━━━━❮FinOps – Análise Multi-Cloud❯━━━━━━━━━
app.include_router(finops_router)

#━━━━━━━━━❮Histórico de Chats por Módulo❯━━━━━━━━━
app.include_router(chat_history_router)

#━━━━━━━━━❮Relatórios PDF (PulsoCSA, Cloud IAC, FinOps, Inteligência de Dados)❯━━━━━━━━━
app.include_router(reports_router)
app.include_router(finance_router)

#━━━━━━━━━❮Rota Raiz e Health Checks❯━━━━━━━━━

@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint – basic API info.
    """
    return {
        "status": "online",
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
    }


@app.get("/health", tags=["Health"])
def health_liveness():
    """Liveness: indica que o processo está rodando."""
    return {"status": "ok", "service": APP_NAME}


@app.get("/health/ready", tags=["Health"])
async def health_readiness():
    """Readiness: verifica se dependências críticas (MongoDB) estão acessíveis."""
    try:
        from app.storage.database.database_core import get_client
        client = get_client()
        client.server_info()
        return {"status": "ok", "mongo": "connected"}
    except Exception as e:
        add_log("error", f"Health readiness failed: {type(e).__name__}", "health")
        err_msg = str(e)[:100] if not _is_production() else "MongoDB indisponível"
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "mongo": "disconnected", "error": err_msg},
        )


# Compatibilidade: POST / delegado ao webhook do subscription (evita duplicação)
@app.post("/", tags=["Root"])
async def root_webhook(request: Request):
    """
    Webhook Stripe (compatibilidade). Delega para /subscription/webhook.
    Configure o Stripe para usar /subscription/webhook diretamente.
    """
    from app.PulsoCSA.Python.routers.subscription_router.router_subscription import stripe_webhook
    return await stripe_webhook(request)


#━━━━━━━━━❮Execução Local❯━━━━━━━━━
#python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
#0x00