#━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮POST /infra/validate❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import auth_and_rate_limit
from app.CloudIAC.agents.infra.infra_agent import run_validate
from app.CloudIAC.models.infra.requests import InfraValidateRequest
from app.utils.log_manager import add_log
from app.utils.path_validation import is_production, sanitize_root_path

router = APIRouter()
SOURCE = "infra_validate"


@router.post("/validate")
async def infra_validate(req: InfraValidateRequest, user: dict = Depends(auth_and_rate_limit)):
    """Executa terraform fmt, validate, plan + policy. Retorna deploy_token e confirm_phrase."""
    add_log("info", f"infra/validate iniciada | id_requisicao={req.id_requisicao}", SOURCE)
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
            lambda: run_validate(
                root_path=root_path,
                tenant_id=req.tenant_id,
                id_requisicao=req.id_requisicao,
                terraform_path=req.terraform_path,
            ),
        )
        add_log("info", f"infra/validate concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return {
            "status": "ok",
            "warnings": [],
            "errors": [],
            "validation_report": result.get("validation_report"),
            "plan_summary": result.get("plan_summary"),
            "policy_report": result.get("policy_report"),
            "deploy_token": result.get("deploy_token"),
            "confirm_phrase": result.get("confirm_phrase"),
            "instruction": result.get("instruction"),
            "request_id": req.id_requisicao,
        }
    except Exception as e:
        add_log("error", f"infra/validate falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "INFRA_VALIDATE_FAILED", "message": "Erro na validação de infra."} if is_production() else str(e)
        raise HTTPException(status_code=500, detail=detail)
