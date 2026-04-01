#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router – Sistema de Compreensão (Intent Router)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import asyncio
import os
import time
from contextvars import copy_context
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from models.comprehension_models import (
    ComprehensionRequest,
    ComprehensionResponse,
    PROMPT_MAX_LENGTH,
)
from services.comprehension_services import (
    route_decision,
    build_humanized_message,
    generate_analysis_text,
    build_project_file_tree,
    extract_new_paths_from_workflow_result,
    get_system_behavior_spec,
    get_route_contract,
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
from workflow.creator_workflow.workflow_core import run_workflow_pipeline
from workflow.correct_workflow.workflow_core_cor import run_correct_workflow
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

router = APIRouter(tags=["Sistema de Compreensão – Entrada do Workflow"])


def _want_async_mode(async_mode_query: bool) -> bool:
    """FORCE_SYNC no .env desliga async (deploy legado). Caso contrário usa o query param."""
    if os.getenv("COMPREHENSION_FORCE_SYNC_WORKFLOW", "").strip().lower() in ("1", "true", "yes"):
        return False
    return async_mode_query


def _owner_sub(user: dict) -> str:
    return user.get("email") or user.get("_id") or "anonymous"


def _extra_response_fields_py(
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
    api_base_url: str,
    preview_url: str,
) -> Dict[str, Any]:
    rp = (root_path or "").strip()
    if workflow_result and rp and executed_target:
        new_paths = extract_new_paths_from_workflow_result(workflow_result, rp, executed_target)
        file_tree = build_project_file_tree(rp, new_paths)
    elif rp:
        file_tree = build_project_file_tree(rp, None)
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
        "preview_frontend_url": preview_url if (workflow_result and executed_target) else None,
    }


async def _job_run_governance_py(
    job_id: str,
    payload: ComprehensionRequest,
    decision: dict,
    root_path: Optional[str],
    module: str,
    api_base_url: str,
    preview_url: str,
    workflow_usuario: str,
) -> None:
    from core.llm.llm_context import clear_request_api_key, set_request_api_key

    loop = asyncio.get_event_loop()
    mark_running(job_id)
    t0 = time.perf_counter()
    try:
        add_log(
            "info",
            f"[_job_run_governance_py] executor | job_id={job_id} | workflow_usuario={workflow_usuario[:48]!r} | "
            f"payload.usuario={str(payload.usuario)[:48]!r} | root_path={(root_path or '')[:160]!r}",
            "comprehension_router",
        )
        if getattr(payload, "openai_api_key", None) and str(payload.openai_api_key).strip():
            set_request_api_key(str(payload.openai_api_key).strip())
        ctx = copy_context()

        def _run():
            return run_workflow_pipeline(payload.prompt, workflow_usuario, root_path)

        job_budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
        result = await job_budget.run_in_executor(loop, lambda: ctx.run(_run))
        log_workflow("workflow.log", f"[comprehension] governance/run (job assíncrono) para {workflow_usuario}")
        intent = decision["intent"]
        project_state = decision.get("mode", "ROOT_VAZIA")
        target_endpoint = decision.get("target_endpoint")
        message = build_humanized_message(
            intent=intent,
            project_state=project_state,
            should_execute=True,
            target_endpoint=target_endpoint,
            workflow_result=result,
        )
        extra = _extra_response_fields_py(
            workflow_result=result,
            executed_target=TARGET_GOVERNANCE,
            root_path=root_path,
            prompt=(payload.prompt or "").strip(),
            usuario=workflow_usuario,
            target_endpoint=target_endpoint,
            intent=intent,
            project_state=project_state,
            should_execute=True,
            api_base_url=api_base_url,
            preview_url=preview_url,
        )
        resp = ComprehensionResponse(
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
            processing_time_ms=int((time.perf_counter() - t0) * 1000),
            module=module,
        )
        mark_completed(job_id, resp.model_dump(mode="json"))
        add_log(
            "info",
            f"[_job_run_governance_py] job OK | job_id={job_id} | ms={int((time.perf_counter()-t0)*1000)}",
            "comprehension_router",
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
            f"[comprehension] GOVERNANCE_JOB_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
            "comprehension_router",
        )
        mark_failed(job_id, "GOVERNANCE_RUN_FAILED", (str(e).strip() or type(e).__name__))
    finally:
        clear_request_api_key()


async def _job_run_correct_py(
    job_id: str,
    payload: ComprehensionRequest,
    decision: dict,
    root_path: str,
    module: str,
    api_base_url: str,
    preview_url: str,
    workflow_usuario: str,
) -> None:
    from core.llm.llm_context import clear_request_api_key, set_request_api_key

    loop = asyncio.get_event_loop()
    mark_running(job_id)
    t0 = time.perf_counter()
    rp = str(root_path).strip()
    try:
        add_log(
            "info",
            f"[_job_run_correct_py] executor | job_id={job_id} | workflow_usuario={workflow_usuario[:48]!r} | root_path={rp[:160]!r}",
            "comprehension_router",
        )
        if getattr(payload, "openai_api_key", None) and str(payload.openai_api_key).strip():
            set_request_api_key(str(payload.openai_api_key).strip())
        ctx = copy_context()

        def _run():
            return run_correct_workflow(
                log_type="info",
                prompt=payload.prompt,
                usuario=workflow_usuario,
                root_path=rp,
            )

        job_budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
        result = await job_budget.run_in_executor(loop, lambda: ctx.run(_run))
        log_workflow("workflow.log", f"[comprehension] workflow/correct/run (job assíncrono) para {workflow_usuario}")
        intent = decision["intent"]
        project_state = decision.get("mode", "ROOT_COM_CONTEUDO")
        target_endpoint = decision.get("target_endpoint")
        message = build_humanized_message(
            intent=intent,
            project_state=project_state,
            should_execute=True,
            target_endpoint=target_endpoint,
            workflow_result=result,
        )
        extra = _extra_response_fields_py(
            workflow_result=result,
            executed_target=TARGET_CORRECT,
            root_path=root_path,
            prompt=(payload.prompt or "").strip(),
            usuario=workflow_usuario,
            target_endpoint=target_endpoint,
            intent=intent,
            project_state=project_state,
            should_execute=True,
            api_base_url=api_base_url,
            preview_url=preview_url,
        )
        resp = ComprehensionResponse(
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
            processing_time_ms=int((time.perf_counter() - t0) * 1000),
            module=module,
        )
        mark_completed(job_id, resp.model_dump(mode="json"))
        add_log(
            "info",
            f"[_job_run_correct_py] job OK | job_id={job_id} | ms={int((time.perf_counter()-t0)*1000)}",
            "comprehension_router",
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
            f"[comprehension] CORRECT_JOB_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
            "comprehension_router",
        )
        mark_failed(job_id, "CORRECT_RUN_FAILED", (str(e).strip() or type(e).__name__))
    finally:
        clear_request_api_key()


#━━━━━━━━━❮Contrato da rota (ida e volta) para o frontend❯━━━━━━━━━


@router.get("/comprehension/contract")
def get_comprehension_contract():
    """
    Retorna o JSON de parâmetros da rota ida e volta (request + response) para o frontend.
    """
    return get_route_contract()


@router.get("/comprehension/jobs/{job_id}")
async def get_comprehension_job(job_id: str, user: dict = Depends(require_valid_access)):
    """
    Consulta o estado de um workflow disparado com POST /comprehension/run?async_mode=true (HTTP 202).
    status: pending | running | completed | failed. Em completed, 'response' contém o mesmo JSON de um run síncrono.
    """
    job = assert_job_owner(job_id, _owner_sub(user))
    if not job:
        add_log(
            "info",
            f"[comprehension/jobs] GET 404 | job_id={job_id} | owner={_owner_sub(user)[:40]!r}",
            "comprehension_router",
        )
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job inexistente ou sem permissão."},
        )
    add_log(
        "info",
        f"[comprehension/jobs] GET 200 | job_id={job_id} | status={job['status']} | stack={job.get('stack')}",
        "comprehension_router",
    )
    return {
        "job_id": job_id,
        "status": job["status"],
        "response": job.get("response"),
        "error": job.get("error"),
    }


#━━━━━━━━━❮Entrada principal do workflow❯━━━━━━━━━


@router.post("/comprehension/run", response_model=None)
async def run_comprehension(
    payload: ComprehensionRequest,
    user: dict = Depends(require_valid_access),
    async_mode: bool = Query(
        True,
        description=(
            "Se true, criação/correção longa retorna 202 + job_id; consulte GET /comprehension/jobs/{job_id}. "
            "false = síncrono. Orçamento máximo de execução: PULSO_CSA_WORKFLOW_MAX_SEC (default 300 s)."
        ),
    ),
) -> Union[ComprehensionResponse, JSONResponse]:
    """
    Primeira etapa do workflow: classifica a intenção, decide o modo do projeto
    e dispara (ou não) governance/run ou workflow/correct/run.
    Com async_mode=true (padrão), fluxos longos respondem 202 e processam em background.
    Orçamento máximo de execução (síncrono ou por job): PULSO_CSA_WORKFLOW_MAX_SEC (default 300 s).
    Requer autenticação (Bearer token).
    """
    t0 = time.perf_counter()
    usuario = user.get("email") or user.get("_id") or "anonymous"
    want_async = _want_async_mode(async_mode)
    add_log(
        "info",
        f"[comprehension/run] POST início | usuario={usuario[:48]!r} | async_mode_query={async_mode} | "
        f"effective_async={want_async} | force_SYNC_env={os.getenv('COMPREHENSION_FORCE_SYNC_WORKFLOW', '')!r}",
        "comprehension_router",
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
        # Produção (ex.: Railway): caminho do cliente costuma ser da máquina local (Windows) e não
        # existe no servidor — usa workspace isolado por utilizador sob pulso_workspace.
        if path_is_production():
            root_path = workspace_path_for_user(usuario)
            add_log(
                "info",
                f"[comprehension/run] root_path cliente inválido no servidor → workspace produção | "
                f"raw_root_trecho={raw_root[:80]!r} | resolved={root_path[:200]!r}",
                "comprehension_router",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={"message": "root_path inválido ou fora do permitido.", "code": "ROOT_PATH_INVALID"},
            )

    force_execute = getattr(payload, "force_execute", None) or False
    force_module = getattr(payload, "force_module", None) or None
    history = getattr(payload, "history", None) or None

    # BYOK: chave no body tem precedência sobre header (nunca armazenada)
    if getattr(payload, "openai_api_key", None) and str(payload.openai_api_key).strip():
        from core.llm.llm_context import set_request_api_key
        set_request_api_key(str(payload.openai_api_key).strip())

    from services.comprehension_services.comprehension_orchestrator import route_to_module
    loop = asyncio.get_event_loop()
    budget = CsaRequestBudget(CSA_WORKFLOW_WALL_CLOCK_SEC)
    add_log(
        "info",
        f"[comprehension/run] antes route_to_module | prompt_len={len(prompt)} | root_path={(root_path or '')[:200]!r} | "
        f"force_execute={force_execute} force_module={force_module!r}",
        "comprehension_router",
    )
    decision = await budget.run_in_executor(
        loop,
        lambda: route_to_module(
            prompt=prompt,
            root_path=root_path,
            usuario=usuario,
            force_execute=force_execute,
            force_module=force_module,
            history=history,
        ),
    )
    add_log(
        "info",
        f"[comprehension/run] após route_to_module em {(time.perf_counter()-t0)*1000:.0f}ms | module={decision.get('module')} | "
        f"intent={decision.get('intent')} | should_execute={decision.get('should_execute')} | "
        f"target={decision.get('target_endpoint')} | mode={decision.get('mode')}",
        "comprehension_router",
    )

    module = decision.get("module", "codigo")
    intent = decision["intent"]
    project_state = decision.get("mode", "ROOT_VAZIA")
    should_execute = decision["should_execute"]
    target_endpoint = decision.get("target_endpoint")

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
            "preview_frontend_url": preview_url if (workflow_result and executed_target) else None,
        }

    # —— Módulo Infraestrutura ou ID: retorna decisão (cliente chama target_endpoint) ——
    if module == "infraestrutura" or module == "inteligencia-dados":
        add_log("info", f"[comprehension/run] ramo infra/id | module={module} | {(time.perf_counter()-t0):.2f}s", "comprehension_router")
        target = decision.get("target_endpoint", "")
        if module == "infraestrutura":
            message = f"Módulo Infraestrutura detectado. Intenção: {intent}. Para executar: chame POST {target} com root_path, tenant_id, id_requisicao."
        else:
            message = f"Módulo Inteligência de Dados detectado. Intenção: {intent}. Para executar: chame POST /inteligencia-dados/chat com mensagem, usuario, id_requisicao."
        extra = _extra_response_fields()
        return ComprehensionResponse(
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
            processing_time_ms=int((time.perf_counter() - t0) * 1000),
            module=module,
        )

    # —— Módulo Código: ANALISAR ——
    if intent == INTENT_ANALISAR:
        add_log("info", f"[comprehension/run] ramo ANALISAR (generate_analysis_text) | {(time.perf_counter()-t0):.2f}s", "comprehension_router")
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
        add_log(
            "info",
            f"[comprehension/run] resposta 200 ANALISAR | analysis_ok={analysis_ok} | total_ms={int((time.perf_counter()-t0)*1000)}",
            "comprehension_router",
        )
        return ComprehensionResponse(
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
            processing_time_ms=int((time.perf_counter() - t0) * 1000),
            error_code=error_code,
            module=module,
        )

    # —— Módulo Código: EXECUTAR sem sinal: pedir confirmação (com resumo do que foi compreendido) ——
    if intent == INTENT_EXECUTAR and not should_execute:
        add_log(
            "info",
            f"[comprehension/run] resposta 200 EXECUTAR pede confirmação | target={target_endpoint} | {(time.perf_counter()-t0):.2f}s",
            "comprehension_router",
        )
        message = build_humanized_message(
            intent=intent,
            project_state=project_state,
            should_execute=False,
            target_endpoint=target_endpoint,
            prompt=payload.prompt,
        )
        extra = _extra_response_fields()
        return ComprehensionResponse(
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
        )

    # —— EXECUTAR com sinal: validar root_path quando necessário ——
    if intent == INTENT_EXECUTAR and should_execute and project_state == PROJECT_STATE_COM_CONTEUDO:
        if not root_path or not str(root_path).strip():
            raise HTTPException(
                status_code=400,
                detail={"message": "Para executar o fluxo de correção é necessário informar 'root_path' válido.", "code": "ROOT_PATH_REQUIRED"},
            )

    # —— Disparar governance/run (criação) ——
    if intent == INTENT_EXECUTAR and should_execute and project_state == PROJECT_STATE_VAZIA:
        if _want_async_mode(async_mode):
            jid = create_job(_owner_sub(user), "python")
            add_log(
                "info",
                f"[comprehension/run] 202 ASYNC governance | job_id={jid} | usuario={usuario[:40]!r} | root_path={(root_path or '')[:160]!r}",
                "comprehension_router",
            )
            asyncio.create_task(
                _job_run_governance_py(
                    jid,
                    payload,
                    decision,
                    root_path,
                    module,
                    api_base_url,
                    preview_url,
                    usuario,
                )
            )
            _rp = (root_path or "").strip()
            _raw = raw_root[:500] if raw_root else ""
            _cloud_hint = (
                "Ambiente cloud: a geração ocorre no disco do servidor (não na pasta local do PC). "
                "Caminhos Windows enviados no body não existem no Railway — usa-se pulso_workspace/<utilizador>."
                if path_is_production()
                else None
            )
            return JSONResponse(
                status_code=202,
                content={
                    "job_id": jid,
                    "status": "pending",
                    "message": (
                        "Workflow de criação em execução em segundo plano. "
                        "Faça polling em GET /comprehension/jobs/{job_id} até status ser completed ou failed."
                    ),
                    "poll_path": f"/comprehension/jobs/{jid}",
                    "resolved_root_path": _rp,
                    "client_root_path_sent": _raw or None,
                    "execution_host": "server",
                    "cloud_workspace_note_pt": _cloud_hint,
                },
            )
        try:
            add_log("info", "[comprehension/run] SYNC governance run_workflow_pipeline iniciando", "comprehension_router")
            result = await budget.run_in_executor(
                loop, lambda: run_workflow_pipeline(payload.prompt, usuario, root_path)
            )
            log_workflow("workflow.log", f"[comprehension] governance/run executado para {usuario}")
            add_log("info", f"[comprehension/run] SYNC governance concluído | status={result.get('status')!r}", "comprehension_router")
            message = build_humanized_message(
                intent=intent,
                project_state=project_state,
                should_execute=True,
                target_endpoint=target_endpoint,
                workflow_result=result,
            )
            extra = _extra_response_fields(workflow_result=result, executed_target=TARGET_GOVERNANCE)
            return ComprehensionResponse(
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
                processing_time_ms=int((time.perf_counter() - t0) * 1000),
                module=module,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=csa_timeout_http_detail())
        except Exception as e:
            add_log(
                "error",
                f"[comprehension] GOVERNANCE_RUN_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
                "comprehension_router",
            )
            raise HTTPException(
                status_code=500,
                detail={"code": "GOVERNANCE_RUN_FAILED", "message": "Erro ao executar fluxo de criação (governance)."},
            )

    # —— Disparar workflow/correct/run (correção) ——
    if intent == INTENT_EXECUTAR and should_execute and project_state == PROJECT_STATE_COM_CONTEUDO:
        if _want_async_mode(async_mode):
            jid = create_job(_owner_sub(user), "python")
            add_log(
                "info",
                f"[comprehension/run] 202 ASYNC correct | job_id={jid} | root_path={str(root_path)[:160]!r}",
                "comprehension_router",
            )
            asyncio.create_task(
                _job_run_correct_py(
                    jid,
                    payload,
                    decision,
                    str(root_path).strip(),
                    module,
                    api_base_url,
                    preview_url,
                    usuario,
                )
            )
            _rp_c = str(root_path or "").strip()
            _raw_c = raw_root[:500] if raw_root else ""
            _cloud_hint_c = (
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
                        "Workflow de correção em execução em segundo plano. "
                        "Faça polling em GET /comprehension/jobs/{job_id} até status ser completed ou failed."
                    ),
                    "poll_path": f"/comprehension/jobs/{jid}",
                    "resolved_root_path": _rp_c,
                    "client_root_path_sent": _raw_c or None,
                    "execution_host": "server",
                    "cloud_workspace_note_pt": _cloud_hint_c,
                },
            )
        try:
            rp = str(root_path).strip()
            add_log("info", f"[comprehension/run] SYNC correct iniciando | root_path={rp[:160]!r}", "comprehension_router")
            result = await budget.run_in_executor(
                loop,
                lambda: run_correct_workflow(
                    log_type="info",
                    prompt=payload.prompt,
                    usuario=usuario,
                    root_path=rp,
                ),
            )
            log_workflow("workflow.log", f"[comprehension] workflow/correct/run executado para {usuario}")
            add_log("info", f"[comprehension/run] SYNC correct concluído | status={result.get('status')!r}", "comprehension_router")
            message = build_humanized_message(
                intent=intent,
                project_state=project_state,
                should_execute=True,
                target_endpoint=target_endpoint,
                workflow_result=result,
            )
            extra = _extra_response_fields(workflow_result=result, executed_target=TARGET_CORRECT)
            return ComprehensionResponse(
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
                processing_time_ms=int((time.perf_counter() - t0) * 1000),
                module=module,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=csa_timeout_http_detail())
        except Exception as e:
            add_log(
                "error",
                f"[comprehension] CORRECT_RUN_FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}",
                "comprehension_router",
            )
            raise HTTPException(
                status_code=500,
                detail={"code": "CORRECT_RUN_FAILED", "message": "Erro ao executar fluxo de correção (workflow/correct)."},
            )

    # Fallback (não deveria chegar aqui)
    add_log(
        "warning",
        f"[comprehension/run] FALLBACK inesperado | intent={intent} should_execute={should_execute} project_state={project_state}",
        "comprehension_router",
    )
    message = build_humanized_message(
        intent=intent,
        project_state=project_state,
        should_execute=should_execute,
        target_endpoint=target_endpoint,
    )
    extra = _extra_response_fields()
    return ComprehensionResponse(
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
    )
