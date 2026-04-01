#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Contexto por request – API key (nunca armazenada em DB)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Chave OpenAI enviada pelo usuário (plano BYOK) fica apenas em memória durante o request.
Nunca é persistida em banco.
"""

from contextvars import ContextVar
from typing import Optional

_request_openai_api_key: ContextVar[Optional[str]] = ContextVar(
    "request_openai_api_key",
    default=None,
)


def set_request_api_key(api_key: Optional[str]) -> None:
    """Define a chave OpenAI para o request atual (em memória, descartada ao fim)."""
    _request_openai_api_key.set(api_key)


def get_request_api_key() -> Optional[str]:
    """Retorna a chave OpenAI do request atual, se houver."""
    return _request_openai_api_key.get()


def clear_request_api_key() -> None:
    """Limpa a chave do contexto (segurança ao fim do request)."""
    try:
        _request_openai_api_key.set(None)
    except LookupError:
        pass
