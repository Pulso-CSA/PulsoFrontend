# Artefatos do subsistema ID (datasets, modelos)
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import (
    get_artifact_dir,
    load_dataframe,
    save_dataframe,
    ensure_artifact_dir,
)

__all__ = [
    "get_artifact_dir",
    "load_dataframe",
    "save_dataframe",
    "ensure_artifact_dir",
]
