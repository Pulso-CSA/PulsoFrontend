#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮POST /infra/generate❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import auth_and_rate_limit
from app.CloudIAC.agents.infra.infra_agent import run_generate
from app.CloudIAC.models.infra.requests import InfraGenerateRequest
from app.utils.log_manager import add_log
from app.utils.path_validation import is_production, sanitize_root_path

router = APIRouter()
SOURCE = "infra_generate"


def _read_terraform_code(terraform_base: str, artifacts: list[str]) -> str:
    """Lê conteúdo dos arquivos .tf criados e retorna concatenado para o frontend."""
    if not terraform_base or not artifacts:
        return ""
    base = Path(terraform_base)
    parts = []
    for rel in artifacts:
        if rel.endswith(".tf"):
            fp = base / rel
            if fp.exists():
                try:
                    parts.append(f"# {rel}\n{fp.read_text(encoding='utf-8')}")
                except Exception:
                    pass
    return "\n\n".join(parts) if parts else ""


@router.post("/generate")
async def infra_generate(req: InfraGenerateRequest, user: dict = Depends(auth_and_rate_limit)):
    """Gera artefatos Terraform a partir de InfraSpec ou user_request."""
    add_log("info", f"infra/generate iniciada | id_requisicao={req.id_requisicao}", SOURCE)
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
            lambda: run_generate(
                root_path=root_path,
                tenant_id=req.tenant_id,
                id_requisicao=req.id_requisicao,
                infra_spec=req.infra_spec,
                user_request=req.user_request,
            ),
        )
        terraform_tree = result.get("terraform_tree") or {}
        terraform_base = terraform_tree.get("base", "")
        artifacts = result.get("artifacts", [])
        terraform_code = _read_terraform_code(terraform_base, artifacts)
        result["terraform_code"] = terraform_code

        add_log("info", f"infra/generate concluída | id_requisicao={req.id_requisicao}", SOURCE)
        return {
            "status": "ok",
            "warnings": [],
            "errors": [],
            "artifacts": artifacts,
            "commands": result.get("commands", []),
            "reports": result,
            "terraform_code": terraform_code,
            "request_id": req.id_requisicao,
        }
    except Exception as e:
        add_log("error", f"infra/generate falhou: {type(e).__name__}", SOURCE)
        detail = {"code": "INFRA_GENERATE_FAILED", "message": "Erro na geração de infra."} if is_production() else str(e)
        raise HTTPException(status_code=500, detail=detail)
