#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Service – Code Plan (LLM Diff/Impact Core) — OPTIMIZED❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client
from models.correct_models.code_plan_models import (
    CodePlanArtifact,
    CodePlanChange,
    CodePlanDocument,
    CodePlanNewFile,
)
from services.struc_anal.structure_scanner_service import scan_full_project
from storage.database.correct_analyse.code_plan_database import save_code_plan
from utils.log_manager import add_log

CODE_PLAN_CACHE_TTL_SEC = int(os.environ.get("CODE_PLAN_CACHE_TTL_SEC", "60"))
CODE_PLAN_CACHE_MAX = 80
_code_plan_cache: Dict[str, tuple] = {}
_code_plan_cache_lock = threading.Lock()


def _code_plan_cache_key(prompt: str, root_path: str, module: str, resumo_prefix: str) -> str:
    return hashlib.sha256(f"{(prompt or '').strip()[:400]}|{root_path}|{module}|{(resumo_prefix or '')[:200]}".encode()).hexdigest()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Module Inference (deterministic)❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _infer_module_from_prompt(prompt_usuario: str) -> str:
    """
    Infer module slug from user prompt.

    Rules:
    - Prefer the first explicit route token like /TTST, "/ttst", '/ttst'
    - Fallback to a safe default "module"
    """
    text = (prompt_usuario or "").strip()
    if not text:
        return "module"

    # 1) explicit /NAME (prefer first)
    m = re.search(r"(?i)(?:^|[\s\"'“”‘’])/(?:v\d+/)?([a-z0-9_\-]+)", text)
    if m:
        slug = m.group(1)

        # normalize slug
        slug = slug.replace("-", "_").strip("_").lower()
        slug = re.sub(r"[^a-z0-9_]", "", slug)
        return slug or "module"

    # 2) try common "rota TTST" / "rota 'TTST'"
    m2 = re.search(r"(?i)\brota\b[^a-z0-9]*([a-z0-9_\-]{2,})", text)
    if m2:
        slug = m2.group(1).replace("-", "_").strip("_").lower()
        slug = re.sub(r"[^a-z0-9_]", "", slug)
        return slug or "module"

    return "module"


def _build_expected_paths(module: str) -> Dict[str, str]:
    """
    Canonical modular layout enforced by the pipeline.
    """
    mod = module or "module"
    return {
        "router": f"api/app/routers/{mod}_router/{mod}_router.py",
        "models": f"api/app/models/{mod}_models/{mod}_models.py",
        "services": f"api/app/services/{mod}_services/{mod}_services.py",
        "tests": f"api/app/tests/{mod}_tests/{mod}_tests.py",
    }


def _ensure_router_in_plan(plan_dict: Dict[str, Any], module: str) -> None:
    """
    Hard guarantee: router file MUST exist in new_files_to_create.
    """
    expected = _build_expected_paths(module)
    new_files: List[Dict[str, Any]] = plan_dict.get("new_files_to_create", []) or []
    existing_paths = {str(it.get("path", "")).replace("\\", "/") for it in new_files}

    if expected["router"] in existing_paths:
        return

    new_files.append(
        {
            "path": expected["router"],
            "reason": f"Expor o endpoint /{module.upper()} via APIRouter em arquivo dedicado.",
            "content_description": (
                "Criar APIRouter com rota GET '/"
                + module.upper()
                + "' retornando um JSON de teste (message + timestamp). "
                "O router deve delegar ao service correspondente."
            ),
            "interface": "router = APIRouter()",
            "test_outline": (
                "Usar TestClient para GET /"
                + module.upper()
                + " e validar status 200 e chaves message/timestamp."
            ),
            "acceptance_criteria": [
                f"GET /{module.upper()} retorna status 200",
                "Resposta JSON contém message e timestamp",
            ],
        }
    )

    plan_dict["new_files_to_create"] = new_files


def _normalize_plan_paths(plan_dict: Dict[str, Any], module: str) -> Dict[str, Any]:
    """
    Normalize any 'module_*' placeholders and enforce canonical paths.
    """
    expected = _build_expected_paths(module)
    new_files: List[Dict[str, Any]] = plan_dict.get("new_files_to_create", []) or []

    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _norm(p: str) -> str:
        p = (p or "").replace("\\", "/").lstrip("/")
        return p

    for item in new_files:
        path = _norm(str(item.get("path", "")))

        # If LLM used "module_*" placeholders, remap to canonical paths
        lower = path.lower()
        if "api/app/models/module_models/" in lower or lower.endswith("/module_models.py"):
            path = expected["models"]
        elif "api/app/services/module_services/" in lower or lower.endswith("/module_services.py"):
            path = expected["services"]
        elif "api/app/tests/module_tests/" in lower or lower.endswith("/module_tests.py"):
            path = expected["tests"]
        elif "api/app/routers/module_router/" in lower or lower.endswith("/module_router.py"):
            path = expected["router"]

        item["path"] = path

        # de-dup by path
        if path and path not in seen:
            normalized.append(item)
            seen.add(path)

    plan_dict["new_files_to_create"] = normalized

    # Ensure router exists no matter what
    _ensure_router_in_plan(plan_dict, module)

    # If LLM suggests implementing route inside main.py, discourage (keep info but do not rely on it)
    changes: List[Dict[str, Any]] = plan_dict.get("changes_in_existing_files", []) or []
    cleaned_changes: List[Dict[str, Any]] = []
    for ch in changes:
        p = _norm(str(ch.get("path", "")))
        desc = (ch.get("new_snippet_description") or "")
        if p.endswith("api/app/main.py") and ("@app.get" in desc or "def " in desc and "/TTST" in desc):
            # rewrite description: main.py should only include_router for the new router
            ch["new_snippet_description"] = (
                "NÃO implementar endpoint em main.py. "
                "Apenas registrar o router via app.include_router(...) apontando para "
                f"{expected['router']}."
            )
        cleaned_changes.append(ch)

    plan_dict["changes_in_existing_files"] = cleaned_changes
    return plan_dict


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Context Builder — HEAVILY OPTIMIZED❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _build_project_context(scanned: Any, prompt_usuario: str, module: str) -> str:
    """
    Builds a compact project context for the LLM:
      - up to 15 files (otimizado)
      - up to 15 lines per file (otimizado)
      - only structural roles (router, service, model, agent, workflow).

    Also provides the deterministic module slug for path discipline.
    """

    roles = {"router", "service", "model", "agent", "workflow"}

    lines: List[str] = []
    lines.append(f"ROOT_PATH: {scanned.root_path}")
    lines.append(f"SUGGESTED_MODULE_SLUG: {module}")
    lines.append(f"SUGGESTED_ROUTE_PATH: /{module.upper()}")
    lines.append("AMOSTRA DE ARQUIVOS (reduzida):\n")

    count = 0

    for file_info in scanned.arquivos:
        if file_info.papel not in roles:
            continue

        count += 1
        if count > 15:
            break

        preview = "\n".join(file_info.conteudo.splitlines()[:15])

        lines.append(f"# FILE: {file_info.path}")
        lines.append(f"# papel: {file_info.papel}")
        lines.append(preview)
        lines.append("\n")

    lines.append("OBJETIVO_USUARIO:")
    lines.append(prompt_usuario)

    return "\n".join(lines)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮System Prompt — OPTIMIZED❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _build_system_prompt(module: str) -> str:
    """
    Builds the LLM system prompt a partir do arquivo prompts/correct/code_plan_system.txt.
    """
    from app.prompts.loader import load_prompt

    expected = _build_expected_paths(module)
    return load_prompt("correct/code_plan_system").format(
        module=module,
        router_path=expected["router"],
        services_path=expected["services"],
        models_path=expected["models"],
        tests_path=expected["tests"],
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Safe LLM Call — OPTIMIZED❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _safe_llm_call(user_prompt: str, system_prompt: str) -> str:
    """
    Performs a robust LLM call with small retry/backoff loop,
    always returning a syntactically valid JSON string as fallback.
    """

    client = get_openai_client()
    retries = 3
    delay_sec = 1

    final_prompt = (
        user_prompt
        + "\nIMPORTANTE: Responda SOMENTE com JSON válido."
        + "\nNÃO escreva comentários ou texto fora do JSON."
    )

    timeout_sec = int(os.getenv("CODE_PLAN_LLM_TIMEOUT_SEC", "120"))
    for _ in range(retries):
        resp = client.generate_text(
            final_prompt,
            system_prompt=system_prompt,
            num_predict=1536,
            use_fast_model=True,
            timeout_override=timeout_sec,
        )
        if "Erro ao gerar texto" not in resp:
            return resp

        import time
        time.sleep(delay_sec)
        delay_sec *= 2

    # Minimal valid fallback
    return (
        '{"summary":"Falha ao gerar plano.",'
        '"changes_in_existing_files":[],'
        '"new_files_to_create":[],'
        '"artifacts":[]}'
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮JSON Parser — SAFE❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _parse_code_plan_json(raw: str) -> Dict[str, Any]:
    """
    Parses the raw JSON string coming from the LLM.

    It is tolerant to missing keys and returns a normalized structure.
    """
    default = {
        "summary": "Falha ao interpretar JSON.",
        "changes_in_existing_files": [],
        "new_files_to_create": [],
        "artifacts": [],
    }
    if not raw or not isinstance(raw, str):
        return default.copy()
    raw = raw.strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
        if m:
            raw = m.group(1)
    try:
        data = json.loads(raw)
    except Exception:
        return default.copy()
    if not isinstance(data, dict):
        return default.copy()
    data.setdefault("summary", "")
    data.setdefault("changes_in_existing_files", [])
    data.setdefault("new_files_to_create", [])
    data.setdefault("artifacts", [])
    if not isinstance(data.get("changes_in_existing_files"), list):
        data["changes_in_existing_files"] = []
    if not isinstance(data.get("new_files_to_create"), list):
        data["new_files_to_create"] = []
    if not isinstance(data.get("artifacts"), list):
        data["artifacts"] = []
    return data


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Core – Code Plan Generator❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def generate_code_plan(
    id_requisicao: str,
    root_path: str,
    prompt_usuario: str,
    analise_sistema: Optional[Dict[str, Any]] = None,
) -> CodePlanDocument:
    """
    Generates a full CodePlanDocument by:
      - scanning the project structure,
      - building a compact context,
      - calling the LLM with a strict JSON schema,
      - normalizing and persisting the result.
    """

    log_type = "info"
    add_log(
        log_type,
        f"[code_plan_service] Starting code-plan for {id_requisicao}",
        "code_plan_service",
    )

    project_root = Path(root_path)

    scanned = scan_full_project(
        log_type=log_type,
        root_path=root_path,
        id_requisicao=id_requisicao,
        prompt=prompt_usuario,
    )

    module = _infer_module_from_prompt(prompt_usuario)

    context = _build_project_context(scanned, prompt_usuario, module)

    resumo_programatico = ""
    if analise_sistema:
        resumo_programatico = analise_sistema.get("resumo_programatico", "")

    cache_key = _code_plan_cache_key(prompt_usuario, root_path, module, resumo_programatico)
    with _code_plan_cache_lock:
        now = time.time()
        if cache_key in _code_plan_cache:
            ts, cached_raw = _code_plan_cache[cache_key]
            if now - ts <= CODE_PLAN_CACHE_TTL_SEC:
                raw_json = cached_raw
            else:
                del _code_plan_cache[cache_key]
                raw_json = None
        else:
            raw_json = None

    if raw_json is None:
        expected = _build_expected_paths(module)
        user_prompt = (
            "RESUMO DO SISTEMA:\n"
            f"{resumo_programatico}\n\n"
            "CONTEXTO:\n"
            f"{context}\n\n"
            "CONTRATO DE PATHS (OBRIGATÓRIO):\n"
            f"- router: {expected['router']}\n"
            f"- services: {expected['services']}\n"
            f"- models: {expected['models']}\n"
            f"- tests: {expected['tests']}\n"
        )
        system_prompt = _build_system_prompt(module)
        raw_json = _safe_llm_call(user_prompt=user_prompt, system_prompt=system_prompt)
        with _code_plan_cache_lock:
            if len(_code_plan_cache) >= CODE_PLAN_CACHE_MAX:
                by_ts = sorted(_code_plan_cache.items(), key=lambda x: x[1][0])
                for k, _ in by_ts[: CODE_PLAN_CACHE_MAX // 2]:
                    del _code_plan_cache[k]
            _code_plan_cache[cache_key] = (time.time(), raw_json)
    else:
        expected = _build_expected_paths(module)

    plan_dict = _parse_code_plan_json(raw_json)
    plan_dict = _normalize_plan_paths(plan_dict, module)

    summary = plan_dict.get("summary")
    if summary is None or (isinstance(summary, str) and not summary.strip()):
        summary = "Plano gerado (resumo não disponível)."
    elif not isinstance(summary, str):
        summary = str(summary)[:500]
    changes = plan_dict.get("changes_in_existing_files") or []
    new_files = plan_dict.get("new_files_to_create") or []
    artifacts = plan_dict.get("artifacts") or []

    doc = CodePlanDocument(
        id_requisicao=id_requisicao,
        root_path=str(project_root),
        prompt_original=prompt_usuario,
        generated_at=datetime.utcnow().isoformat(),
        summary=summary,
        changes_in_existing_files=[CodePlanChange(**item) for item in changes],
        new_files_to_create=[CodePlanNewFile(**item) for item in new_files],
        artifacts=[CodePlanArtifact(**item) for item in artifacts],
    )

    # Persist to MongoDB
    try:
        save_code_plan(
            id_requisicao=id_requisicao,
            request_obj={
                "root_path": doc.root_path,
                "prompt": doc.prompt_original,
                "generated_at": doc.generated_at,
            },
            analysis_obj=doc.model_dump(),
        )
    except Exception as exc:
        add_log(
            "error",
            f"[code_plan_service] Mongo save failed: {exc}",
            "code_plan_service",
        )

    # Persist to filesystem (JSON snapshot)
    try:
        output_path = project_root / f"code_plan_{id_requisicao}.json"
        output_path.write_text(json.dumps(doc.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        add_log(
            "error",
            f"[code_plan_service] Failed writing JSON: {exc}",
            "code_plan_service",
        )

    return doc


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Router Facade❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def run_code_plan(
    prompt: str,
    root_path: str,
    usuario: str = "anonymous",
    id_requisicao: Optional[str] = None,
    analise_sistema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Lightweight facade used by routers and workflows.

    It hides details of scanning, LLM interaction and persistence.
    """

    if id_requisicao:
        now_id = id_requisicao
    else:
        now_id = f"CODEPLAN-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    add_log(
        "info",
        f"[code_plan_service] HTTP /code-plan/run user={usuario}",
        "code_plan_service",
    )

    doc = generate_code_plan(
        id_requisicao=now_id,
        root_path=root_path,
        prompt_usuario=prompt,
        analise_sistema=analise_sistema,
    )

    return {
        "status": "ok",
        "message": "Code plan generated successfully.",
        "id_requisicao": doc.id_requisicao,
        "usuario": usuario,
        "root_path": doc.root_path,
        "summary": doc.summary,
        "code_plan": doc.model_dump(),
    }
