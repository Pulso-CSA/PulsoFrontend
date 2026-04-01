#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Database – Code Writer Layer❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Any, Dict, List, Optional

# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection, timestamp
except ImportError:
    from app.storage.database.database_core import get_collection, timestamp
from utils.log_manager import add_log

# NOTE:
# We are reusing the same physical collection used by "code_plan".
# Documents are tagged with doc_type = "code_writer" to avoid mixing concerns.
_collection = get_collection("code_plan")


def save_code_writer_result(id_requisicao: str, result_payload: Dict[str, Any]) -> bool:
    """
    Upsert a Code Writer execution result.
    Documents are tagged with doc_type = "code_writer".
    """
    doc = {
        "doc_type": "code_writer",
        "id_requisicao": id_requisicao,
        "timestamp": timestamp(),
        "result": result_payload,
    }

    try:
        _collection.update_one(
            {"id_requisicao": id_requisicao, "doc_type": "code_writer"},
            {"$set": doc},
            upsert=True,
        )
        add_log("info", f"[code_writer_db] Saved result for {id_requisicao}", "code_writer_db")
        return True
    except Exception as exc:
        add_log("error", f"[code_writer_db] Failed to save result for {id_requisicao}: {exc}", "code_writer_db")
        return False


def get_code_writer_result(id_requisicao: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a Code Writer result by id_requisicao.
    """
    try:
        doc = _collection.find_one(
            {"id_requisicao": id_requisicao, "doc_type": "code_writer"}
        )
        if doc:
            doc.pop("_id", None)
        return doc
    except Exception as exc:
        add_log("error", f"[code_writer_db] Failed to fetch {id_requisicao}: {exc}", "code_writer_db")
        return None


def list_code_writer_results(limit: int = 50) -> List[Dict[str, Any]]:
    """
    List recent Code Writer results (ordered by timestamp desc).
    """
    try:
        cursor = (
            _collection.find(
                {"doc_type": "code_writer"},
                {"_id": 0},
            )
            .sort("timestamp", -1)
            .limit(limit)
        )
        return list(cursor)
    except Exception as exc:
        add_log("error", f"[code_writer_db] Failed to list results: {exc}", "code_writer_db")
        return []


def delete_code_writer_result(id_requisicao: str) -> bool:
    """
    Delete a Code Writer result.
    """
    try:
        res = _collection.delete_one(
            {"id_requisicao": id_requisicao, "doc_type": "code_writer"}
        )
        return res.deleted_count > 0
    except Exception as exc:
        add_log("error", f"[code_writer_db] Failed to delete {id_requisicao}: {exc}", "code_writer_db")
        return False
