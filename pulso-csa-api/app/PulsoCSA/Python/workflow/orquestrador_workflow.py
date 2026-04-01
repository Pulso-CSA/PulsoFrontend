#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Orquestrador Global de Workflows❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Este módulo centraliza a orquestração completa do pipeline Pulso (Camadas 1 → 3).

Funções delegadas:
    - Camada 1: Governança  → execute_layer1()
    - Camada 2: Arquitetura → execute_layer2()
    - Camada 3: Execução    → execute_layer3()
"""

from fastapi import HTTPException
from datetime import datetime

from workflow.creator_workflow.workflow_steps import (
    execute_layer1,
    execute_layer2,
    execute_layer3,
)
from utils.logger import log_workflow
from utils.path_validation import is_production, resolve_project_root_for_workflow


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Orquestração Principal❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def run_full_pipeline(prompt: str, usuario: str, root_path: str = None):
    """
    Executa o pipeline completo (Governança → Arquitetura → Execução).
    Retorna o documento consolidado final com todos os artefatos.
    """
    workflow_log = []

    try:
        workflow_log.append("🚀 Iniciando orquestração global de workflow...")

        #━━━━━━━━━❮Camada 1 – Governança❯━━━━━━━━━
        layer1_result = execute_layer1(prompt, usuario, root_path)
        id_requisicao = layer1_result["id_requisicao"]
        refined_prompt = layer1_result["final_prompt"]
        root_path = layer1_result.get("root_path") or root_path
        root_path = resolve_project_root_for_workflow(usuario, root_path)
        workflow_log.append(f"✅ Camada 1 concluída: {id_requisicao}")

        #━━━━━━━━━❮Camada 2 – Arquitetura❯━━━━━━━━━
        layer2_result = execute_layer2(id_requisicao, refined_prompt, root_path)
        workflow_log.append("✅ Camada 2 concluída com sucesso.")

        #━━━━━━━━━❮Camada 3 – Execução❯━━━━━━━━━
        workflow_log.append("⚙️ Iniciando Camada 3 – Criação de Estrutura e Código...")
        structure_manifest = execute_layer3(id_requisicao, root_path)
        workflow_log.append("✅ Camada 3 concluída com sucesso.")

        #━━━━━━━━━❮Consolidação Final❯━━━━━━━━━
        consolidated = {
            "workflow": "Camadas 1 + 2 + 3 - Pipeline Completo",
            "usuario": usuario,
            "id_requisicao": id_requisicao,
            "final_prompt": refined_prompt,
            "estrutura_arquivos": layer2_result["estrutura"],
            "backend": layer2_result["backend"],
            "infraestrutura": layer2_result["infra"],
            "seguranca_codigo": layer2_result["seguranca_codigo"],
            "seguranca_infra": layer2_result["seguranca_infra"],
            "estrutura_manifest": structure_manifest,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "sucesso",
        }

        log_workflow("workflow.log", f"✅ Workflow completo concluído: {id_requisicao}")
        return consolidated

    except Exception as e:
        log_workflow("workflow_error.log", f"❌ Erro no workflow: {e}")
        msg = "Erro no orquestrador global." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "ORCHESTRATOR_FAILED", "message": msg})
