#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import asyncio
from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from utils.log_manager import add_log
from utils.path_validation import is_production
from models.analise_models.backend_models import (
    AnalysisStructureRequest, AnalysisStructureResponse,
    AnalysisBackendRequest, AnalysisBackendResponse, AnalysisBackendDoc,
    SecurityCodeRequest, SecurityCodeResponse
)
from agents.architecture.planning.agent_structure import analyze_structure
from agents.architecture.planning.agent_backend import analyze_backend
from agents.architecture.planning.agent_sec_code import analyze_code_security  # ✅ correção

router = APIRouter()
SOURCE = "backend"

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮/analise-estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/analise-estrutura", response_model=AnalysisStructureResponse)
async def analise_estrutura(req: AnalysisStructureRequest, user: dict = Depends(auth_and_rate_limit)):
    add_log("info", f"analise-estrutura iniciada | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        estrutura = await loop.run_in_executor(None, analyze_structure, req.id_requisicao)
        add_log("info", f"analise-estrutura concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return AnalysisStructureResponse(
            id_requisicao=req.id_requisicao,
            estrutura_arquivos=estrutura
        )
    except Exception as e:
        add_log("error", f"analise-estrutura falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "ANALISE_ESTRUTURA_FAILED", "message": "Erro na análise de estrutura."} if is_production() else f"Erro na análise de estrutura: {e}"
        raise HTTPException(status_code=500, detail=detail)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮/analise-backend❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/analise-backend", response_model=AnalysisBackendResponse)
async def analise_backend(req: AnalysisBackendRequest, user: dict = Depends(auth_and_rate_limit)):
    add_log("info", f"analise-backend iniciada | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        backend_doc = await loop.run_in_executor(None, lambda: analyze_backend(req.id_requisicao, req.estrutura_arquivos))
        add_log("info", f"analise-backend concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return AnalysisBackendResponse(
            id_requisicao=req.id_requisicao,
            backend=AnalysisBackendDoc(**backend_doc)
        )
    except Exception as e:
        add_log("error", f"analise-backend falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "ANALISE_BACKEND_FAILED", "message": "Erro na análise de backend."} if is_production() else f"Erro na análise de backend: {e}"
        raise HTTPException(status_code=500, detail=detail)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮/seguranca-codigo❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/seguranca-codigo", response_model=SecurityCodeResponse)
async def seguranca_codigo(req: SecurityCodeRequest, user: dict = Depends(auth_and_rate_limit)):
    add_log("info", f"seguranca-codigo iniciada | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        backend_dump = req.backend.model_dump()
        report = await loop.run_in_executor(None, lambda: analyze_code_security(req.id_requisicao, backend_dump))
        add_log("info", f"seguranca-codigo concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return SecurityCodeResponse(
            id_requisicao=req.id_requisicao,
            seguranca_codigo=report
        )
    except Exception as e:
        add_log("error", f"seguranca-codigo falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "SEGURANCA_CODIGO_FAILED", "message": "Erro na segurança de código."} if is_production() else f"Erro na segurança de código: {e}"
        raise HTTPException(status_code=500, detail=detail)
