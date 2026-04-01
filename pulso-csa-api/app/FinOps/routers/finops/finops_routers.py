#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮POST /finops/analyze e /finops/chat❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
POST /finops/analyze: payload estruturado.
POST /finops/chat: entrada única do chat FinOps — mensagem em linguagem natural, comprehension interno.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import auth_and_rate_limit
from app.core.entitlement.deps import require_valid_access
from models.finops.finops_models import FinOpsAnalyzeRequest, FinOpsAnalyzeResponse
from models.finops.finops_chat_models import FinOpsChatInput, FinOpsChatOutput
from agents.finops.finops_agents import run_finops_agent
from services.finops.finops_chat_service import run_finops_chat
from services.chat_history_service import persist_chat
from app.utils.log_manager import add_log
from app.utils.path_validation import is_production

router = APIRouter(prefix="/finops", tags=["FinOps – Análise Multi-Cloud"])
SOURCE = "finops_router"


# Exemplo de payload (para documentação):
# {
#   "cloud": "aws",
#   "aws_credentials": {"access_key_id": "...", "secret_access_key": "...", "region": "us-east-1"},
#   "start_date": "2025-01-01",
#   "end_date": "2025-01-31",
#   "quick_win_mode": "quick_wins",
#   "guardrails_mode": true
# }
# Exemplo de resposta: {"message": "<texto narrativo completo>", "id_requisicao": "FINOP-..."}


@router.post("/chat", response_model=FinOpsChatOutput)
async def finops_chat(payload: FinOpsChatInput, user: dict = Depends(require_valid_access)):
    """
    Chat FinOps: entrada única com mensagem em linguagem natural.
    Usa comprehension exclusivo do módulo para interpretar intent e extrair parâmetros.
    Requer credenciais do provider (aws_credentials, azure_credentials ou gcp_credentials).
    """
    add_log("info", f"POST /finops/chat | usuario={payload.usuario or 'default'}", SOURCE)
    if not payload.usuario:
        payload.usuario = user.get("email") or user.get("_id")
    try:
        result = run_finops_chat(payload)
        tenant_id = user.get("_id") or user.get("email") or ""
        asyncio.create_task(
            persist_chat(
                tenant_id=tenant_id,
                usuario_id=payload.usuario or tenant_id,
                service_id="finops",
                session_id=payload.id_requisicao,
                mensagem_user=payload.mensagem,
                mensagem_assistant=result.resposta_texto,
            )
        )
        return result
    except Exception as e:
        add_log("error", f"finops/chat falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "FINOPS_CHAT_FAILED", "message": "Erro no chat FinOps."} if is_production() else str(e)
        raise HTTPException(status_code=500, detail=detail)


@router.post("/analyze", response_model=FinOpsAnalyzeResponse)
async def finops_analyze(req: FinOpsAnalyzeRequest, user: dict = Depends(require_valid_access)):
    """
    Analisa custos, performance e segurança na cloud (AWS/Azure/GCP).
    Retorna texto em linguagem natural para o chat (sem PDF, sem anexos).
    Requer credenciais do provider selecionado.
    """
    add_log("info", f"POST /finops/analyze | cloud={req.cloud}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_finops_agent, req)
        message = result.get("message", "")
        return FinOpsAnalyzeResponse(
            message=message,
            cloud=result.get("cloud"),
            id_requisicao=result.get("id_requisicao"),
        )
    except Exception as e:
        add_log("error", f"finops/analyze falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "FINOPS_ANALYZE_FAILED", "message": "Erro na análise FinOps."} if is_production() else str(e)
        raise HTTPException(status_code=500, detail=detail)
