#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Database Layer – Execution❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection
except ImportError:
    from app.storage.database.database_core import get_collection

collection = get_collection("execution")  # Camada 3

def upsert_execution_manifest(id_requisicao: str, manifest: dict):
    """Insere ou atualiza o manifesto da estrutura física."""
    collection.update_one(
        {"id_requisicao": id_requisicao},
        {"$set": {"structure_manifest": manifest}},
        upsert=True
    )

def upsert_code_manifest(id_requisicao: str, manifest: dict):
    """Insere ou atualiza o manifesto da geração de código."""
    collection.update_one(
        {"id_requisicao": id_requisicao},
        {"$set": {"code_manifest": manifest}},
        upsert=True
    )

