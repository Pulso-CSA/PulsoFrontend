#━━━━━━━━━❮Inteligência de Dados – Análise Estatística❯━━━━━━━━━
# POST /analise-estatistica: métricas, correlações, resposta à pergunta, insights.
import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.analise_estatistica_models import (
    AnaliseEstatisticaInput,
    AnaliseEstatisticaOutput,
)
from app.InteligenciaDados.services.ID_services.analise_estatistica_service import AnaliseEstatisticaService

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Análise Estatística"],
)

_service = AnaliseEstatisticaService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/analise-estatistica",
    response_model=AnaliseEstatisticaOutput,
    status_code=status.HTTP_200_OK,
)
async def analise_estatistica(payload: AnaliseEstatisticaInput, user: dict = Depends(require_valid_access)) -> AnaliseEstatisticaOutput:
    """
    Gera métricas, correlações, insights e sugere modelos de ML.
    Usa LLM para narrativa.
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
            detail="Erro interno na análise estatística.",
        )
