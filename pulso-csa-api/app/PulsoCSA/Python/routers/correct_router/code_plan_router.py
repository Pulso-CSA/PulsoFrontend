#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Code Plan Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from services.agents.correct_services.code_plan_services.code_plan_service import run_code_plan
from utils.path_validation import sanitize_root_path

router = APIRouter(
    prefix="/code-plan",
    tags=["Code Plan – Correção de Código"]
)

@router.post("/run")
async def run_code_plan_endpoint(data: dict, user: dict = Depends(auth_and_rate_limit)):
    """
    Executa o agente de plano de código.
    Espera um JSON contendo:
        - id_requisicao
        - prompt_refinado
        - root_path
    """
    raw_root = data.get("root_path")
    if raw_root is not None and str(raw_root).strip():
        root_path = sanitize_root_path(raw_root)
        if not root_path:
            raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    else:
        root_path = raw_root
    return run_code_plan(
        prompt=data.get("prompt"),
        root_path=root_path,
        usuario=data.get("usuario", "anonymous")
    )
