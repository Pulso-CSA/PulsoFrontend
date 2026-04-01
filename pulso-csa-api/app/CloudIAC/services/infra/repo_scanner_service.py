#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Repo Scanner – fingerprint + cache❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import hashlib
import os
import threading
import time
from pathlib import Path
from typing import Any, Optional

# Cache por fingerprint (repo_fingerprint -> (ts, context))
_INFRA_REPO_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_INFRA_REPO_CACHE_LOCK = threading.Lock()
INFRA_REPO_CACHE_TTL_SEC = int(os.getenv("INFRA_REPO_FINGERPRINT_CACHE_TTL_SEC", "300"))
INFRA_REPO_CACHE_MAX = 200

# Arquivos relevantes para fingerprint
RELEVANT_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".tf", ".toml", ".md"}
IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".terraform"}


def compute_fingerprint(root_path: str) -> str:
    """
    Calcula hash da árvore do repositório (arquivos relevantes).
    Permite cache incremental: se o hash não mudou, não reprocessar.
    """
    if not root_path or not os.path.isdir(root_path):
        return ""
    parts: list[str] = []
    root = Path(root_path).resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        rel = os.path.relpath(dirpath, root).replace("\\", "/")
        for f in sorted(filenames):
            ext = os.path.splitext(f)[1].lower()
            if ext in RELEVANT_EXTENSIONS or f in ("Dockerfile", "docker-compose.yml", "requirements.txt"):
                fp = os.path.join(dirpath, f)
                try:
                    stat = os.stat(fp)
                    parts.append(f"{rel}/{f}:{stat.st_mtime}:{stat.st_size}")
                except OSError:
                    pass
    content = "|".join(parts)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def scan_repo(root_path: str, use_cache: bool = True) -> dict[str, Any]:
    """
    Escaneia root_path e retorna contexto do repositório.
    Usa cache por fingerprint quando use_cache=True.
    """
    safe_path = str(Path(root_path).resolve()) if root_path else ""
    if not safe_path or not os.path.isdir(safe_path):
        return {"error": "root_path inválido ou inexistente", "fingerprint": ""}

    fingerprint = compute_fingerprint(safe_path)
    if use_cache:
        with _INFRA_REPO_CACHE_LOCK:
            if fingerprint in _INFRA_REPO_CACHE:
                ts, cached = _INFRA_REPO_CACHE[fingerprint]
                if time.time() - ts <= INFRA_REPO_CACHE_TTL_SEC:
                    return cached
                del _INFRA_REPO_CACHE[fingerprint]

    # Scan real
    tree: list[str] = []
    languages: set[str] = set()
    has_docker = False
    has_terraform = False
    root = Path(safe_path)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        rel = os.path.relpath(dirpath, root).replace("\\", "/")
        for f in filenames:
            fp = os.path.join(dirpath, f)
            rel_f = f"{rel}/{f}" if rel != "." else f
            tree.append(rel_f)
            ext = os.path.splitext(f)[1].lower()
            if ext == ".py":
                languages.add("python")
            elif ext in (".js", ".ts", ".tsx"):
                languages.add("javascript")
            elif f == "Dockerfile" or f == "docker-compose.yml":
                has_docker = True
            elif ext == ".tf":
                has_terraform = True

    result = {
        "root_path": safe_path,
        "fingerprint": fingerprint,
        "tree": tree[:500],
        "tree_count": len(tree),
        "languages": list(languages),
        "has_docker": has_docker,
        "has_terraform": has_terraform,
    }

    with _INFRA_REPO_CACHE_LOCK:
        if len(_INFRA_REPO_CACHE) >= INFRA_REPO_CACHE_MAX:
            by_ts = sorted(_INFRA_REPO_CACHE.items(), key=lambda x: x[1][0])
            for k, _ in by_ts[: INFRA_REPO_CACHE_MAX // 2]:
                del _INFRA_REPO_CACHE[k]
        _INFRA_REPO_CACHE[fingerprint] = (time.time(), result)

    return result
