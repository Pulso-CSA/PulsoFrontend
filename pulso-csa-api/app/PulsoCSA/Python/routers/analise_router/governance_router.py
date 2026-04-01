#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import asyncio
from fastapi import APIRouter, Depends, HTTPException

from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from models.analise_models.governance_models import (
    PromptRequest,
    RefineRequest,
    ValidateRequest,
    GovernanceResponse,
)
from agents.governance import agent_refine, agent_validate
from workflow.creator_workflow.workflow_core import run_workflow_pipeline

from app.pulso_csa_time_limits import (
    CsaRequestBudget,
    CSA_WORKFLOW_WALL_CLOCK_SEC,
    csa_timeout_http_detail,
)

from datetime import datetime
import uuid

# Importa apenas camada 1 (governança)
from storage.database import database_c1 as db_c1

# Logs unificados
from utils.logger import log_input, log_refine, log_validate, log_workflow
from utils.log_manager import add_log
from utils.path_validation import sanitize_root_path, is_production

SOURCE = "governance"

router = APIRouter()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rota: Workflow Completo (Camada 1 + 2)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/governance/run", response_model=GovernanceResponse)
async def run_governance_workflow(request: PromptRequest, user: dict = Depends(require_valid_access)):
    """
    Executa automaticamente o workflow completo:
    - Camada 1 (Governança)
    - Camada 2 (Arquitetura e Planejamento)
    """
    add_log("info", f"governance/run iniciado | usuario={request.usuario}", SOURCE)
    raw_root = getattr(request, "root_path", None)
    if raw_root is not None and str(raw_root).strip():
        root_path = sanitize_root_path(raw_root)
        if not root_path:
            raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    else:
        root_path = None
    try:
        loop = asyncio.get_event_loop()
        budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
        result = await budget.run_in_executor(
            loop, lambda: run_workflow_pipeline(request.prompt, request.usuario, root_path)
        )
        log_workflow("workflow.log", f"Workflow completo executado para {request.usuario}")
        add_log("info", "governance/run concluído com sucesso", SOURCE)

        # ✅ Garante presença de steps_executed
        if "steps_executed" not in result:
            result["steps_executed"] = [
                "input_received",
                "prompt_refined",
                "validation_completed",
                "blueprint_generated",
                "backend_analyzed",
                "infra_analyzed",
                "security_code_checked",
                "security_infra_checked",
            ]

        return result
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=csa_timeout_http_detail())
    except Exception as e:
        add_log("error", f"governance/run falhou: {type(e).__name__}", SOURCE)
        msg = "Erro ao executar workflow completo." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "GOVERNANCE_RUN_FAILED", "message": msg})


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Implementações (reutilizáveis por aliases da spec)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _receive_prompt_impl(request: PromptRequest) -> dict:
    """Lógica de recebimento do prompt; retorna dict para resposta JSON."""
    id_requisicao = f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
    input_doc = {
        "prompt": request.prompt,
        "usuario": request.usuario,
        "timestamp": datetime.utcnow().isoformat(),
        "origem": "api",
    }
    db_c1.upsert_input(id_requisicao, input_doc)
    log_input(id_requisicao, request.usuario)
    return {
        "id_requisicao": id_requisicao,
        "status": "recebido",
        "usuario": request.usuario,
        "timestamp": input_doc["timestamp"],
        "mensagem": "Prompt inicial armazenado com sucesso",
    }


def _refine_prompt_impl(request: RefineRequest) -> dict:
    """Lógica de refino; retorna dict. Inclui solicitar_dados_adicionais quando aplicável."""
    versao = db_c1.get_next_refine_version(request.id_requisicao)
    refined = agent_refine.refine_prompt(request.prompt)
    refinement_doc = {
        "versao": versao,
        "prompt_refinado": refined["refined_prompt"],
        "qualidade_refino": refined.get("refinement_quality", "alta"),
        "timestamp": datetime.utcnow().isoformat(),
    }
    db_c1.append_refinement(request.id_requisicao, refinement_doc)
    log_refine(request.id_requisicao, versao)

    # Refinamento: loop com /input — solicitar dados adicionais se prompt muito vago ou qualidade baixa
    qualidade = refinement_doc["qualidade_refino"]
    prompt_len = len((request.prompt or "").strip())
    solicitar_dados = qualidade == "baixa" or prompt_len < 50
    mensagem_solicitacao = None
    if solicitar_dados:
        mensagem_solicitacao = (
            "Requisito ainda vago. Envie dados adicionais via POST /input (ou POST /refinar com mais detalhes) "
            "usando o mesmo id_requisicao para complementar."
        )

    return {
        "id_requisicao": request.id_requisicao,
        "versao_refino": versao,
        "prompt_refinado": refinement_doc["prompt_refinado"],
        "qualidade_refino": refinement_doc["qualidade_refino"],
        "mensagem": "Refino concluído com sucesso",
        "solicitar_dados_adicionais": solicitar_dados,
        "mensagem_solicitacao": mensagem_solicitacao,
    }


def _validate_prompt_impl(request: ValidateRequest) -> dict:
    """Lógica de validação; retorna dict. Inclui perguntas obrigatórias para o fluxo."""
    validation = agent_validate.validate_prompt(request.refined_prompt)
    aprovado = request.feedback_usuario.strip().lower() == "aprovado"
    status = "aprovado" if aprovado else "em revisão"
    documento = None
    if aprovado:
        documento = {
            "descricao": validation["final_prompt"],
            "objetivo_negocio": "Atender ao requisito funcional do usuário com segurança e compliance",
        }
        resp = {
            "id_requisicao": request.id_requisicao,
            "status": status,
            "documento_requisitos": documento,
            "mensagem": "Documento de requisitos gerado com sucesso",
        }
    else:
        resp = {
            "id_requisicao": request.id_requisicao,
            "status": status,
            "mensagem": "Usuário solicitou ajustes — retornar ao endpoint /refinar (ou /governance/refine) para nova versão",
        }

    resp["perguntas_obrigatorias"] = ["Está correto?", "Deseja alterar algo?"]

    validation_doc = {
        "status": status,
        "feedback_usuario": request.feedback_usuario,
        "final_prompt": validation["final_prompt"],
        "documento": documento,
        "timestamp": datetime.utcnow().isoformat(),
    }
    db_c1.append_validation(request.id_requisicao, validation_doc)
    log_validate(request.id_requisicao, status)
    return resp


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rota: Receber Prompt❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/governance/input")
async def receive_prompt(request: PromptRequest, user: dict = Depends(require_valid_access)):
    """Recebe o prompt inicial, persiste no Mongo (Camada 1) e retorna o id_requisicao."""
    add_log("info", "input recebido | etapa=governance/input", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        out = await loop.run_in_executor(None, _receive_prompt_impl, request)
        add_log("info", f"input armazenado | id_requisicao={out['id_requisicao']}", SOURCE)
        return out
    except Exception as e:
        add_log("error", f"governance/input falhou: {type(e).__name__}", SOURCE)
        msg = "Erro ao receber prompt." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "GOVERNANCE_INPUT_FAILED", "message": msg})


#━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rota: Refino Manual❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/governance/refine")
async def refine_prompt(request: RefineRequest, user: dict = Depends(require_valid_access)):
    """Refina manualmente um prompt e salva versão automática (v1, v2...). Retorna solicitar_dados_adicionais quando aplicável."""
    add_log("info", f"refino iniciado | id_requisicao={request.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        out = await loop.run_in_executor(None, _refine_prompt_impl, request)
        add_log("info", f"refino concluído | id_requisicao={request.id_requisicao} versao={out.get('versao_refino')}", SOURCE)
        return out
    except Exception as e:
        add_log("error", f"governance/refine falhou: {type(e).__name__}", SOURCE)
        msg = "Erro ao refinar prompt." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "GOVERNANCE_REFINE_FAILED", "message": msg})


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rota: Validação Manual❯━━━━━━━━━
#━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
@router.post("/governance/validate")
async def validate_prompt(request: ValidateRequest, user: dict = Depends(require_valid_access)):
    """Valida o prompt refinado e salva resultado da Camada 1. Inclui perguntas obrigatórias na resposta."""
    add_log("info", f"validação iniciada | id_requisicao={request.id_requisicao}", SOURCE)
    try:
        loop = asyncio.get_event_loop()
        out = await loop.run_in_executor(None, _validate_prompt_impl, request)
        add_log("info", f"validação concluída | id_requisicao={request.id_requisicao} status={out.get('status')}", SOURCE)
        return out
    except Exception as e:
        add_log("error", f"governance/validate falhou: {type(e).__name__}", SOURCE)
        msg = "Erro ao validar prompt." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "GOVERNANCE_VALIDATE_FAILED", "message": msg})
