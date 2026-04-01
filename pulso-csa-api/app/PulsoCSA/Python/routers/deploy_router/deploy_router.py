#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rotas de Controle de Deploy❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from models.deploy_models.deploy_models import DeployRequest, DeployResponse, LogEntry
from services.deploy import deploy_service
from utils.log_manager import get_logs, clear_logs
from utils.path_validation import sanitize_root_path

router = APIRouter(prefix="/deploy/docker", tags=["Deploy"])


def _sanitize_deploy_paths(project_path: str | None, root_path: str | None):
    """Retorna (project_path_safe, root_path_safe) ou levanta 400 se inválido."""
    pp = sanitize_root_path(project_path) if project_path else None
    rp = sanitize_root_path(root_path) if root_path else None
    if project_path and not pp:
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_INVALID", "message": "project_path inválido ou fora do permitido."})
    if root_path and not rp:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    return (pp or project_path, rp or root_path)


#━━━━━━━━━❮Rota: Iniciar Containers❯━━━━━━━━━#
@router.post("/start", response_model=DeployResponse)
async def start_containers(request: DeployRequest, user: dict = Depends(require_valid_access)):
    """Inicia os containers Docker."""
    project_path, root_path = _sanitize_deploy_paths(request.project_path, request.root_path)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: deploy_service.start_compose(project_path, root_path)
    )
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response


#━━━━━━━━━❮Rota: Rebuild Containers❯━━━━━━━━━#
@router.post("/rebuild", response_model=DeployResponse)
async def rebuild_containers(request: DeployRequest, user: dict = Depends(require_valid_access)):
    """Recria os containers Docker."""
    project_path, root_path = _sanitize_deploy_paths(request.project_path, request.root_path)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: deploy_service.rebuild_compose(project_path, root_path)
    )
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response


#━━━━━━━━━❮Rota: Desligar Containers❯━━━━━━━━━#
@router.post("/stop", response_model=DeployResponse)
async def stop_containers(request: DeployRequest, user: dict = Depends(require_valid_access)):
    """Desliga os containers Docker."""
    project_path, root_path = _sanitize_deploy_paths(request.project_path, request.root_path)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: deploy_service.stop_compose(project_path, root_path)
    )
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    return response


#━━━━━━━━━❮Rota: Logs da Aplicação❯━━━━━━━━━#
@router.get("/logs", response_model=list[LogEntry])
def get_application_logs(level: str = Query(default="todos", description="Filtro: todos, info, warning, error"), user: dict = Depends(require_valid_access)):
    """Retorna logs da aplicação (filtrados por nível)."""
    return get_logs(level)


#━━━━━━━━━❮Rota: Limpar Logs❯━━━━━━━━━#
@router.delete("/logs/clear")
def clear_application_logs(user: dict = Depends(require_valid_access)):
    """Limpa todos os logs da aplicação."""
    clear_logs()
    return {"message": "🧹 Logs da aplicação foram limpos."}
