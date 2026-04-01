#━━━━━━━━━❮Inteligência de Dados – Query❯━━━━━━━━━
# POST /query: pergunta em linguagem natural + db_config; retorna SQL/consulta.
import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.query_get_models import (
    QueryGetInput,
    QueryGetOutput,
)
from app.InteligenciaDados.services.ID_services.query_get_service import QueryGetService

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados"],
)

_service = QueryGetService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/query",
    response_model=QueryGetOutput,
    status_code=status.HTTP_200_OK,
)
async def query_database(payload: QueryGetInput, user: dict = Depends(require_valid_access)) -> QueryGetOutput:
    """
    Endpoint de Inteligência de Dados.

    Recebe uma pergunta em linguagem natural + config do banco
    e devolve uma resposta humanizada baseada em dados SQL reais.
    Requer autenticação (Bearer token). SQL gerado é read-only (SELECT apenas).
    """
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _service.run, payload)
    except ValueError as e:
        detail = str(e) if not _is_production() else "Parâmetros inválidos."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a consulta.",
        )