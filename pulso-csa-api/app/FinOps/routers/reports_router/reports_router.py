#━━━━━━━━━❮Relatórios PDF por área (PulsoCSA, Cloud IAC, FinOps, Inteligência de Dados)❯━━━━━━━
"""Endpoints para gerar e baixar relatório PDF das partes mais relevantes das conversas por área."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.entitlement.deps import require_valid_access
from services.chat_history_service import get_chat_history
from services.report_services.report_pdf_service import (
    build_report_pdf,
    REPORT_SERVICE_IDS,
)

router = APIRouter(prefix="/reports", tags=["Relatórios PDF"])


def _tenant_id(user: dict) -> str:
    return (user.get("_id") or user.get("email") or "").strip() or "anonymous"


async def _get_messages_for_area(tenant_id: str, area: str, session_id: Optional[str], limit: int):
    service_id = REPORT_SERVICE_IDS.get(area, "codigo")
    return await get_chat_history(
        tenant_id=tenant_id,
        service_id=service_id,
        session_id=session_id,
        limit=limit,
    )


@router.get("/pulsocsa", response_class=Response)
async def report_pulsocsa(
    session_id: Optional[str] = Query(None, description="Filtrar por sessão de chat"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de mensagens"),
    user: dict = Depends(require_valid_access),
):
    """Gera e retorna relatório PDF das conversas mais relevantes da área PulsoCSA (criação e correção de código)."""
    tenant_id = _tenant_id(user)
    messages = await _get_messages_for_area(tenant_id, "pulsocsa", session_id, limit)
    pdf_bytes = build_report_pdf("pulsocsa", messages)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="relatorio-pulsocsa.pdf"'},
    )


@router.get("/cloud-iac", response_class=Response)
async def report_cloud_iac(
    session_id: Optional[str] = Query(None, description="Filtrar por sessão de chat"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de mensagens"),
    user: dict = Depends(require_valid_access),
):
    """Gera e retorna relatório PDF das conversas mais relevantes da área Cloud IAC (infraestrutura)."""
    tenant_id = _tenant_id(user)
    messages = await _get_messages_for_area(tenant_id, "cloud-iac", session_id, limit)
    pdf_bytes = build_report_pdf("cloud-iac", messages)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="relatorio-cloud-iac.pdf"'},
    )


@router.get("/finops", response_class=Response)
async def report_finops(
    session_id: Optional[str] = Query(None, description="Filtrar por sessão de chat"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de mensagens"),
    user: dict = Depends(require_valid_access),
):
    """Gera e retorna relatório PDF das conversas mais relevantes da área FinOps."""
    tenant_id = _tenant_id(user)
    messages = await _get_messages_for_area(tenant_id, "finops", session_id, limit)
    pdf_bytes = build_report_pdf("finops", messages)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="relatorio-finops.pdf"'},
    )


@router.get("/inteligencia-dados", response_class=Response)
async def report_inteligencia_dados(
    session_id: Optional[str] = Query(None, description="Filtrar por sessão de chat"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de mensagens"),
    user: dict = Depends(require_valid_access),
):
    """Gera e retorna relatório PDF das conversas mais relevantes da área Inteligência de Dados."""
    tenant_id = _tenant_id(user)
    messages = await _get_messages_for_area(tenant_id, "inteligencia-dados", session_id, limit)
    pdf_bytes = build_report_pdf("inteligencia-dados", messages)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="relatorio-inteligencia-dados.pdf"'},
    )
