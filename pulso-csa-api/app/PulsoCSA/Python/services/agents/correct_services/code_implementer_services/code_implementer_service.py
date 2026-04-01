#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Service – Code Implementer (C4)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from __future__ import annotations

import ast
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client

from models.correct_models.code_implementer_models.code_implementer_models import (
    CodeImplementerRequest,
    CodeImplementerFileResult,
    CodeImplementerExecutionResult,
)

from models.correct_models.code_plan_models.code_plan_models import (
    CodePlanDocument,
    CodePlanNewFile,
)

from storage.database.correct_analyse.code_plan_database import get_code_plan

# Prefer a dedicated persist layer for implementer results; fallback to existing writer DB if not available.
try:
    from storage.database.correct_analyse.code_implementer_database import (  # type: ignore
        save_code_implementer_result,  # noqa: F401
    )
except Exception:  # pragma: no cover
    save_code_implementer_result = None  # type: ignore

from storage.database.correct_analyse.code_writer_database import (
    save_code_writer_result,
)

from utils.log_manager import add_log


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Load Code Plan (mesmo usado pelo C3)❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _try_load_code_plan_from_filesystem(root_path: Path, id_requisicao: str) -> Optional[Dict[str, Any]]:
    """
    Fallback when DB is unavailable (NoOpCollection): read code plan snapshot from filesystem.

    Expected snapshot location created by code_plan_service:
      <root_path>/code_plan_<id_requisicao>.json
    """
    candidate = (root_path / f"code_plan_{id_requisicao}.json").resolve()
    if not candidate.exists():
        return None

    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception as exc:
        add_log("error", f"[code_implementer] Failed to read code-plan snapshot {candidate}: {exc}", "code_implementer")
        return None

    # Normalize to the same shape DB returns: {"analysis": <CodePlanDocument dict>}
    return {"analysis": data}


def _load_code_plan_document(log_type: str, id_requisicao: str, root_path: Path) -> Optional[CodePlanDocument]:
    add_log(log_type, f"[code_implementer] Loading code-plan for {id_requisicao}", "code_implementer")

    raw = get_code_plan(id_requisicao)
    if not raw:
        # FS fallback (DB might be down)
        raw = _try_load_code_plan_from_filesystem(root_path, id_requisicao)

    if not raw:
        add_log("error", f"[code_implementer] Code-plan not found for {id_requisicao}", "code_implementer")
        return None

    analysis = raw.get("analysis")
    if not analysis:
        add_log("error", "[code_implementer] Invalid code-plan document: missing 'analysis' key", "code_implementer")
        return None

    try:
        return CodePlanDocument(**analysis)
    except Exception as exc:
        add_log("error", f"[code_implementer] Failed to parse CodePlanDocument: {exc}", "code_implementer")
        return None


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮FS / Backup / Syntax❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _create_backup(path: Path) -> Optional[Path]:
    if not path.exists():
        return None

    timestamp_str = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak_{timestamp_str}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def _validate_python_syntax(source: str, file_label: str) -> Optional[str]:
    try:
        ast.parse(source)
        return None
    except SyntaxError as exc:
        return (
            f"Invalid Python syntax in {file_label}: "
            f"SyntaxError at {exc.lineno}:{exc.offset} – {exc.msg}"
        )
    except Exception as exc:
        return f"Failed to parse {file_label}: {exc}"


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Symbol Freeze – preserve stub API❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _extract_public_symbols(existing_source: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Extract top-level public symbols from stub/source:
    - classes
    - functions
    - assigned names (e.g., 'router')
    """
    if not existing_source.strip():
        return ([], [], [])

    try:
        tree = ast.parse(existing_source)
    except Exception:
        return ([], [], [])

    classes: List[str] = []
    functions: List[str] = []
    assigned: List[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                functions.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    assigned.append(t.id)

    # common: keep deterministic ordering
    classes = sorted(set(classes))
    functions = sorted(set(functions))
    assigned = sorted(set(assigned))
    return (classes, functions, assigned)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Prompts – System e User❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _build_implementation_system_prompt() -> str:
    from app.prompts.loader import load_prompt
    return load_prompt("correct/implementation_system")


def _build_implementation_user_prompt(
    project_root: Path,
    plan_file: CodePlanNewFile,
    existing_source: str,
) -> str:
    classes, functions, assigned = _extract_public_symbols(existing_source)

    frozen_lines: List[str] = []
    if classes:
        frozen_lines.append(f"- Classes (must keep names): {', '.join(classes)}")
    if functions:
        frozen_lines.append(f"- Functions (must keep names): {', '.join(functions)}")
    if assigned:
        frozen_lines.append(f"- Assigned names (must keep): {', '.join(assigned)}")
    frozen_section = "\n".join(frozen_lines) if frozen_lines else "- (No symbols detected in stub.)"

    from app.prompts.loader import load_prompt
    return load_prompt("correct/implementation_user").format(
        project_root=project_root,
        target_file=plan_file.path,
        reason=plan_file.reason,
        content_description=plan_file.content_description,
        existing_source=existing_source,
        frozen_section=frozen_section,
    )


def _safe_llm_call_for_implementation(user_prompt: str, system_prompt: str) -> str:
    client = get_openai_client()
    retries = 3
    delay_sec = 1
    timeout_sec = int(os.getenv("CODE_IMPLEMENTER_LLM_TIMEOUT_SEC", "120"))

    for _ in range(retries):
        resp = client.generate_text(
            user_prompt,
            system_prompt=system_prompt,
            num_predict=2048,
            use_fast_model=False,
            timeout_override=timeout_sec,
        )
        if "Erro ao gerar texto" not in resp:
            return resp

        import time
        time.sleep(delay_sec)
        delay_sec *= 2

    return (
        "def _code_implementer_fallback() -> None:\n"
        '    """Fallback implementation (C4 failed)."""\n'
        "    pass\n"
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Implementar Arquivo Individual❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _apply_file_implementation(
    log_type: str,
    project_root: Path,
    plan_file: CodePlanNewFile,
    dry_run: bool,
) -> CodeImplementerFileResult:
    full_path = (project_root / plan_file.path).resolve()
    _ensure_parent_dir(full_path)

    existing_source = ""
    if full_path.exists():
        try:
            raw = full_path.read_text(encoding="utf-8")
            # Limitar contexto para reduzir tokens (qualidade mantida com trecho relevante).
            max_source_lines = 120
            lines = raw.splitlines()
            existing_source = "\n".join(lines[:max_source_lines]) if len(lines) > max_source_lines else raw
        except Exception as exc:
            message = f"Failed to read existing stub for {full_path}: {exc}"
            add_log("error", message, "code_implementer")
            return CodeImplementerFileResult(
                path=str(full_path),
                action="error",
                success=False,
                message=message,
                backup_path=None,
            )

    system_prompt = _build_implementation_system_prompt()
    user_prompt = _build_implementation_user_prompt(project_root, plan_file, existing_source)

    generated_source = _safe_llm_call_for_implementation(user_prompt, system_prompt)

    error = _validate_python_syntax(generated_source, str(full_path))
    if error:
        add_log("error", error, "code_implementer")
        return CodeImplementerFileResult(
            path=str(full_path),
            action="error",
            success=False,
            message=error,
            backup_path=None,
        )

    if dry_run:
        return CodeImplementerFileResult(
            path=str(full_path),
            action="planned_implementation",
            success=True,
            message="Dry-run: file implementation would be written.",
            backup_path=None,
        )

    backup = _create_backup(full_path) if full_path.exists() else None

    try:
        full_path.write_text(generated_source, encoding="utf-8")
    except Exception as exc:
        message = f"Failed to write implemented file for {full_path}: {exc}"
        add_log("error", message, "code_implementer")
        return CodeImplementerFileResult(
            path=str(full_path),
            action="error",
            success=False,
            message=message,
            backup_path=str(backup) if backup else None,
        )

    return CodeImplementerFileResult(
        path=str(full_path),
        action="implemented",
        success=True,
        message="File implemented successfully.",
        backup_path=str(backup) if backup else None,
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Execução Principal C4❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _persist_implementer_result(id_requisicao: str, payload: Dict[str, Any]) -> None:
    """
    Persist implementer results.
    Prefer dedicated implementer DB if available; fallback to writer DB to avoid breaking runtime.
    """
    try:
        if save_code_implementer_result is not None:
            save_code_implementer_result(id_requisicao, payload)  # type: ignore
        else:
            save_code_writer_result(id_requisicao, payload)
    except Exception as exc:  # pragma: no cover
        add_log("error", f"[code_implementer] Failed to persist result: {exc}", "code_implementer")


def run_code_implementer(request: CodeImplementerRequest) -> CodeImplementerExecutionResult:
    log_type = "info"
    add_log(log_type, f"[code_implementer] Running for {request.id_requisicao}", "code_implementer")

    root = Path(request.root_path).resolve()
    results: List[CodeImplementerFileResult] = []
    errors: List[str] = []

    doc = _load_code_plan_document(log_type, request.id_requisicao, root)
    if not doc:
        message = f"Code-plan not found or invalid for {request.id_requisicao}"
        exec_result = CodeImplementerExecutionResult(
            id_requisicao=request.id_requisicao,
            root_path=str(root),
            usuario=request.usuario,
            dry_run=request.dry_run,
            status="error",
            files=[],
            errors=[message],
        )
        _persist_implementer_result(exec_result.id_requisicao, exec_result.model_dump())
        add_log("error", message, "code_implementer")
        return exec_result

    plan_files = list(doc.new_files_to_create)
    max_workers = min(len(plan_files), 4) if plan_files else 1

    def _apply_one(plan_file: CodePlanNewFile) -> CodeImplementerFileResult:
        try:
            return _apply_file_implementation(
                log_type=log_type,
                project_root=root,
                plan_file=plan_file,
                dry_run=request.dry_run,
            )
        except Exception as exc:
            msg = f"Unexpected error implementing {plan_file.path}: {exc}"
            add_log("error", msg, "code_implementer")
            return CodeImplementerFileResult(
                path=str(root / plan_file.path),
                action="error",
                success=False,
                message=msg,
                backup_path=None,
            )

    if max_workers <= 1:
        for plan_file in plan_files:
            res = _apply_one(plan_file)
            results.append(res)
            if not res.success:
                errors.append(f"{res.path}: {res.message}")
    else:
        results_ordered: List[Optional[CodeImplementerFileResult]] = [None] * len(plan_files)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {executor.submit(_apply_one, pf): i for i, pf in enumerate(plan_files)}
            for future in as_completed(future_to_idx):
                i = future_to_idx[future]
                try:
                    res = future.result()
                    results_ordered[i] = res
                except Exception as exc:
                    results_ordered[i] = CodeImplementerFileResult(
                        path=str(root / plan_files[i].path),
                        action="error",
                        success=False,
                        message=str(exc),
                        backup_path=None,
                    )
        for res in results_ordered:
            if res is not None:
                results.append(res)
                if not res.success:
                    errors.append(f"{res.path}: {res.message}")

    if errors and any(r.success for r in results):
        status = "partial"
    elif errors:
        status = "error"
    else:
        status = "success"

    exec_result = CodeImplementerExecutionResult(
        id_requisicao=request.id_requisicao,
        root_path=str(root),
        usuario=request.usuario,
        dry_run=request.dry_run,
        status=status,
        files=results,
        errors=errors,
    )

    _persist_implementer_result(exec_result.id_requisicao, exec_result.model_dump())
    add_log(log_type, f"[code_implementer] Finished with {status}", "code_implementer")

    return exec_result
