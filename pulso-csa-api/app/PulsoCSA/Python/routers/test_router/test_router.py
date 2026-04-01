#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rotas de Teste Automatizado (Venv + Docker)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from models.test_models.test_models import TestRunRequest, TestRunResponse
from services.test_runner_service.test_runner_service import run_automated_test
from utils.path_validation import sanitize_root_path

router = APIRouter(prefix="/test", tags=["Test"])


#━━━━━━━━━❮Rota: Executar teste automatizado❯━━━━━━━━━
@router.post("/run", response_model=TestRunResponse)
async def run_test(data: TestRunRequest, user: dict = Depends(auth_and_rate_limit)):
    """
    Executa teste automatizado no projeto: tenta Docker (docker-compose) e,
    se não disponível ou falhar, usa Venv. Útil para o frontend (botão de testar)
    e para o workflow de correção.
    """
    if not data.project_path or not str(data.project_path).strip():
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_REQUIRED", "message": "project_path é obrigatório."})
    root_path = sanitize_root_path(data.project_path)
    if not root_path:
        raise HTTPException(status_code=400, detail={"code": "PROJECT_PATH_INVALID", "message": "project_path inválido ou fora do permitido."})
    return run_automated_test(
        root_path=root_path,
        log_type="info",
        prefer_docker=data.prefer_docker,
    )
