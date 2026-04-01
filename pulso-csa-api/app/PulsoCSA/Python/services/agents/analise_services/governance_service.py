#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Governança e Orquestração❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Any
from fastapi import HTTPException

from agents.governance import agent_input, agent_refine, agent_validate
from agents.architecture.planning import (
    agent_structure,
    agent_backend,
    agent_infra,
    agent_sec_code,
    agent_sec_infra,
)
from storage.database import database_c1 as db_c1
from storage.database import database_c2 as db_c2
from utils.report_writer import save_agent_report
from utils.path_validation import get_app_package_dir


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função simples de log❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def log_event(filename: str, message: str):
    """Registra eventos em arquivos de log separados por agente (sob api/app/logs, não depende do CWD)."""
    logs_dir = Path(get_app_package_dir()) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / filename
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {message}\n")


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Execução Camada 1❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def execute_layer1_workflow(prompt: str, usuario: str, root_path: str, logs: list):
    """Executa o fluxo básico de governança (Camada 1)."""
    input_data = agent_input.receive_prompt(prompt, usuario, root_path)
    id_requisicao = input_data["id_requisicao"]

    log_event("governance_input.log", f"Prompt recebido de {usuario}: {prompt[:80]}...")

    aprovado = False
    refined_prompt = input_data["prompt"]

    while not aprovado:
        versao = db_c1.get_next_refine_version(id_requisicao)

        refined = agent_refine.refine_prompt(refined_prompt)
        refined["versao_refino"] = versao
        refined["timestamp"] = datetime.now().isoformat()
        db_c1.append_refinement(id_requisicao, refined)
        log_event("governance_refine.log", f"{id_requisicao}: versão {versao} gerada")

        validation = agent_validate.validate_prompt(refined["refined_prompt"])
        validation["timestamp"] = datetime.now().isoformat()
        db_c1.append_validation(id_requisicao, validation)
        log_event("governance_validate.log", f"{id_requisicao}: status {validation['validation_status']}")

        if validation["validation_status"] == "aprovado":
            aprovado = True
            logs.append("Prompt aprovado e documento final gerado.")
        else:
            refined_prompt = validation["final_prompt"]

    return {
        "workflow": "Camada 1 - Governança",
        "id_requisicao": id_requisicao,
        "steps_executed": ["input_received", "prompt_refined", "validation_completed"],
        "final_prompt": validation["final_prompt"],
        "status": "sucesso",
        "log": logs
    }


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Execução Camadas 1 + 2❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def execute_full_workflow(prompt: str, usuario: str, root_path: str = None) -> Dict[str, Any]:
    """Executa automaticamente o pipeline completo (Camada 1 + Camada 2)."""
    try:
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        #━━━━━━━━━❮Inicialização❯━━━━━━━━━
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        from storage.database import database_c1 as db_c1
        from storage.database import database_c2 as db_c2

        #━━━━━━━━━ Etapa 1 – Input ❯
        input_result = agent_input.receive_prompt(prompt, usuario, root_path)
        id_requisicao = input_result["id_requisicao"]

        input_result["root_path"] = root_path or ""
        db_c1.upsert_input(id_requisicao, input_result)

        # root_path não é definido em variável de ambiente (evita conflito entre usuários no mesmo worker).
        log_event("workflow.log", f"[{id_requisicao}] Input recebido com sucesso")

        #━━━━━━━━━ Etapa 2 – Refino ❯
        refined_result = agent_refine.refine_prompt(prompt)
        refined_prompt = refined_result.get("prompt_refinado", prompt)
        db_c1.append_refinement(id_requisicao, refined_result)
        log_event("workflow.log", f"[{id_requisicao}] Refino concluído")

        #━━━━━━━━━ Etapa 3 – Validação ❯
        validated_result = agent_validate.agent_validate(
            id_requisicao=id_requisicao,
            refined_prompt=refined_prompt,
            feedback_usuario="aprovado"
        )
        db_c1.append_validation(id_requisicao, validated_result)
        log_event("workflow.log", f"[{id_requisicao}] Validação aprovada")

        #━━━━━━━━━ Etapa 4 – Estrutura ❯
        estrutura_result = agent_structure.analyze_structure(id_requisicao)
        db_c2.upsert_blueprint(id_requisicao, estrutura_result)
        save_agent_report(id_requisicao, "01_structure_report", estrutura_result, root_path)
        log_event("workflow.log", f"[{id_requisicao}] Estrutura gerada")

        #━━━━━━━━━ Etapa 5 – Backend ❯
        estrutura_arquivos = estrutura_result.get("estrutura_arquivos", estrutura_result) if isinstance(estrutura_result, dict) else {}
        backend_result = agent_backend.analyze_backend(id_requisicao, estrutura_arquivos, refined_prompt)
        db_c2.upsert_backend_doc(id_requisicao, backend_result)
        save_agent_report(id_requisicao, "02_backend_report", backend_result, root_path)
        log_event("workflow.log", f"[{id_requisicao}] Backend definido")

        #━━━━━━━━━ Etapa 6 – Infra ❯
        infra_result = agent_infra.analyze_infra(id_requisicao, estrutura_result, backend_result)
        db_c2.upsert_infra_doc(id_requisicao, infra_result)
        save_agent_report(id_requisicao, "03_infrastructure_report", infra_result, root_path)
        log_event("workflow.log", f"[{id_requisicao}] Infraestrutura criada")

        #━━━━━━━━━ Etapa 7 – Segurança de Código ❯
        sec_code_result = agent_sec_code.analyze_code_security(id_requisicao, backend_result)
        db_c2.upsert_security_code(id_requisicao, sec_code_result)
        save_agent_report(id_requisicao, "04_code_security_report", sec_code_result, root_path)
        log_event("workflow.log", f"[{id_requisicao}] Segurança de código analisada")

        #━━━━━━━━━ Etapa 8 – Segurança de Infra ❯
        sec_infra_result = agent_sec_infra.analyze_infra_security(id_requisicao, infra_result)
        db_c2.upsert_security_infra(id_requisicao, sec_infra_result)
        save_agent_report(id_requisicao, "05_infra_security_report", sec_infra_result, root_path)
        log_event("workflow.log", f"[{id_requisicao}] Segurança de infra analisada")

        #━━━━━━━━━ Etapa Final – Consolidação ❯
        summary = {
            "workflow": "Camada 1 + Camada 2 - Pipeline Completo",
            "usuario": usuario,
            "id_requisicao": id_requisicao,
            "final_prompt": refined_prompt,
            "estrutura_arquivos": estrutura_result,
            "backend": backend_result,
            "infraestrutura": infra_result,
            "seguranca_codigo": sec_code_result,
            "seguranca_infra": sec_infra_result,
            "steps_executed": [
                "input_received",
                "prompt_refined",
                "validation_completed",
                "blueprint_generated",
                "backend_analyzed",
                "infra_analyzed",
                "security_code_checked",
                "security_infra_checked"
            ],
            "status": "sucesso",
            "timestamp": datetime.utcnow().isoformat()
        }

        save_agent_report(id_requisicao, "summary_pipeline", summary, root_path)
        log_event("workflow.log", f"[{id_requisicao}] Pipeline completo salvo com sucesso")

        return summary

    except Exception as e:
        from utils.path_validation import is_production
        msg = "Erro no workflow completo." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "GOVERNANCE_WORKFLOW_FAILED", "message": msg})
