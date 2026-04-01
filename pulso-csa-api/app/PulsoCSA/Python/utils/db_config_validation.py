#━━━━━━━━━❮Validação db_config❯━━━━━━━━━
# Allowlist de hosts/databases permitidos para evitar abuso.
import os
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse


def _is_production() -> bool:
    return (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENV", "").lower()) == "production"


def _hostname_from_mongo_uri(uri: str) -> Optional[str]:
    if not uri or not isinstance(uri, str):
        return None
    s = uri.strip()
    if not s.lower().startswith("mongodb"):
        return None
    try:
        p = urlparse(s)
        return p.hostname.lower() if p.hostname else None
    except Exception:
        return None


def _allowed_hosts_list() -> List[str]:
    """Hosts permitidos (lowercase). Em produção, se ALLOWED_DB_HOSTS vazio, usa o host de MONGO_URI (Railway)."""
    raw = (os.getenv("ALLOWED_DB_HOSTS") or "").strip()
    items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    if items:
        return items
    if _is_production():
        h = _hostname_from_mongo_uri(os.getenv("MONGO_URI") or "")
        return [h] if h else []
    return []


def _allowed_databases_list() -> List[str]:
    """
    Nomes de base permitidos para db_config.
    - Se ALLOWED_DB_DATABASES estiver definido: usa só essa lista (estrito).
    - Em produção com MONGO_URI sem path de base (típico Railway: ...host:port sem /db):
      retorna lista vazia = não restringe o nome da base; o host já foi validado na allowlist.
    - Em produção com path em MONGO_URI: permite só essa base + MONGO_DB_NAME.
    - Fora de produção com lista vazia: qualquer base (comportamento dev).
    """
    raw = (os.getenv("ALLOWED_DB_DATABASES") or "").strip()
    items = [x.strip() for x in raw.split(",") if x.strip()]
    if items:
        return items
    if not _is_production():
        return []
    u = (os.getenv("MONGO_URI") or "").strip()
    if not u.lower().startswith("mongodb"):
        return []
    try:
        p = urlparse(u)
        path = (p.path or "").strip("/")
        if not path:
            # Ex.: mongodb://user:pass@proxy.rlwy.net:18083 — várias bases no mesmo cluster
            return []
        dbs: List[str] = []
        seg = unquote(path.split("/")[0])
        if seg:
            dbs.append(seg)
        mdb = (os.getenv("MONGO_DB_NAME") or "").strip()
        if mdb and mdb not in dbs:
            dbs.append(mdb)
        return dbs
    except Exception:
        return []


def _candidate_hosts_from_config(db_config: Dict[str, Any]) -> List[str]:
    """
    Hostnames extraídos de db_config.
    O frontend costuma colocar o URI completo em `host` (campo Host/URI); isso precisa ser parseado.
    """
    out: List[str] = []
    uri = db_config.get("uri")
    host = db_config.get("host") or db_config.get("hostname")
    for val in (uri, host):
        if not val or not isinstance(val, str):
            continue
        s = val.strip()
        if s.lower().startswith("mongodb"):
            h = _hostname_from_mongo_uri(s)
            if h:
                out.append(h)
        elif val is host and s and "://" not in s:
            hpart = s.split(":")[0].strip().lower()
            if hpart:
                out.append(hpart)
    seen = set()
    uniq: List[str] = []
    for h in out:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq


_MSG_ENV = (
    "Configure nas variáveis de ambiente do serviço (Railway: Variables). "
    "Não é necessário arquivo .env no disco."
)


def validar_db_config(db_config: Optional[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """
    Valida db_config contra allowlist de hosts/databases.
    Retorna (is_valid, error_message).
    Em desenvolvimento com allowlists vazias, permite qualquer host/database.
    Em produção: allowlist de hosts nunca fica vazia se MONGO_URI tiver hostname (fallback anti-SSRF com mesmo cluster Railway).
    SQLite ignora validação de host (usa path/database como arquivo).
    """
    if not db_config:
        return True, None
    db_type = (db_config.get("db_type") or "").strip().lower()
    database = db_config.get("database") or db_config.get("db") or db_config.get("path")
    allowed_hosts = _allowed_hosts_list()
    allowed_dbs = _allowed_databases_list()

    if db_type == "sqlite":
        if allowed_dbs and database and database not in allowed_dbs:
            return False, f"Database '{database}' não está na allowlist permitida."
        return True, None

    if _is_production() and not allowed_hosts:
        return (
            False,
            f"Em produção, defina ALLOWED_DB_HOSTS ou MONGO_URI com hostname. {_MSG_ENV}",
        )

    candidates = _candidate_hosts_from_config(db_config)
    uri = db_config.get("uri")
    host = db_config.get("host") or db_config.get("hostname")

    if allowed_hosts:
        if not candidates:
            if uri or host:
                return (
                    False,
                    "Não foi possível extrair o hostname a partir de db_config. "
                    "Para MongoDB, use um URI válido (mongodb://...) em `uri` ou em `host`.",
                )
        for c in candidates:
            if c not in allowed_hosts:
                return False, (
                    f"Host '{c}' não está na allowlist permitida "
                    f"({', '.join(allowed_hosts)}). Ajuste ALLOWED_DB_HOSTS ou use o host correto."
                )

    # Com allowed_dbs vazio em prod + MONGO_URI sem /db, qualquer nome de base é aceite (ver _allowed_databases_list).

    if allowed_dbs and database and database not in allowed_dbs:
        return (
            False,
            f"Database '{database}' não está na allowlist permitida ({', '.join(allowed_dbs)}).",
        )

    return True, None


def __getattr__(name: str) -> Any:
    """Compat: ALLOWED_DB_HOSTS / ALLOWED_DB_DATABASES avaliados sob demanda."""
    if name == "ALLOWED_DB_HOSTS":
        return _allowed_hosts_list()
    if name == "ALLOWED_DB_DATABASES":
        return _allowed_databases_list()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
