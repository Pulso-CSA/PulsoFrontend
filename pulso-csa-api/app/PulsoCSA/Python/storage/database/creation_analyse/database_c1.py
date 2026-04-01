#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Camada 1 – Governança❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from datetime import datetime
from typing import Dict, Any
# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection, timestamp
except ImportError:
    from app.storage.database.database_core import get_collection, timestamp

  
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Input❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def upsert_input(id_requisicao: str, input_doc: Dict[str, Any]) -> None:
    """
    Insere ou atualiza documento de input na governance_layer.
    profileId e userId são definidos no insert para satisfazer o índice único
    (profileId_1_userId_1); evitam E11000 duplicate key com (null, null).
    """
    coll = get_collection()
    # Índice único (profileId, userId): usar valores que evitem (null, null) e duplicatas
    profile_id = id_requisicao
    user_id = input_doc.get("id_requisicao") or input_doc.get("usuario") or id_requisicao
    coll.update_one(
        {"id_requisicao": id_requisicao},
        {
            "$setOnInsert": {
                "id_requisicao": id_requisicao,
                "camada": "governance",
                "created_at": timestamp(),
                "refinamentos": [],
                "validacoes": [],
                "workflow_status": "iniciado",
                "profileId": profile_id,
                "userId": user_id,
            },
            "$set": {
                "input": input_doc,
                "root_path": input_doc.get("root_path"),
                "updated_at": timestamp()
            }
        },
        upsert=True
    )

  
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Controle de Versões❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def get_next_refine_version(id_requisicao: str) -> str:
    coll = get_collection()
    doc = coll.find_one({"id_requisicao": id_requisicao}, {"refinamentos": 1})
    count = len(doc.get("refinamentos", [])) if doc else 0
    return f"v{count + 1}"

  
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Refino❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def append_refinement(id_requisicao: str, refinement: Dict[str, Any]) -> None:
    coll = get_collection()
    coll.update_one(
        {"id_requisicao": id_requisicao},
        {"$push": {"refinamentos": refinement}, "$set": {"updated_at": timestamp()}},
        upsert=True
    )

  
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Validação❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def append_validation(id_requisicao: str, validation: Dict[str, Any]) -> None:
    coll = get_collection()
    set_fields = {"updated_at": timestamp()}
    if validation.get("validation_status") == "aprovado":
        set_fields["workflow_status"] = "validado"

    coll.update_one(
        {"id_requisicao": id_requisicao},
        {"$push": {"validacoes": validation}, "$set": set_fields},
        upsert=True
    )

  
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Prompt refinado❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def get_refined_prompt(id_requisicao: str) -> str:
    coll = get_collection()
    doc = coll.find_one({"id_requisicao": id_requisicao}, {"refinamentos": 1})
    if not doc or not doc.get("refinamentos"):
        return ""
    ultimo = doc["refinamentos"][-1]
    return ultimo.get("prompt_refinado") or ultimo.get("refined_prompt", "")


def get_original_prompt(id_requisicao: str) -> str:
    """Retorna o prompt original (antes do refino) para uso em fast path."""
    coll = get_collection()
    doc = coll.find_one({"id_requisicao": id_requisicao}, {"input": 1})
    if not doc or not doc.get("input"):
        return ""
    return (doc.get("input") or {}).get("prompt", "")
