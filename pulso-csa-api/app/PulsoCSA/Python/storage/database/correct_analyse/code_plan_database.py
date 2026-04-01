#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Database – Code Plan Layer❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Optional, Dict, Any, List

# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection, timestamp
except ImportError:
    from app.storage.database.database_core import get_collection, timestamp
from utils.log_manager import add_log


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Coleção MongoDB❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

_collection = get_collection("code_plan")


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Salvar / Atualizar❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def save_code_plan(
    id_requisicao: str,
    request_obj: Dict[str, Any],
    analysis_obj: Dict[str, Any],
) -> bool:
    """
    Upsert completo (substitui ou cria) de um plano de código.
    """

    doc = {
        "id_requisicao": id_requisicao,
        "timestamp": timestamp(),
        "request": request_obj,
        "analysis": analysis_obj,
    }

    try:
        _collection.update_one(
            {"id_requisicao": id_requisicao},
            {"$set": doc},
            upsert=True,
        )
        add_log("info", f"[code_plan] Saved record for {id_requisicao}", "code_plan_db")
        return True

    except Exception as e:
        add_log("error", f"[code_plan] Failed to save record for {id_requisicao}: {e}", "code_plan_db")
        return False


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Buscar por ID❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def get_code_plan(id_requisicao: str) -> Optional[Dict[str, Any]]:
    """
    Retorna um documento completo do plano de código pelo id_requisicao.
    """
    try:
        result = _collection.find_one({"id_requisicao": id_requisicao})
        if result:
            result.pop("_id", None)
        return result
    except Exception as e:
        add_log("error", f"[code_plan] Failed to fetch {id_requisicao}: {e}", "code_plan_db")
        return None


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Listar Registros (Opcionalmente Filtrado)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def list_code_plans(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Lista até 'limit' registros ordenados pelo timestamp desc.
    """
    try:
        cursor = _collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return list(cursor)
    except Exception as e:
        add_log("error", f"[code_plan] Failed to list records: {e}", "code_plan_db")
        return []


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Remover❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def delete_code_plan(id_requisicao: str) -> bool:
    """
    Remove um registro.
    """
    try:
        res = _collection.delete_one({"id_requisicao": id_requisicao})
        return res.deleted_count > 0
    except Exception as e:
        add_log("error", f"[code_plan] Failed to delete {id_requisicao}: {e}", "code_plan_db")
        return False
