#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from models.struc_anal.struc_anal_models import (
    StructurePlanRequest,
    StructurePlanResponse
)

from services.struc_anal.structure_scanner_service import scan_full_project
from services.struc_anal.change_plan_service import generate_change_plan

from utils.log_manager import add_log
from utils.path_validation import sanitize_root_path

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
router = APIRouter(prefix="/struc-anal", tags=["Análise Estrutural"])


@router.post("/plan", response_model=StructurePlanResponse)
async def route_plan(req: StructurePlanRequest, user: dict = Depends(auth_and_rate_limit)):

    log_type = "info"

    if not req.id_requisicao:
        raise HTTPException(status_code=400, detail="id_requisicao obrigatório.")

    root_path = sanitize_root_path(req.root_path) if req.root_path else None
    if not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})

    add_log(log_type, f"Iniciando análise estrutural: {req.id_requisicao}", "struc_anal")

    scanned = scan_full_project(
        log_type=log_type,
        root_path=root_path,
        id_requisicao=req.id_requisicao,
        prompt=req.prompt
    )

    resumo, novos, alterar = generate_change_plan(
        log_type=log_type,
        scanned=scanned,
        prompt=req.prompt
    )

    return StructurePlanResponse(
        id_requisicao=req.id_requisicao,
        resumo_sistema=resumo,
        novos_arquivos=novos,
        arquivos_a_alterar=alterar
    )
