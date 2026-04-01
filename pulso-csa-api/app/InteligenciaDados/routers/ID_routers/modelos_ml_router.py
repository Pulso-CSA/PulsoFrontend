#━━━━━━━━━❮Inteligência de Dados – Modelos ML❯━━━━━━━━━
# POST /criar-modelo-ml, GET /listar-modelos (múltiplas versões).
import asyncio
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.modelos_ml_models import ModelosMLInput, ModelosMLOutput
from app.InteligenciaDados.services.ID_services.modelos_ml_service import ModelosMLService
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import list_model_refs

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Modelos ML"],
)

_service = ModelosMLService()


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


@router.post(
    "/criar-modelo-ml",
    response_model=ModelosMLOutput,
    status_code=status.HTTP_200_OK,
)
async def criar_modelo_ml(payload: ModelosMLInput, user: dict = Depends(require_valid_access)) -> ModelosMLOutput:
    """
    Compara e seleciona modelos de ML com limiar mínimo de qualidade (70% acurácia).
    Retorna modelo escolhido, métricas e recomendações. Usa LLM para explicação.
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
            detail="Erro interno ao criar modelo.",
        )


@router.get("/listar-modelos")
def listar_modelos(id_requisicao: str, usuario: Optional[str] = None, user: dict = Depends(require_valid_access)):
    """Lista todos os model_ref disponíveis para o id_requisicao (múltiplas versões / A-B). Requer autenticação."""
    usuario_final = usuario or user.get("email") or user.get("_id")
    refs = list_model_refs(usuario_final, id_requisicao)
    return {"id_requisicao": id_requisicao, "lista_model_refs": refs}
