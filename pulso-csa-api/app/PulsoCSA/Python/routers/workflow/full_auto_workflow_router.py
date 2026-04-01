#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow – Full Auto (Code Plan → Code Writer)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from datetime import datetime
from functools import partial

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from services.agents.correct_services.code_plan_services.code_plan_service import run_code_plan
from services.agents.correct_services.code_writer_services.code_writer_service import run_code_writer
from models.correct_models.code_writer_models.code_writer_models import CodeWriterRequest
from utils.log_manager import add_log
from utils.path_validation import sanitize_root_path

router = APIRouter(prefix="/workflow/correct", tags=["Workflow – Correção Full Auto"])


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Request Model❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class FullAutoWorkflowRequest(BaseModel):
    usuario: str
    prompt: str
    root_path: str
    dry_run: bool = False


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Full Auto Endpoint❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _run_full_auto_sync(request: FullAutoWorkflowRequest, root_path: str) -> dict:
    """Executa o workflow síncrono (para run_in_executor)."""
    plan_result = run_code_plan(
        prompt=request.prompt,
        root_path=root_path,
        usuario=request.usuario,
    )
    id_req = plan_result.get("id_requisicao")
    if not id_req:
        raise RuntimeError("Missing id_requisicao from Code Plan.")
    writer_request = CodeWriterRequest(
        id_requisicao=id_req,
        root_path=root_path,
        usuario=request.usuario,
        dry_run=request.dry_run,
    )
    writer_result = run_code_writer(writer_request)
    return {"plan_result": plan_result, "writer_result": writer_result, "id_req": id_req}


@router.post("/full-run")
async def full_auto_workflow(request: FullAutoWorkflowRequest, user: dict = Depends(require_valid_access)):
    """Executa workflow completo de correção. Requer autenticação (Bearer token)."""
    log_type = "info"
    start_time = datetime.utcnow().isoformat()
    if not request.usuario:
        request.usuario = user.get("email") or user.get("_id")

    root_path = sanitize_root_path(request.root_path) if request.root_path else None
    if not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})

    add_log(log_type, f"[full_auto_workflow] Starting full workflow for user={request.usuario}", "workflow")

    try:
        loop = asyncio.get_event_loop()
        out = await loop.run_in_executor(None, partial(_run_full_auto_sync, request, root_path))
    except RuntimeError as e:
        add_log("error", f"[full_auto_workflow] {e}", "workflow")
        raise HTTPException(status_code=500, detail="Failed to retrieve id_requisicao from Code Plan.")

    plan_result = out["plan_result"]
    writer_result = out["writer_result"]
    id_req = out["id_req"]
    add_log(log_type, f"[full_auto_workflow] Code Writer finished for id={id_req}", "workflow")

    return {
        "workflow": "full_auto_correct",
        "started_at": start_time,
        "ended_at": datetime.utcnow().isoformat(),
        "usuario": request.usuario,
        "root_path": root_path,
        "prompt": request.prompt,
        "id_requisicao": id_req,
        "code_plan": plan_result,
        "code_writer": writer_result,
    }
