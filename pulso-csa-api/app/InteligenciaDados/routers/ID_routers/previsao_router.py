#━━━━━━━━━❮Inteligência de Dados – Previsão❯━━━━━━━━━
# POST /prever: aplica modelo salvo a dataset ou dados em tempo real.
import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.previsao_models import PrevisaoInput, PrevisaoOutput
from app.InteligenciaDados.services.ID_services.previsao_service import PrevisaoService

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Previsão"],
)

_service = PrevisaoService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/prever",
    response_model=PrevisaoOutput,
    status_code=status.HTTP_200_OK,
)
async def prever(payload: PrevisaoInput, user: dict = Depends(require_valid_access)) -> PrevisaoOutput:
    """
    Aplica modelo treinado (model_ref) a um dataset (dataset_ref) ou a registros em tempo real (dados).
    Use após criar-modelo-ml para obter model_ref. Ideal para previsões no chat.
    Requer autenticação (Bearer token).
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
            detail="Erro interno ao aplicar previsões.",
        )
