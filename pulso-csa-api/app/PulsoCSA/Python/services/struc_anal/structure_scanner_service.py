#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import os
from typing import List

from utils.log_manager import add_log
# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection, timestamp
except ImportError:
    from app.storage.database.database_core import get_collection, timestamp
from models.struc_anal.struc_anal_models import ScannedFile, ScannedProject

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Configurações de Scan❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# Pastas que não interessam para análise estrutural
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Classificação Dinâmica por Conteúdo❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def detect_role_dynamic(content: str, filename: str) -> str:
    """
    Dynamically classifies a Python file role based purely on its content.
    No folder-name heuristics are used.
    """
    lower = content.lower()
    fname = filename.lower()

    # Routers
    if "apirouter" in lower or "@router" in lower:
        return "router"

    # Models
    if "basemodel" in lower:
        return "model"

    # Agents
    if " agent_" in lower or "agent " in lower or "agent__" in lower or "openai" in lower:
        return "agent"

    # Workflow / orchestration
    if "workflow" in lower or "orquestrador" in lower or "orchestrator" in lower:
        return "workflow"

    # Services
    if "def " in lower and ("service" in fname or "service" in lower):
        return "service"

    # Database
    if "get_collection" in lower or "insert_one" in lower or "update_one" in lower or "pymongo" in lower:
        return "database"

    # Utils
    if "def " in lower and ("utils" in fname or "helper" in fname or "util" in fname):
        return "utils"

    # Core / config
    if "config" in lower or "settings" in lower or "client" in lower:
        return "core"

    # Default role
    return "auxiliary"


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Resumo Programático de Distribuição❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def build_programmatic_summary(root_path: str, arquivos: List[ScannedFile]) -> str:
    """
    Builds a lightweight, fully programmatic summary of the scanned project.
    This is a fallback summary; the LLM will generate a richer one later.
    """
    counts = {}
    for arq in arquivos:
        counts[arq.papel] = counts.get(arq.papel, 0) + 1

    lines = [
        f"System at '{root_path}' analyzed programmatically.",
        "Detected file distribution by inferred role:",
    ]
    for role, qty in sorted(counts.items(), key=lambda x: x[0]):
        lines.append(f"- {role}: {qty} file(s)")

    return "\n".join(lines)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Scan Completo do Projeto❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def scan_full_project(
    log_type: str,
    root_path: str,
    id_requisicao: str,
    prompt: str,
) -> ScannedProject:
    """
    Reads ALL .py files under the given root_path, classifies them dynamically,
    and persists the complete snapshot into the 'struc_analise' collection.

    This function is strictly:
    - filesystem I/O
    - dynamic role classification
    - snapshot persistence

    No LLM is called here. LLM is used only in the subsequent planning service.
    """

    add_log(log_type, f"Scanning project recursively: {root_path}", "structure_scanner")

    arquivos: List[ScannedFile] = []

    #━━━━━━━━━❮Leitura Real de TODOS os Arquivos .py❯━━━━━━━━━
    for current_dir, dirnames, filenames in os.walk(root_path):
        # remove diretórios ignorados dinamicamente
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue

            fpath = os.path.join(current_dir, fname)

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    conteudo = f.read()
            except Exception as e:
                conteudo = f"<<Erro ao ler arquivo: {e}>>"

            papel = detect_role_dynamic(conteudo, fname)

            arquivos.append(
                ScannedFile(
                    path=fpath,
                    linhas=conteudo.count("\n") + 1,
                    tamanho_bytes=len(conteudo.encode("utf-8")),
                    conteudo=conteudo,
                    papel=papel,
                )
            )

    #━━━━━━━━━━━━━━❮Resumo Programático Inicial❯━━━━━━━━━━━━━━
    resumo_sistema = build_programmatic_summary(root_path, arquivos)

    #━━━━━━━━━━━━━━❮Persistência Completa no Mongo (Snapshot)❯━━━━━━━━━━━━━━
    coll = get_collection("struc_analise")
    try:
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
        add_log("error", f"Error persisting structural scan: {e}", "structure_scanner")

    return ScannedProject(
        id_requisicao=id_requisicao,
        root_path=root_path,
        arquivos=arquivos,
        resumo_sistema=resumo_sistema,
    )
