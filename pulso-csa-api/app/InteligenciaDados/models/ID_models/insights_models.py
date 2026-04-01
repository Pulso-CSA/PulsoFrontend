from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class InsightChartPoint(BaseModel):
    label: str
    value: float


class InsightWidget(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str
    title: str
    value: str
    trend: str = Field(default="+0%")
    period: str = Field(default="Agora")
    chart_type: Literal["area", "bar", "line", "pie", "progress"] = Field(default="bar")
    progress_percent: Optional[float] = None
    insights: List[str] = Field(default_factory=list)
    service_filter: Optional[Literal["pulso", "cloud", "finops", "data", "custom"]] = "data"
    custom_prompt: Optional[str] = None
    analysis_summary: Optional[str] = None
    technical_conclusion: Optional[str] = None
    data: Optional[List[InsightChartPoint]] = None


class InsightGenerateInput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    prompt: str = Field(..., min_length=1, max_length=2048)
    id_requisicao: str = Field(..., min_length=1, max_length=128)
    dataset_ref: Optional[str] = Field(default=None, max_length=2048)
    service_filter: Optional[Literal["pulso", "cloud", "finops", "data", "custom"]] = "data"


class InsightGenerateOutput(BaseModel):
    id_requisicao: str
    dataset_ref: Optional[str] = None
    widget: InsightWidget


class InsightWidgetsOutput(BaseModel):
    widgets: List[InsightWidget] = Field(default_factory=list)
