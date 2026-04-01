#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮POST /infra/deploy❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import auth_and_rate_limit
from app.CloudIAC.agents.infra.infra_agent import run_deploy
from app.CloudIAC.models.infra.requests import InfraDeployRequest
from app.utils.log_manager import add_log
from app.utils.path_validation import is_production, sanitize_root_path

router = APIRouter()
SOURCE = "infra_deploy"


@router.post("/deploy")
async def infra_deploy(req: InfraDeployRequest, user: dict = Depends(auth_and_rate_limit)):
    """
    Deploy terraform apply.
    Pré-condições: confirm=true, deploy_token válido, confirm_phrase='EU ENTENDO QUE ISTO CRIARÁ RECURSOS E CUSTOS'
    """
    add_log("info", f"infra/deploy iniciada | id_requisicao={req.id_requisicao}", SOURCE)
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
            lambda: run_deploy(
                root_path=root_path,
                tenant_id=req.tenant_id,
                id_requisicao=req.id_requisicao,
                confirm=req.confirm,
                deploy_token=req.deploy_token,
                confirm_phrase=req.confirm_phrase,
                terraform_path=req.terraform_path,
                allow_policy_override=req.allow_policy_override,
                override_reason=req.override_reason,
                budget_max=req.budget_max,
                allow_budget_override=req.allow_budget_override,
            ),
        )
        if "error" in result:
            add_log("warn", f"infra/deploy recusado: {result.get('error')}", SOURCE)
            raise HTTPException(status_code=400, detail=result)
        add_log("info", f"infra/deploy concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return {
            "status": "ok",
            "warnings": [],
            "errors": [],
            "apply_summary": result.get("apply_summary"),
            "request_id": req.id_requisicao,
        }
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"infra/deploy falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "INFRA_DEPLOY_FAILED", "message": "Erro no deploy de infra."} if is_production() else str(e)
        raise HTTPException(status_code=500, detail=detail)
