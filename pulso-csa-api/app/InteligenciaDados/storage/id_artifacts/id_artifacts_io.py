#━━━━━━━━━❮I/O Artefatos ID❯━━━━━━━━━
# Diretório por usuario/id_requisicao; leitura/escrita Parquet e metadados de modelo.
# load_dataframe: suporta Parquet, CSV (comprimido ou não), Excel, JSON com paginação.
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

try:
    from filelock import FileLock
except ImportError:
    # Linux/Docker (ex.: Railway com cache de imagem sem filelock): fcntl evita falha de import.
    if os.name != "posix":
        raise

    import fcntl

    class _FcntlFileLock:
        """Subset compatível com filelock.FileLock(lock_path, timeout=...) como context manager."""

        def __init__(self, lock_file: Union[str, Path], timeout: float = -1) -> None:
            self.lock_file = os.fspath(lock_file)
            self.timeout = float(timeout)
            self._fd: Optional[int] = None

        def __enter__(self) -> "_FcntlFileLock":
            Path(self.lock_file).parent.mkdir(parents=True, exist_ok=True)
            self._fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR, 0o644)
            deadline = None if self.timeout < 0 else time.monotonic() + self.timeout
            while True:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return self
                except BlockingIOError:
                    if deadline is not None and time.monotonic() >= deadline:
                        os.close(self._fd)
                        self._fd = None
                        raise TimeoutError(f"Timeout ao obter lock: {self.lock_file}") from None
                    time.sleep(0.05)

        def __exit__(self, *args: Any) -> None:
            if self._fd is not None:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                finally:
                    os.close(self._fd)
                    self._fd = None

    FileLock = _FcntlFileLock  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)

# Limite opcional por env (None = sem limite). Ajuda a evitar OOM em datasets muito grandes.
_ID_DATASET_MAX_ROWS = os.getenv("ID_DATASET_MAX_ROWS", "").strip()
_ID_DATASET_MAX_ROWS_INT: Optional[int] = None
if _ID_DATASET_MAX_ROWS and _ID_DATASET_MAX_ROWS.isdigit():
    _ID_DATASET_MAX_ROWS_INT = int(_ID_DATASET_MAX_ROWS)

# Base: api/app/storage/id_artifacts_data ou env ID_ARTIFACTS_DIR
_BASE = os.getenv("ID_ARTIFACTS_DIR")
if not _BASE:
    _BASE = str(Path(__file__).resolve().parent.parent.parent / "id_artifacts_data")
Path(_BASE).mkdir(parents=True, exist_ok=True)


def get_artifact_dir(usuario: str, id_requisicao: str, subdir: str = "datasets") -> str:
    """Retorna caminho do diretório de artefatos para usuario e id_requisicao."""
    safe_user = "".join(c for c in usuario if c.isalnum() or c in "._-") or "default"
    safe_id = "".join(c for c in id_requisicao if c.isalnum() or c in "._-")[:64] or "req"
    path = os.path.join(_BASE, safe_user, safe_id, subdir)
    return path


def ensure_artifact_dir(usuario: str, id_requisicao: str, subdir: str = "datasets") -> str:
    """Cria o diretório se não existir e retorna o caminho."""
    path = get_artifact_dir(usuario, id_requisicao, subdir)
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def save_dataframe(
    df: pd.DataFrame,
    usuario: str,
    id_requisicao: str,
    filename: str,
    subdir: str = "datasets",
) -> str:
    """Salva DataFrame em Parquet; retorna path absoluto do arquivo."""
    base_dir = ensure_artifact_dir(usuario, id_requisicao, subdir)
    if not filename.endswith(".parquet"):
        filename = filename + ".parquet"
    filepath = os.path.join(base_dir, filename)
    df.to_parquet(filepath, index=False)
    return filepath


def load_dataframe(
    path: Union[str, Path],
    max_rows: Optional[int] = None,
    skip_rows: int = 0,
    use_env_limit: bool = True,
) -> pd.DataFrame:
    """
    Carrega dataset em DataFrame com suporte a múltiplos formatos, compactação e paginação.

    Formatos suportados:
    - Parquet (.parquet)
    - CSV (.csv, .csv.gz, .csv.bz2, .csv.xz, .csv.zip) — compactação auto-detectada
    - Excel (.xlsx, .xls)
    - JSON (.json, .jsonl, .json.gz)

    Args:
        path: Caminho do arquivo (local).
        max_rows: Máximo de linhas a carregar (paginação). None = todas.
        skip_rows: Linhas a pular no início (paginação, apenas CSV).
        use_env_limit: Se True, aplica ID_DATASET_MAX_ROWS quando max_rows for None.

    Returns:
        DataFrame carregado.
    """
    path = str(path).strip()
    if not path:
        raise ValueError("load_dataframe: path vazio")
    path_lower = path.lower()

    # Limite global opcional
    effective_max = max_rows
    if effective_max is None and use_env_limit and _ID_DATASET_MAX_ROWS_INT is not None:
        effective_max = _ID_DATASET_MAX_ROWS_INT

    # Parquet
    if path_lower.endswith(".parquet"):
        return _load_parquet(path, effective_max, skip_rows)

    # CSV (incl. .csv.gz, .csv.bz2, .csv.xz, .csv.zip — pandas infere compression)
    if any(path_lower.endswith(ext) for ext in (".csv", ".csv.gz", ".csv.bz2", ".csv.xz", ".tsv", ".tsv.gz")):
        return _load_csv(path, path_lower, effective_max, skip_rows)

    # ZIP com CSV dentro (ex.: arquivo.zip/dados.csv)
    if ".zip" in path_lower and "csv" in path_lower:
        return _load_csv(path, path_lower, effective_max, skip_rows)

    # Excel
    if path_lower.endswith((".xlsx", ".xls")):
        return _load_excel(path, effective_max, skip_rows)

    # JSON
    if path_lower.endswith((".json", ".jsonl", ".json.gz")):
        return _load_json(path, path_lower, effective_max, skip_rows)

    # Fallback: tratar como CSV (delimitador inferido)
    return _load_csv(path, path_lower, effective_max, skip_rows)


def _load_parquet(path: str, max_rows: Optional[int], skip_rows: int) -> pd.DataFrame:
    """Carrega Parquet com paginação via iteração em batches."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        df = pd.read_parquet(path)
        return _slice_df(df, max_rows, skip_rows)

    if max_rows is None and skip_rows == 0:
        return pd.read_parquet(path)

    pf = pq.ParquetFile(path)
    chunks: List[pd.DataFrame] = []
    rows_read = 0
    rows_skipped = 0
    limit = (max_rows + skip_rows) if max_rows is not None else None

    for batch in pf.iter_batches(batch_size=min(50000, limit or 50000)):
        df_batch = batch.to_pandas()
        n = len(df_batch)

        if skip_rows > 0:
            if rows_skipped + n <= skip_rows:
                rows_skipped += n
                continue
            start = skip_rows - rows_skipped
            df_batch = df_batch.iloc[start:]
            rows_skipped = skip_rows
            n = len(df_batch)

        if max_rows is not None:
            space_left = max_rows - rows_read
            if space_left <= 0:
                break
            if n > space_left:
                df_batch = df_batch.head(space_left)
            rows_read += len(df_batch)

        chunks.append(df_batch)
        if max_rows is not None and rows_read >= max_rows:
            break

    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)


def _load_csv(
    path: str, path_lower: str, max_rows: Optional[int], skip_rows: int
) -> pd.DataFrame:
    """Carrega CSV com compactação inferida e encoding robusto."""
    kw: Dict[str, Any] = {
        "compression": "infer",
        "on_bad_lines": "skip",
        "low_memory": False,
        "encoding_errors": "replace",
    }
    sep = "," if ".tsv" not in path_lower else "\t"
    kw["sep"] = sep

    if skip_rows > 0:
        kw["skiprows"] = range(1, skip_rows + 1)  # manter header (linha 0)
    if max_rows is not None:
        kw["nrows"] = max_rows

    try:
        return pd.read_csv(path, **kw)
    except UnicodeDecodeError:
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                kw["encoding"] = enc
                return pd.read_csv(path, **kw)
            except UnicodeDecodeError:
                continue
        kw["encoding"] = "utf-8"
        kw["encoding_errors"] = "replace"
        return pd.read_csv(path, **kw)


def _load_excel(path: str, max_rows: Optional[int], skip_rows: int) -> pd.DataFrame:
    """Carrega Excel (.xlsx, .xls). Requer openpyxl para .xlsx."""
    try:
        engine = "openpyxl" if path.lower().endswith(".xlsx") else None
        df = pd.read_excel(path, engine=engine)
        return _slice_df(df, max_rows, skip_rows)
    except ImportError as e:
        logger.warning("Excel requer openpyxl: pip install openpyxl. Fallback: %s", e)
        raise ValueError("Leitura de Excel requer openpyxl. Instale com: pip install openpyxl")


def _load_json(
    path: str, path_lower: str, max_rows: Optional[int], skip_rows: int
) -> pd.DataFrame:
    """Carrega JSON ou JSONL (lines=True para .jsonl)."""
    lines = path_lower.endswith(".jsonl") or path_lower.endswith(".jsonl.gz")
    try:
        if lines:
            df = pd.read_json(path, lines=True)
        else:
            df = pd.read_json(path)
            if not isinstance(df, pd.DataFrame):
                with open(path, encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                df = pd.json_normalize(data) if isinstance(data, list) else pd.DataFrame(data)
    except (ValueError, TypeError) as e:
        logger.debug("read_json direto falhou (%s), tentando json_normalize", e)
        with open(path, encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        df = pd.json_normalize(data) if isinstance(data, list) else pd.DataFrame([data])
    return _slice_df(df, max_rows, skip_rows)


def _slice_df(
    df: pd.DataFrame, max_rows: Optional[int], skip_rows: int
) -> pd.DataFrame:
    """Aplica skip_rows e max_rows a um DataFrame já carregado."""
    if skip_rows > 0 and len(df) > skip_rows:
        df = df.iloc[skip_rows:].reset_index(drop=True)
    if max_rows is not None and len(df) > max_rows:
        df = df.head(max_rows)
    return df


def get_model_path(usuario: str, id_requisicao: str, model_filename: str = "modelo") -> str:
    """Retorna caminho absoluto para salvar/carregar modelo (ex.: .pkl) no diretório de artefatos."""
    base_dir = ensure_artifact_dir(usuario or "default", id_requisicao, subdir="models")
    name = "".join(c for c in model_filename if c.isalnum() or c in "._-") or "modelo"
    if not name.endswith(".pkl"):
        name = name + ".pkl"
    return os.path.join(base_dir, name)


def ensure_model_dir(usuario: str, id_requisicao: str) -> str:
    """Cria diretório de modelos se não existir; retorna o caminho."""
    return ensure_artifact_dir(usuario or "default", id_requisicao, subdir="models")


def get_model_metadata_path(model_ref: str) -> str:
    """Dado path do modelo (com ou sem .pkl), retorna path do JSON de metadados."""
    base = model_ref.replace(".pkl", "")
    return base + "_metadata.json"


def save_model_metadata(model_ref: str, metadata: Dict[str, Any]) -> None:
    """Salva metadados do modelo (features, variavel_alvo, tipo) junto ao .pkl."""
    path = get_model_metadata_path(model_ref)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def load_model_metadata(model_ref: str) -> Optional[Dict[str, Any]]:
    """Carrega metadados do modelo se existirem."""
    path = get_model_metadata_path(model_ref)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _is_dataset_file(filename: str) -> bool:
    """Verifica se o arquivo é um dataset suportado (Parquet, CSV, Excel, JSON)."""
    fl = filename.lower()
    return any(fl.endswith(ext) for ext in (
        ".parquet", ".csv", ".csv.gz", ".csv.bz2", ".csv.xz", ".tsv", ".tsv.gz",
        ".xlsx", ".xls", ".json", ".jsonl", ".json.gz"
    ))


def list_dataset_refs(usuario: str, id_requisicao: str) -> List[str]:
    """Lista paths de datasets salvos para usuario/id_requisicao, do mais recente ao mais antigo."""
    base_dir = get_artifact_dir(usuario or "default", id_requisicao, subdir="datasets")
    if not os.path.isdir(base_dir):
        return []
    refs: List[str] = []
    for f in os.listdir(base_dir):
        if _is_dataset_file(f):
            path = os.path.join(base_dir, f)
            mtime = os.path.getmtime(path)
            refs.append((mtime, path))
    refs.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in refs]


def get_latest_dataset_ref(usuario: str, id_requisicao: str) -> Optional[str]:
    """Retorna o path do dataset mais recente para usuario/id_requisicao, ou None se não houver."""
    u = usuario or "default"
    refs = list_dataset_refs(u, id_requisicao)
    if refs:
        logger.debug("id_artifacts: get_latest_dataset_ref encontrou %d refs em id_req; retornando %s", len(refs), refs[0][:80] + "..." if len(refs[0]) > 80 else refs[0])
        return refs[0]
    logger.debug("id_artifacts: get_latest_dataset_ref sem refs em id_req=%s; tentando fallback por usuario=%s", id_requisicao, u)
    fallback = _get_latest_dataset_ref_by_usuario(u)
    if fallback:
        logger.info("id_artifacts: get_latest_dataset_ref fallback encontrou dataset para usuario=%s", u)
        return fallback
    # Fallback extra: tentar "default" quando usuario autenticado não tem datasets
    # (ex.: primeira requisição usou default, segunda veio com email)
    if u != "default":
        fallback_default = _get_latest_dataset_ref_by_usuario("default")
        if fallback_default:
            logger.info("id_artifacts: get_latest_dataset_ref fallback 'default' encontrou dataset (usuario=%s não tinha)", u)
            return fallback_default
    logger.warning("id_artifacts: get_latest_dataset_ref NENHUM dataset encontrado para usuario=%s, id_req=%s", u, id_requisicao)
    return None


def _get_latest_dataset_ref_by_usuario(usuario: str) -> Optional[str]:
    """Retorna o dataset mais recente do usuário, em qualquer id_requisicao."""
    user_dir = os.path.join(_BASE, "".join(c for c in usuario if c.isalnum() or c in "._-") or "default")
    if not os.path.isdir(user_dir):
        return None
    candidates: List[tuple] = []
    for req_dir in os.listdir(user_dir):
        req_path = os.path.join(user_dir, req_dir)
        if not os.path.isdir(req_path):
            continue
        ds_dir = os.path.join(req_path, "datasets")
        if not os.path.isdir(ds_dir):
            continue
        for f in os.listdir(ds_dir):
            if _is_dataset_file(f):
                path = os.path.join(ds_dir, f)
                mtime = os.path.getmtime(path)
                candidates.append((mtime, path))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def list_model_refs(usuario: str, id_requisicao: str) -> List[str]:
    """Lista paths (sem .pkl) de modelos salvos para usuario/id_requisicao (múltiplas versões)."""
    base_dir = ensure_model_dir(usuario or "default", id_requisicao)
    refs: List[str] = []
    if not os.path.isdir(base_dir):
        return []
    for f in os.listdir(base_dir):
        if f.endswith(".pkl"):
            refs.append(os.path.join(base_dir, f.replace(".pkl", "")))
    return sorted(refs)


def get_latest_model_ref(usuario: str, id_requisicao: str) -> Optional[str]:
    """Retorna o model_ref mais recente para usuario/id_requisicao, ou do usuário em qualquer id_requisicao."""
    u = usuario or "default"
    refs = list_model_refs(u, id_requisicao)
    if refs:
        logger.debug("id_artifacts: get_latest_model_ref encontrou %d refs; retornando %s", len(refs), refs[-1][:80] + "..." if len(refs[-1]) > 80 else refs[-1])
        return refs[-1]  # último por nome (modelo_v1, modelo_v2, etc.)
    fallback = _get_latest_model_ref_by_usuario(u)
    if fallback:
        logger.info("id_artifacts: get_latest_model_ref fallback encontrou modelo para usuario=%s", u)
        return fallback
    if u != "default":
        fallback_default = _get_latest_model_ref_by_usuario("default")
        if fallback_default:
            logger.info("id_artifacts: get_latest_model_ref fallback 'default' encontrou modelo (usuario=%s não tinha)", u)
            return fallback_default
    logger.warning("id_artifacts: get_latest_model_ref NENHUM modelo encontrado para usuario=%s, id_req=%s", u, id_requisicao)
    return None


def _get_latest_model_ref_by_usuario(usuario: str) -> Optional[str]:
    """Retorna o modelo mais recente do usuário, em qualquer id_requisicao."""
    user_dir = os.path.join(_BASE, "".join(c for c in usuario if c.isalnum() or c in "._-") or "default")
    if not os.path.isdir(user_dir):
        return None
    candidates: List[tuple] = []
    for req_dir in os.listdir(user_dir):
        req_path = os.path.join(user_dir, req_dir)
        if not os.path.isdir(req_path):
            continue
        models_dir = os.path.join(req_path, "models")
        if not os.path.isdir(models_dir):
            continue
        for f in os.listdir(models_dir):
            if f.endswith(".pkl"):
                path = os.path.join(models_dir, f.replace(".pkl", ""))
                pkl_path = path + ".pkl"
                if os.path.isfile(pkl_path):
                    mtime = os.path.getmtime(pkl_path)
                    candidates.append((mtime, path))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _agendamentos_path() -> str:
    return os.path.join(_BASE, "agendamentos_retreino.json")


def _agendamentos_lock_path() -> str:
    return _agendamentos_path() + ".lock"


def load_agendamentos() -> List[Dict[str, Any]]:
    """Carrega lista de agendamentos de retreino (com lock para evitar race conditions)."""
    path = _agendamentos_path()
    if not os.path.isfile(path):
        return []
    with FileLock(_agendamentos_lock_path(), timeout=10):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


def save_agendamento(ag: Dict[str, Any]) -> None:
    """Append um agendamento à lista e persiste (com lock para evitar race conditions)."""
    path = _agendamentos_path()
    with FileLock(_agendamentos_lock_path(), timeout=10):
        lista = []
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    lista = json.load(f)
            except Exception:
                pass
        lista.append(ag)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)


def pop_agendamento_por_id(agendamento_id: str) -> Optional[Dict[str, Any]]:
    """Remove e retorna o agendamento com o ID dado (com lock para evitar race conditions)."""
    path = _agendamentos_path()
    with FileLock(_agendamentos_lock_path(), timeout=10):
        lista = []
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    lista = json.load(f)
            except Exception:
                return None
        idx = next((i for i, item in enumerate(lista) if item.get("agendamento_id") == agendamento_id), None)
        if idx is not None:
            item = lista.pop(idx)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(lista, f, ensure_ascii=False, indent=2)
            return item
    return None


def get_next_model_version(usuario: str, id_requisicao: str, base_name: str = "modelo") -> str:
    """Retorna nome para próxima versão do modelo (modelo_v1, modelo_v2, ...)."""
    refs = list_model_refs(usuario, id_requisicao)
    prefix = base_name + "_v"
    vers = []
    for r in refs:
        name = os.path.basename(r)
        if name.startswith(prefix):
            try:
                n = int(name[len(prefix) :])
                vers.append(n)
            except ValueError:
                pass
    next_v = max(vers, default=0) + 1
    return f"{base_name}_v{next_v}"
