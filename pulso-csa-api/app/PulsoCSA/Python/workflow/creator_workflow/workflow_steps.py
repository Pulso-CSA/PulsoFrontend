#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow Steps❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from concurrent.futures import ThreadPoolExecutor

from agents.governance import agent_input, agent_refine, agent_validate
from agents.architecture.planning import (
    agent_structure,
    agent_backend,
    agent_infra,
    agent_sec_code,
    agent_sec_infra,
)
import uuid
from datetime import datetime

# ✅ Correção — imports adicionais
from agents.execution.agent_code_creator import create_code_from_reports

from storage.database.creation_analyse import database_c1 as db_c1
from storage.database.creation_analyse import database_c2 as db_c2
from utils.report_writer import save_agent_report
import os

#━━━━━━━━━❮Camada 1 – Governança❯━━━━━━━━━
def execute_layer1(prompt: str, usuario: str, root_path: str = None):
    """Executa input, refino e validação. id_requisicao único por request (evita colisão multi-usuário)."""

    prompt_id = f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    # usuario = utilizador real (email/id JWT), não o REQ — alinha Mongo/RAG com workspace por utilizador.
    input_doc = agent_input.receive_prompt(prompt, usuario, root_path, id_requisicao=prompt_id)

    # Garantir root_path no documento (register já grava; reforço pós-receive)
    input_doc["root_path"] = root_path or ""
    db_c1.upsert_input(prompt_id, input_doc)

    refined = agent_refine.refine_prompt(prompt)
    refined["timestamp"] = datetime.now().isoformat()
    db_c1.append_refinement(prompt_id, refined)

    validation = agent_validate.validate_prompt(refined["refined_prompt"])
    db_c1.append_validation(prompt_id, validation)

    out = {
        "id_requisicao": prompt_id,
        "final_prompt": validation["final_prompt"],
        "status": "camada1_finalizada",
    }
    # Só inclui a chave se houver caminho real — senão dict.get("root_path", fallback) não recebia o fallback
    # quando a camada 1 devolvia explicitamente root_path=None.
    if root_path is not None and str(root_path).strip():
        out["root_path"] = os.path.normpath(os.path.abspath(str(root_path).strip()))
    return out



#━━━━━━━━━❮Camada 2 – Arquitetura (paralelizada)❯━━━━━━━━━
def execute_layer2(id_requisicao: str, refined_prompt: str, root_path: str = None):
    """Executa estrutura, backend, infra e segurança. Infra e sec_code em paralelo."""
    estrutura = agent_structure.analyze_structure(id_requisicao)
    save_agent_report(id_requisicao, "01_structure_report", estrutura, root_path)

    backend = agent_backend.analyze_backend(
        id_requisicao,
        estrutura["estrutura_arquivos"],
        refined_prompt,
    )
    save_agent_report(id_requisicao, "02_backend_report", backend, root_path)

    # Paralelizar infra e sec_code (ambos dependem de backend)
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_infra = ex.submit(
            agent_infra.analyze_infra,
            id_requisicao,
            estrutura["estrutura_arquivos"],
            backend,
        )
        fut_sec_code = ex.submit(
            agent_sec_code.analyze_code_security,
            id_requisicao,
            backend,
        )
        infra = fut_infra.result()
        sec_code = fut_sec_code.result()

    save_agent_report(id_requisicao, "03_infrastructure_report", infra, root_path)
    save_agent_report(id_requisicao, "04_code_security_report", sec_code, root_path)

    sec_infra = agent_sec_infra.analyze_infra_security(id_requisicao, infra)
    save_agent_report(id_requisicao, "05_infra_security_report", sec_infra, root_path)

    # ✅ Correção — salvar corretamente em database_c2
    db_c2.upsert_blueprint(id_requisicao, estrutura)
    db_c2.upsert_backend_doc(id_requisicao, backend)
    db_c2.upsert_infra_doc(id_requisicao, infra)
    db_c2.upsert_security_code(id_requisicao, sec_code)
    db_c2.upsert_security_infra(id_requisicao, sec_infra)

    # 🔄 Relatório resumo (inclui refined_prompt para code_creator)
    summary = {
        "id_requisicao": id_requisicao,
        "refined_prompt": refined_prompt,
        "workflow": "Camada 1 + 2 - Pipeline Completo",
        "steps_executed": [
            "input_received", "prompt_refined", "validation_completed",
            "blueprint_generated", "backend_analyzed", "infra_analyzed",
            "security_code_checked", "security_infra_checked"
        ],
        "timestamp": datetime.now().isoformat()
    }
    save_agent_report(id_requisicao, "summary_pipeline", summary, root_path)

    return {
        "id_requisicao": id_requisicao,
        "estrutura": estrutura,
        "backend": backend,
        "infra": infra,
        "seguranca_codigo": sec_code,
        "seguranca_infra": sec_infra,
        "status": "camada2_finalizada",
    }

#━━━━━━━━━❮Camada 3 – Execução❯━━━━━━━━━

def execute_layer3(id_requisicao: str, root_path: str):
    """Executa a geração de código a partir dos relatórios da Camada 2."""
    result = create_code_from_reports(root_path, id_requisicao)
    return result
