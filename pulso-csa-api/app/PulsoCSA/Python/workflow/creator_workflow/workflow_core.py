#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow Core❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import json
import os
from fastapi import HTTPException
from datetime import datetime

from workflow.creator_workflow.workflow_steps import execute_layer1, execute_layer2
from utils.logger import log_workflow
from utils.path_validation import is_production, resolve_project_root_for_workflow
from utils.execution_timer import execution_timer

# Camada 3 – Estrutura
from agents.execution.agent_structure_creator import create_structure_from_report
from agents.execution import agent_structure_creator

# Camada 3.2 – Código
from agents.execution.agent_code_creator import create_code_from_reports
from services.agents.correct_services.code_plan_services.code_plan_agent import run_code_plan_agent
from services.agents.correct_services.code_writer_services.code_writer_service import run_code_writer
from services.agents.correct_services.code_implementer_services.code_implementer_service import run_code_implementer
from services.test_runner_service.test_runner_service import run_automated_test
from models.correct_models.code_writer_models.code_writer_models import CodeWriterRequest
from models.correct_models.code_implementer_models.code_implementer_models import CodeImplementerRequest


def _to_dict(obj):
    """Compatível com Pydantic v1 (.dict()) e v2 (.model_dump())."""
    if obj is None:
        return {}
    fn = getattr(obj, "model_dump", None) or getattr(obj, "dict", None)
    return fn() if callable(fn) else {}


def _build_analise_sistema(id_requisicao: str, refined_prompt: str, layer2_result: dict) -> dict:
    """Constrói analise_sistema para o code_plan a partir dos resultados da Camada 2."""
    estrutura = layer2_result.get("estrutura", {}) or {}
    estrutura_arquivos = estrutura.get("estrutura_arquivos", {})
    backend = layer2_result.get("backend", {}) or {}
    infra = layer2_result.get("infra", {}) or {}

    planned_new_files = []
    for folder, files in estrutura_arquivos.items():
        folder_norm = (folder or ".").strip("/")
        for f in files if isinstance(files, list) else []:
            path = f"{folder_norm}/{f}".strip("/") if folder_norm and folder_norm != "." else str(f)
            planned_new_files.append(path)

    resumo = refined_prompt
    if backend:
        funcs = backend.get("funcionalidades") or backend.get("arquivos") or []
        resumo = f"{refined_prompt}\n\nBackend: {json.dumps(funcs, ensure_ascii=False)[:500]}"
    if infra:
        resumo += f"\nInfra: {json.dumps(infra, ensure_ascii=False)[:300]}"

    return {
        "id_requisicao": id_requisicao,
        "resumo_programatico": resumo[:2000],
        "planned_new_files": planned_new_files,
    }


def run_workflow_pipeline(prompt: str, usuario: str, root_path: str = None):
    """
    Orquestra a execução das camadas 1, 2 e 3 de ponta a ponta.
    Retorna o documento consolidado final.
    """
    with execution_timer("workflow/creator (governance)", "workflow_core"):
        return _run_workflow_pipeline_impl(prompt, usuario, root_path)


def _run_workflow_pipeline_impl(prompt: str, usuario: str, root_path: str = None):
    workflow_log = []

    try:
        workflow_log.append("🚀 Iniciando workflow completo...")

        #━━━━━━━━━❮Camada 1❯━━━━━━━━━
        layer1_result = execute_layer1(prompt, usuario, root_path)
        workflow_log.append(f"✅ Camada 1 concluída: {layer1_result['id_requisicao']}")

        id_requisicao = layer1_result["id_requisicao"]
        refined_prompt = layer1_result["final_prompt"]
        root_path = layer1_result.get("root_path") or root_path
        root_path = resolve_project_root_for_workflow(usuario, root_path)
        try:
            from utils.log_manager import add_log
            add_log(
                "info",
                f"[workflow_core] root_path efetivo (pós-resolve)={root_path[:240]!r} | usuario={(usuario or '')[:80]!r}",
                "workflow_core",
            )
        except Exception:
            try:
                from app.utils.log_manager import add_log
                add_log(
                    "info",
                    f"[workflow_core] root_path efetivo (pós-resolve)={root_path[:240]!r} | usuario={(usuario or '')[:80]!r}",
                    "workflow_core",
                )
            except Exception:
                pass

        #━━━━━━━━━❮Camada 2❯━━━━━━━━━
        layer2_result = execute_layer2(id_requisicao, refined_prompt, root_path)
        workflow_log.append("✅ Camada 2 concluída com sucesso.")

        #━━━━━━━━━❮Camada 3❯━━━━━━━━━
        workflow_log.append("⚙️ Iniciando Camada 3 – Criação de Estrutura...")
        estrutura_manifest = agent_structure_creator.create_structure_from_report(root_path, id_requisicao)
        workflow_log.append("✅ Estrutura criada com sucesso.")

        #━━━━━━━━━❮Camada 3.2 – Código❯━━━━━━━━━
        if estrutura_manifest.get("status") == "falha" or estrutura_manifest.get("erro"):
            raise ValueError(estrutura_manifest.get("erro", "Falha ao criar estrutura"))
        base_dir = estrutura_manifest.get("root_path") or os.path.join(root_path or "", id_requisicao, "generated_code")
        if not os.path.isdir(base_dir):
            raise FileNotFoundError(f"Diretório do projeto não encontrado: {base_dir}")

        use_ollama = os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes")
        if use_ollama:
            # Ollama: code_creator (1 chamada LLM por arquivo) — muito mais rápido que Code Plan+Writer+Implementer
            workflow_log.append("⚙️ Gerando código-fonte (code_creator, modo Ollama)...")
            code_manifest = create_code_from_reports(root_path, id_requisicao)
            if code_manifest.get("status") == "falha":
                err = code_manifest.get("erro", "Falha ao gerar código")
                raise ValueError(str(err)[:300] if err else "Falha ao gerar código")
            workflow_log.append("✅ Código-fonte criado.")
            consolidated = {
                "workflow": "Camada 1 + 2 + 3 - Pipeline Completo",
                "usuario": usuario,
                "id_requisicao": id_requisicao,
                "final_prompt": refined_prompt,
                "estrutura_arquivos": layer2_result["estrutura"],
                "backend": layer2_result["backend"],
                "infraestrutura": layer2_result["infra"],
                "seguranca_codigo": layer2_result["seguranca_codigo"],
                "seguranca_infra": layer2_result["seguranca_infra"],
                "estrutura_manifest": estrutura_manifest,
                "code_manifest": code_manifest,
                "code_plan": None,
                "code_writer": None,
                "code_implementer": None,
                "test_run": None,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "sucesso",
            }
        else:
            # OpenAI: pipeline completo (Code Plan → Writer → Implementer → Teste)
            analise_sistema = _build_analise_sistema(id_requisicao, refined_prompt, layer2_result)
            workflow_log.append("⚙️ C2b – Code Plan...")
            code_plan_result = run_code_plan_agent("info", usuario, refined_prompt, base_dir, analise_sistema)
            workflow_log.append("⚙️ C3 – Code Writer...")
            writer_result = run_code_writer(CodeWriterRequest(id_requisicao=id_requisicao, root_path=base_dir, usuario=usuario, dry_run=False))
            workflow_log.append("⚙️ C4 – Code Implementer...")
            implementer_result = run_code_implementer(CodeImplementerRequest(id_requisicao=id_requisicao, root_path=base_dir, usuario=usuario, dry_run=False))
            workflow_log.append("⚙️ C5 – Teste automatizado...")
            test_resp = run_automated_test(root_path=base_dir, log_type="info", prefer_docker=True)
            test_result = {"success": test_resp.success, "message": test_resp.message, "method_used": test_resp.method_used, "logs": test_resp.logs, "details": test_resp.details}
            workflow_log.append("✅ Código-fonte criado e testado.")
            files_written = []
            for r in (_to_dict(writer_result).get("files") or []) + (_to_dict(implementer_result).get("files") or []):
                p = r.get("path") if isinstance(r, dict) else getattr(r, "path", None)
                if p and p not in files_written:
                    files_written.append(p)
            code_manifest = {"root_path": base_dir, "files_written": files_written, "status": "sucesso"}
            consolidated = {
                "workflow": "Camada 1 + 2 + 3 - Pipeline Completo",
                "usuario": usuario,
                "id_requisicao": id_requisicao,
                "final_prompt": refined_prompt,
                "estrutura_arquivos": layer2_result["estrutura"],
                "backend": layer2_result["backend"],
                "infraestrutura": layer2_result["infra"],
                "seguranca_codigo": layer2_result["seguranca_codigo"],
                "seguranca_infra": layer2_result["seguranca_infra"],
                "estrutura_manifest": estrutura_manifest,
                "code_manifest": code_manifest,
                "code_plan": code_plan_result,
                "code_writer": _to_dict(writer_result),
                "code_implementer": _to_dict(implementer_result),
                "test_run": test_result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "sucesso",
            }

        log_workflow("workflow.log", f"Pipeline concluído com sucesso: {id_requisicao}")
        return consolidated

    except Exception as e:
        log_workflow("workflow_error.log", f"Erro no workflow: {type(e).__name__}: {e}")
        raw_msg = str(e).strip()[:400].replace('"', "'")
        if not raw_msg:
            raw_msg = type(e).__name__
        msg = "Erro no workflow completo." if is_production() else (raw_msg or "Erro desconhecido")
        raise HTTPException(status_code=500, detail={"code": "WORKFLOW_FAILED", "message": msg})
