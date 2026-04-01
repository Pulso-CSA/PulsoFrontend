#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Orquestrador Camada 1 → Camada 2❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from agents.architecture.planning import (
    agent_structure,
    agent_backend,
    agent_infra,
    agent_sec_code,
    agent_sec_infra,
)
from storage.database import database_c2 as db


def run_layer2_pipeline(id_requisicao: str, prompt_refinado: str):
    """
    Executa a Camada 2 (Arquitetura e Planejamento) de forma local,
    sem depender de chamadas HTTP, e salva resultados diretamente no Mongo.
    """
    resultados = {}

    # 1️⃣ Estrutura
    estrutura = agent_structure.analyze_structure(id_requisicao)
    db.upsert_blueprint(id_requisicao, estrutura)
    resultados["estrutura"] = estrutura

    # 2️⃣ Backend
    backend = agent_backend.analyze_backend(id_requisicao, estrutura.get("estrutura_arquivos", {}))
    db.upsert_backend_doc(id_requisicao, backend)
    resultados["backend"] = backend

    # 3️⃣ Infra
    infra = agent_infra.analyze_infra(id_requisicao, estrutura.get("estrutura_arquivos", {}), backend)
    db.upsert_infra_doc(id_requisicao, infra)
    resultados["infraestrutura"] = infra

    # 4️⃣ Segurança Código
    sec_code = agent_sec_code.analyze_code_security(id_requisicao, backend)
    db.upsert_security_code(id_requisicao, sec_code)
    resultados["seguranca_codigo"] = sec_code

    # 5️⃣ Segurança Infra
    sec_infra = agent_sec_infra.analyze_infra_security(id_requisicao, infra)
    db.upsert_security_infra(id_requisicao, sec_infra)
    resultados["seguranca_infra"] = sec_infra

    return {
        "workflow": "Camada 2 – Arquitetura e Planejamento",
        "id_requisicao": id_requisicao,
        "steps_executed": list(resultados.keys()),
        "resultados": resultados,
        "status": "executado"
    }
