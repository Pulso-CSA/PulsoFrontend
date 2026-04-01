#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow Core – Correção / Estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import json
import uuid
from typing import Any, Dict, Optional, List
from datetime import datetime

from utils.log_manager import add_log
from utils.execution_timer import timed

# Camada 1 – Governança
from workflow.creator_workflow.workflow_steps import execute_layer1

# C2 – Structural analysis
from services.struc_anal.structure_scanner_service import scan_full_project
from services.struc_anal.change_plan_service import generate_change_plan

# Para projetos novos
from services.agents.analise_services.structure_service import generate_structure_blueprint

# Aplicação de mudanças estruturais
from services.agents.creator_services.structure_creator_service import (
    apply_change_plan_to_filesystem,
)

# Complemento estrutural / blueprint
from workflow.correct_workflow.structure_apply_service import (
    apply_blueprint_tree,
    expand_plan_with_missing_files,
)

# C2b – Code Plan
from services.agents.correct_services.code_plan_services.code_plan_agent import (
    run_code_plan_agent,
)

# C3 – Code Writer
from services.agents.correct_services.code_writer_services.code_writer_service import (
    run_code_writer,
)
from models.correct_models.code_writer_models.code_writer_models import (
    CodeWriterRequest,
)

# C4 – Code Implementer
from services.agents.correct_services.code_implementer_services.code_implementer_service import (  # noqa: E501
    run_code_implementer,
)
from models.correct_models.code_implementer_models.code_implementer_models import (
    CodeImplementerRequest,
)

# C5 – Teste automatizado (venv ou docker)
from services.test_runner_service.test_runner_service import run_automated_test

# Pipeline de autocorreção (11 → 12 → 13 → 13.1 → 13.2)
from models.pipeline_models.pipeline_models import (
    RelatorioTestes,
    AnaliseRetornoRequest,
    CorrecaoErrosRequest,
    CorrecaoPayload,
    SegurancaCodigoPosRequest,
    SegurancaInfraPosRequest,
)
from services.pipeline_services.analise_retorno_service import run_analise_retorno
from services.pipeline_services.correcao_erros_service import run_correcao_erros
from services.pipeline_services.seguranca_codigo_pos_service import run_seguranca_codigo_pos
from services.pipeline_services.seguranca_infra_pos_service import run_seguranca_infra_pos

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Detecta tipo do projeto❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def _detect_project_status(root_path: str) -> str:
    if not root_path or not os.path.isdir(root_path):
        return "novo"

    for _, _, filenames in os.walk(root_path):
        if filenames:
            return "existente"

    return "novo"


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Helper – filtra lixo genérico do change_plan❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def _infer_feature_slug_from_prompt(prompt: str) -> Optional[str]:
    """
    Extrai algo como 'ttst' a partir de:
      - '/TTST'
      - 'TTST'
    """
    import re

    if not prompt:
        return None

    m = re.search(r"/\s*([a-zA-Z0-9_\-]+)", prompt)
    if m:
        return m.group(1).strip().lower()

    m = re.search(r"\b([A-Z]{3,})\b", prompt)
    if m:
        return m.group(1).strip().lower()

    return None


def _filter_new_files_by_feature(novos_models: List[Any], feature_slug: Optional[str]) -> List[Any]:
    """
    Mantém somente novos arquivos que fazem sentido para a feature.
    Ex.: feature_slug='ttst' → mantém paths contendo 'ttst'.
    Se não conseguir inferir, devolve como está (fallback).
    """
    if not feature_slug:
        return novos_models

    filtered = []
    for n in novos_models:
        try:
            p = (getattr(n, "path", "") or "").lower().replace("\\", "/")
        except Exception:
            p = ""
        if feature_slug in p:
            filtered.append(n)

    return filtered


def _pydantic_to_dict(obj: Any) -> Dict[str, Any]:
    """Compatível com Pydantic v1 (.dict()) e v2 (.model_dump())."""
    if obj is None:
        return {}
    fn = getattr(obj, "model_dump", None) or getattr(obj, "dict", None)
    return fn() if callable(fn) else {}


def _persist_code_plan_snapshot_to_filesystem(root_path: str, id_requisicao: str, code_plan_result: Optional[Dict[str, Any]]) -> None:
    """
    Salva snapshot do CodePlanDocument em:
      <root_path>/code_plan_<id_requisicao>.json

    Isso garante fallback para C3/C4 quando DB estiver indisponível.
    """
    if not isinstance(code_plan_result, dict):
        return

    container = code_plan_result.get("code_plan")
    if not isinstance(container, dict):
        return

    doc = container.get("code_plan")
    if not isinstance(doc, dict):
        return

    try:
        os.makedirs(root_path, exist_ok=True)
        snapshot_path = os.path.join(root_path, f"code_plan_{id_requisicao}.json")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        add_log("info", f"[correct_workflow] Code-plan snapshot saved at {snapshot_path}", "correct_workflow")
    except Exception as exc:
        add_log("error", f"[correct_workflow] Failed to persist code-plan snapshot: {exc}", "correct_workflow")


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow Principal❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


@timed("workflow/correct", "correct_workflow")
def run_correct_workflow(
    log_type: str,
    prompt: str,
    usuario: str,
    root_path: str,
    run_pipeline_autocorrection: bool = True,
    only_c4_c5: bool = False,
    id_requisicao_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    FULL CORRECT WORKFLOW (C1 → C2 → C2b → C3 → C4 → C5 → Pipeline 11–13.2)

    C1 – Governança / refinamento de prompt
    C2 – Análise estrutural / Plano de Mudanças
    C2b – Code Plan | C3 – Code Writer | C4 – Code Implementer
    C5 – Teste automatizado (venv/docker)
    Se run_pipeline_autocorrection: análise retorno → correção (1 rodada) → segurança código/infra.
    only_c4_c5=True: pula C1–C3 e executa só C4+C5 (retry barato a partir do code plan existente).
    """

    add_log(log_type, "[correct_workflow] ========== INÍCIO ==========", "correct_workflow")
    add_log(log_type, f"[correct_workflow] root_path={root_path}", "correct_workflow")

    if only_c4_c5 and id_requisicao_override:
        id_requisicao = id_requisicao_override
        add_log(log_type, "[correct_workflow] Modo only_c4_c5: apenas C4 (implementer) + C5 (teste)", "correct_workflow")
        implementer_request = CodeImplementerRequest(
            id_requisicao=id_requisicao,
            root_path=root_path,
            usuario=usuario,
            dry_run=False,
        )
        implementer_result_obj = run_code_implementer(implementer_request)
        add_log(log_type, "[correct_workflow] C4 – Code Implementer: concluído", "correct_workflow")
        add_log(log_type, "[correct_workflow] C5 – Teste automatizado: iniciando (venv/docker)", "correct_workflow")
        test_resp = run_automated_test(root_path=root_path, log_type=log_type, prefer_docker=True)
        test_result = {
            "success": test_resp.success,
            "message": test_resp.message,
            "method_used": test_resp.method_used,
            "logs": test_resp.logs,
            "details": test_resp.details,
        }
        return {
            "id_requisicao": id_requisicao,
            "projeto_status": "existente",
            "governanca": None,
            "analise_estrutural": None,
            "plano_de_codigo": None,
            "blueprint": None,
            "plano_de_mudancas": None,
            "execucao": None,
            "code_writer": None,
            "code_implementer": _pydantic_to_dict(implementer_result_obj) if implementer_result_obj else None,
            "test_run": test_result,
            "pipeline_analise_retorno": None,
            "pipeline_correcao": None,
            "pipeline_seguranca_codigo_pos": None,
            "pipeline_seguranca_infra_pos": None,
        }

    project_status = _detect_project_status(root_path)
    add_log(log_type, f"[correct_workflow] Projeto detectado: {project_status}", "correct_workflow")

    #━━━━━━━━━❮Camada 1 – Governança❯━━━━━━━━━
    add_log(log_type, "[correct_workflow] C1 – Governança: iniciando (input, refino, validação)", "correct_workflow")
    camada1_result = execute_layer1(
        prompt=prompt,
        usuario=usuario,
        root_path=root_path,
    )
    add_log(log_type, "[correct_workflow] C1 – Governança: concluído", "correct_workflow")

    id_requisicao = (
        camada1_result.get("id_requisicao")
        or f"REQ-COR-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    )
    refined_prompt = camada1_result.get("final_prompt", prompt)

    analise_estrutural: Optional[Dict[str, Any]] = None
    plano_de_mudancas: Optional[Dict[str, Any]] = None
    novos_models = []
    alterar_models = []
    code_plan_result: Optional[Dict[str, Any]] = None
    writer_result_obj = None
    implementer_result_obj = None
    test_result: Optional[Dict[str, Any]] = None
    pipeline_analise_retorno: Optional[Dict[str, Any]] = None
    pipeline_correcao: Optional[Dict[str, Any]] = None
    pipeline_seguranca_codigo_pos: Optional[Dict[str, Any]] = None
    pipeline_seguranca_infra_pos: Optional[Dict[str, Any]] = None
    correcao_payload: Optional[Any] = None  # CorrecaoPayload para 13.1/13.2

    blueprint_info: Optional[Dict[str, Any]] = None
    execucao_info: Optional[Dict[str, Any]] = None

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
    #━━━━━━━━━❮Projeto Existente❯━━━━━━━━━
    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

    if project_status == "existente":
        # C2 – Scanner
        add_log(log_type, "[correct_workflow] C2 – Scanner: iniciando análise estrutural do projeto", "correct_workflow")
        scanned = scan_full_project(
            log_type=log_type,
            root_path=root_path,
            id_requisicao=id_requisicao,
            prompt=refined_prompt,
        )
        add_log(log_type, f"[correct_workflow] C2 – Scanner: concluído ({len(scanned.arquivos)} arquivos)", "correct_workflow")

        analise_estrutural = {
            "id_requisicao": scanned.id_requisicao,
            "root_path": scanned.root_path,
            "resumo_programatico": scanned.resumo_sistema,
            "total_arquivos": len(scanned.arquivos),
        }

        # C2 – Change Plan
        add_log(log_type, "[correct_workflow] C2 – Plano de mudanças: gerando (novos arquivos / alterar)", "correct_workflow")
        resumo_sistema, novos, alterar = generate_change_plan(
            log_type=log_type,
            scanned=scanned,
            prompt=refined_prompt,
        )
        add_log(log_type, f"[correct_workflow] C2 – Plano de mudanças: {len(novos)} novos, {len(alterar)} a alterar", "correct_workflow")

        novos_models = novos
        alterar_models = alterar

        # ⛔ Evita “module_models/test_models” (lixo genérico)
        feature_slug = _infer_feature_slug_from_prompt(refined_prompt)
        novos_models = _filter_new_files_by_feature(novos_models, feature_slug)

        # ⛔ Evitar expand_plan_with_missing_files (é um dos gatilhos do lixo)
        # Se você quiser reativar, faça isso só quando for 100% determinístico.
        # novos_models = expand_plan_with_missing_files(
        #     id_requisicao=id_requisicao,
        #     root_path=root_path,
        #     novos=novos_models,
        #     alterar=alterar_models,
        # )

        plano_de_mudancas = {
            "resumo_sistema": resumo_sistema,
            "novos_arquivos": [_pydantic_to_dict(n) for n in novos_models],
            "arquivos_a_alterar": [_pydantic_to_dict(a) for a in alterar_models],
        }

        add_log(
            log_type,
            f"Change plan updated for {id_requisicao} "
            f"(new={len(novos_models)}, update={len(alterar_models)})",
            "correct_workflow",
        )

        # ✅ orientar o code-plan com paths reais planejados (reduz divergência)
        if analise_estrutural is not None:
            analise_estrutural["planned_new_files"] = [n.path for n in novos_models]

        # ✅ aplicar mudanças estruturais NO CLONE (como você quer)
        add_log(log_type, "[correct_workflow] C2 – Aplicando mudanças estruturais no filesystem", "correct_workflow")
        if novos_models:
            execucao_info = apply_change_plan_to_filesystem(
                root_path=root_path,
                id_requisicao=id_requisicao,
                novos_arquivos=novos_models,
            )
            add_log(log_type, f"[correct_workflow] C2 – Estrutura aplicada: {len(execucao_info.get('created_files', []))} arquivos criados", "correct_workflow")
        else:
            execucao_info = {
                "root_path": root_path,
                "created_files": [],
                "skipped_existing_files": [],
                "touched_dirs": [],
                "message": "No structural changes required.",
            }
            add_log(log_type, "[correct_workflow] C2 – Estrutura: nenhuma mudança estrutural necessária", "correct_workflow")

        # C2b – Code Plan
        add_log(log_type, "[correct_workflow] C2b – Code Plan: iniciando agente de plano de código", "correct_workflow")
        code_plan_result = run_code_plan_agent(
            log_type=log_type,
            usuario=usuario,
            prompt_usuario=refined_prompt,
            root_path=root_path,
            analise_sistema=analise_estrutural,
        )
        add_log(log_type, "[correct_workflow] C2b – Code Plan: concluído", "correct_workflow")

        # ✅ snapshot do code_plan dentro do clone (fallback DB OFF)
        _persist_code_plan_snapshot_to_filesystem(
            root_path=root_path,
            id_requisicao=id_requisicao,
            code_plan_result=code_plan_result,
        )

        # C3 – Code Writer (ESCREVE NO CLONE)
        writer_request = CodeWriterRequest(
            id_requisicao=id_requisicao,
            root_path=root_path,
            usuario=usuario,
            dry_run=False,
        )
        writer_result_obj = run_code_writer(writer_request)

        # C4 – Code Implementer (ESCREVE NO CLONE)
        implementer_request = CodeImplementerRequest(
            id_requisicao=id_requisicao,
            root_path=root_path,
            usuario=usuario,
            dry_run=False,
        )
        implementer_result_obj = run_code_implementer(implementer_request)
        add_log(log_type, "[correct_workflow] C4 – Code Implementer: concluído", "correct_workflow")

        # C5 – Teste automatizado (último passo): venv ou docker
        add_log(log_type, "[correct_workflow] C5 – Teste automatizado: iniciando (venv/docker)", "correct_workflow")
        test_resp = run_automated_test(root_path=root_path, log_type=log_type, prefer_docker=True)
        test_result = {
            "success": test_resp.success,
            "message": test_resp.message,
            "method_used": test_resp.method_used,
            "logs": test_resp.logs,
            "details": test_resp.details,
        }
        if not test_resp.success:
            add_log(
                "warning",
                f"[correct_workflow] Teste automatizado falhou: {test_resp.message}",
                "correct_workflow",
            )

        #━━━━━━━━━❮Pipeline de autocorreção (11 → 12 → 13 → 13.1 → 13.2)❯━━━━━━━━━
        if run_pipeline_autocorrection and test_result is not None:
            add_log(log_type, "[correct_workflow] Iniciando pipeline de autocorreção completo", "correct_workflow")
            logs_list = test_result.get("logs") or []
            if test_result.get("details"):
                logs_list.append(str(test_result["details"])[:500])
            relatorio = RelatorioTestes(
                status="aprovado" if test_result.get("success") else "parcialmente aprovado",
                erros=[] if test_result.get("success") else [test_result.get("message", ""), (test_result.get("details") or "")[:300]],
                vulnerabilidades=[],
                logs=logs_list,
            )
            analise_req = AnaliseRetornoRequest(
                id_requisicao=id_requisicao,
                relatorio_testes=relatorio,
                root_path=root_path,
            )
            add_log(log_type, "[correct_workflow] 12 – Análise de retorno: iniciando", "correct_workflow")
            analise_resp = run_analise_retorno(analise_req)
            pipeline_analise_retorno = _pydantic_to_dict(analise_resp)
            add_log(log_type, f"[correct_workflow] 12 – Análise de retorno: concluído (objetivo_final={analise_resp.analise_retorno.objetivo_final})", "correct_workflow")

            if analise_resp.analise_retorno.objetivo_final != "atingido":
                add_log(log_type, "[correct_workflow] 13 – Correção de erros: iniciando (1 rodada)", "correct_workflow")
                correcao_req = CorrecaoErrosRequest(
                    id_requisicao=id_requisicao,
                    analise_retorno=analise_resp.analise_retorno,
                    root_path=root_path,
                    usuario=usuario,
                )
                correcao_resp = run_correcao_erros(correcao_req, run_pipeline_autocorrection=False)
                pipeline_correcao = _pydantic_to_dict(correcao_resp)
                correcao_payload = correcao_resp.correcao
                add_log(log_type, f"[correct_workflow] 13 – Correção de erros: concluído (status={correcao_payload.status})", "correct_workflow")
            else:
                correcao_payload = CorrecaoPayload(
                    erros_corrigidos=[],
                    funcionalidades_atualizadas=[],
                    estrutura_atualizada=[],
                    status="sem correção necessária",
                )
                pipeline_correcao = {
                    "id_requisicao": id_requisicao,
                    "correcao": _pydantic_to_dict(correcao_payload),
                    "workflow_result": None,
                }

            add_log(log_type, "[correct_workflow] 13.1 – Segurança código (pós-correção): iniciando", "correct_workflow")
            sec_codigo_req = SegurancaCodigoPosRequest(
                id_requisicao=id_requisicao,
                relatorio_correcao=correcao_payload,
            )
            pipeline_seguranca_codigo_pos = _pydantic_to_dict(run_seguranca_codigo_pos(sec_codigo_req))
            add_log(log_type, "[correct_workflow] 13.1 – Segurança código: concluído", "correct_workflow")
            add_log(log_type, "[correct_workflow] 13.2 – Segurança infra (pós-correção): iniciando", "correct_workflow")
            sec_infra_req = SegurancaInfraPosRequest(
                id_requisicao=id_requisicao,
                relatorio_correcao=correcao_payload,
            )
            pipeline_seguranca_infra_pos = _pydantic_to_dict(run_seguranca_infra_pos(sec_infra_req))
            add_log(log_type, "[correct_workflow] 13.2 – Segurança infra: concluído", "correct_workflow")
            add_log(log_type, "[correct_workflow] ---------- Pipeline de autocorreção finalizado ----------", "correct_workflow")

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
    #━━━━━━━━━❮Projeto Novo❯━━━━━━━━━
    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

    else:
        add_log(log_type, "[correct_workflow] Projeto novo: gerando blueprint e aplicando estrutura", "correct_workflow")
        blueprint_info = generate_structure_blueprint(id_requisicao)
        estrutura_arquivos = blueprint_info.get("estrutura_arquivos", {})
        execucao_info = apply_blueprint_tree(
            log_type=log_type,
            root_path=root_path,
            blueprint_tree=estrutura_arquivos,
        )

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
    #━━━━━━━━━❮Resposta Final❯━━━━━━━━━
    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

    response: Dict[str, Any] = {
        "id_requisicao": id_requisicao,
        "projeto_status": project_status,
        "governanca": camada1_result,
        "analise_estrutural": analise_estrutural,
        "plano_de_codigo": code_plan_result,
        "blueprint": blueprint_info,
        "plano_de_mudancas": plano_de_mudancas,
        "execucao": execucao_info,
        "code_writer": _pydantic_to_dict(writer_result_obj) if writer_result_obj else None,
        "code_implementer": (
            _pydantic_to_dict(implementer_result_obj) if implementer_result_obj else None
        ),
        "test_run": test_result,
        "pipeline_analise_retorno": pipeline_analise_retorno,
        "pipeline_correcao": pipeline_correcao,
        "pipeline_seguranca_codigo_pos": pipeline_seguranca_codigo_pos,
        "pipeline_seguranca_infra_pos": pipeline_seguranca_infra_pos,
    }

    add_log(log_type, f"[correct_workflow] ========== FIM (id_requisicao={id_requisicao}) ==========", "correct_workflow")

    return response
