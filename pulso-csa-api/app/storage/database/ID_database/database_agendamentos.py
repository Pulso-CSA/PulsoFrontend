#━━━━━━━━━❮Database Agendamentos Retreino❯━━━━━━━━━
# Estrutura mínima para agendamentos em MongoDB (substitui arquivo JSON).
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.storage.database.database_core import get_collection

agendamentos_collection = get_collection("id_agendamentos")

# Índice único em agendamento_id
try:
    agendamentos_collection.create_index("agendamento_id", unique=True)
except Exception:
    pass

# Índice composto para queries eficientes
try:
    agendamentos_collection.create_index([("usuario", 1), ("created_at", -1)])
except Exception:
    pass


async def salvar_agendamento(agendamento: Dict[str, Any]) -> None:
    """Salva agendamento no MongoDB."""
    agendamento["created_at"] = datetime.utcnow()
    agendamento["executado"] = False
    agendamentos_collection.insert_one(agendamento)


async def buscar_agendamento_por_id(agendamento_id: str) -> Optional[Dict[str, Any]]:
    """Busca agendamento por ID."""
    doc = agendamentos_collection.find_one({"agendamento_id": agendamento_id, "executado": False})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def remover_agendamento_por_id(agendamento_id: str) -> Optional[Dict[str, Any]]:
    """Remove agendamento da fila (marca como executado)."""
    doc = agendamentos_collection.find_one_and_update(
        {"agendamento_id": agendamento_id, "executado": False},
        {"$set": {"executado": True, "executado_em": datetime.utcnow()}},
        return_document=True
    )
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def listar_agendamentos_pendentes(usuario: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista agendamentos pendentes (opcionalmente filtrado por usuario)."""
    query = {"executado": False}
    if usuario:
        query["usuario"] = usuario
    docs = list(agendamentos_collection.find(query).sort("created_at", 1))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs
