#━━━━━━━━━❮Inteligência de Dados – Análise Inicial❯━━━━━━━━━
# POST /analise-dados-inicial: objetivo, variáveis alvo e tratamentos sugeridos (LLM).
import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.analise_dados_models import AnaliseDadosInicialInput, AnaliseDadosInicialOutput
from app.InteligenciaDados.services.ID_services.analise_dados_service import AnaliseDadosService

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Análise Inicial"],
)

_service = AnaliseDadosService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/analise-dados-inicial",
    response_model=AnaliseDadosInicialOutput,
    status_code=status.HTTP_200_OK,
)
async def analise_dados_inicial(
    payload: AnaliseDadosInicialInput,
    user: dict = Depends(require_valid_access),
) -> AnaliseDadosInicialOutput:
    """
    Interpreta o retorno de /captura-dados e propõe objetivo de análise,
    variáveis alvo e tratamentos necessários. Usa LLM.
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
            detail="Erro interno na análise inicial.",
        )
