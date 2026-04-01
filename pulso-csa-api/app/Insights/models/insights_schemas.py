from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from Insights.core.constants import SUPPORTED_CHART_TYPES, SUPPORTED_SERVICES

ChartTypeLiteral = Literal["line", "bar", "pie", "area", "kpi_card"]
ServiceLiteral = Literal["pulso_csa", "cloud_iac", "finops", "dados_ia"]
InsightStatusLiteral = Literal["success", "ambiguity", "degraded"]


class DataPointPayload(BaseModel):
    """Ponto único para séries temporais ou categóricas (frontend mapeia para eixos)."""

    label: str
    value: float


class ChartSeriesPayload(BaseModel):
    name: str
    points: List[DataPointPayload] = Field(default_factory=list)


class KPIPayload(BaseModel):
    """Métrica agregada para cartão KPI (sem instruções de renderização visual)."""

    value: float
    target: Optional[float] = None
    unit: str = ""
    delta_percent: Optional[float] = None
    label: str = ""


class AmbiguityPayload(BaseModel):
    message: str
    suggested_prompts: List[str] = Field(default_factory=list)
    valid_options: List[Dict[str, Any]] = Field(default_factory=list)


class InsightQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4096)
    session_id: Optional[str] = Field(default=None, max_length=64)
    id_requisicao: Optional[str] = Field(default=None, max_length=128)
    locale: str = Field(default="pt-BR", max_length=32)


class InsightQueryResponse(BaseModel):
    insight_id: str
    session_id: str
    status: InsightStatusLiteral = "success"
    chart_type: ChartTypeLiteral
    title: str
    description: str
    labels: Optional[List[str]] = None
    series: List[ChartSeriesPayload] = Field(default_factory=list)
    kpi: Optional[KPIPayload] = None
    aggregated_metrics: Dict[str, float] = Field(default_factory=dict)
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ambiguity: Optional[AmbiguityPayload] = None


class InsightSessionCreateBody(BaseModel):
    title: Optional[str] = Field(default=None, max_length=256)


class InsightSessionCreateResponse(BaseModel):
    session_id: str
    created_at: str


class InsightSessionDetail(BaseModel):
    session_id: str
    tenant_id: str
    created_at: str
    updated_at: str
    title: Optional[str] = None
    last_prompt_preview: Optional[str] = None
    insight_count: int = 0
    prompt_count: int = 0


class CatalogChartTypeInfo(BaseModel):
    id: str
    label: str
    description: str


class CatalogServiceInfo(BaseModel):
    id: str
    label: str
    description: str


class CatalogResponse(BaseModel):
    chart_types: List[CatalogChartTypeInfo]
    services: List[CatalogServiceInfo]
    capabilities: List[str]
    example_prompts: List[str]
    version: str = "1.0.0"


def validate_chart_type(v: str) -> str:
    t = (v or "").strip().lower()
    if t in SUPPORTED_CHART_TYPES:
        return t
    if t == "progress":
        return "kpi_card"
    raise ValueError(f"chart_type inválido: {v}")


def validate_services_list(services: List[str]) -> List[str]:
    out: List[str] = []
    for s in services:
        x = (s or "").strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "pulso": "pulso_csa",
            "pulsocsa": "pulso_csa",
            "cloud": "cloud_iac",
            "iac": "cloud_iac",
            "terraform": "cloud_iac",
            "inteligencia": "dados_ia",
            "inteligencia_dados": "dados_ia",
            "dados": "dados_ia",
        }
        x = aliases.get(x, x)
        if x in SUPPORTED_SERVICES and x not in out:
            out.append(x)
    return out
