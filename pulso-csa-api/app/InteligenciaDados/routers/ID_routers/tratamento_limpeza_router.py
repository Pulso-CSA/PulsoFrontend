#━━━━━━━━━❮Inteligência de Dados – Tratamento e Limpeza❯━━━━━━━━━
# POST /tratamento-limpeza: ETL (duplicatas, missing, outliers); retorna dataset_pronto.
import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.tratamento_limpeza_models import TratamentoLimpezaInput, TratamentoLimpezaOutput
from app.InteligenciaDados.services.ID_services.tratamento_limpeza_service import TratamentoLimpezaService

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Tratamento e Limpeza"],
)

_service = TratamentoLimpezaService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/tratamento-limpeza",
    response_model=TratamentoLimpezaOutput,
    status_code=status.HTTP_200_OK,
)
async def tratamento_limpeza(payload: TratamentoLimpezaInput, user: dict = Depends(require_valid_access)) -> TratamentoLimpezaOutput:
    """
    Executa pipeline de ETL e limpeza conforme análise inicial.
    Retorna ações, justificativas e referência ao dataset pronto.
    Requer autenticação (Bearer token).
    """
    try:
        if not payload.usuario:
            payload.usuario = user.get("email") or user.get("_id")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _service.run, payload)
    except ValueError as e:
        detail = str(e) if not _is_production() else "Parâmetros inválidos."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no tratamento.",
        )
