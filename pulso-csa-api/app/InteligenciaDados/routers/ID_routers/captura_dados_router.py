#━━━━━━━━━❮Inteligência de Dados – Captura❯━━━━━━━━━
# POST /captura-dados: conecta MySQL/MongoDB, extrai estrutura e opcionalmente amostra.
import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.captura_dados_models import CapturaDadosInput, CapturaDadosOutput
from app.InteligenciaDados.services.ID_services.captura_dados_service import CapturaDadosService

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Captura"],
)

_service = CapturaDadosService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/captura-dados",
    response_model=CapturaDadosOutput,
    status_code=status.HTTP_200_OK,
)
async def captura_dados(payload: CapturaDadosInput, user: dict = Depends(require_valid_access)) -> CapturaDadosOutput:
    """
    Conecta à base de dados externa (MySQL ou MongoDB), extrai estrutura
    e gera relatório com tipo_base, tabelas/coleções, contagens e teor dos dados.
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
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erro ao conectar na base externa.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a captura.",
        )
