#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router – Aliases da spec (rotas no raiz como documentado)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Expõe as rotas exatamente como na especificação: /input, /refinar, /validar,
/analise-estrutura, /analise-backend, /analise-infra, /seguranca-infra,
/seguranca-codigo, /criar-estrutura, /criar-codigo.
As rotas com prefixo (/governance/*, /backend/*, /infra/*, /execution/*) continuam válidas.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from models.analise_models.governance_models import (
    PromptRequest,
    RefineRequest,
    ValidateRequest,
)
from models.analise_models.backend_models import (
    AnalysisStructureRequest,
    AnalysisStructureResponse,
    AnalysisBackendRequest,
    AnalysisBackendResponse,
    AnalysisBackendDoc,
    SecurityCodeRequest,
    SecurityCodeResponse,
)
from models.analise_models.infra_models import (
    AnalysisInfraRequest,
    AnalysisInfraResponse,
    SecurityInfraRequest,
    SecurityInfraResponse,
)
from models.creation_models.execution_models import ExecutionRequest, ManifestResponse

from routers.analise_router.governance_router import (
    _receive_prompt_impl,
    _refine_prompt_impl,
    _validate_prompt_impl,
)
from agents.architecture.planning.agent_structure import analyze_structure
from agents.architecture.planning.agent_backend import analyze_backend
from agents.architecture.planning.agent_sec_code import analyze_code_security
from agents.architecture.planning.agent_infra import analyze_infra
from agents.architecture.planning.agent_sec_infra import analyze_infra_security
from agents.execution.agent_structure_creator import create_structure_from_report
from agents.execution.agent_code_creator import create_code_from_reports
from workflow.creator_workflow.workflow_steps import execute_layer2
from utils.log_manager import add_log
from utils.path_validation import sanitize_root_path, is_production

router = APIRouter(tags=["Spec – Aliases (rotas da documentação)"])
SOURCE = "spec_aliases"


#━━━━━━━━━❮Camada 1 – Aliases❯━━━━━━━━━

@router.post("/input")
async def input_alias(request: PromptRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /input (equivalente a POST /governance/input)."""
    add_log("info", "alias /input chamado", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        out = await loop.run_in_executor(None, _receive_prompt_impl, request)
        add_log("info", f"alias /input concluído | id_requisicao={out['id_requisicao']}", SOURCE)
        return out
    except Exception as e:
        add_log("error", f"alias /input falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


@router.post("/refinar")
async def refinar_alias(request: RefineRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /refinar (equivalente a POST /governance/refine)."""
    add_log("info", f"alias /refinar chamado | id_requisicao={request.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _refine_prompt_impl, request)
    except Exception as e:
        add_log("error", f"alias /refinar falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


@router.post("/validar")
async def validar_alias(request: ValidateRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /validar (equivalente a POST /governance/validate)."""
    add_log("info", f"alias /validar chamado | id_requisicao={request.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _validate_prompt_impl, request)
    except Exception as e:
        add_log("error", f"alias /validar falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


#━━━━━━━━━❮Camada 2 – Aliases❯━━━━━━━━━


from pydantic import BaseModel, Field


class AnaliseCamada2Request(BaseModel):
    """Request para execução paralela da Camada 2 (estrutura + backend + infra + seg)."""
    id_requisicao: str = Field(..., description="ID da requisição (Camada 1)")
    refined_prompt: str = Field(..., description="Prompt refinado")
    root_path: str | None = Field(None, description="Caminho raiz para relatórios")


@router.post("/analise-camada2")
async def analise_camada2_alias(
    req: AnaliseCamada2Request,
    user: dict = Depends(require_valid_access),
):
    """
    Executa Camada 2 inteira em uma requisição (paraleliza infra + sec_code).
    Substitui 5 chamadas sequenciais por 1.
    """
    id_requisicao = req.id_requisicao
    refined_prompt = req.refined_prompt
    root_path = req.root_path
    if not id_requisicao or not refined_prompt:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "id_requisicao e refined_prompt são obrigatórios."},
        )
    add_log("info", f"alias /analise-camada2 | id_requisicao={id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: execute_layer2(id_requisicao, refined_prompt, root_path),
        )
        return result
    except Exception as e:
        add_log("error", f"alias /analise-camada2 falhou: {type(e).__name__}: {e}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


@router.post("/analise-estrutura", response_model=AnalysisStructureResponse)
async def analise_estrutura_alias(req: AnalysisStructureRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /analise-estrutura."""
    add_log("info", f"alias /analise-estrutura | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        estrutura = await loop.run_in_executor(None, analyze_structure, req.id_requisicao)
        return AnalysisStructureResponse(
            id_requisicao=req.id_requisicao,
            estrutura_arquivos=estrutura,
        )
    except Exception as e:
        add_log("error", f"alias /analise-estrutura falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


@router.post("/analise-backend", response_model=AnalysisBackendResponse)
async def analise_backend_alias(req: AnalysisBackendRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /analise-backend."""
    add_log("info", f"alias /analise-backend | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        backend_doc = await loop.run_in_executor(None, lambda: analyze_backend(req.id_requisicao, req.estrutura_arquivos))
        return AnalysisBackendResponse(
            id_requisicao=req.id_requisicao,
            backend=AnalysisBackendDoc(**backend_doc),
        )
    except Exception as e:
        add_log("error", f"alias /analise-backend falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


@router.post("/analise-infra", response_model=AnalysisInfraResponse)
async def analise_infra_alias(req: AnalysisInfraRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /analise-infra."""
    add_log("info", f"alias /analise-infra | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        infra_doc = await loop.run_in_executor(None, lambda: analyze_infra(req.id_requisicao, req.estrutura_arquivos, req.backend))
        return AnalysisInfraResponse(
            id_requisicao=req.id_requisicao,
            infraestrutura=infra_doc,
        )
    except Exception as e:
        add_log("error", f"alias /analise-infra falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


@router.post("/seguranca-infra", response_model=SecurityInfraResponse)
async def seguranca_infra_alias(req: SecurityInfraRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /seguranca-infra."""
    add_log("info", f"alias /seguranca-infra | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, lambda: analyze_infra_security(req.id_requisicao, req.infraestrutura))
        return SecurityInfraResponse(
            id_requisicao=req.id_requisicao,
            seguranca_infra=report,
        )
    except Exception as e:
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


def _backend_to_dict(backend):
    """Compatível com Pydantic v1 (.dict()) e v2 (.model_dump())."""
    if getattr(backend, "model_dump", None):
        return backend.model_dump()
    return backend.dict()


@router.post("/seguranca-codigo", response_model=SecurityCodeResponse)
async def seguranca_codigo_alias(req: SecurityCodeRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /seguranca-codigo."""
    add_log("info", f"alias /seguranca-codigo | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        backend_dict = _backend_to_dict(req.backend)
        report = await loop.run_in_executor(None, lambda: analyze_code_security(req.id_requisicao, backend_dict))
        return SecurityCodeResponse(
            id_requisicao=req.id_requisicao,
            seguranca_codigo=report,
        )
    except Exception as e:
        add_log("error", f"alias /seguranca-codigo falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})


#━━━━━━━━━❮Camada 3 – Aliases❯━━━━━━━━━

@router.post("/criar-estrutura", response_model=ManifestResponse)
async def criar_estrutura_alias(request: ExecutionRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /criar-estrutura."""
    root_path = sanitize_root_path(request.root_path) if request.root_path else None
    if request.root_path and not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    root_path = root_path or request.root_path
    add_log("info", f"alias /criar-estrutura | id_requisicao={request.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: create_structure_from_report(root_path, request.id_requisicao))
        if result.get("status") != "sucesso":
            raise HTTPException(status_code=400, detail=result.get("erro") or result.get("mensagem", "Falha ao criar estrutura"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"alias /criar-estrutura falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro ao criar estrutura." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "CRIAR_ESTRUTURA_FAILED", "message": _msg})


@router.post("/criar-codigo")
async def criar_codigo_alias(request: ExecutionRequest, user: dict = Depends(require_valid_access)):
    """Alias da spec: POST /criar-codigo (body: id_requisicao, root_path)."""
    root_path = sanitize_root_path(request.root_path) if request.root_path else None
    if request.root_path and not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    root_path = root_path or request.root_path
    add_log("info", f"alias /criar-codigo | id_requisicao={request.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: create_code_from_reports(root_path, request.id_requisicao))
        add_log("info", f"alias /criar-codigo concluído | id_requisicao={request.id_requisicao}", SOURCE)
        return {
            "id_requisicao": request.id_requisicao,
            "mensagem": "Código gerado com sucesso",
            "resultado": result,
        }
    except Exception as e:
        add_log("error", f"alias /criar-codigo falhou: {type(e).__name__}", SOURCE)
        _msg = "Erro interno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SPEC_ALIAS_FAILED", "message": _msg})
