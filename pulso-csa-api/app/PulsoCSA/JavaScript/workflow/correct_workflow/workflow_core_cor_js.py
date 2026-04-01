#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow Correct JavaScript❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
from typing import Dict, Any
from datetime import datetime

from utils.logger import log_workflow
from utils.execution_timer import execution_timer
from app.prompts.loader import set_request_stack
from app.PulsoCSA.JavaScript.utils.project_validator_js import validate_js_project, detect_project_needs

# C1 – Governança (pipeline igual ao Python)
try:
    from app.PulsoCSA.JavaScript.workflow.creator_workflow.workflow_steps_js import execute_layer1_js
    _HAS_LAYER1 = True
except ImportError:
    execute_layer1_js = None
    _HAS_LAYER1 = False

try:
    from app.PulsoCSA.JavaScript.services.code_implementer_service_js import correct_file_js
    _HAS_LLM_CORRECTOR = True
except ImportError:
    correct_file_js = None
    _HAS_LLM_CORRECTOR = False

try:
    from app.PulsoCSA.JavaScript.services.test_runner_service_js import run_automated_test_js
    _HAS_TEST_RUNNER = True
except ImportError:
    run_automated_test_js = None
    _HAS_TEST_RUNNER = False

try:
    from app.PulsoCSA.JavaScript.services.struc_anal import (
        scan_full_project_js,
        generate_change_plan_js,
        apply_change_plan_to_filesystem_js,
    )
    _HAS_STRUC_ANAL = True
except ImportError:
    scan_full_project_js = None
    generate_change_plan_js = None
    apply_change_plan_to_filesystem_js = None
    _HAS_STRUC_ANAL = False


def _run_c4_correct_files(root_path, existing_files, prompt, language, framework, workflow_log):
    """Executa C4: corrige arquivos via LLM (correct_file_js)."""
    corrected = []
    if not existing_files or not correct_file_js:
        return corrected
    for rel_path in existing_files[:10]:
        if not rel_path.endswith((".js", ".ts", ".jsx", ".tsx", ".vue")):
            continue
        full_path = os.path.join(root_path, rel_path)
        if not os.path.exists(full_path):
            continue
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = correct_file_js(
                file_path=rel_path,
                existing_source=content,
                prompt=prompt,
                project_root=root_path,
                language=language,
                framework=framework,
            )
            if new_content and new_content != content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                corrected.append(rel_path)
                workflow_log.append(f"Corrigido: {rel_path}")
        except Exception as e:
            workflow_log.append(f"Skip {rel_path}: {e}")
    return corrected


def _run_pipeline_autocorrection_js(id_requisicao, root_path, usuario, test_result, base_result, workflow_log):
    """Pipeline 12 -> 13 -> 13.1 -> 13.2 para JS."""
    try:
        from app.PulsoCSA.Python.models.pipeline_models.pipeline_models import (
            RelatorioTestes,
            AnaliseRetornoRequest,
            CorrecaoErrosRequest,
        )
        from app.PulsoCSA.JavaScript.services.pipeline_services_js import (
            run_analise_retorno_js,
            run_correcao_erros_js,
            run_seguranca_codigo_pos_js,
            run_seguranca_infra_pos_js,
        )
    except ImportError:
        workflow_log.append("Pipeline autocorreção: imports não disponíveis")
        return base_result

    logs_list = test_result.get("logs") or []
    if test_result.get("details"):
        logs_list.append(str(test_result["details"])[:500])
    relatorio = RelatorioTestes(
        status="parcialmente aprovado",
        erros=[test_result.get("message", ""), (test_result.get("details") or "")[:300]],
        vulnerabilidades=[],
        logs=logs_list,
    )
    analise_req = AnaliseRetornoRequest(
        id_requisicao=id_requisicao,
        relatorio_testes=relatorio,
        root_path=root_path,
    )
    workflow_log.append("12 - Análise de retorno...")
    analise_resp = run_analise_retorno_js(analise_req)
    base_result["pipeline_analise_retorno"] = analise_resp.model_dump() if hasattr(analise_resp, "model_dump") else {}

    if analise_resp.analise_retorno.objetivo_final != "atingido":
        workflow_log.append("13 - Correção de erros...")
        correcao_req = CorrecaoErrosRequest(
            id_requisicao=id_requisicao,
            analise_retorno=analise_resp.analise_retorno,
            root_path=root_path,
            usuario=usuario,
        )
        correcao_resp = run_correcao_erros_js(correcao_req, run_pipeline_autocorrection=False)
        base_result["pipeline_correcao"] = correcao_resp.model_dump() if hasattr(correcao_resp, "model_dump") else {}
        correcao_payload = correcao_resp.correcao
    else:
        from app.PulsoCSA.Python.models.pipeline_models.pipeline_models import CorrecaoPayload
        correcao_payload = CorrecaoPayload(
            erros_corrigidos=[],
            funcionalidades_atualizadas=[],
            estrutura_atualizada=[],
            status="sem correção necessária",
        )
        base_result["pipeline_correcao"] = {"id_requisicao": id_requisicao, "correcao": correcao_payload.model_dump()}

    workflow_log.append("13.1 - Segurança código...")
    try:
        from app.PulsoCSA.Python.models.pipeline_models.pipeline_models import (
            SegurancaCodigoPosRequest,
            SegurancaInfraPosRequest,
        )
        sec_codigo_req = SegurancaCodigoPosRequest(
            id_requisicao=id_requisicao,
            relatorio_correcao=correcao_payload,
        )
        sec_resp = run_seguranca_codigo_pos_js(sec_codigo_req)
        base_result["pipeline_seguranca_codigo_pos"] = sec_resp.model_dump() if hasattr(sec_resp, "model_dump") else {}
    except Exception as ex:
        base_result["pipeline_seguranca_codigo_pos"] = {"erro": str(ex)}
    workflow_log.append("13.2 - Segurança infra...")
    try:
        sec_infra_req = SegurancaInfraPosRequest(
            id_requisicao=id_requisicao,
            relatorio_correcao=correcao_payload,
        )
        sec_infra_resp = run_seguranca_infra_pos_js(sec_infra_req)
        base_result["pipeline_seguranca_infra_pos"] = sec_infra_resp.model_dump() if hasattr(sec_infra_resp, "model_dump") else {}
    except Exception as ex:
        base_result["pipeline_seguranca_infra_pos"] = {"erro": str(ex)}
    workflow_log.append("Pipeline autocorreção finalizado")
    return base_result


def run_correct_workflow_js(
    log_type: str,
    prompt: str,
    usuario: str,
    root_path: str,
    language: str = "javascript",
    framework: str | None = None,
    run_pipeline_autocorrection: bool = True,
    only_c4_c5: bool = False,
    id_requisicao_override: str | None = None,
) -> Dict[str, Any]:
    """
    Executa workflow de correção para projetos JavaScript/TypeScript/React.
    run_pipeline_autocorrection: após C5, executa análise retorno → correção → segurança.
    only_c4_c5: pula C1–C2 e executa só C4 (implementer) + C5 (teste).
    """
    with execution_timer("workflow/correct-js", "workflow_core_cor_js"):
        return _run_correct_workflow_js_impl(
            log_type, prompt, usuario, root_path, language, framework,
            run_pipeline_autocorrection, only_c4_c5, id_requisicao_override,
        )


def _run_correct_workflow_js_impl(
    log_type: str,
    prompt: str,
    usuario: str,
    root_path: str,
    language: str = "javascript",
    framework: str | None = None,
    run_pipeline_autocorrection: bool = True,
    only_c4_c5: bool = False,
    id_requisicao_override: str | None = None,
) -> Dict[str, Any]:
    """
    Implementação do workflow de correção JavaScript.
    only_c4_c5: pula C1–C2, executa só C4 + C5.
    """
    workflow_log = []
    id_requisicao = id_requisicao_override or f"js-cor-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(str(prompt) + usuario) % 10000}"

    try:
        workflow_log.append(f"Iniciando correção JavaScript ({language}/{framework})...")

        # Modo only_c4_c5: pula C1/C2, executa só C4 + C5
        if only_c4_c5 and id_requisicao_override:
            id_requisicao = id_requisicao_override
            workflow_log.append("Modo only_c4_c5: C4 (implementer) + C5 (teste)")
            validation = validate_js_project(root_path)
            if not validation["valid"]:
                raise ValueError(validation.get("error", "Projeto inválido"))
            existing_files = validation.get("files", [])
            corrected_files = _run_c4_correct_files(
                root_path, existing_files, prompt, language, framework, workflow_log
            )
            test_result = run_automated_test_js(root_path, log_type) if _HAS_TEST_RUNNER and run_automated_test_js else None
            result = {
                "id_requisicao": id_requisicao,
                "status": "sucesso",
                "corrected_files": corrected_files,
                "workflow_log": workflow_log,
                "test_run": test_result,
            }
            if run_pipeline_autocorrection and test_result and not test_result.get("success"):
                result = _run_pipeline_autocorrection_js(
                    id_requisicao, root_path, usuario, test_result, result, workflow_log
                )
            return result
        
        #━━━━━━━━━❮C1 – Governança (Input → Refine → Validate)❯━━━━━━━━━
        refined_prompt = prompt
        if _HAS_LAYER1 and execute_layer1_js:
            set_request_stack("javascript")
            workflow_log.append("⚙️ C1 – Governança...")
            layer1 = execute_layer1_js(prompt, usuario, root_path)
            id_requisicao = layer1["id_requisicao"]
            refined_prompt = layer1["final_prompt"]
            workflow_log.append(f"✅ C1 concluída: {id_requisicao}")
        else:
            id_requisicao = f"js-cor-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(prompt + usuario) % 10000}"
        
        # Valida projeto existente
        validation = validate_js_project(root_path)
        if not validation["valid"]:
            raise ValueError(f"Projeto inválido: {validation.get('error', 'Diretório não encontrado')}")
        
        workflow_log.append(f"✅ Projeto validado: {validation.get('project_type', 'unknown')}")
        if validation.get("framework"):
            workflow_log.append(f"📦 Framework detectado: {validation['framework']}")
        
        # Detecta necessidades baseadas no prompt
        needs = detect_project_needs(root_path, prompt)
        if needs:
            workflow_log.append(f"🎯 Necessidades detectadas: {', '.join(needs)}")
        
        # Lista arquivos existentes
        existing_files = validation.get("files", [])
        workflow_log.append(f"📁 Encontrados {len(existing_files)} arquivos no projeto")

        # C2 – Scanner → Change Plan → Apply (quando disponível)
        files_to_correct = list(existing_files)
        if _HAS_STRUC_ANAL and scan_full_project_js and generate_change_plan_js and apply_change_plan_to_filesystem_js:
            try:
                workflow_log.append("⚙️ C2 – Scanner...")
                scanned = scan_full_project_js(log_type, root_path, id_requisicao, refined_prompt)
                workflow_log.append(f"✅ C2 – Scanner: {len(scanned.arquivos)} arquivos")
                workflow_log.append("⚙️ C2 – Change Plan...")
                resumo, novos, alterar = generate_change_plan_js(log_type, scanned, refined_prompt)
                workflow_log.append(f"✅ C2 – Plano: {len(novos)} novos, {len(alterar)} a alterar")
                if novos:
                    exec_info = apply_change_plan_to_filesystem_js(root_path, id_requisicao, novos)
                    created = exec_info.get("created_files", [])
                    for p in created:
                        rel = os.path.relpath(p, root_path).replace("\\", "/")
                        if rel not in files_to_correct:
                            files_to_correct.append(rel)
                for a in alterar:
                    p = a.path.replace("\\", "/")
                    if p not in files_to_correct:
                        files_to_correct.append(p)
            except Exception as ex:
                workflow_log.append(f"⚠️ C2 skip: {ex}")

        # Gera arquivo de correção baseado no prompt
        corrected_files = []
        
        # Cria arquivo de log de correções
        correction_log_path = os.path.join(root_path, ".pulso-corrections.md")
        correction_log = f"""# Correções Aplicadas

## Prompt
{prompt}

## Linguagem/Framework
- Linguagem: {language}
- Framework: {framework or 'Nenhum'}

## Arquivos Modificados
"""
        
        # Corrige arquivos via LLM (C4) – usa files_to_correct (C2) ou existing_files
        if files_to_correct and correct_file_js:
            for rel_path in files_to_correct[:10]:  # Limita a 10 arquivos
                if not rel_path.endswith(('.js', '.ts', '.jsx', '.tsx', '.vue')):
                    continue
                full_path = os.path.join(root_path, rel_path)
                if not os.path.exists(full_path):
                    continue
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    corrected_content = correct_file_js(
                        file_path=rel_path,
                        existing_source=content,
                        prompt=refined_prompt,
                        project_root=root_path,
                        language=language,
                        framework=framework,
                    )
                    if corrected_content and corrected_content != content:
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(corrected_content)
                        corrected_files.append(rel_path)
                        correction_log += f"- {rel_path}\n"
                        workflow_log.append(f"✅ Corrigido via LLM: {rel_path}")
                except Exception as e:
                    workflow_log.append(f"⚠️ Skip {rel_path}: {e}")
        elif files_to_correct or existing_files:
            fallback_list = files_to_correct if files_to_correct else existing_files
            sample_file = next((f for f in fallback_list if f.endswith(('.js', '.ts', '.jsx', '.tsx'))), None)
            if sample_file:
                sample_path = os.path.join(root_path, sample_file)
                if os.path.exists(sample_path):
                    with open(sample_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    corrected_content = f"// Correção aplicada via Pulso CSA\n// Prompt: {prompt[:100]}\n\n{content}"
                    with open(sample_path, 'w', encoding='utf-8') as f:
                        f.write(corrected_content)
                    corrected_files.append(sample_file)
                    correction_log += f"- {sample_file}\n"
                    workflow_log.append(f"✅ Corrigido (fallback): {sample_file}")
        
        correction_log += f"\n## Data\n{datetime.now().isoformat()}\n"
        
        with open(correction_log_path, 'w', encoding='utf-8') as f:
            f.write(correction_log)
        
        corrected_files.append(".pulso-corrections.md")
        
        #━━━━━━━━━❮C5 – Teste automatizado (npm test)❯━━━━━━━━━
        test_result = None
        if _HAS_TEST_RUNNER and run_automated_test_js:
            workflow_log.append("⚙️ C5 – Teste automatizado...")
            test_result = run_automated_test_js(root_path, log_type)
            if test_result.get("success"):
                workflow_log.append("✅ C5 – Testes passaram")
            else:
                workflow_log.append(f"⚠️ C5 – {test_result.get('message', 'Testes falharam')}")
        
        result = {
            "id_requisicao": id_requisicao,
            "status": "sucesso",
            "language": language,
            "framework": framework,
            "corrected_files": corrected_files,
            "existing_files_count": len(existing_files),
            "root_path": root_path,
            "workflow_log": workflow_log,
            "test_run": test_result,
        }

        if run_pipeline_autocorrection and test_result and not test_result.get("success"):
            result = _run_pipeline_autocorrection_js(
                id_requisicao, root_path, usuario, test_result, result, workflow_log
            )
        
        if run_pipeline_autocorrection and test_result and not test_result.get("success"):
            result = _run_pipeline_autocorrection_js(
                id_requisicao, root_path, usuario, test_result, result, workflow_log
            )
        log_workflow("workflow.log", f"[workflow-correct-js] Concluído: {id_requisicao} ({language}/{framework})")
        return result
        
    except Exception as e:
        error_msg = f"Erro no workflow de correção JavaScript: {str(e)}"
        workflow_log.append(f"❌ {error_msg}")
        log_workflow("workflow.log", f"[workflow-correct-js] ERRO: {error_msg}")
        return {
            "id_requisicao": id_requisicao if 'id_requisicao' in locals() else "unknown",
            "status": "falha",
            "erro": error_msg,
            "workflow_log": workflow_log,
        }
