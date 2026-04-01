#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Scanner de Projeto JavaScript/TypeScript/React❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from __future__ import annotations

import os
from typing import List

from utils.log_manager import add_log

try:
    from storage.database.database_core import get_collection, timestamp
except ImportError:
    from app.storage.database.database_core import get_collection, timestamp

try:
    from models.struc_anal.struc_anal_models import ScannedFile, ScannedProject
except ImportError:
    from app.PulsoCSA.Python.models.struc_anal.struc_anal_models import ScannedFile, ScannedProject

#━━━━━━━━━❮Configurações de Scan❯━━━━━━━━━
IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules",
    ".idea", ".vscode", "dist", "build", ".next", ".nuxt",
    "__pycache__", ".mypy_cache", ".pytest_cache", "coverage",
}

JS_EXTENSIONS = (".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte")


def detect_role_dynamic_js(content: str, filename: str, rel_path: str) -> str:
    """
    Classifica dinamicamente o papel de um arquivo JS/TS/React baseado no conteúdo.
    """
    lower = content.lower()
    fname = filename.lower()
    path_lower = rel_path.lower().replace("\\", "/")

    # Componentes React/Vue/Svelte
    if "react" in lower or "jsx" in fname or "tsx" in fname:
        if "function " in lower and ("return" in lower or "=>" in lower):
            return "component"
        if "class " in lower and "component" in lower:
            return "component"
    if "vue" in lower or ".vue" in fname:
        return "component"
    if "svelte" in lower or ".svelte" in fname:
        return "component"

    # Pages / Views
    if "pages" in path_lower or "page" in path_lower or "views" in path_lower:
        return "page"

    # Router
    if "router" in lower or "route" in lower or "browserrouter" in lower or "createbrowserrouter" in lower:
        return "router"
    if "routes" in path_lower or "router" in path_lower:
        return "router"

    # Hooks
    if "use" in fname and ("hook" in path_lower or "hooks" in path_lower):
        return "hook"
    if "use" in fname and ("function " in lower or "const " in lower):
        return "hook"

    # Services / API
    if "service" in fname or "api" in fname or "fetch" in lower or "axios" in lower:
        return "service"
    if "services" in path_lower or "api" in path_lower:
        return "service"

    # Utils / Helpers
    if "util" in fname or "helper" in fname or "utils" in path_lower:
        return "utils"

    # Store / State
    if "store" in lower or "redux" in lower or "zustand" in lower or "recoil" in lower:
        return "store"

    # Config / Core
    if "config" in lower or "env" in lower or "main" in fname or "app" in fname:
        return "core"

    return "auxiliary"


def build_programmatic_summary_js(root_path: str, arquivos: List[ScannedFile]) -> str:
    """Resumo programático da distribuição de arquivos."""
    counts = {}
    for arq in arquivos:
        counts[arq.papel] = counts.get(arq.papel, 0) + 1
    lines = [
        f"Projeto JS/TS em '{root_path}' analisado programaticamente.",
        "Distribuição por papel detectado:",
    ]
    for role, qty in sorted(counts.items(), key=lambda x: x[0]):
        lines.append(f"- {role}: {qty} arquivo(s)")
    return "\n".join(lines)


def scan_full_project_js(
    log_type: str,
    root_path: str,
    id_requisicao: str,
    prompt: str,
) -> ScannedProject:
    """
    Escaneia todos os arquivos .js, .ts, .jsx, .tsx, .vue, .svelte sob root_path,
    classifica dinamicamente e persiste snapshot em 'struc_analise_js'.
    """
    add_log(log_type, f"[structure_scanner_js] Escaneando projeto: {root_path}", "structure_scanner_js")
    arquivos: List[ScannedFile] = []

    for current_dir, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for fname in filenames:
            if not any(fname.endswith(ext) for ext in JS_EXTENSIONS):
                continue
            fpath = os.path.join(current_dir, fname)
            rel_path = os.path.relpath(fpath, root_path)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    conteudo = f.read()
            except Exception as e:
                conteudo = f"<<Erro ao ler arquivo: {e}>>"
            papel = detect_role_dynamic_js(conteudo, fname, rel_path)
            arquivos.append(
                ScannedFile(
                    path=fpath,
                    linhas=conteudo.count("\n") + 1,
                    tamanho_bytes=len(conteudo.encode("utf-8")),
                    conteudo=conteudo,
                    papel=papel,
                )
            )

    resumo_sistema = build_programmatic_summary_js(root_path, arquivos)

    try:
        coll = get_collection("struc_analise_js")
        coll.update_one(
            {"_id": id_requisicao},
            {
                "$set": {
                    "id_requisicao": id_requisicao,
                    "root_path": root_path,
                    "prompt_usuario": prompt,
                    "resumo_programatico": resumo_sistema,
                    "arquivos_lidos": [a.model_dump() for a in arquivos],
                    "saved_at": timestamp(),
                }
            },
            upsert=True,
        )
    except Exception as e:
        add_log("error", f"[structure_scanner_js] Erro ao persistir scan: {e}", "structure_scanner_js")

    add_log(log_type, f"[structure_scanner_js] Concluído: {len(arquivos)} arquivos", "structure_scanner_js")
    return ScannedProject(
        id_requisicao=id_requisicao,
        root_path=root_path,
        arquivos=arquivos,
        resumo_sistema=resumo_sistema,
    )
