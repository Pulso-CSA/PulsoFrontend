#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router – Workflow Correção / Estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from pydantic import BaseModel, Field

from utils.path_validation import sanitize_root_path, is_production
from workflow.correct_workflow.workflow_core_cor import run_correct_workflow

from app.pulso_csa_time_limits import (
    CsaRequestBudget,
    CSA_WORKFLOW_WALL_CLOCK_SEC,
    csa_timeout_http_detail,
)

router = APIRouter(
    prefix="/workflow/correct",
    tags=["Workflow – Correção Estrutural"],
)


class CorrectWorkflowRequest(BaseModel):
    """
    Request payload for the full correction / structural workflow.
    """

    usuario: str = Field(
        ...,
        description="Identificação do usuário que disparou o workflow.",
    )
    prompt: str = Field(
        ...,
        description="Prompt cru informado pelo usuário.",
    )
    root_path: str = Field(
        ...,
        description="Caminho raiz do projeto no filesystem.",
    )


class CorrectWorkflowResponse(BaseModel):
    """
    High-level response for the full correction / structural workflow:

    - governanca (C1)
    - analise_estrutural / plano_de_mudancas (C2)
    - plano_de_codigo (C2b – Code Plan)
    - execucao estrutural (C2 → filesystem)
    - code_writer (C3 – stubs + integração)
    - code_implementer (C4 – implementação real)
    """

    id_requisicao: str
    projeto_status: str
    governanca: Dict[str, Any]
    analise_estrutural: Dict[str, Any] | None = None
    blueprint: Dict[str, Any] | None = None
    plano_de_mudancas: Dict[str, Any] | None = None
    execucao: Dict[str, Any] | None = None
    plano_de_codigo: Dict[str, Any] | None = None
    code_writer: Dict[str, Any] | None = None
    code_implementer: Dict[str, Any] | None = None
    test_run: Dict[str, Any] | None = None
    pipeline_analise_retorno: Dict[str, Any] | None = None
    pipeline_correcao: Dict[str, Any] | None = None
    pipeline_seguranca_codigo_pos: Dict[str, Any] | None = None
    pipeline_seguranca_infra_pos: Dict[str, Any] | None = None


@router.post("/run", response_model=CorrectWorkflowResponse)
async def run_correct_workflow_endpoint(
    payload: CorrectWorkflowRequest,
    user: dict = Depends(require_valid_access),
) -> CorrectWorkflowResponse:
    """
    Executa o workflow completo de correção / estrutura.

    Este endpoint dispara todas as camadas:

    - Governança (C1)
    - Análise estrutural e plano de mudanças (C2)
    - Code Plan (C2b)
    - Code Writer – stubs, criação de arquivos e integração (C3)
    - Code Implementer – implementação real dos arquivos (C4)
    - Teste automatizado (C5) + Pipeline de autocorreção (11→12→13→13.1→13.2).
    Última coisa: código pronto, estável, funcional.
    Requer autenticação (Bearer token).
    """
    # Usuario obrigatório do token
    if not payload.usuario:
        payload.usuario = user.get("email") or user.get("_id")

    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    root_path = sanitize_root_path(payload.root_path) if payload.root_path else None
    if not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})

    try:
        loop = asyncio.get_event_loop()
        budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
        result = await budget.run_in_executor(
            loop,
            lambda: run_correct_workflow(
                log_type="info",
                prompt=payload.prompt,
                usuario=payload.usuario,
                root_path=root_path,
            ),
        )
        return CorrectWorkflowResponse(**result)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=csa_timeout_http_detail())
    except Exception as e:
        msg = "Erro ao executar workflow de correção." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "CORRECT_WORKFLOW_FAILED", "message": msg})
