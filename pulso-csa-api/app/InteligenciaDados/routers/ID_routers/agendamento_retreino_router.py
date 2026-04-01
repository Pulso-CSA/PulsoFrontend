#━━━━━━━━━❮Inteligência de Dados – Agendamento❯━━━━━━━━━
# Router: agendar-retreino, executar-retreino-agendado, agendamentos-pendentes.
import asyncio
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.agendamento_retreino_models import (
    AgendamentoRetreinoInput,
    AgendamentoRetreinoOutput,
    ExecutarRetreinoOutput,
)
from app.InteligenciaDados.services.ID_services.agendamento_retreino_service import AgendamentoRetreinoService

router = APIRouter(
    prefix="/inteligencia-dados",
    tags=["Inteligência de Dados – Agendamento"],
)

_service = AgendamentoRetreinoService()


class ExecutarRetreinoBody(BaseModel):
    agendamento_id: str = Field(..., min_length=1)


@router.post(
    "/agendar-retreino",
    response_model=AgendamentoRetreinoOutput,
    status_code=status.HTTP_200_OK,
)
async def agendar_retreino(payload: AgendamentoRetreinoInput, user: dict = Depends(require_valid_access)) -> AgendamentoRetreinoOutput:
    """
    Registra um agendamento de retreino. Para executar, chame POST /inteligencia-dados/executar-retreino-agendado
    com o agendamento_id retornado (ou use um cron externo).
    Requer autenticação (Bearer token).
    """
    if not payload.usuario:
        payload.usuario = user.get("email") or user.get("_id")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _service.agendar, payload)


@router.post(
    "/executar-retreino-agendado",
    response_model=ExecutarRetreinoOutput,
    status_code=status.HTTP_200_OK,
)
async def executar_retreino_agendado(body: ExecutarRetreinoBody, user: dict = Depends(require_valid_access)) -> ExecutarRetreinoOutput:
    """Executa um retreino previamente agendado. Body: {"agendamento_id": "xxx"}. Requer autenticação."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: _service.executar_um(body.agendamento_id))


@router.get("/agendamentos-pendentes")
async def listar_agendamentos_pendentes(user: dict = Depends(require_valid_access)):
    """Lista agendamentos de retreino ainda não executados. Requer autenticação."""
    loop = asyncio.get_event_loop()
    pendentes = await loop.run_in_executor(None, _service.listar_pendentes)
    return {"agendamentos": pendentes}
