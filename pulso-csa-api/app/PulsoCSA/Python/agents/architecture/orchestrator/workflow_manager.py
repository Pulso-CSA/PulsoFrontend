#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Workflow Manager — Modular Orchestrator
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from datetime import datetime
from fastapi import HTTPException
from app.storage import database as db
from agents.governance import agent_input, agent_refine, agent_validate
from agents.architecture.planning import (
    agent_structure, agent_backend, agent_infra, agent_sec_code, agent_sec_infra
)
from utils.path_validation import is_production

class WorkflowManager:
    """Executa o pipeline completo (C1 → C2) de forma modular."""

    def __init__(self, usuario: str):
        self.usuario = usuario
        self.context = {"usuario": usuario, "timestamp": datetime.utcnow().isoformat()}
        self.layers = [
            self.run_governance_layer,
            self.run_architecture_layer
        ]

    #━━━━━━━━━❮◆❯━━━━━━━━━
    def run(self, prompt: str):
        try:
            self.context["prompt"] = prompt

            for step in self.layers:
                self.context = step(self.context)

            db.upsert_full_workflow(
                self.context["id_requisicao"],
                {**self.context, "status": "sucesso", "timestamp": datetime.utcnow().isoformat()}
            )
            return self.context

        except Exception as e:
            msg = "Erro no workflow completo." if is_production() else str(e)
            raise HTTPException(status_code=500, detail={"code": "WORKFLOW_MANAGER_FAILED", "message": msg})

    #━━━━━━━━━❮Camada 1 – Governança❯━━━━━━━━━
    def run_governance_layer(self, ctx):
        input_result = agent_input.receive_prompt(ctx["prompt"], ctx["usuario"])
        id_req = input_result.get("id_requisicao")
        if not id_req:
            raise ValueError("Falha ao gerar id_requisicao na etapa de input.")

        refined = agent_refine.refine_prompt(ctx["prompt"])
        refined_prompt = refined.get("prompt_refinado", ctx["prompt"])

        validated = agent_validate.validate_prompt(refined_prompt)
        ctx.update({
            "id_requisicao": id_req,
            "final_prompt": refined_prompt,
            "validation": validated,
            "workflow_stage": "Camada 1 - Governança"
        })
        return ctx

    #━━━━━━━━━❮Camada 2 – Arquitetura❯━━━━━━━━━
    def run_architecture_layer(self, ctx):
        estrutura = agent_structure.analyze_structure(ctx["id_requisicao"])
        backend = agent_backend.analyze_backend(ctx["id_requisicao"], estrutura)
        infra = agent_infra.analyze_infra(ctx["id_requisicao"], estrutura, backend)
        sec_code = agent_sec_code.analyze_code_security(ctx["id_requisicao"], backend)
        sec_infra = agent_sec_infra.analyze_infra_security(ctx["id_requisicao"], infra)

        ctx.update({
            "estrutura_arquivos": estrutura,
            "backend": backend,
            "infraestrutura": infra,
            "seguranca_codigo": sec_code,
            "seguranca_infra": sec_infra,
            "workflow_stage": "Camada 2 - Arquitetura"
        })
        return ctx
