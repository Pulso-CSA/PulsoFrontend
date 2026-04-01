import os
from pathlib import Path

#━━━━━━━━━❮Base Paths❯━━━━━━━━━
BASE_DIR = Path(__file__).resolve().parent.parent

#━━━━━━━━━❮Configurações Gerais❯━━━━━━━━━
APP_NAME = "PulsoCSA API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "API modular de Inteligência Artificial com camadas integradas para "
    "governança, backend, infraestrutura, dados e aprendizado de máquina."
)

#━━━━━━━━━❮OpenAI Keys❯━━━━━━━━━
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

#━━━━━━━━━❮CORS❯━━━━━━━━━
ALLOWED_ORIGINS = ["*"]  # sobrescrito abaixo em produção (ver get_frontend_origins)

#━━━━━━━━━❮Logs (Railway – /tmp para evitar PermissionError)❯━━━━━━━━━
LOGS_DIR = "/tmp/pulso_logs"
os.makedirs(LOGS_DIR, exist_ok=True)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Configuração Geral da API❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
API_BASE_URL = "http://127.0.0.1:8000"



def get_frontend_origins():
    raw = os.getenv("FRONTEND_ORIGINS", "")
    if not raw:
        return None  # usa defaults do setup_cors
    return [o.strip() for o in raw.split(",") if o.strip()]


# Em produção, restringir origens (nunca "*") para reduzir superfície de ataque.
_env = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()
if _env == "production":
    _origins = get_frontend_origins()
    if _origins:
        ALLOWED_ORIGINS = _origins
    else:
        ALLOWED_ORIGINS = ["https://pulsoapi-production-d109.up.railway.app"]
#━━━━━━━━━❮Prompts: usar app.prompts.loader.load_prompt("analyse/base_refine") etc.❯━━━━━━━━━

#━━━━━━━━━❮API Base URL Railway❯━━━━━━━━━
# Railway usa RAILWAY_STATIC_URL ou API_BASE_URL; em dev usa localhost
_railway_url = os.getenv("RAILWAY_STATIC_URL") or os.getenv("API_BASE_URL")
if _railway_url:
    API_BASE_URL = _railway_url.rstrip("/")
elif _env == "production":
    API_BASE_URL = "https://pulsoapi-production-d109.up.railway.app"


#━━━━━━━━━❮Chaves que NUNCA devem ter valor exibido em log❯━━━━━━━━━
_SENSITIVE_ENV_KEYS = frozenset({
    "OPENAI_API_KEY", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
    "DATABASE_URL", "MONGO_URL", "MONGODB_URI", "MONGODB_URL", "REDIS_URL",
})


def _env_status(key: str) -> str:
    """Retorna apenas 'definida' ou 'não definida', nunca o valor (para chaves sensíveis)."""
    return "definida" if os.getenv(key) else "não definida"


#━━━━━━━━━❮Função para Debug das Variáveis Railway❯━━━━━━━━━
def print_railway_env(log: str):
    """
    Exibe status das variáveis de ambiente (sem expor valores sensíveis).
    Chaves de API, secrets e URLs de banco nunca são exibidas.
    """
    railway_keys = [
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_PROJECT_ID",
        "RAILWAY_SERVICE_NAME",
        "DATABASE_URL",
        "MONGO_URL",
        "MONGODB_URI",
        "MONGODB_URL",
        "REDIS_URL",
        "PORT",
        "OPENAI_API_KEY",
    ]

    print(f"\n[Pulso-{log}] Variáveis de ambiente (valores sensíveis não exibidos):\n")
    for key in railway_keys:
        if key in _SENSITIVE_ENV_KEYS:
            print(f"  {key}: {_env_status(key)}")
        else:
            value = os.getenv(key, "não definida")
            print(f"  {key}: {value}")

    print("\n— Fim do dump —\n")
