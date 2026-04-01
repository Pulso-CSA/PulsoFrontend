#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Venv Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter, Depends, Query, HTTPException
from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from models.venv_models.venv_models import VenvRequest, VenvResponse
from models.deploy_models.deploy_models import LogEntry
from services.venv_service.venv_service import (
    create_venv,
    recreate_venv,
    activate_venv,
    deactivate_venv
)
from utils.log_manager import get_logs, clear_logs
from utils.path_validation import sanitize_root_path

router = APIRouter(prefix="/venv", tags=["Venv"])


def _safe_project_path(data: VenvRequest):
    """Retorna project_path sanitizado ou levanta 400 se inválido."""
    if not data.project_path or not str(data.project_path).strip():
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_REQUIRED", "message": "project_path é obrigatório."})
    safe = sanitize_root_path(data.project_path)
    if not safe:
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_INVALID", "message": "project_path inválido ou fora do permitido."})
    return safe


#━━━━━━━━━❮Logs Venv❯━━━━━━━━━
@router.get("/logs", response_model=list[LogEntry])
def get_venv_logs(level: str = Query(default="todos", description="Filtro: todos, info, warning, error"), user: dict = Depends(require_valid_access)):
    """Retorna logs do venv (filtrados por nível)."""
    return get_logs(level, filter_source="venv")


#━━━━━━━━━❮Limpar Logs Venv❯━━━━━━━━━
@router.delete("/logs/clear")
def clear_venv_logs(user: dict = Depends(require_valid_access)):
    """Limpa os logs do venv."""
    clear_logs("venv")
    return {"message": "🧹 Logs do venv foram limpos."}


#━━━━━━━━━❮Create Venv❯━━━━━━━━━
@router.post("/create", response_model=VenvResponse)
async def route_create_venv(data: VenvRequest, user: dict = Depends(require_valid_access)):
    path = _safe_project_path(data)
    return create_venv("info", path)


#━━━━━━━━━❮Recreate Venv❯━━━━━━━━━
@router.post("/recreate", response_model=VenvResponse)
async def route_recreate_venv(data: VenvRequest, user: dict = Depends(require_valid_access)):
    path = _safe_project_path(data)
    return recreate_venv("info", path)


#━━━━━━━━━❮Execute Venv Code❯━━━━━━━━━
@router.post("/execute", response_model=VenvResponse)
async def route_execute_venv(data: VenvRequest, user: dict = Depends(require_valid_access)):
    path = _safe_project_path(data)
    return activate_venv("info", path)


#━━━━━━━━━❮Deactivate (No-op)❯━━━━━━━━━
@router.post("/deactivate", response_model=VenvResponse)
async def route_deactivate_venv(data: VenvRequest, user: dict = Depends(require_valid_access)):
    path = _safe_project_path(data)
    return deactivate_venv("info", path)
