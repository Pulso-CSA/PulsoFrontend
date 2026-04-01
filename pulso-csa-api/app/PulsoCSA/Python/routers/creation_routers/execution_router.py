#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router: Camada 3 – Execução❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from utils.log_manager import add_log
from utils.path_validation import sanitize_root_path, is_production
from models.creation_models.execution_models import ExecutionRequest, ManifestResponse
from agents.execution.agent_structure_creator import create_structure_from_report
from agents.execution.agent_code_creator import create_code_from_reports

router = APIRouter()
SOURCE = "execution"

#━━━━━━━━━❮Rota: Criação de Estrutura❯━━━━━━━━━

@router.post("/execution/create-structure", response_model=ManifestResponse)
async def create_structure(request: ExecutionRequest, user: dict = Depends(auth_and_rate_limit)):
    """Cria estrutura de pastas e arquivos com base no relatório da Camada 2."""
    root_path = sanitize_root_path(request.root_path) if request.root_path else None
    if request.root_path and not root_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    root_path = root_path or request.root_path
    add_log("info", f"criar-estrutura iniciada | id_requisicao={request.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: create_structure_from_report(root_path, request.id_requisicao))
        if result.get("status") != "sucesso":
            add_log("warning", f"criar-estrutura retornou status não sucesso | id_requisicao={request.id_requisicao}", SOURCE)
            raise HTTPException(status_code=400, detail=result.get("mensagem"))
        add_log("info", f"criar-estrutura concluída | id_requisicao={request.id_requisicao}", SOURCE)
        return result
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"criar-estrutura falhou: {type(e).__name__}", SOURCE)
        detail = "Erro ao criar estrutura." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "CREATE_STRUCTURE_FAILED", "message": detail})



@router.post("/execution/create-code")
async def generate_code(id_requisicao: str, root_path: str, user: dict = Depends(auth_and_rate_limit)):
    """Camada 3 – Criação de Código. Gera código-fonte a partir dos relatórios."""
    safe_path = sanitize_root_path(root_path) if root_path else None
    if root_path and not safe_path:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    safe_path = safe_path or root_path
    add_log("info", f"criar-codigo iniciada | id_requisicao={id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: create_code_from_reports(safe_path, id_requisicao))
        add_log("info", f"criar-codigo concluída | id_requisicao={id_requisicao}", SOURCE)
        return {"mensagem": "Código gerado com sucesso", "resultado": result}
    except Exception as e:
        add_log("error", f"criar-codigo falhou: {type(e).__name__}", SOURCE)
        detail = "Erro ao gerar código." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "CREATE_CODE_FAILED", "message": detail})
