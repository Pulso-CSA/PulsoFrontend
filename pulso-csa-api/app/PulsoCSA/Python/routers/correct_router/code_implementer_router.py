#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router – Code Implementer (C4)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from pydantic import BaseModel, Field

from services.agents.correct_services.code_implementer_services.code_implementer_service import (
    run_code_implementer,
)
from models.correct_models.code_implementer_models.code_implementer_models import (
    CodeImplementerRequest,
    CodeImplementerExecutionResult,
)
from utils.path_validation import sanitize_root_path

router = APIRouter(
    prefix="/code-implementer",
    tags=["Code Implementer – C4"],
)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Schemas❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class CodeImplementerHTTPInput(BaseModel):
    """
    Payload enviado pelo usuário para executar C4 manualmente.
    """

    id_requisicao: str = Field(
        ...,
        description="O mesmo id gerado em C2/C3. O Code Implementer só funciona com Code Plan existente.",
    )
    root_path: str = Field(..., description="Caminho raiz do projeto.")
    usuario: str = Field(..., description="Usuário executor.")
    dry_run: bool = Field(False, description="Se True, não grava arquivos.")


class CodeImplementerHTTPResponse(BaseModel):
    """
    Resposta HTTP estruturada de C4.
    """

    id_requisicao: str
    root_path: str
    usuario: str
    dry_run: bool
    status: str
    files: list[Dict[str, Any]]
    errors: list[str]
    executed_at: str


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Endpoint – Run C4❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

@router.post("/run", response_model=CodeImplementerHTTPResponse)
async def run_code_implementer_endpoint(
    payload: CodeImplementerHTTPInput,
    user: dict = Depends(auth_and_rate_limit),
) -> CodeImplementerHTTPResponse:
    """
    Executa **C4 – Code Implementer**, que transforma os stubs criados pelo Code Writer
    em arquivos de código reais, completos e válidos.

    Fluxo:
    - Lê Code Plan (C2b) via id_requisicao.
    - Carrega stubs criados pelo Code Writer (C3).
    - Gera implementações reais usando LLM.
    - Valida sintaxe.
    - Grava arquivo final (ou dry_run).
    - Persiste resultado no MongoDB.
    """

    if not payload.id_requisicao.strip():
        raise HTTPException(
            status_code=400,
            detail="id_requisicao is required and must not be empty.",
        )

    root_path = sanitize_root_path(payload.root_path) if payload.root_path else None
    if not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})

    request = CodeImplementerRequest(
        id_requisicao=payload.id_requisicao,
        root_path=root_path,
        usuario=payload.usuario,
        dry_run=payload.dry_run,
    )

    result: CodeImplementerExecutionResult = run_code_implementer(request)

    return CodeImplementerHTTPResponse(**result.model_dump())
