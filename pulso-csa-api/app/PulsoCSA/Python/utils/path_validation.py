#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Validação de paths (multi-usuário e segurança)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
from pathlib import Path
from typing import Optional

# Base path permitido. Se definido (ALLOWED_ROOT_BASE ou COMPREHENSION_ALLOWED_ROOT_BASE), paths devem estar sob ele.
_ALLOWED_BASE = (
    os.getenv("ALLOWED_ROOT_BASE") or os.getenv("COMPREHENSION_ALLOWED_ROOT_BASE") or ""
).strip()


def _is_production() -> bool:
    r = (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV") or "").strip().lower()
    return r == "production"


def get_app_package_dir() -> str:
    """
    Diretório api/app (main.py, PulsoCSA, storage, pulso_workspace).
    path_validation.py está em …/PulsoCSA/Python/utils/ → parents[2] = app.
    """
    return str(Path(__file__).resolve().parents[2])


def _default_production_workspace() -> str:
    """Pasta gravável dentro da app (ex.: Railway) quando não há ALLOWED_ROOT_BASE."""
    return str(Path(get_app_package_dir()) / "pulso_workspace")


def get_effective_allowed_base() -> str:
    """
    Base usada para validar root_path. Em produção sem env explícito, usa pulso_workspace em disco.
    Cria o diretório se não existir.
    """
    explicit = (
        os.getenv("ALLOWED_ROOT_BASE") or os.getenv("COMPREHENSION_ALLOWED_ROOT_BASE") or ""
    ).strip()
    if explicit:
        p = os.path.normpath(os.path.abspath(explicit))
        os.makedirs(p, exist_ok=True)
        return p
    if _is_production():
        p = os.path.normpath(os.path.abspath(_default_production_workspace()))
        os.makedirs(p, exist_ok=True)
        return p
    return ""


def resolve_project_root_for_workflow(usuario: str, root_path: Optional[str]) -> str:
    """
    Garante um diretório raiz não vazio para relatórios e generated_code.
    - Se root_path vier preenchido: normaliza com abspath.
    - Produção sem path: mesmo workspace isolado que o router de compreensão (pulso_workspace).
    - Desenvolvimento sem path: api/app/pulso_workspace_dev/<usuario> (gravável, sem depender de ALLOWED_ROOT_BASE).
    """
    rp = (root_path or "").strip()
    if rp:
        return os.path.normpath(os.path.abspath(rp))
    if _is_production():
        return workspace_path_for_user(usuario)
    base = str(Path(get_app_package_dir()) / "pulso_workspace_dev")
    os.makedirs(base, exist_ok=True)
    safe = "".join(c for c in (usuario or "default") if c.isalnum() or c in "._-@")[:120] or "default"
    out = os.path.join(base, safe)
    os.makedirs(out, exist_ok=True)
    return os.path.normpath(os.path.abspath(out))


def workspace_path_for_user(usuario: str) -> str:
    """
    Diretório de projeto isolado por utilizador sob a base efetiva (produção / env).
    Usado quando o cliente envia um root_path inválido no servidor (ex.: caminho Windows local).
    """
    base = get_effective_allowed_base()
    if not base:
        raise ValueError("workspace base não configurado")
    safe = "".join(c for c in (usuario or "default") if c.isalnum() or c in "._-@")[:120] or "default"
    path = os.path.join(base, safe)
    os.makedirs(path, exist_ok=True)
    return os.path.normpath(os.path.abspath(path))


def sanitize_root_path(root_path: Optional[str], allowed_base: Optional[str] = None) -> Optional[str]:
    """
    Normaliza e valida root_path; rejeita path traversal (..) e paths fora da base.
    Em produção, paths devem ficar sob ALLOWED_ROOT_BASE / COMPREHENSION_ALLOWED_ROOT_BASE,
    ou sob o workspace por defeito (api/app/pulso_workspace) se essas env não estiverem definidas.
    Retorna None se inválido. allowed_base sobrescreve a base efetiva se informado (string; use \"\" para desativar prefixo).
    """
    if not root_path or not str(root_path).strip():
        return None
    raw = str(root_path).strip()
    if ".." in raw:
        return None
    if allowed_base is not None:
        base = (allowed_base or "").strip()
    else:
        base = get_effective_allowed_base() if _is_production() else _ALLOWED_BASE
    try:
        resolved = os.path.normpath(os.path.abspath(raw))
        if base and not resolved.startswith(os.path.normpath(base)):
            return None
        return resolved
    except Exception:
        return None


def is_production() -> bool:
    """Indica se o ambiente é produção (para não expor detalhes de exceção)."""
    return _is_production()


def is_path_under_base(resolved_path: str, base_path: str) -> bool:
    """
    Verifica se resolved_path está contido em base_path (evita path traversal).
    Ambos devem ser paths absolutos normalizados.
    """
    if not resolved_path or not base_path:
        return False
    base = os.path.normpath(os.path.abspath(base_path))
    resolved = os.path.normpath(os.path.abspath(resolved_path))
    return resolved == base or resolved.startswith(base + os.sep)


def sanitize_relative_path(relative: str) -> Optional[str]:
    """
    Rejeita path traversal (..), paths absolutos e caracteres perigosos.
    Retorna o path normalizado ou None se inválido. "" e "." retornam ".".
    """
    raw = str(relative or "").strip().replace("\\", "/") or "."
    if ".." in raw or raw.startswith("/") or raw.startswith("\\"):
        return None
    parts = raw.split("/")
    if any(".." in p for p in parts):
        return None
    return raw.strip("/") or "."
