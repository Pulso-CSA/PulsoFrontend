#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮POST /infra/analyze❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import auth_and_rate_limit
from app.CloudIAC.agents.infra.infra_agent import run_analyze
from app.CloudIAC.models.infra.requests import InfraAnalyzeRequest
from app.utils.log_manager import add_log
from app.utils.path_validation import is_production, sanitize_root_path

router = APIRouter()
SOURCE = "infra_analyze"


@router.post("/analyze")
async def infra_analyze(req: InfraAnalyzeRequest, user: dict = Depends(auth_and_rate_limit)):
    """Analisa root_path e retorna repo_context, infra_spec_draft, cost_estimate, provider_diff_report."""
    add_log("info", f"infra/analyze iniciada | id_requisicao={req.id_requisicao}", SOURCE)
    root_path = sanitize_root_path(req.root_path)
    if not root_path:
        raise HTTPException(
            status_code=400,
            detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."},
        )
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_analyze(
                root_path=root_path,
                tenant_id=req.tenant_id,
                id_requisicao=req.id_requisicao,
                user_request=req.user_request,
                providers=req.providers,
                envs=req.envs,
            ),
        )
        add_log("info", f"infra/analyze concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return {
            "status": "ok",
            "warnings": [],
            "errors": [],
            "artifacts": [],
            "commands": [],
            "reports": result,
            "request_id": req.id_requisicao,
        }
    except Exception as e:
        add_log("error", f"infra/analyze falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "INFRA_ANALYZE_FAILED", "message": "Erro na análise de infra."} if is_production() else str(e)
        raise HTTPException(status_code=500, detail=detail)
