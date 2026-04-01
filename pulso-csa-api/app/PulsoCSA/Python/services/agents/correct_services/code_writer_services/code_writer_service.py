#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Service – Code Writer (Modelo AB – Revisado | Modo 2)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from __future__ import annotations

import ast
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.correct_models.code_writer_models.code_writer_models import (
    CodeWriterExecutionResult,
    CodeWriterFileResult,
    CodeWriterRequest,
)
from models.correct_models.code_plan_models.code_plan_models import (
    CodePlanDocument,
    CodePlanNewFile,
)
from storage.database.correct_analyse.code_plan_database import get_code_plan
from storage.database.correct_analyse.code_writer_database import (
    save_code_writer_result,
)
from utils.log_manager import add_log


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Helpers – Code-plan load❯━━━━━━━━━
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
        add_log("error", f"[code_writer] Failed to read code-plan snapshot {candidate}: {exc}", "code_writer")
        return None

    # Normalize to the same shape DB returns: {"analysis": <CodePlanDocument dict>}
    return {"analysis": data}


def _load_code_plan_document(log_type: str, id_requisicao: str, root_path: Path) -> Optional[CodePlanDocument]:
    add_log(log_type, f"[code_writer] Loading code-plan for {id_requisicao}", "code_writer")

    raw: Optional[Dict[str, Any]] = get_code_plan(id_requisicao)
    if not raw:
        # FS fallback (DB might be down)
        raw = _try_load_code_plan_from_filesystem(root_path, id_requisicao)

    if not raw:
        add_log("error", f"[code_writer] Code-plan not found for {id_requisicao}", "code_writer")
        return None

    analysis = raw.get("analysis")
    if not analysis:
        add_log(
            "error",
            f"[code_writer] Invalid code-plan document (missing 'analysis') for {id_requisicao}",
            "code_writer",
        )
        return None

    try:
        return CodePlanDocument(**analysis)
    except Exception as exc:
        add_log("error", f"[code_writer] Failed to parse CodePlanDocument: {exc}", "code_writer")
        return None


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Helpers – FS / backup / syntax❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _create_backup(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak_{ts}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def _validate_python_syntax(source: str, file_label: str) -> Optional[str]:
    try:
        ast.parse(source)
        return None
    except SyntaxError as exc:
        return (
            f"Refused to apply change due to invalid Python syntax in {file_label}: "
            f"SyntaxError at {exc.lineno}:{exc.offset} – {exc.msg}"
        )
    except Exception as exc:  # pragma: no cover
        return f"Refused to parse {file_label}: {exc}"


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Helpers – detect tipo de arquivo❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _normalize_path_str(value: Optional[str]) -> str:
    return (value or "").replace("\\", "/")


def _is_router_file(pf: CodePlanNewFile) -> bool:
    lower = _normalize_path_str(pf.path).lower()
    return "/routers/" in lower and "/tests/" not in lower and not lower.startswith("tests/")


def _is_test_file(pf: CodePlanNewFile) -> bool:
    lower = _normalize_path_str(pf.path).lower()
    return lower.startswith("tests/") or "/tests/" in lower or lower.endswith("_test.py")


def _is_model_file(pf: CodePlanNewFile) -> bool:
    lower = _normalize_path_str(pf.path).lower()
    return "/models/" in lower or lower.endswith("_model.py") or lower.endswith("_models.py")


def _is_ttst_router_file(pf: CodePlanNewFile) -> bool:
    """
    Deterministic rule: TTST router must always map to prefix '/TTST' and tags ['TTST'].
    This avoids the previous '"/test"' fallback and keeps contract stable.
    """
    lower = _normalize_path_str(pf.path).lower()
    return "/routers/ttst" in lower or "ttst_router" in lower or "/ttst_router/" in lower


def _is_ttst_model_file(pf: CodePlanNewFile) -> bool:
    lower = _normalize_path_str(pf.path).lower()
    return "/models/ttst" in lower or "ttst_models" in lower or "/ttst_models/" in lower


def _is_ttst_service_file(pf: CodePlanNewFile) -> bool:
    lower = _normalize_path_str(pf.path).lower()
    return "/services/ttst" in lower or "ttst_services" in lower or "/ttst_services/" in lower


def _infer_router_prefix_from_description(description: str) -> str:
    import re

    text = (description or "")
    # Canonical TTST handling (case-insensitive)
    if re.search(r"/\s*ttst\b", text, flags=re.IGNORECASE) or re.search(r"\bttst\b", text, flags=re.IGNORECASE):
        return "/TTST"

    matches = re.findall(r"/[a-zA-Z0-9_\-]+", text)
    return matches[0] if matches else "/test"


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Helpers – stubs❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _build_ttst_router_stub(module_name: str, pf: CodePlanNewFile) -> str:
    doc = (pf.content_description or "Auto-generated test endpoint.").strip()
    safe_module = module_name or "ttst_router"

    # NOTE: this is only a stub; implementer will replace it
    # IMPORTANT: endpoint path must be '/' and prefix is applied via include_router in main.py
    return (
        "# Auto-generated by Code Writer – router stub\n"
        f"# Module: {safe_module}\n\n"
        "from fastapi import APIRouter, status\n"
        "from services.ttst_services.ttst_services import get_test_json  # noqa: F401\n"
        "from models.ttst_models.ttst_models import TTSTResponse  # noqa: F401\n\n"
        "router = APIRouter(tags=[\"TTST\"])\n\n"
        "@router.get(\"/\", response_model=TTSTResponse, status_code=status.HTTP_200_OK)\n"
        "def handler() -> TTSTResponse:\n"
        f"    \"\"\"{doc}\"\"\"\n"
        "    payload = get_test_json()\n"
        "    return TTSTResponse(**payload)\n"
    )


def _build_generic_router_stub(module_name: str, pf: CodePlanNewFile) -> str:
    doc = (pf.content_description or "Auto-generated endpoint.").strip()
    safe_module = module_name or "auto_generated_router"

    # NOTE: this is only a stub; implementer will replace it
    # IMPORTANT: endpoint path must be '/' and prefix is applied via include_router in main.py
    return (
        "# Auto-generated by Code Writer – router stub\n"
        f"# Module: {safe_module}\n\n"
        "from fastapi import APIRouter, status\n\n"
        "router = APIRouter()\n\n"
        "@router.get(\"/\", status_code=status.HTTP_200_OK)\n"
        "def handler() -> dict:\n"
        f"    \"\"\"{doc}\"\"\"\n"
        "    return {\"status\": \"ok\"}\n"
    )


def _build_router_stub(module_name: str, pf: CodePlanNewFile) -> str:
    if _is_ttst_router_file(pf):
        return _build_ttst_router_stub(module_name, pf)
    return _build_generic_router_stub(module_name, pf)


def _build_model_stub(pf: CodePlanNewFile) -> str:
    safe_path = _normalize_path_str(pf.path)

    # TTST model default
    if _is_ttst_model_file(pf):
        return (
            "# Auto-generated by Code Writer – model stub\n"
            f"# Path: {safe_path}\n\n"
            "from pydantic import BaseModel, Field\n\n\n"
            "class TTSTResponse(BaseModel):\n"
            "    \"\"\"Modelo de resposta para rota TTST.\"\"\"\n\n"
            "    status: str = Field(default=\"ok\", description=\"Status da rota.\")\n"
            "    message: str = Field(default=\"ttst alive\", description=\"Mensagem de teste.\")\n\n"
            "    class Config:\n"
            "        title = \"TTSTResponse\"\n"
            "        allow_mutation = False\n"
        )

    # generic model stub
    return (
        "# Auto-generated by Code Writer – model stub\n"
        f"# Path: {safe_path}\n\n"
        "from pydantic import BaseModel\n\n\n"
        "class AutoGeneratedModel(BaseModel):\n"
        "    \"\"\"Modelo genérico auto-gerado.\"\"\"\n\n"
        "    pass\n"
    )


def _build_service_stub(pf: CodePlanNewFile, *, default_payload: bool = False) -> str:
    safe_path = _normalize_path_str(pf.path)

    # TTST service default payload
    if default_payload and _is_ttst_service_file(pf):
        return (
            "# Auto-generated by Code Writer – service stub\n"
            f"# Path: {safe_path}\n\n"
            "from typing import Dict\n\n\n"
            "def get_test_json() -> Dict[str, str]:\n"
            "    \"\"\"Payload de teste devolvendo status e message.\"\"\"\n"
            "    return {\"status\": \"ok\", \"message\": \"ttst alive\"}\n"
        )

    interface = (pf.interface or "def todo_implement_me() -> None").strip()
    desc = pf.content_description or pf.reason or ""
    body = (
        "    \"\"\"\n"
        "    Auto-generated service stub.\n"
        + (f"\n    {desc}" if desc else "")
        + "\n    This function MUST be manually implemented.\n"
        "    \"\"\"\n"
        "    raise NotImplementedError\n"
    )
    return (
        "# Auto-generated by Code Writer – service stub\n"
        f"# Path: {safe_path}\n\n{interface}:\n{body}"
    )


def _build_pytest_stub(pf: CodePlanNewFile) -> str:
    safe_path = _normalize_path_str(pf.path)

    return (
        '"""Auto-generated pytest stub for {0}"""\n\n'
        "import pytest\n\n\n"
        "def test_placeholder() -> None:\n"
        '    """Substitua por testes reais."""\n'
        "    assert True\n"
    ).format(safe_path)


def _build_generic_stub(pf: CodePlanNewFile) -> str:
    safe = _normalize_path_str(pf.path)

    return (
        "# Auto-generated by Code Writer – generic stub\n"
        f"# Path: {safe}\n\n"
        "def todo_implement_me() -> None:\n"
        '    """TODO: Implement."""\n'
        "    raise NotImplementedError\n"
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Helpers – criação de arquivo❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _apply_new_file_creation(
    log_type: str,
    root_path: Path,
    pf: CodePlanNewFile,
    dry_run: bool,
) -> CodeWriterFileResult:
    full_path = (root_path / pf.path).resolve()

    if full_path.exists():
        return CodeWriterFileResult(
            path=str(full_path),
            action="skipped_existing",
            success=False,
            message="File already exists. Skipping.",
            backup_path=None,
        )

    if dry_run:
        return CodeWriterFileResult(
            path=str(full_path),
            action="planned_create",
            success=True,
            message="Dry-run: file would be created.",
            backup_path=None,
        )

    _ensure_parent_dir(full_path)

    # ► roteador > modelo > teste > service (_services.py) > genérico
    if _is_router_file(pf):
        content = _build_router_stub(Path(pf.path).stem, pf)
    elif _is_model_file(pf):
        content = _build_model_stub(pf)
    elif _is_test_file(pf):
        content = _build_pytest_stub(pf)
    elif pf.path.endswith("_services.py") or pf.path.endswith("_service.py"):
        # default payload only for TTST service; otherwise generic service stub
        content = _build_service_stub(pf, default_payload=True)
    else:
        content = _build_generic_stub(pf)

    full_path.write_text(content, encoding="utf-8")
    add_log(log_type, f"[code_writer] Created stub at {full_path}", "code_writer")

    return CodeWriterFileResult(
        path=str(full_path),
        action="created",
        success=True,
        message="New file stub created.",
        backup_path=None,
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Helpers – main.py integration❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _infer_main_path(root_path: Path) -> Path:
    return (root_path / "api" / "app" / "main.py").resolve()


def _build_import_line(module_import: str, alias: str) -> str:
    return f"from {module_import} import router as {alias}\n"


def _build_include_router_line(alias: str, prefix: str, tags: Optional[List[str]] = None) -> str:
    tags = tags or ["AutoGenerated"]
    tags_repr = "[" + ", ".join([f'"{t}"' for t in tags]) + "]"
    return f'app.include_router({alias}, prefix="{prefix}", tags={tags_repr})\n'


def _integrate_router_into_main(
    log_type: str,
    root_path: Path,
    new_router_files: List[CodePlanNewFile],
    dry_run: bool,
) -> CodeWriterFileResult:
    main_path = _infer_main_path(root_path)
    if not main_path.exists():
        return CodeWriterFileResult(
            path=str(main_path),
            action="skipped_main_integration",
            success=False,
            message="main.py not found.",
            backup_path=None,
        )

    original_src = main_path.read_text(encoding="utf-8")
    lines = original_src.splitlines(keepends=True)

    last_import = max((i for i, l in enumerate(lines) if l.startswith("from ")), default=0)
    new_imports, new_includes = [], []

    for nf in new_router_files:
        relative = _normalize_path_str(nf.path)
        if relative.startswith("api/"):
            relative = relative[4:]
        if relative.startswith("app/"):
            relative = relative[4:]

        module_import = "app." + relative[:-3].replace("/", ".")

        # default alias = stem
        alias = Path(nf.path).stem

        # ✅ Deterministic TTST: stable alias + stable prefix + stable tags
        if _is_ttst_router_file(nf):
            prefix = "/TTST"
            tags = ["TTST"]
            if alias != "ttst_router":
                alias = "ttst_router"
        else:
            prefix = _infer_router_prefix_from_description(nf.content_description or nf.reason or "")
            tags = ["AutoGenerated"]

        imp_line = _build_import_line(module_import, alias)
        inc_line = _build_include_router_line(alias, prefix, tags)

        if imp_line not in original_src:
            new_imports.append(imp_line)
        if inc_line not in original_src:
            new_includes.append(inc_line)

    if not new_imports and not new_includes:
        return CodeWriterFileResult(
            path=str(main_path),
            action="skipped_main_integration",
            success=True,
            message="Nothing to integrate.",
            backup_path=None,
        )

    new_lines = list(lines)
    insert_pos = last_import + 1
    for idx, imp in enumerate(new_imports):
        new_lines.insert(insert_pos + idx, imp)

    anchor_idx = next(
        (i for i, l in enumerate(new_lines) if l.lstrip().startswith("@app.get")),
        len(new_lines),
    )
    if anchor_idx and new_lines[anchor_idx - 1].strip():
        new_lines.insert(anchor_idx, "\n")
        anchor_idx += 1
    for idx, inc in enumerate(new_includes):
        new_lines.insert(anchor_idx + idx, inc)

    new_src = "".join(new_lines)
    if (err := _validate_python_syntax(new_src, str(main_path))) is not None:
        add_log("error", f"[code_writer] main.py integration refused: {err}", "code_writer")
        return CodeWriterFileResult(
            path=str(main_path),
            action="error",
            success=False,
            message=err,
            backup_path=None,
        )

    if dry_run:
        return CodeWriterFileResult(
            path=str(main_path),
            action="planned_main_integration",
            success=True,
            message="Dry-run: main.py would be modified.",
            backup_path=None,
        )

    backup = _create_backup(main_path)
    main_path.write_text(new_src, encoding="utf-8")
    add_log(log_type, "[code_writer] main.py updated", "code_writer")

    return CodeWriterFileResult(
        path=str(main_path),
        action="modified",
        success=True,
        message="main.py updated.",
        backup_path=str(backup) if backup else None,
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮CORE – execução principal❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def run_code_writer(request: CodeWriterRequest) -> CodeWriterExecutionResult:
    log_type = "info"
    add_log(log_type, f"[code_writer] Running for {request.id_requisicao}", "code_writer")

    root = Path(request.root_path).resolve()
    files_results: List[CodeWriterFileResult] = []
    errors: List[str] = []

    doc = _load_code_plan_document(log_type, request.id_requisicao, root)
    if not doc:
        exec_res = CodeWriterExecutionResult(
            id_requisicao=request.id_requisicao,
            root_path=str(root),
            usuario=request.usuario,
            dry_run=request.dry_run,
            status="error",
            files=[],
            errors=[f"Code-plan not found for {request.id_requisicao}"],
        )
        save_code_writer_result(exec_res.id_requisicao, exec_res.model_dump())
        return exec_res

    # 🔹 deduplicar por path / stem (evita router duplicado)
    uniq: Dict[str, CodePlanNewFile] = {}
    for nf in doc.new_files_to_create:
        key = _normalize_path_str(nf.path).rstrip("/")
        if _is_router_file(nf):
            # keep TTST stable even if path changes slightly
            if _is_ttst_router_file(nf):
                key = "router:ttst_router"
            else:
                key = f"router:{Path(key).stem}"
        uniq.setdefault(key, nf)
    new_files = list(uniq.values())

    # criar arquivos
    for nf in new_files:
        try:
            res = _apply_new_file_creation(log_type, root, nf, request.dry_run)
            files_results.append(res)
            if not res.success:
                errors.append(f"{res.path}: {res.message}")
        except Exception as exc:  # pragma: no cover
            msg = f"Unexpected error creating {nf.path}: {exc}"
            files_results.append(
                CodeWriterFileResult(
                    path=str(root / nf.path),
                    action="error",
                    success=False,
                    message=msg,
                    backup_path=None,
                )
            )
            errors.append(msg)

    # integrar routers
    routers = [nf for nf in new_files if _is_router_file(nf)]
    if routers:
        try:
            main_res = _integrate_router_into_main(log_type, root, routers, request.dry_run)
            files_results.append(main_res)
            if not main_res.success:
                errors.append(main_res.message)
        except Exception as exc:  # pragma: no cover
            errors.append(f"main.py integration failed: {exc}")

    status = "success"
    if errors and any(r.success for r in files_results):
        status = "partial"
    elif errors:
        status = "error"

    exec_res = CodeWriterExecutionResult(
        id_requisicao=request.id_requisicao,
        root_path=str(root),
        usuario=request.usuario,
        dry_run=request.dry_run,
        status=status,
        files=files_results,
        errors=errors,
    )
    save_code_writer_result(exec_res.id_requisicao, exec_res.model_dump())
    add_log(log_type, f"[code_writer] Finished with {status}", "code_writer")

    return exec_res
