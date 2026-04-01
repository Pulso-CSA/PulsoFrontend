#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Core de Conexão MongoDB❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import threading
from datetime import datetime
from typing import Any, Optional
from pymongo import MongoClient, ASCENDING

# .env é carregado em main.py antes de qualquer import. Evitar load_dotenv redundante.

#━━━━━━━━━❮Detecção Automática: Railway → Cloud | Local → Docker❯━━━━━━━━━

# Railway define automaticamente estas variáveis:
RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID")

if RAILWAY:
    #━━━━━━━━━❮Modo Railway (Cloud)❯━━━━━━━━━
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pulso_database")

else:
    #━━━━━━━━━❮Modo Local❯━━━━━━━━━
    # Use localhost quando rodando uvicorn fora do Docker; use mongo:27017 dentro do docker-compose
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pulso_database")

#━━━━━━━━━❮Coleções❯━━━━━━━━━

COLLECTIONS = {
    "governance": os.getenv("GOVERNANCE_COLLECTION", "governance_layer"),
    "architecture": os.getenv("ARCHITECTURE_COLLECTION", "architecture_layer"),
    "execution": os.getenv("EXECUTION_COLLECTION", "execution_layer"),
    "login": os.getenv("LOGIN_COLLECTION", "login_layer"),
    "struc_analise": os.getenv("STRUC_ANAL", "anal_correct_layer"),
    "auto_cor_arq": os.getenv("AUTO_COR_ARQ", "auto_cor_arq_layer"),
    "code_plan": os.getenv("CODE_PLAN", "code_plan_layer"),
    "profiles": os.getenv("PROFILES_COLLECTION", "profiles"),
    "subscriptions": os.getenv("SUBSCRIPTIONS_COLLECTION", "subscriptions"),
    "invoices": os.getenv("INVOICES_COLLECTION", "invoices"),
    "service_entitlements": "service_entitlements",
    "chat_history": "chat_history",
    "stripe_webhook_events": "stripe_webhook_events",
    "id_agendamentos": "id_agendamentos",
    # Auth: blacklist de tokens e reset de senha (obrigatório para logout/reset funcionar)
    "token_blacklist": "token_blacklist",
    "password_reset_tokens": "password_reset_tokens",
    # Versão do app Electron (patches/updates)
    "app_versions": os.getenv("APP_VERSIONS_COLLECTION", "app_versions"),
    # SFAP – Sistema Financeiro Administrativo Pulso (receita planos + custo operação)
    "financeiro": os.getenv("FINANCEIRO_COLLECTION", "Financeiro"),
    # Insights conversacional (Power BI chat) — sessões, histórico de prompts, artefatos gerados
    "insights_sessions": os.getenv("INSIGHTS_SESSIONS_COLLECTION", "insights_sessions"),
    "insights_prompts": os.getenv("INSIGHTS_PROMPTS_COLLECTION", "insights_prompts"),
    "insights_generated": os.getenv("INSIGHTS_GENERATED_COLLECTION", "insights_charts"),
}

_client: Optional[MongoClient] = None

# ✅ Fallback leve para quando o Mongo estiver indisponível (não derruba o app)
class _NoOpCollection:
    def __init__(self, name: str):
        self.name = name
    def create_index(self, *a, **kw): return None
    def insert_one(self, *a, **kw): return type("Res", (), {"inserted_id": None})()
    def update_one(self, *a, **kw): return type("Res", (), {"modified_count": 0})()
    def find_one(self, *a, **kw): return None
    def delete_one(self, *a, **kw): return type("Res", (), {"deleted_count": 0})()
    def find(self, *a, **kw): return []
    def aggregate(self, *a, **kw): return []

#━━━━━━━━━❮Criação do Cliente MongoDB❯━━━━━━━━━
_client_lock = threading.Lock()


def get_client() -> MongoClient:
    """Retorna o cliente MongoDB (singleton). Thread-safe. Não derruba a app se indisponível."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = MongoClient(
                    MONGO_URI,
                    connectTimeoutMS=8000,
                    serverSelectionTimeoutMS=8000,
                )
                try:
                    _client.server_info()
                    print(f"[DB] MongoDB conectado | URI={MONGO_URI[:50]}...")
                except Exception as e:
                    print(f"[DB] AVISO: Mongo indisponível no startup | URI={MONGO_URI} | erro={type(e).__name__}: {e}")
    return _client

#━━━━━━━━━❮Selecionar Coleção❯━━━━━━━━━
def get_collection(layer: str = "governance"):
    """Obtém a coleção da camada informada (governance, architecture, execution, etc).
       Se o Mongo estiver indisponível, retorna NoOpCollection para não quebrar o startup/import."""
    db = get_client()[MONGO_DB_NAME]

    # Aceita chave ("execution") ou valor ("execution_layer")
    collection_name = COLLECTIONS.get(layer, COLLECTIONS["governance"])

    # Coleções que NÃO devem ter índice id_requisicao (usar COLLECTIONS[...] para bater com o nome real, ex.: login → login_layer)
    _layers_skip_id_req = (
        "profiles",
        "login",
        "token_blacklist",
        "password_reset_tokens",
        "subscriptions",
        "invoices",
        "service_entitlements",
        "chat_history",
        "stripe_webhook_events",
        "id_agendamentos",
        "app_versions",
        "financeiro",
        "insights_sessions",
        "insights_prompts",
        "insights_generated",
    )
    collections_without_id_requisicao = [COLLECTIONS[k] for k in _layers_skip_id_req]

    try:
        coll = db[collection_name]
        # Cria índice id_requisicao apenas para coleções que precisam dele
        if collection_name not in collections_without_id_requisicao:
            coll.create_index([("id_requisicao", ASCENDING)], unique=True)
        return coll
    except Exception as e:
        print(f"[DB] indisponível, usando NoOpCollection('{collection_name}'): {e}")
        return _NoOpCollection(collection_name)

#━━━━━━━━━❮Timestamp❯━━━━━━━━━
def timestamp() -> str:
    return datetime.utcnow().isoformat()
