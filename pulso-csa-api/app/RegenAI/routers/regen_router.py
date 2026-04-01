import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request

from app.PulsoCSA.Python.core.entitlement.deps import require_valid_access
from app.PulsoCSA.Python.utils.idempotency import (
    gerar_run_id,
    registrar_idempotency_key,
    verificar_idempotency_key,
)

from RegenAI.models.regen_report import RegenReport
from RegenAI.models.regen_request import RegenRequest
from RegenAI.models.regen_status import RegenStatus
from RegenAI.storage.execution_cache import execution_cache
from RegenAI.workflow.regen_workflow import RegenWorkflow

router = APIRouter(prefix="/regenai", tags=["RegenAI"])
_workflow = RegenWorkflow()


@router.post("/run")
async def run_regenai(
    payload: RegenRequest,
    request: Request,
    user: dict = Depends(require_valid_access),
) -> Dict[str, Any]:
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        is_new, cached = verificar_idempotency_key(idempotency_key)
        if not is_new and cached:
            return cached

    usuario = payload.usuario or user.get("email") or user.get("_id") or "regenai"
    payload = payload.model_copy(update={"usuario": usuario})
    execution_id = gerar_run_id("regen")
    status = execution_cache.create_execution(execution_id, payload)
    request_headers = {}
    authorization = request.headers.get("Authorization")
    if authorization:
        request_headers["Authorization"] = authorization
    asyncio.create_task(_workflow.execute(execution_id, payload, request.app, request_headers))

    response = {
        "execution_id": execution_id,
        "status": status.status,
        "current_round": status.current_round,
        "max_rounds": status.max_rounds,
        "objective": status.objective,
        "scopes": status.scopes,
    }
    if idempotency_key:
        registrar_idempotency_key(idempotency_key, response)
    return response


@router.get("/status/{execution_id}", response_model=RegenStatus)
async def get_regen_status(
    execution_id: str,
    user: dict = Depends(require_valid_access),
) -> RegenStatus:
    status = execution_cache.get_status(execution_id)
    if status is None:
        raise HTTPException(status_code=404, detail="execution_id nao encontrado")
    return status


@router.get("/report/{execution_id}", response_model=RegenReport)
async def get_regen_report(
    execution_id: str,
    user: dict = Depends(require_valid_access),
) -> RegenReport:
    report = execution_cache.get_report(execution_id)
    if report is None:
        raise HTTPException(status_code=404, detail="relatorio ainda nao disponivel")
    return report


@router.get("/logs/{execution_id}")
async def get_regen_logs(
    execution_id: str,
    user: dict = Depends(require_valid_access),
) -> Dict[str, Any]:
    status = execution_cache.get_status(execution_id)
    if status is None:
        raise HTTPException(status_code=404, detail="execution_id nao encontrado")
    return {
        "execution_id": execution_id,
        "status": status.status,
        "logs": execution_cache.get_logs(execution_id),
        "live_results": execution_cache.get_live_results(execution_id),
        "exception_questions": execution_cache.get_exception_questions(execution_id),
    }

