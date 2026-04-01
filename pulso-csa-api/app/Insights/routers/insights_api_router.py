from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.PulsoCSA.Python.core.entitlement.deps import require_valid_access
from app.utils.log_manager import add_log

from Insights.models.insights_schemas import (
    CatalogResponse,
    InsightQueryRequest,
    InsightQueryResponse,
    InsightSessionCreateBody,
    InsightSessionCreateResponse,
    InsightSessionDetail,
)
from Insights.services.insights_catalog import build_catalog_response
from Insights.storage.insights_repository import InsightsRepository
from Insights.workflow.insight_workflow import run_insight_query

SOURCE = "insights_router"

router = APIRouter(prefix="/insights/v1", tags=["Insights – Analytics conversacional"])
_repo = InsightsRepository()


@router.get("/catalog", response_model=CatalogResponse)
async def get_insights_catalog() -> CatalogResponse:
    """Catálogo público de tipos de gráfico, serviços, capacidades e exemplos de prompts."""
    return build_catalog_response()


@router.post("/query", response_model=InsightQueryResponse)
async def post_insight_query(
    body: InsightQueryRequest,
    user: dict = Depends(require_valid_access),
) -> InsightQueryResponse:
    """
    Interpreta linguagem natural, classifica intent (Ollama + fallback) e devolve dados estruturados para o frontend.
    """
    add_log("info", f"POST /insights/v1/query len={len(body.prompt)}", SOURCE)
    try:
        return run_insight_query(body, user)
    except Exception as e:
        add_log("error", f"Insights query falhou: {type(e).__name__}: {e}", SOURCE)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INSIGHTS_QUERY_FAILED", "message": "Falha ao processar o pedido de insight."},
        ) from e


@router.post("/sessions", response_model=InsightSessionCreateResponse)
async def create_insight_session(
    body: InsightSessionCreateBody = InsightSessionCreateBody(),
    user: dict = Depends(require_valid_access),
) -> InsightSessionCreateResponse:
    """Cria sessão vazia para agrupar prompts e artefatos."""
    tenant = str(user.get("_id") or user.get("email") or "anonymous")
    doc = _repo.create_session(tenant, title=body.title)
    return InsightSessionCreateResponse(session_id=doc["session_id"], created_at=doc["created_at"])


@router.get("/sessions", response_model=List[InsightSessionDetail])
async def list_insight_sessions(
    user: dict = Depends(require_valid_access),
    limit: int = 30,
) -> List[InsightSessionDetail]:
    tenant = str(user.get("_id") or user.get("email") or "anonymous")
    rows = _repo.list_sessions(tenant, limit=limit)
    out: List[InsightSessionDetail] = []
    for r in rows:
        sid = r.get("session_id")
        if not sid:
            continue
        prompts = _repo.list_prompts_for_session(sid, tenant, limit=200)
        arts = _repo.list_insights_for_session(sid, tenant, limit=200)
        last_p = prompts[0].get("prompt_text") if prompts else None
        out.append(
            InsightSessionDetail(
                session_id=sid,
                tenant_id=tenant,
                created_at=r.get("created_at", ""),
                updated_at=r.get("updated_at", ""),
                title=r.get("title"),
                last_prompt_preview=(last_p[:120] + "…") if last_p and len(last_p) > 120 else last_p,
                insight_count=len(arts),
                prompt_count=len(prompts),
            )
        )
    return out


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_insight_session(
    session_id: str,
    user: dict = Depends(require_valid_access),
) -> Dict[str, Any]:
    tenant = str(user.get("_id") or user.get("email") or "anonymous")
    doc = _repo.get_session(session_id, tenant)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND", "message": "Sessão não encontrada."})
    doc.pop("_id", None)
    return doc


@router.get("/sessions/{session_id}/prompts", response_model=List[Dict[str, Any]])
async def list_session_prompts(
    session_id: str,
    user: dict = Depends(require_valid_access),
    limit: int = 50,
) -> List[Dict[str, Any]]:
    tenant = str(user.get("_id") or user.get("email") or "anonymous")
    if not _repo.get_session(session_id, tenant):
        raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND", "message": "Sessão não encontrada."})
    rows = _repo.list_prompts_for_session(session_id, tenant, limit=limit)
    for r in rows:
        r.pop("_id", None)
    return rows


@router.get("/sessions/{session_id}/artifacts", response_model=List[Dict[str, Any]])
async def list_session_artifacts(
    session_id: str,
    user: dict = Depends(require_valid_access),
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Histórico de insights/gráficos gerados na sessão (payload completo por item)."""
    tenant = str(user.get("_id") or user.get("email") or "anonymous")
    if not _repo.get_session(session_id, tenant):
        raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND", "message": "Sessão não encontrada."})
    rows = _repo.list_insights_for_session(session_id, tenant, limit=limit)
    for r in rows:
        r.pop("_id", None)
    return rows
