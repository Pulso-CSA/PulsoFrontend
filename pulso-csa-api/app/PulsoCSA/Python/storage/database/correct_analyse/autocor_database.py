#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Auto-Correção – Banco de Dados❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, Any
# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection, timestamp
except ImportError:
    from app.storage.database.database_core import get_collection, timestamp

COLL = get_collection("auto_cor_arq")

def save_autocor_snapshot(id_requisicao: str, payload: Dict[str, Any]):
    doc = {
        "id_requisicao": id_requisicao,
        "timestamp": timestamp(),
        "snapshot": payload,
    }
    COLL.update_one(
        {"id_requisicao": id_requisicao},
        {"$set": doc},
        upsert=True
    )
    return True
