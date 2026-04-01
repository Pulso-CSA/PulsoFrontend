#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Finance Service❯━━━━━━━━━
# Lógica de negócio SFAP (sem Streamlit); dados em MongoDB Financeiro
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Any, Dict, List, Optional

from app.InteligenciaDados.storage.database.finance.database_finance import (
    list_planos as db_list_planos,
    insert_plano as db_insert_plano,
    update_plano as db_update_plano,
    delete_plano as db_delete_plano,
    list_movimentos as db_list_movimentos,
    insert_movimento as db_insert_movimento,
    update_movimento as db_update_movimento,
    delete_movimento as db_delete_movimento,
    get_dashboard_totals as db_get_dashboard_totals,
)


async def list_planos_service(filtro_tipo: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    return await db_list_planos(filtro_tipo=filtro_tipo)


async def create_plano_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await db_insert_plano(payload)


async def update_plano_service(plano_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return await db_update_plano(plano_id, payload)


async def delete_plano_service(plano_id: str) -> bool:
    return await db_delete_plano(plano_id)


async def list_movimentos_service(
    tipo: Optional[str] = None,
    categoria: Optional[List[str]] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return await db_list_movimentos(tipo=tipo, categoria=categoria, data_inicio=data_inicio, data_fim=data_fim)


async def create_movimento_service(payload: Dict[str, Any]) -> Dict[str, Any]:
    return await db_insert_movimento(payload)


async def update_movimento_service(movimento_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return await db_update_movimento(movimento_id, payload)


async def delete_movimento_service(movimento_id: str) -> bool:
    return await db_delete_movimento(movimento_id)


async def dashboard_service() -> Dict[str, Any]:
    return await db_get_dashboard_totals()
