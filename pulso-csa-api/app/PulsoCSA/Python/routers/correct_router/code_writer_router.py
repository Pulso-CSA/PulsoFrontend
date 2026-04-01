#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Code Writer Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter, Depends

from core.auth import auth_and_rate_limit
from models.correct_models.code_writer_models.code_writer_models import CodeWriterRequest
from services.agents.correct_services.code_writer_services.code_writer_service import run_code_writer
from utils.log_manager import add_log

router = APIRouter(
    prefix="/code-writer",
    tags=["Code Writer – Aplicação de Código"]
)


@router.post("/run")
async def run_code_writer_endpoint(request: CodeWriterRequest, user: dict = Depends(auth_and_rate_limit)):
    """
    Executa o Code Writer para aplicar (ou simular) o plano de código.
    """
    add_log("info", f"[code_writer_router] Request received for {request.id_requisicao}", "code_writer_router")
    return run_code_writer(request=request)
