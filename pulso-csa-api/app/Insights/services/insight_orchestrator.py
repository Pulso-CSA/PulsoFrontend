import re
import uuid
from typing import Any, Dict, List

from app.utils.log_manager import add_log

from Insights.agents.intent_agent import classify_intent_with_ollama
from Insights.models.insights_schemas import (
    AmbiguityPayload,
    InsightQueryRequest,
    InsightQueryResponse,
)
from Insights.services.data_providers import build_chart_payload
from Insights.services.fallback_intent_service import (
    ambiguity_suggestions,
    merge_intent,
    normalize_prompt_text,
)
from Insights.storage.insights_repository import InsightsRepository

SOURCE = "insights_orchestrator"


def _is_vague_prompt(prompt: str) -> bool:
    t = normalize_prompt_text(prompt)
    if len(t) < 6:
        return True
    if not re.search(r"[a-záàâãéèêíïóôõöúçñ]{3,}", t, re.IGNORECASE):
        return True
    return False


def _response_model_dump(resp: InsightQueryResponse) -> Dict[str, Any]:
    return resp.model_dump(mode="json")


class InsightOrchestrator:
    def __init__(self, repo: InsightsRepository | None = None) -> None:
        self._repo = repo or InsightsRepository()

    def _tenant(self, user: dict) -> str:
        return str(user.get("_id") or user.get("email") or user.get("sub") or "anonymous")

    def run_query(self, body: InsightQueryRequest, user: dict) -> InsightQueryResponse:
        tenant_id = self._tenant(user)
        prompt_raw = body.prompt
        prompt = normalize_prompt_text(prompt_raw)

        if _is_vague_prompt(prompt):
            amb = ambiguity_suggestions(prompt_raw)
            session_id = body.session_id or self._repo.create_session(tenant_id)["session_id"]
            return InsightQueryResponse(
                insight_id=str(uuid.uuid4().hex),
                session_id=session_id,
                status="ambiguity",
                chart_type="bar",
                title="Pedido ambíguo",
                description=amb["message"],
                series=[],
                metadata={"intent_source": "guardrail", "services_targeted": []},
                ambiguity=AmbiguityPayload(
                    message=amb["message"],
                    suggested_prompts=amb["suggested_prompts"],
                    valid_options=amb["valid_options"],
                ),
            )

        session_id = body.session_id
        if not session_id:
            session_id = self._repo.create_session(tenant_id)["session_id"]
        elif not self._repo.get_session(session_id, tenant_id):
            session_id = self._repo.create_session(tenant_id)["session_id"]

        llm_raw = classify_intent_with_ollama(prompt)
        intent, source = merge_intent(llm_raw, prompt)

        add_log(
            "info",
            f"Insights intent source={source} chart={intent.get('chart_type')} svcs={intent.get('services')}",
            SOURCE,
        )

        prompt_id = self._repo.insert_prompt(
            tenant_id=tenant_id,
            session_id=session_id,
            prompt_text=prompt,
            id_requisicao=body.id_requisicao,
            intent_snapshot={"raw_llm": llm_raw, "merged": intent, "source": source},
        )

        chart_type = str(intent.get("chart_type", "line"))
        services: List[str] = list(intent.get("services") or ["finops"])
        metric_key = str(intent.get("metric_key", "weekly_cost_evolution"))
        comparison = bool(intent.get("comparison", False))
        title_hint = str(intent.get("title_hint") or prompt[:80])

        series, labels, kpi, agg, desc = build_chart_payload(
            prompt=prompt,
            chart_type=chart_type,
            services=services,
            metric_key=metric_key,
            comparison=comparison,
            title_hint=title_hint,
        )

        confidence = float(intent.get("confidence", 0.5))
        status: Any = "success"
        ambiguity: AmbiguityPayload | None = None

        if source == "hybrid_low_confidence" and confidence < 0.42:
            status = "degraded"
            amb = ambiguity_suggestions(prompt)
            ambiguity = AmbiguityPayload(
                message="A interpretação automática teve baixa confiança; exibimos o melhor palpite com dados de referência.",
                suggested_prompts=amb["suggested_prompts"][:3],
                valid_options=amb["valid_options"][:3],
            )

        title = title_hint[:140]
        filters_applied: Dict[str, Any] = {
            "services": services,
            "metric_key": metric_key,
            "time_grain": intent.get("time_grain"),
            "locale": body.locale,
        }
        if body.id_requisicao:
            filters_applied["id_requisicao"] = body.id_requisicao

        insight_id = uuid.uuid4().hex

        resp = InsightQueryResponse(
            insight_id=insight_id,
            session_id=session_id,
            status=status,
            chart_type=chart_type,  # type: ignore[arg-type]
            title=title,
            description=desc,
            labels=labels or None,
            series=series,
            kpi=kpi,
            aggregated_metrics=agg,
            filters_applied=filters_applied,
            metadata={
                "intent_source": source,
                "confidence": confidence,
                "services_targeted": services,
                "metric_key": metric_key,
                "comparison": comparison,
                "prompt_id": prompt_id,
            },
            ambiguity=ambiguity,
        )

        self._repo.insert_insight_artifact(
            tenant_id=tenant_id,
            session_id=session_id,
            prompt_id=prompt_id,
            payload=_response_model_dump(resp),
        )
        return resp
