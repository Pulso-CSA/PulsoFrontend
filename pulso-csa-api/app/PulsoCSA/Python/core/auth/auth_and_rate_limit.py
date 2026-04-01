#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Auth + Rate Limit por usuário❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import Depends, HTTPException

from core.auth.auth_deps import verificar_token
from utils.rate_limit import check_rate_limit_user, record_user_request


async def auth_and_rate_limit(user: dict = Depends(verificar_token)) -> dict:
    """
    Dependency: autenticação obrigatória + rate limit por usuário.
    Retorna user dict. Levanta 429 se rate limit excedido.
    """
    usuario = user.get("email") or user.get("_id") or "anonymous"
    allowed, _ = check_rate_limit_user(usuario)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"message": "Limite de requisições por usuário excedido. Tente novamente em alguns minutos.", "code": "RATE_LIMIT_USER_EXCEEDED"},
        )
    record_user_request(usuario)
    return user
