#━━━━━━━━━❮Config – Usuários Isentos e Planos❯━━━━━━━━━
"""
Usuários isentos de pagamento (sócios e exceções).
Acesso 100% à plataforma sem assinatura.
"""
import os
from typing import Set

# Lista de nomes/emails de usuários isentos. Configurável via env.
# Default: G!, E!, T!, V!, P! (sócios)
_EXEMPT_RAW = os.getenv("PAYMENT_EXEMPT_USERS", "G!,E!,T!,V!,P!")
PAYMENT_EXEMPT_USERS: Set[str] = {
    u.strip() for u in _EXEMPT_RAW.split(",") if u.strip()
}

# Max serviços por plano (regra de negócio)
PLAN_MAX_SERVICES = {
    "basic": 1,
    "plus": 2,
    "pro": 3,
    "elite": 4,
}

# IDs dos serviços/módulos (ordem para default)
SERVICE_IDS = [
    "id",           # Inteligência de Dados (chat, query, captura, etc.)
    "finops",       # FinOps
    "comprehension",# Compreensão
    "governance",   # Governança
    "workflow",     # Workflow (correct, full_auto)
    "infra",        # Infra (Terraform)
    "pipeline",     # Pipeline (teste, correção, segurança)
    "creation",     # Criação (estrutura, código)
    "deploy",       # Deploy
    "venv",         # Venv
    "test",         # Test
    "analise",      # Análise (estrutural, backend, infra)
    "correct",      # Correção (code plan, writer, implementer)
    "tela_teste",   # Tela de teste
]
SERVICE_IDS_SET = set(SERVICE_IDS)


def is_payment_exempt(user: dict) -> bool:
    """
    Verifica se o usuário é isento de pagamento (sócio ou exceção).
    Compara email e name (username) contra a lista PAYMENT_EXEMPT_USERS.
    """
    if not user:
        return False
    email = (user.get("email") or "").strip()
    name = (user.get("name") or "").strip()
    # Compara exato (case-sensitive para G!, E!, etc.)
    return email in PAYMENT_EXEMPT_USERS or name in PAYMENT_EXEMPT_USERS
