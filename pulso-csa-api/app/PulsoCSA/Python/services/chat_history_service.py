#━━━━━━━━━❮Chat History Service❯━━━━━━━━━
"""Serviço para persistir e recuperar histórico de chats por módulo. Cada session = um chat isolado."""
import time
import uuid
from typing import List, Optional

# chat_history está em api/app/storage/database/chat_history/ (compartilhado)
try:
    from storage.database.chat_history.database_chat_history import (
        save_chat_message,
        list_chat_history,
        list_sessions,
    )
except ImportError:
    from app.storage.database.chat_history.database_chat_history import (
        save_chat_message,
        list_chat_history,
        list_sessions,
    )


async def create_session(tenant_id: str, service_id: str) -> str:
    """Cria um novo chat (session). Retorna session_id para usar como id_requisicao."""
    return f"id-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"


async def persist_chat(
    tenant_id: str,
    usuario_id: str,
    service_id: str,
    session_id: str,
    mensagem_user: str,
    mensagem_assistant: str,
    dataset_ref: Optional[str] = None,
    model_ref: Optional[str] = None,
) -> None:
    """Persiste uma troca de mensagens no histórico. Cada session_id = um chat isolado."""
    await save_chat_message(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        service_id=service_id,
        session_id=session_id,
        mensagem_user=mensagem_user,
        mensagem_assistant=mensagem_assistant,
        dataset_ref=dataset_ref,
        model_ref=model_ref,
    )


async def get_chat_history(
    tenant_id: str,
    service_id: str,
    session_id: Optional[str] = None,
    limit: int = 100,
) -> List[dict]:
    """Retorna histórico de chat para o tenant + módulo."""
    return await list_chat_history(
        tenant_id=tenant_id,
        service_id=service_id,
        session_id=session_id,
        limit=limit,
    )


async def get_sessions(
    tenant_id: str,
    service_id: str,
    limit: int = 50,
) -> List[str]:
    """Retorna lista de session_ids do tenant para o módulo."""
    return await list_sessions(
        tenant_id=tenant_id,
        service_id=service_id,
        limit=limit,
    )
