"""
Orquestração explícita da feature Insights (entrada → intent → dados → persistência → saída).
Mantém routers finos e facilita testes futuros.
"""
from typing import Any, Dict

from Insights.models.insights_schemas import InsightQueryRequest, InsightQueryResponse
from Insights.services.insight_orchestrator import InsightOrchestrator

_orchestrator = InsightOrchestrator()


def run_insight_query(body: InsightQueryRequest, user: dict) -> InsightQueryResponse:
    return _orchestrator.run_query(body, user)


def get_orchestrator() -> InsightOrchestrator:
    return _orchestrator
