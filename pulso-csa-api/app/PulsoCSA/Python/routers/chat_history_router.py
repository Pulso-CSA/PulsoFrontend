#━━━━━━━━━❮Histórico de Chats por Módulo❯━━━━━━━━━
"""Endpoints para listar/retomar histórico de chats. Cada session = um chat isolado."""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from core.entitlement.deps import require_valid_access
from services.chat_history_service import create_session, get_chat_history, get_sessions

router = APIRouter(prefix="/chat-history", tags=["Histórico de Chats"])


@router.post("/{service_id}/sessions")
async def create_session_endpoint(
    service_id: str,
    user: dict = Depends(require_valid_access),
):
    """Cria um novo chat (session). Retorna session_id para usar como id_requisicao nas mensagens."""
    tenant_id = user.get("_id") or user.get("email") or ""
    session_id = await create_session(tenant_id=tenant_id, service_id=service_id)
    return {"service_id": service_id, "session_id": session_id}


@router.get("/{service_id}/sessions")
async def list_sessions_endpoint(
    service_id: str,
    limit: int = Query(default=50, le=100),
    user: dict = Depends(require_valid_access),
):
    """Lista chats do usuário. Cada session = um chat com histórico isolado."""
    tenant_id = user.get("_id") or user.get("email") or ""
    sessions = await get_sessions(tenant_id=tenant_id, service_id=service_id, limit=limit)
    return {"service_id": service_id, "sessions": sessions}


@router.get("/{service_id}/messages")
async def list_messages_endpoint(
    service_id: str,
    session_id: Optional[str] = Query(None),
    limit: int = Query(default=100, le=200),
    user: dict = Depends(require_valid_access),
):
    """Lista mensagens do histórico por módulo (e opcionalmente por session)."""
    tenant_id = user.get("_id") or user.get("email") or ""
    messages = await get_chat_history(
        tenant_id=tenant_id,
        service_id=service_id,
        session_id=session_id,
        limit=limit,
    )
    return {"service_id": service_id, "session_id": session_id, "messages": messages}
