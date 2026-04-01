#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import asyncio
from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from utils.log_manager import add_log
from utils.path_validation import is_production
from models.analise_models.infra_models import (
    AnalysisInfraRequest, AnalysisInfraResponse,
    SecurityInfraRequest, SecurityInfraResponse
)
from agents.architecture.planning.agent_infra import analyze_infra
from agents.architecture.planning.agent_sec_infra import analyze_infra_security

router = APIRouter()
SOURCE = "infra"

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮/analise-infra❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/analise-infra", response_model=AnalysisInfraResponse)
async def analise_infra(req: AnalysisInfraRequest, user: dict = Depends(auth_and_rate_limit)):
    add_log("info", f"analise-infra iniciada | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        infra_doc = await loop.run_in_executor(None, lambda: analyze_infra(req.id_requisicao, req.estrutura_arquivos, req.backend))
        add_log("info", f"analise-infra concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return AnalysisInfraResponse(
            id_requisicao=req.id_requisicao,
            infraestrutura=infra_doc
        )
    except Exception as e:
        add_log("error", f"analise-infra falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "ANALISE_INFRA_FAILED", "message": "Erro na análise de infra."} if is_production() else f"Erro na análise de infra: {e}"
        raise HTTPException(status_code=500, detail=detail)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮/seguranca-infra❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/seguranca-infra", response_model=SecurityInfraResponse)
async def seguranca_infra(req: SecurityInfraRequest, user: dict = Depends(auth_and_rate_limit)):
    add_log("info", f"seguranca-infra iniciada | id_requisicao={req.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, lambda: analyze_infra_security(req.id_requisicao, req.infraestrutura))
        add_log("info", f"seguranca-infra concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return SecurityInfraResponse(
            id_requisicao=req.id_requisicao,
            seguranca_infra=report
        )
    except Exception as e:
        add_log("error", f"seguranca-infra falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "SEGURANCA_INFRA_FAILED", "message": "Erro na segurança de infra."} if is_production() else f"Erro na segurança de infra: {e}"
        raise HTTPException(status_code=500, detail=detail)
