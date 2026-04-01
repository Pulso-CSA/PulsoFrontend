"""
Fornecedores de dados analíticos por serviço (v1: séries sintéticas determinísticas).

Substituição futura: conectar FinOps connectors, Mongo PulsoCSA, CloudIAC analyze cache, pipelines ID.
"""
import hashlib
from typing import Any, Dict, List, Tuple

from Insights.core.constants import SERVICE_LABELS
from Insights.models.insights_schemas import ChartSeriesPayload, DataPointPayload, KPIPayload


def _seed(prompt: str, salt: str) -> int:
    h = hashlib.sha256(f"{salt}:{prompt}".encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _series_weekly_cost(prompt: str, label: str) -> ChartSeriesPayload:
    base = 800 + (_seed(prompt, "cost") % 400)
    points: List[DataPointPayload] = []
    for i in range(8):
        v = base + (i * 37) % 120 - 40 + (_seed(prompt, f"w{i}") % 25)
        points.append(DataPointPayload(label=f"Sem {i + 1}", value=float(v)))
    return ChartSeriesPayload(name=label, points=points)


def _series_conversions_by_service(prompt: str) -> List[ChartSeriesPayload]:
    names = ["API", "Web", "Mobile", "Batch", "Integrações"]
    pts = []
    for j, n in enumerate(names):
        v = 40 + (_seed(prompt, n) % 160) + j * 12
        pts.append(DataPointPayload(label=n, value=float(v)))
    return [ChartSeriesPayload(name="Conversões", points=pts)]


def _series_iac_mix(prompt: str) -> List[ChartSeriesPayload]:
    labels = ["AWS", "Azure", "GCP", "On-prem"]
    pts = [DataPointPayload(label=L, value=float(15 + (_seed(prompt, L) % 70))) for L in labels]
    return [ChartSeriesPayload(name="Estimativa de recursos (u.arb.)", points=pts)]


def _series_pulso_activity(prompt: str) -> List[ChartSeriesPayload]:
    labels = ["Governança", "Backend", "Infra", "Execução", "Testes"]
    pts = [DataPointPayload(label=L, value=float(20 + (_seed(prompt, L) % 80))) for L in labels]
    return [ChartSeriesPayload(name="Atividade por camada", points=pts)]


def _series_ml_metric(prompt: str) -> List[ChartSeriesPayload]:
    pts = []
    for i in range(10):
        pts.append(
            DataPointPayload(
                label=f"Epoca {i + 1}",
                value=float(0.55 + (i * 0.03) + (_seed(prompt, str(i)) % 10) / 100),
            )
        )
    return [ChartSeriesPayload(name="Acurácia (exemplo)", points=pts)]


def _kpi_savings_goal(prompt: str) -> Tuple[KPIPayload, Dict[str, float]]:
    target = 100_000.0
    value = 62_000.0 + float((_seed(prompt, "kpi") % 25_000))
    delta = round((value / target - 1) * 100, 2)
    kpi = KPIPayload(
        value=value,
        target=target,
        unit="BRL",
        delta_percent=delta,
        label="Economia acumulada no mês",
    )
    metrics = {"current": value, "target": target, "achievement_ratio": round(value / target, 4)}
    return kpi, metrics


def build_chart_payload(
    *,
    prompt: str,
    chart_type: str,
    services: List[str],
    metric_key: str,
    comparison: bool,
    title_hint: str,
) -> Tuple[List[ChartSeriesPayload], List[str], KPIPayload | None, Dict[str, float], str]:
    """
    Retorna (series, labels_flat_optional, kpi_or_none, aggregated_metrics, description).
    """
    description = (
        "Dados agregados para visualização no cliente. "
        "Fonte v1: amostra determinística por serviço — substituir por conectores reais quando disponíveis."
    )
    all_labels: List[str] = []
    kpi: KPIPayload | None = None
    metrics: Dict[str, float] = {}

    if chart_type == "kpi_card":
        kpi, metrics = _kpi_savings_goal(prompt)
        return [], [], kpi, metrics, description + " KPI alinhado a FinOps (meta de economia)."

    series: List[ChartSeriesPayload] = []

    if comparison and len(services) >= 2:
        # Barras agrupadas: um ponto por serviço com score composto
        pts = []
        for svc in services[:4]:
            lab = SERVICE_LABELS.get(svc, svc)
            pts.append(DataPointPayload(label=lab, value=float(50 + (_seed(prompt, svc) % 50))))
        series = [ChartSeriesPayload(name="Indice comparativo (0-100)", points=pts)]
        all_labels = [p.label for p in pts]
        metrics = {"max": max(p.value for p in pts), "min": min(p.value for p in pts)}
        return series, all_labels, None, metrics, description + " Comparativo entre módulos solicitados."

    primary = services[0] if services else "finops"

    if metric_key == "conversions_by_service" or chart_type == "bar" and primary == "dados_ia":
        series = _series_conversions_by_service(prompt)
    elif primary == "cloud_iac" or metric_key == "iac_resource_mix":
        series = _series_iac_mix(prompt)
    elif primary == "pulso_csa" or metric_key == "governance_activity":
        series = _series_pulso_activity(prompt)
    elif primary == "dados_ia" or metric_key == "ml_pipeline_metric":
        series = _series_ml_metric(prompt)
    else:
        # FinOps / default
        series = [_series_weekly_cost(prompt, "Custo (referência)")]

    if series and series[0].points:
        all_labels = [p.label for p in series[0].points]
        metrics["sum"] = round(sum(p.value for p in series[0].points), 4)
        metrics["avg"] = round(metrics["sum"] / len(series[0].points), 4)

    return series, all_labels, None, metrics, description
