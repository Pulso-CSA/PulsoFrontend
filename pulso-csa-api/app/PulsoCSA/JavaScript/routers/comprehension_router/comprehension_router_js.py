#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router – Sistema de Compreensão JavaScript❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
import os
import time
from contextvars import copy_context
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pathlib import Path

from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from app.PulsoCSA.JavaScript.models.comprehension_models import (
    ComprehensionJSRequest,
    ComprehensionJSResponse,
    PROMPT_MAX_LENGTH,
)
from app.PulsoCSA.JavaScript.services.comprehension_services import route_to_module_js
from app.PulsoCSA.Python.services.comprehension_services import (
    build_humanized_message,
    generate_analysis_text,
    build_project_file_tree,
    build_file_tree_from_manifest,
    extract_new_paths_from_workflow_result,
    get_system_behavior_spec,
    get_frontend_suggestion,
    build_curl_commands,
    INTENT_ANALISAR,
    INTENT_EXECUTAR,
    PROJECT_STATE_VAZIA,
    PROJECT_STATE_COM_CONTEUDO,
    TARGET_GOVERNANCE,
    TARGET_CORRECT,
    ANALYSIS_UNAVAILABLE_MESSAGE,
)
from app.PulsoCSA.JavaScript.workflow.creator_workflow.workflow_core_js import run_workflow_pipeline_js
from app.PulsoCSA.JavaScript.workflow.correct_workflow.workflow_core_cor_js import run_correct_workflow_js
from app.PulsoCSA.Python.workflow.creator_workflow.workflow_core import run_workflow_pipeline
from app.PulsoCSA.Python.workflow.correct_workflow.workflow_core_cor import run_correct_workflow
from utils.logger import log_workflow
from utils.path_validation import sanitize_root_path, workspace_path_for_user, is_production as path_is_production
from utils.log_manager import add_log
import traceback

from app.pulso_csa_time_limits import (
    CsaRequestBudget,
    CSA_WORKFLOW_WALL_CLOCK_SEC,
    csa_timeout_http_detail,
    csa_timeout_user_message,
)

from services.comprehension_services.comprehension_job_store import (
    assert_job_owner,
    create_job,
    mark_completed,
    mark_failed,
    mark_running,
)

router = APIRouter(tags=["Sistema de Compreensão JavaScript – Entrada do Workflow"])


def _want_async_mode(async_mode_query: bool) -> bool:
    if os.getenv("COMPREHENSION_FORCE_SYNC_WORKFLOW", "").strip().lower() in ("1", "true", "yes"):
        return False
    return async_mode_query


def _owner_sub(user: dict) -> str:
    return user.get("email") or user.get("_id") or "anonymous"


def _js_extra_response_fields(
    *,
    workflow_result: Optional[dict],
    executed_target: Optional[str],
    root_path: Optional[str],
    prompt: str,
    usuario: str,
    target_endpoint: Optional[str],
    intent: str,
    project_state: str,
    should_execute: bool,
    language: str,
    framework: Optional[str],
    api_base_url: str,
    preview_url: str,
) -> Dict[str, Any]:
    rp = (root_path or "").strip()
    if workflow_result and rp and executed_target:
        new_paths = extract_new_paths_from_workflow_result(workflow_result, rp, executed_target)
        file_tree = build_project_file_tree(rp, new_paths)
    elif rp:
        file_tree = build_project_file_tree(rp, None)
    elif workflow_result and executed_target:
        file_tree = build_file_tree_from_manifest(workflow_result)
    else:
        file_tree = None
    return {
        "file_tree": file_tree,
        "system_behavior": get_system_behavior_spec(),
        "frontend_suggestion": get_frontend_suggestion(
            intent=intent,
            project_state=project_state,
            should_execute=should_execute,
            has_file_tree=bool(file_tree),
            target_endpoint=target_endpoint,
        ),
        "curl_commands": build_curl_commands(
            base_url=api_base_url,
            prompt=prompt,
            usuario=usuario,
            root_path=root_path,
            target_endpoint=target_endpoint,
            executed=bool(workflow_result and executed_target),
            workflow_result=workflow_result,
        ),
        "preview_frontend_url": (preview_url if (workflow_result and executed_target and language != "python") else None),
        "preview_auto_open": False,
    }


async def _job_run_governance_js(
    job_id: str,
    payload: ComprehensionJSRequest,
    decision: dict,
    root_path: Optional[str],
    module: str,
    language: str,
    framework: Optional[str],
    run_backend: bool,
    run_frontend: bool,
    backend_root_path: Optional[str],
    api_base_url: str,
    preview_url: str,
    intent: str,
    project_state: str,
    target_endpoint: Optional[str],
    workflow_usuario: str,
) -> None:
    from core.llm.llm_context import clear_request_api_key, set_request_api_key

    loop = asyncio.get_event_loop()
    mark_running(job_id)
    t0 = time.perf_counter()
    try:
        add_log(
            "info",
            f"[_job_run_governance_js] início | job_id={job_id} | workflow_usuario={workflow_usuario[:48]!r} | "
            f"run_backend={run_backend} run_frontend={run_frontend}",
            "comprehension_router_js",
        )
        if getattr(payload, "openai_api_key", None) and str(payload.openai_api_key).strip():
            set_request_api_key(str(payload.openai_api_key).strip())
        ctx = copy_context()
        job_budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
        backend_result = None
        if run_backend:
            rp_backend = backend_root_path or root_path
            backend_result = await job_budget.run_in_executor(
                loop,
                lambda: ctx.run(
                    lambda: run_workflow_pipeline(
                        prompt=payload.prompt,
                        usuario=workflow_usuario,
                        root_path=rp_backend,
                    )
                ),
            )
            log_workflow("workflow.log", f"[comprehension-js] governance/run (job, PY) para {workflow_usuario}")

        if run_frontend:
            result = await job_budget.run_in_executor(
                loop,
                lambda: ctx.run(
                    lambda: run_workflow_pipeline_js(
                        prompt=payload.prompt,
                        usuario=workflow_usuario,
                        root_path=root_path,
                        language=language,
                        framework=framework,
                    )
                ),
            )
            log_workflow("workflow.log", f"[comprehension-js] governance/run (job) para {workflow_usuario} ({language}/{framework})")
            if backend_result:
                try:
                    result.setdefault("workflow_log", []).append("🧩 Backend (Python) executado em paralelo ao frontend")
                    result["_backend_result"] = {
                        "status": backend_result.get("status"),
                        "id_requisicao": backend_result.get("id_requisicao"),
                        "root_path": backend_result.get("root_path"),
                    }
                except Exception:
                    pass
        else:
            result = backend_result or {"status": "sucesso", "workflow_log": ["Backend executado; frontend skip (backend_only)"]}

        message = build_humanized_message(
            intent=intent,
            project_state=project_state,
            should_execute=True,
            target_endpoint=target_endpoint,
            workflow_result=result,
        )
        extra = _js_extra_response_fields(
            workflow_result=result,
            executed_target=TARGET_GOVERNANCE,
            root_path=root_path,
            prompt=(payload.prompt or "").strip(),
            usuario=workflow_usuario,
            target_endpoint=target_endpoint,
            intent=intent,
            project_state=project_state,
            should_execute=True,
            language=language,
            framework=framework,
            api_base_url=api_base_url,
            preview_url=preview_url,
        )
        elapsed = time.perf_counter() - t0
        resp = ComprehensionJSResponse(
            intent=intent,
            project_state=project_state,
            should_execute=True,
            target_endpoint=target_endpoint,
            explanation=decision["explanation"],
            next_action=decision["next_action"],
            message=message,
            file_tree=extra["file_tree"],
            system_behavior=extra["system_behavior"],
            frontend_suggestion=extra["frontend_suggestion"],
            curl_commands=extra["curl_commands"],
            preview_frontend_url=extra["preview_frontend_url"],
            preview_auto_open=extra.get("preview_auto_open", False),
            intent_confidence=decision.get("intent_confidence"),
            intent_warning=decision.get("intent_warning"),
            processing_time_ms=int(elapsed * 1000),
            module=module,
            language=language,
            framework=framework,
        )
        mark_completed(job_id, resp.model_dump(mode="json"))
        add_log(
            "info",
            f"[_job_run_governance_js] OK | job_id={job_id} | ms={int((time.perf_counter()-t0)*1000)}",
            "comprehension_router_js",
        )
    except HTTPException as he:
        detail = he.detail
        if isinstance(detail, dict):
            mark_failed(job_id, str(detail.get("code", "HTTP_ERROR")), str(detail.get("message", he.detail)))
        else:
            mark_failed(job_id, "HTTP_ERROR", str(detail))
    except asyncio.TimeoutError:
        mark_failed(job_id, "CSA_TIME_BUDGET_EXCEEDED", csa_timeout_user_message())
    except Exception as e:
        add_log(
            "error",
            f"[comprehension-js] GOVERNANCE_JOB_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
            "comprehension_router_js",
        )
        mark_failed(job_id, "GOVERNANCE_RUN_FAILED", (str(e).strip() or type(e).__name__))
    finally:
        clear_request_api_key()


async def _job_run_correct_js(
    job_id: str,
    payload: ComprehensionJSRequest,
    decision: dict,
    root_path: str,
    module: str,
    language: str,
    framework: Optional[str],
    run_backend: bool,
    run_frontend: bool,
    backend_root_path: Optional[str],
    api_base_url: str,
    preview_url: str,
    intent: str,
    project_state: str,
    target_endpoint: Optional[str],
    workflow_usuario: str,
) -> None:
    from core.llm.llm_context import clear_request_api_key, set_request_api_key

    loop = asyncio.get_event_loop()
    mark_running(job_id)
    t0 = time.perf_counter()
    try:
        add_log(
            "info",
            f"[_job_run_correct_js] início | job_id={job_id} | workflow_usuario={workflow_usuario[:48]!r} | "
            f"run_backend={run_backend} run_frontend={run_frontend}",
            "comprehension_router_js",
        )
        if getattr(payload, "openai_api_key", None) and str(payload.openai_api_key).strip():
            set_request_api_key(str(payload.openai_api_key).strip())
        ctx = copy_context()
        job_budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
        backend_result = None
        if run_backend:
            rp_backend = str((backend_root_path or root_path) or "").strip()
            backend_result = await job_budget.run_in_executor(
                loop,
                lambda: ctx.run(
                    lambda: run_correct_workflow(
                        log_type="info",
                        prompt=payload.prompt,
                        usuario=workflow_usuario,
                        root_path=rp_backend,
                    )
                ),
            )
            log_workflow("workflow.log", f"[comprehension-js] workflow/correct/run (job, PY) para {workflow_usuario}")

        if run_frontend:
            rp = str(root_path).strip()
            result = await job_budget.run_in_executor(
                loop,
                lambda: ctx.run(
                    lambda: run_correct_workflow_js(
                        log_type="info",
                        prompt=payload.prompt,
                        usuario=workflow_usuario,
                        root_path=rp,
                        language=language,
                        framework=framework,
                    )
                ),
            )
            log_workflow("workflow.log", f"[comprehension-js] workflow/correct/run (job) para {workflow_usuario} ({language}/{framework})")
            if backend_result:
                try:
                    result.setdefault("workflow_log", []).append("🧩 Backend (Python) corrigido junto do frontend")
                    result["_backend_result"] = {
                        "status": backend_result.get("status"),
                        "id_requisicao": backend_result.get("id_requisicao"),
                        "root_path": backend_result.get("root_path"),
                    }
                except Exception:
                    pass
        else:
            result = backend_result or {"status": "sucesso", "workflow_log": ["Backend corrigido; frontend skip (backend_only)"]}

        message = build_humanized_message(
            intent=intent,
            project_state=project_state,
            should_execute=True,
            target_endpoint=target_endpoint,
            workflow_result=result,
        )
        extra = _js_extra_response_fields(
            workflow_result=result,
            executed_target=TARGET_CORRECT,
            root_path=root_path,
            prompt=(payload.prompt or "").strip(),
            usuario=workflow_usuario,
            target_endpoint=target_endpoint,
            intent=intent,
            project_state=project_state,
            should_execute=True,
            language=language,
            framework=framework,
            api_base_url=api_base_url,
            preview_url=preview_url,
        )
        elapsed = time.perf_counter() - t0
        resp = ComprehensionJSResponse(
            intent=intent,
            project_state=project_state,
            should_execute=True,
            target_endpoint=target_endpoint,
            explanation=decision["explanation"],
            next_action=decision["next_action"],
            message=message,
            file_tree=extra["file_tree"],
            system_behavior=extra["system_behavior"],
            frontend_suggestion=extra["frontend_suggestion"],
            curl_commands=extra["curl_commands"],
            preview_frontend_url=extra["preview_frontend_url"],
            preview_auto_open=extra.get("preview_auto_open", False),
            intent_confidence=decision.get("intent_confidence"),
            intent_warning=decision.get("intent_warning"),
            processing_time_ms=int(elapsed * 1000),
            module=module,
            language=language,
            framework=framework,
        )
        mark_completed(job_id, resp.model_dump(mode="json"))
        add_log(
            "info",
            f"[_job_run_correct_js] OK | job_id={job_id} | ms={int((time.perf_counter()-t0)*1000)}",
            "comprehension_router_js",
        )
    except HTTPException as he:
        detail = he.detail
        if isinstance(detail, dict):
            mark_failed(job_id, str(detail.get("code", "HTTP_ERROR")), str(detail.get("message", he.detail)))
        else:
            mark_failed(job_id, "HTTP_ERROR", str(detail))
    except asyncio.TimeoutError:
        mark_failed(job_id, "CSA_TIME_BUDGET_EXCEEDED", csa_timeout_user_message())
    except Exception as e:
        add_log(
            "error",
            f"[comprehension-js] CORRECT_JOB_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
            "comprehension_router_js",
        )
        mark_failed(job_id, "CORRECT_RUN_FAILED", (str(e).strip() or type(e).__name__))
    finally:
        clear_request_api_key()


#━━━━━━━━━❮Jobs assíncronos (mesmo store que /comprehension/jobs)❯━━━━━━━━━


@router.get("/comprehension-js/jobs/{job_id}")
async def get_comprehension_js_job(job_id: str, user: dict = Depends(require_valid_access)):
    job = assert_job_owner(job_id, _owner_sub(user))
    if not job:
        add_log(
            "info",
            f"[comprehension-js/jobs] GET 404 | job_id={job_id} | owner={_owner_sub(user)[:40]!r}",
            "comprehension_router_js",
        )
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job inexistente ou sem permissão."},
        )
    add_log(
        "info",
        f"[comprehension-js/jobs] GET 200 | job_id={job_id} | status={job['status']} | stack={job.get('stack')}",
        "comprehension_router_js",
    )
    return {
        "job_id": job_id,
        "status": job["status"],
        "response": job.get("response"),
        "error": job.get("error"),
    }


#━━━━━━━━━❮Entrada principal do workflow JavaScript❯━━━━━━━━━


@router.post("/comprehension-js/run", response_model=None)
async def run_comprehension_js(
    payload: ComprehensionJSRequest,
    user: dict = Depends(require_valid_access),
    async_mode: bool = Query(
        True,
        description=(
            "Se true, governance/correct longos retornam 202 + job_id; consulte GET /comprehension-js/jobs/{job_id}. "
            "Orçamento máximo: PULSO_CSA_WORKFLOW_MAX_SEC (default 300 s)."
        ),
    ),
) -> Union[ComprehensionJSResponse, JSONResponse]:
    """
    Primeira etapa do workflow JavaScript: classifica a intenção, decide o modo do projeto
    e dispara (ou não) governance/run ou workflow/correct/run para JavaScript/TypeScript/React.
    Com async_mode=true (padrão), fluxos longos retornam 202 e evitam timeout de proxy.
    Orçamento máximo por pedido/job: PULSO_CSA_WORKFLOW_MAX_SEC (default 300 s).
    Requer autenticação (Bearer token).
    """
    t0 = time.perf_counter()
    usuario = user.get("email") or user.get("_id") or "anonymous"
    want_async = _want_async_mode(async_mode)
    add_log(
        "info",
        f"[comprehension-js/run] POST início | usuario={usuario[:48]!r} | async_mode_query={async_mode} | "
        f"effective_async={want_async} | FORCE_SYNC={os.getenv('COMPREHENSION_FORCE_SYNC_WORKFLOW', '')!r}",
        "comprehension_router_js",
    )

    prompt = (payload.prompt or "").strip()
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail={"message": "O campo 'prompt' não pode estar vazio.", "code": "PROMPT_EMPTY"},
        )
    if len(prompt) > PROMPT_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail={"message": "Prompt muito longo. Resuma.", "code": "PROMPT_TOO_LONG"},
        )

    raw_root = (getattr(payload, "root_path", None) or "").strip()
    root_path = sanitize_root_path(raw_root or None)
    if root_path is None and raw_root:
        if path_is_production():
            root_path = workspace_path_for_user(usuario)
            add_log(
                "info",
                f"[comprehension-js/run] root_path cliente → workspace prod | raw_trecho={raw_root[:80]!r}",
                "comprehension_router_js",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={"message": "root_path inválido ou fora do permitido.", "code": "ROOT_PATH_INVALID"},
            )

    force_execute = getattr(payload, "force_execute", None) or False
    force_module = getattr(payload, "force_module", None) or None
    history = getattr(payload, "history", None) or None
    
    # Campos específicos JavaScript.
    # Ajuste PulsoCSA: por padrão o sistema só constrói FRONTEND (React+TypeScript) em JavaScript.
    # - Backend Python só é executado se a flag use_python=True vier explicitamente no payload.
    use_python = getattr(payload, "use_python", None) or False
    use_javascript = getattr(payload, "use_javascript", None) or False
    use_typescript = getattr(payload, "use_typescript", None) or False
    use_react = getattr(payload, "use_react", None) or False
    use_vue = getattr(payload, "use_vue", None) or False
    use_angular = getattr(payload, "use_angular", None) or False

    def _looks_like_frontend(prompt_text: str) -> bool:
        p = (prompt_text or "").lower()
        return any(
            kw in p
            for kw in (
                "frontend",
                "tela",
                "ui",
                "interface",
                "react",
                "vue",
                "angular",
                "vite",
                "tsx",
                "jsx",
                "css",
                "componente",
                "pagina",
                "página",
            )
        )

    flags_explicit = any([use_python, use_javascript, use_typescript, use_react, use_vue, use_angular])
    if not flags_explicit:
        # Default: apenas frontend React+TypeScript (sem backend Python)
        use_javascript = True
        use_react = True
        use_typescript = True
        use_python = False

    # BYOK: chave no body tem precedência sobre header (nunca armazenada)
    if getattr(payload, "openai_api_key", None) and str(payload.openai_api_key).strip():
        from core.llm.llm_context import set_request_api_key
        set_request_api_key(str(payload.openai_api_key).strip())

    loop = asyncio.get_event_loop()
    budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
    add_log(
        "info",
        f"[comprehension-js/run] antes route_to_module_js | prompt_len={len(prompt)} | root={(root_path or '')[:180]!r}",
        "comprehension_router_js",
    )
    decision = await budget.run_in_executor(
        loop,
        lambda: route_to_module_js(
            prompt=prompt,
            root_path=root_path,
            usuario=usuario,
            use_python=use_python,
            use_javascript=use_javascript,
            use_typescript=use_typescript,
            use_react=use_react,
            use_vue=use_vue,
            use_angular=use_angular,
            force_execute=force_execute,
            force_module=force_module,
            history=history,
        ),
    )
    add_log("info", f"[comprehension-js/run] route_to_module_js concluído em {time.perf_counter()-t0:.1f}s | module={decision.get('module')} intent={decision.get('intent')}", "comprehension_router_js")

    module = decision.get("module", "codigo")
    intent = decision["intent"]
    project_state = decision.get("mode", "ROOT_VAZIA")
    should_execute = decision["should_execute"]
    target_endpoint = decision.get("target_endpoint")
    language = decision.get("language", "javascript")
    framework = decision.get("framework", None)

    api_base_url = os.getenv("API_BASE_URL") or os.getenv("VITE_API_URL") or "http://localhost:8000"
    preview_url = os.getenv("PREVIEW_FRONTEND_URL") or "http://localhost:3000"

    def _extra_response_fields(
        workflow_result=None,
        executed_target=None,
    ):
        rp = (root_path or "").strip()
        if workflow_result and rp and executed_target:
            new_paths = extract_new_paths_from_workflow_result(
                workflow_result, rp, executed_target
            )
            file_tree = build_project_file_tree(rp, new_paths)
        elif rp:
            file_tree = build_project_file_tree(rp, None)
        elif workflow_result and executed_target:
            file_tree = build_file_tree_from_manifest(workflow_result)
        else:
            file_tree = None
        return {
            "file_tree": file_tree,
            "system_behavior": get_system_behavior_spec(),
            "frontend_suggestion": get_frontend_suggestion(
                intent=intent,
                project_state=project_state,
                should_execute=should_execute,
                has_file_tree=bool(file_tree),
                target_endpoint=target_endpoint,
            ),
            "curl_commands": build_curl_commands(
                base_url=api_base_url,
                prompt=prompt,
                usuario=usuario,
                root_path=root_path,
                target_endpoint=target_endpoint,
                executed=bool(workflow_result and executed_target),
                workflow_result=workflow_result,
            ),
            "preview_frontend_url": (preview_url if (workflow_result and executed_target and language != "python") else None),
            "preview_auto_open": False,
        }

    # —— Módulo Infraestrutura ou ID: retorna decisão (cliente chama target_endpoint) ——
    if module == "infraestrutura" or module == "inteligencia-dados":
        target = decision.get("target_endpoint", "")
        if module == "infraestrutura":
            message = f"Módulo Infraestrutura detectado. Intenção: {intent}. Para executar: chame POST {target} com root_path, tenant_id, id_requisicao."
        else:
            message = f"Módulo Inteligência de Dados detectado. Intenção: {intent}. Para executar: chame POST /inteligencia-dados/chat com mensagem, usuario, id_requisicao."
        extra = _extra_response_fields()
        elapsed = time.perf_counter() - t0
        add_log("info", f"[comprehension-js/run] resposta (infra/id) em {elapsed:.1f}s", "comprehension_router_js")
        return ComprehensionJSResponse(
            intent=intent,
            project_state=project_state,
            should_execute=decision.get("should_execute", False),
            target_endpoint=decision.get("target_endpoint"),
            explanation=decision["explanation"],
            next_action=decision["next_action"],
            message=message,
            file_tree=extra["file_tree"],
            system_behavior=get_system_behavior_spec(),
            frontend_suggestion=extra["frontend_suggestion"],
            curl_commands=extra["curl_commands"],
            preview_frontend_url=extra["preview_frontend_url"],
            intent_confidence=decision.get("intent_confidence"),
            intent_warning=decision.get("intent_warning"),
            processing_time_ms=int(elapsed * 1000),
            module=module,
            language=language,
            framework=framework,
        )

    # —— Módulo Código: ANALISAR ——
    if intent == INTENT_ANALISAR:
        analysis_text, analysis_ok = await budget.run_in_executor(
            loop, lambda: generate_analysis_text(prompt, root_path=root_path, usuario=usuario)
        )
        if not analysis_ok:
            message = ANALYSIS_UNAVAILABLE_MESSAGE
            error_code = "ANALYSIS_UNAVAILABLE"
        else:
            message = build_humanized_message(
                intent=intent,
                project_state=project_state,
                should_execute=False,
                target_endpoint=None,
                analysis_text=analysis_text,
            )
            error_code = None
        extra = _extra_response_fields()
        elapsed = time.perf_counter() - t0
        add_log("info", f"[comprehension-js/run] resposta (ANALISAR) em {elapsed:.1f}s", "comprehension_router_js")
        return ComprehensionJSResponse(
            intent=intent,
            project_state=project_state,
            should_execute=False,
            target_endpoint=None,
            explanation=decision["explanation"],
            next_action=decision["next_action"],
            message=message,
            file_tree=extra["file_tree"],
            system_behavior=extra["system_behavior"],
            frontend_suggestion=extra["frontend_suggestion"],
            curl_commands=extra["curl_commands"],
            preview_frontend_url=extra["preview_frontend_url"],
            intent_confidence=decision.get("intent_confidence"),
            intent_warning=decision.get("intent_warning"),
            processing_time_ms=int(elapsed * 1000),
            error_code=error_code,
            module=module,
            language=language,
            framework=framework,
        )

    # —— Módulo Código: EXECUTAR sem sinal: pedir confirmação (com resumo do que foi compreendido) ——
    if intent == INTENT_EXECUTAR and not should_execute:
        message = build_humanized_message(
            intent=intent,
            project_state=project_state,
            should_execute=False,
            target_endpoint=target_endpoint,
            prompt=payload.prompt,
        )
        extra = _extra_response_fields()
        add_log("info", f"[comprehension-js/run] resposta (EXECUTAR confirmação) em {time.perf_counter()-t0:.1f}s", "comprehension_router_js")
        return ComprehensionJSResponse(
            intent=intent,
            project_state=project_state,
            should_execute=False,
            target_endpoint=target_endpoint,
            explanation=decision["explanation"],
            next_action=decision["next_action"],
            message=message,
            file_tree=extra["file_tree"],
            system_behavior=extra["system_behavior"],
            frontend_suggestion=extra["frontend_suggestion"],
            curl_commands=extra["curl_commands"],
            preview_frontend_url=extra["preview_frontend_url"],
            intent_confidence=decision.get("intent_confidence"),
            intent_warning=decision.get("intent_warning"),
            processing_time_ms=int((time.perf_counter() - t0) * 1000),
            module=module,
            language=language,
            framework=framework,
        )

    # —— EXECUTAR com sinal: validar root_path quando necessário ——
    if intent == INTENT_EXECUTAR and should_execute and project_state == PROJECT_STATE_COM_CONTEUDO:
        if not root_path or not str(root_path).strip():
            raise HTTPException(
                status_code=400,
                detail={"message": "Para executar o fluxo de correção é necessário informar 'root_path' válido.", "code": "ROOT_PATH_REQUIRED"},
            )

    prompt_lower = (prompt or "").lower()
    backend_only = "apenas backend" in prompt_lower or "somente backend" in prompt_lower
    frontend_only = "apenas frontend" in prompt_lower or "somente frontend" in prompt_lower

    run_backend = bool(use_python) and not frontend_only
    run_frontend = bool(any([use_javascript, use_typescript, use_react, use_vue, use_angular])) and not backend_only

    # Root path do backend: sempre a pasta /api (não usar test/teste js)
    backend_root_path = None
    if run_backend:
        try:
            # .../PulsoAPI/api/app/PulsoCSA/JavaScript/routers/... → voltar até .../PulsoAPI/api
            backend_root_path = str(Path(__file__).resolve().parents[5])
        except Exception:
            backend_root_path = None

    # —— Disparar governance/run (criação) ——
    if intent == INTENT_EXECUTAR and should_execute and project_state == PROJECT_STATE_VAZIA:
        if _want_async_mode(async_mode):
            jid = create_job(_owner_sub(user), "javascript")
            add_log(
                "info",
                f"[comprehension-js/run] 202 ASYNC governance | job_id={jid} | run_backend={run_backend} run_frontend={run_frontend}",
                "comprehension_router_js",
            )
            asyncio.create_task(
                _job_run_governance_js(
                    jid,
                    payload,
                    decision,
                    root_path,
                    module,
                    language,
                    framework,
                    run_backend,
                    run_frontend,
                    backend_root_path,
                    api_base_url,
                    preview_url,
                    intent,
                    project_state,
                    target_endpoint,
                    usuario,
                )
            )
            _rp_js = (root_path or "").strip()
            _raw_js = raw_root[:500] if raw_root else ""
            _hint_js = (
                "Ambiente cloud: a geração ocorre no disco do servidor (não na pasta local do PC)."
                if path_is_production()
                else None
            )
            return JSONResponse(
                status_code=202,
                content={
                    "job_id": jid,
                    "status": "pending",
                    "message": (
                        "Workflow JS em execução em segundo plano. "
                        "Faça polling em GET /comprehension-js/jobs/{job_id} até status completed ou failed."
                    ),
                    "poll_path": f"/comprehension-js/jobs/{jid}",
                    "resolved_root_path": _rp_js,
                    "client_root_path_sent": _raw_js or None,
                    "execution_host": "server",
                    "cloud_workspace_note_pt": _hint_js,
                },
            )
        try:
            backend_result = None
            if run_backend:
                rp_backend = backend_root_path or root_path
                backend_result = await budget.run_in_executor(
                    loop,
                    lambda: run_workflow_pipeline(
                        prompt=payload.prompt,
                        usuario=usuario,
                        root_path=rp_backend,
                    ),
                )
                log_workflow("workflow.log", f"[comprehension-js] governance/run executado (PY) para {usuario}")

            if run_frontend:
                # Criação (ROOT_VAZIA): root_path opcional — workflow usa fallback test/teste js se omitido.
                # Correção (ROOT_COM_CONTEUDO): root_path obrigatório.
                if project_state == PROJECT_STATE_COM_CONTEUDO and (not root_path or not str(root_path).strip()):
                    raise HTTPException(
                        status_code=400,
                        detail={"message": "Para executar o fluxo de correção é necessário informar 'root_path' válido.", "code": "ROOT_PATH_REQUIRED_FRONTEND"},
                    )
                result = await budget.run_in_executor(
                    loop, lambda: run_workflow_pipeline_js(
                        prompt=payload.prompt,
                        usuario=usuario,
                        root_path=root_path,
                        language=language,
                        framework=framework,
                    )
                )
                log_workflow("workflow.log", f"[comprehension-js] governance/run executado para {usuario} ({language}/{framework})")
                # anexa um resumo do backend no workflow_result do frontend (sem quebrar contrato existente)
                if backend_result:
                    try:
                        result.setdefault("workflow_log", []).append("🧩 Backend (Python) executado em paralelo ao frontend")
                        result["_backend_result"] = {
                            "status": backend_result.get("status"),
                            "id_requisicao": backend_result.get("id_requisicao"),
                            "root_path": backend_result.get("root_path"),
                        }
                    except Exception:
                        pass
            else:
                # Sem frontend: devolve resultado do backend
                result = backend_result or {"status": "sucesso", "workflow_log": ["Backend executado; frontend skip (backend_only)"]}
            message = build_humanized_message(
                intent=intent,
                project_state=project_state,
                should_execute=True,
                target_endpoint=target_endpoint,
                workflow_result=result,
            )
            extra = _extra_response_fields(workflow_result=result, executed_target=TARGET_GOVERNANCE)
            elapsed = time.perf_counter() - t0
            add_log("info", f"[comprehension-js/run] resposta (EXECUTAR governance) em {elapsed:.1f}s", "comprehension_router_js")
            return ComprehensionJSResponse(
                intent=intent,
                project_state=project_state,
                should_execute=True,
                target_endpoint=target_endpoint,
                explanation=decision["explanation"],
                next_action=decision["next_action"],
                message=message,
                file_tree=extra["file_tree"],
                system_behavior=extra["system_behavior"],
                frontend_suggestion=extra["frontend_suggestion"],
                curl_commands=extra["curl_commands"],
                preview_frontend_url=extra["preview_frontend_url"],
                intent_confidence=decision.get("intent_confidence"),
                intent_warning=decision.get("intent_warning"),
                processing_time_ms=int(elapsed * 1000),
                module=module,
                language=language,
                framework=framework,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=csa_timeout_http_detail())
        except Exception as e:
            add_log(
                "error",
                f"[comprehension-js] GOVERNANCE_RUN_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
                "comprehension_router_js",
            )
            raise HTTPException(
                status_code=500,
                detail={"code": "GOVERNANCE_RUN_FAILED", "message": "Erro ao executar fluxo de criação (governance)."},
            )

    # —— Disparar workflow/correct/run (correção) ——
    if intent == INTENT_EXECUTAR and should_execute and project_state == PROJECT_STATE_COM_CONTEUDO:
        if _want_async_mode(async_mode):
            jid = create_job(_owner_sub(user), "javascript")
            add_log(
                "info",
                f"[comprehension-js/run] 202 ASYNC correct | job_id={jid} | run_backend={run_backend} run_frontend={run_frontend}",
                "comprehension_router_js",
            )
            asyncio.create_task(
                _job_run_correct_js(
                    jid,
                    payload,
                    decision,
                    str(root_path).strip(),
                    module,
                    language,
                    framework,
                    run_backend,
                    run_frontend,
                    backend_root_path,
                    api_base_url,
                    preview_url,
                    intent,
                    project_state,
                    target_endpoint,
                    usuario,
                )
            )
            _rp_jc = str(root_path or "").strip()
            _raw_jc = raw_root[:500] if raw_root else ""
            _hint_jc = (
                "Ambiente cloud: a correção ocorre no disco do servidor (não na pasta local do PC)."
                if path_is_production()
                else None
            )
            return JSONResponse(
                status_code=202,
                content={
                    "job_id": jid,
                    "status": "pending",
                    "message": (
                        "Correção JS em execução em segundo plano. "
                        "Faça polling em GET /comprehension-js/jobs/{job_id} até status completed ou failed."
                    ),
                    "poll_path": f"/comprehension-js/jobs/{jid}",
                    "resolved_root_path": _rp_jc,
                    "client_root_path_sent": _raw_jc or None,
                    "execution_host": "server",
                    "cloud_workspace_note_pt": _hint_jc,
                },
            )
        try:
            backend_result = None
            if run_backend:
                rp_backend = str((backend_root_path or root_path) or "").strip()
                backend_result = await budget.run_in_executor(
                    loop,
                    lambda: run_correct_workflow(
                        log_type="info",
                        prompt=payload.prompt,
                        usuario=usuario,
                        root_path=rp_backend,
                    ),
                )
                log_workflow("workflow.log", f"[comprehension-js] workflow/correct/run executado (PY) para {usuario}")

            if run_frontend:
                rp = str(root_path).strip()
                result = await budget.run_in_executor(
                    loop,
                    lambda: run_correct_workflow_js(
                        log_type="info",
                        prompt=payload.prompt,
                        usuario=usuario,
                        root_path=rp,
                        language=language,
                        framework=framework,
                    ),
                )
                log_workflow("workflow.log", f"[comprehension-js] workflow/correct/run executado para {usuario} ({language}/{framework})")
                if backend_result:
                    try:
                        result.setdefault("workflow_log", []).append("🧩 Backend (Python) corrigido junto do frontend")
                        result["_backend_result"] = {
                            "status": backend_result.get("status"),
                            "id_requisicao": backend_result.get("id_requisicao"),
                            "root_path": backend_result.get("root_path"),
                        }
                    except Exception:
                        pass
            else:
                result = backend_result or {"status": "sucesso", "workflow_log": ["Backend corrigido; frontend skip (backend_only)"]}
            message = build_humanized_message(
                intent=intent,
                project_state=project_state,
                should_execute=True,
                target_endpoint=target_endpoint,
                workflow_result=result,
            )
            extra = _extra_response_fields(workflow_result=result, executed_target=TARGET_CORRECT)
            elapsed = time.perf_counter() - t0
            add_log("info", f"[comprehension-js/run] resposta (EXECUTAR correct) em {elapsed:.1f}s", "comprehension_router_js")
            return ComprehensionJSResponse(
                intent=intent,
                project_state=project_state,
                should_execute=True,
                target_endpoint=target_endpoint,
                explanation=decision["explanation"],
                next_action=decision["next_action"],
                message=message,
                file_tree=extra["file_tree"],
                system_behavior=extra["system_behavior"],
                frontend_suggestion=extra["frontend_suggestion"],
                curl_commands=extra["curl_commands"],
                preview_frontend_url=extra["preview_frontend_url"],
                intent_confidence=decision.get("intent_confidence"),
                intent_warning=decision.get("intent_warning"),
                processing_time_ms=int(elapsed * 1000),
                module=module,
                language=language,
                framework=framework,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=csa_timeout_http_detail())
        except Exception as e:
            add_log(
                "error",
                f"[comprehension-js] CORRECT_RUN_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
                "comprehension_router_js",
            )
            raise HTTPException(
                status_code=500,
                detail={"code": "CORRECT_RUN_FAILED", "message": "Erro ao executar fluxo de correção (workflow/correct)."},
            )

    # Fallback (não deveria chegar aqui)
    message = build_humanized_message(
        intent=intent,
        project_state=project_state,
        should_execute=should_execute,
        target_endpoint=target_endpoint,
    )
    extra = _extra_response_fields()
    add_log("info", f"[comprehension-js/run] resposta (fallback) em {time.perf_counter()-t0:.1f}s", "comprehension_router_js")
    return ComprehensionJSResponse(
        intent=intent,
        project_state=project_state,
        should_execute=should_execute,
        target_endpoint=target_endpoint,
        explanation=decision["explanation"],
        next_action=decision["next_action"],
        message=message,
        file_tree=extra["file_tree"],
        system_behavior=extra["system_behavior"],
        frontend_suggestion=extra["frontend_suggestion"],
        curl_commands=extra["curl_commands"],
        preview_frontend_url=extra["preview_frontend_url"],
        intent_confidence=decision.get("intent_confidence"),
        intent_warning=decision.get("intent_warning"),
        processing_time_ms=int((time.perf_counter() - t0) * 1000),
        module=module,
        language=language,
        framework=framework,
    )
