#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from datetime import datetime
# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection  # ✅ Usa o core central
except ImportError:
    from app.storage.database.database_core import get_collection  # ✅ Usa o core central

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Conexão MongoDB (Camada 2 - Arquitetura)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# ✅ Obtém coleção diretamente via core central (mantém consistência com C1 e C3)
collection = get_collection("architecture")

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Funções de Persistência❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def upsert_blueprint(id_requisicao: str, blueprint_data: dict, root_path: str = None):
    """Insere ou atualiza blueprint (estrutura de arquivos)."""
    collection.update_one(
        {"id_requisicao": id_requisicao},
        {
            "$set": {
                "camada": "architecture",
                "id_requisicao": id_requisicao,
                "estrutura_arquivos": blueprint_data,
                "root_path": root_path,  # ✅ Campo opcional
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )


def upsert_backend_doc(id_requisicao: str, backend_data: dict):
    """Insere ou atualiza documento de backend."""
    collection.update_one(
        {"id_requisicao": id_requisicao},
        {"$set": {"backend_doc": backend_data, "updated_at": datetime.utcnow()}},
        upsert=True,
    )


def upsert_infra_doc(id_requisicao: str, infra_data: dict):
    """Insere ou atualiza documento de infraestrutura."""
    collection.update_one(
        {"id_requisicao": id_requisicao},
        {"$set": {"infra_doc": infra_data, "updated_at": datetime.utcnow()}},
        upsert=True,
    )


def upsert_security_code(id_requisicao: str, security_data: dict):
    """Insere ou atualiza análise de segurança de código."""
    collection.update_one(
        {"id_requisicao": id_requisicao},
        {
            "$push": {
                "security_code_reports": {
                    "timestamp": datetime.utcnow(),
                    "report": security_data,
                }
            }
        },
        upsert=True,
    )


def upsert_security_infra(id_requisicao: str, security_data: dict):
    """Insere ou atualiza análise de segurança de infraestrutura."""
    collection.update_one(
        {"id_requisicao": id_requisicao},
        {
            "$push": {
                "security_infra_reports": {
                    "timestamp": datetime.utcnow(),
                    "report": security_data,
                }
            }
        },
        upsert=True,
    )


def get_architecture_doc(id_requisicao: str) -> dict | None:
    """Retorna documento da arquitetura por id_requisicao (backend_doc, infra_doc, estrutura_arquivos)."""
    doc = collection.find_one({"id_requisicao": id_requisicao})
    return doc
