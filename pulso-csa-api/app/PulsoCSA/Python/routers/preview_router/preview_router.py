#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Preview Router – Iniciar servidor de preview automaticamente❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from models.preview_models.preview_models import PreviewStartRequest, PreviewStartResponse
from services.preview_service.preview_service import start_preview as start_preview_server
from utils.path_validation import sanitize_root_path

router = APIRouter(prefix="/preview", tags=["Preview"])


#━━━━━━━━━❮Iniciar servidor de preview (npm run dev ou streamlit)❯━━━━━━━━━
@router.post("/start", response_model=PreviewStartResponse)
async def start_preview(data: PreviewStartRequest, user: dict = Depends(auth_and_rate_limit)):
    """
    Inicia automaticamente o servidor de preview ao clicar em "Testar preview".
    - JavaScript/React/Vue: executa `npm install` e `npm run dev` em background.
    - Python/Streamlit: executa `streamlit run app.py` (ou FrontendEX/app.py) em background.
    O frontend deve chamar este endpoint quando o usuário clicar em "Testar preview".
    """
    if not data.root_path or not str(data.root_path).strip():
        raise HTTPException(
            status_code=400,
            detail={"code": "ROOT_PATH_REQUIRED", "message": "root_path é obrigatório."},
        )
    safe_path = sanitize_root_path(data.root_path)
    if not safe_path:
        raise HTTPException(
            status_code=400,
            detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."},
        )
    result = start_preview_server(root_path=safe_path, project_type=data.project_type or "auto")
    return PreviewStartResponse(**result)
