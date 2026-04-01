#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router – Desenvolvimento (Workflow Completo)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from utils.path_validation import sanitize_root_path, is_production
from utils.log_manager import add_log
from workflow.creator_workflow.workflow_core import run_workflow_pipeline

from app.pulso_csa_time_limits import (
    CsaRequestBudget,
    CSA_WORKFLOW_WALL_CLOCK_SEC,
    csa_timeout_http_detail,
)

router = APIRouter(prefix="/deve", tags=["Desenvolvimento – Workflow Completo"])
SOURCE = "deve_router"


class DeveRequest(BaseModel):
    """Request para o workflow de desenvolvimento completo."""
    prompt: str = Field(..., min_length=1, description="Descrição do que criar (API, CLI, etc.)")
    usuario: str = Field(default="anonymous", description="Identificador do usuário")
    root_path: Optional[str] = Field(None, description="Caminho raiz onde o projeto será gerado")


@router.post("/run")
async def run_deve_workflow(payload: DeveRequest, user: dict = Depends(require_valid_access)):
    """
    Executa o workflow completo de desenvolvimento:
    Camada 1 (Governança) + Camada 2 (Arquitetura) + Camada 3 (Estrutura + Código).
    Requer root_path válido para gerar o projeto.
    """
    prompt = (payload.prompt or "").strip()
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail={"code": "PROMPT_EMPTY", "message": "O campo 'prompt' não pode estar vazio."},
        )

    root_path = sanitize_root_path(payload.root_path) if payload.root_path else None
    if not root_path:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ROOT_PATH_REQUIRED",
                "message": "root_path é obrigatório e deve ser um caminho válido (ex: C:\\projetos\\meu_app).",
            },
        )

    usuario = payload.usuario or user.get("email") or user.get("_id") or "anonymous"
    add_log("info", f"deve/run iniciado | usuario={usuario} | root_path={root_path}", SOURCE)

    try:
        loop = asyncio.get_event_loop()
        budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
        result = await budget.run_in_executor(
            loop,
            lambda: run_workflow_pipeline(prompt, usuario, root_path),
        )
        add_log("info", "deve/run concluído com sucesso", SOURCE)
        return result
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=csa_timeout_http_detail())
    except Exception as e:
        add_log("error", f"deve/run falhou: {type(e).__name__}: {e}", SOURCE)
        msg = "Erro ao executar workflow de desenvolvimento." if is_production() else str(e)
        raise HTTPException(
            status_code=500,
            detail={"code": "DEVE_RUN_FAILED", "message": msg},
        )
