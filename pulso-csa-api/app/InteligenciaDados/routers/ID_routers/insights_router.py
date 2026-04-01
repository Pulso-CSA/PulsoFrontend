import asyncio
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, status

from app.core.entitlement.deps import require_valid_access
from app.InteligenciaDados.models.ID_models.analise_estatistica_models import AnaliseEstatisticaInput
from app.InteligenciaDados.models.ID_models.insights_models import (
    InsightChartPoint,
    InsightGenerateInput,
    InsightGenerateOutput,
    InsightWidget,
    InsightWidgetsOutput,
)
from app.InteligenciaDados.services.ID_services.analise_estatistica_service import AnaliseEstatisticaService

router = APIRouter(
    prefix="/inteligencia-dados/insights",
    tags=["Inteligência de Dados – Insights"],
)

_service = AnaliseEstatisticaService()


def _format_int_pt_br(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _map_chart_type(meta_tipo: Optional[str], tem_pizza_no_prompt: bool) -> str:
    tipo = (meta_tipo or "").strip().lower()
    if "dispers" in tipo or "linha" in tipo:
        return "line"
    if "barra" in tipo or "hist" in tipo:
        return "bar"
    if "pizza" in tipo or "pie" in tipo or tem_pizza_no_prompt:
        return "pie"
    return "area"


def _extract_chart_data(
    metadados: List[Dict[str, Any]],
    dados: List[Dict[str, Any]],
    prompt: str,
) -> Tuple[str, Optional[List[InsightChartPoint]], Optional[float], Dict[str, Any]]:
    if not metadados or not dados:
        return ("progress", None, 65.0, {})

    meta = metadados[0] if isinstance(metadados[0], dict) else {}
    dado = dados[0] if isinstance(dados[0], dict) else {}
    prompt_lower = prompt.lower()
    chart_type = _map_chart_type(meta.get("tipo"), "pizza" in prompt_lower or "pie" in prompt_lower)

    labels = dado.get("labels") if isinstance(dado.get("labels"), list) else []
    values = dado.get("values") if isinstance(dado.get("values"), list) else []
    x_vals = dado.get("x") if isinstance(dado.get("x"), list) else []
    y_vals = dado.get("y") if isinstance(dado.get("y"), list) else []

    points: List[InsightChartPoint] = []
    if labels and values:
        for idx, raw in enumerate(values[:24]):
            try:
                numeric_value = float(raw)
            except Exception:
                continue
            label = str(labels[idx]) if idx < len(labels) else f"Ponto {idx + 1}"
            points.append(InsightChartPoint(label=label, value=numeric_value))
    elif x_vals and y_vals:
        for idx, raw in enumerate(y_vals[:24]):
            try:
                numeric_value = float(raw)
            except Exception:
                continue
            label = str(x_vals[idx]) if idx < len(x_vals) else f"Ponto {idx + 1}"
            points.append(InsightChartPoint(label=label, value=numeric_value))

    if not points:
        return ("progress", None, 65.0, meta)

    # Gráfico de pizza funciona melhor com até 8 categorias.
    if chart_type == "pie":
        points = points[:8]

    return (chart_type, points, None, meta)


def _create_default_widgets() -> List[InsightWidget]:
    return [
        InsightWidget(
            id="insight-default-pulso",
            title="Post Views",
            value="2.012",
            trend="+12.3%",
            period="Últimas 24h",
            chart_type="area",
            insights=[
                "O pico de visualizações ocorre entre 12h e 14h.",
                "Considere publicar nesse intervalo para maximizar alcance.",
            ],
            service_filter="pulso",
            analysis_summary="Visualizações de posts ao longo do dia.",
            technical_conclusion="Pico de tráfego no horário de almoço.",
            data=[
                InsightChartPoint(label="8h", value=120),
                InsightChartPoint(label="10h", value=280),
                InsightChartPoint(label="12h", value=450),
                InsightChartPoint(label="14h", value=380),
                InsightChartPoint(label="16h", value=520),
                InsightChartPoint(label="18h", value=412),
            ],
        ),
        InsightWidget(
            id="insight-default-data",
            title="Conversões",
            value="1.245",
            trend="+8.1%",
            period="Últimos 7 dias",
            chart_type="bar",
            insights=[
                "A taxa de conversão está acima da média recente.",
                "Vale testar melhorias no checkout para reduzir abandono.",
            ],
            service_filter="data",
            analysis_summary="Conversões por período.",
            technical_conclusion="Há margem de ganho no fim do funil.",
            data=[
                InsightChartPoint(label="Seg", value=140),
                InsightChartPoint(label="Ter", value=165),
                InsightChartPoint(label="Qua", value=172),
                InsightChartPoint(label="Qui", value=188),
                InsightChartPoint(label="Sex", value=201),
                InsightChartPoint(label="Sáb", value=179),
                InsightChartPoint(label="Dom", value=200),
            ],
        ),
        InsightWidget(
            id="insight-default-finops",
            title="Meta de economia",
            value="76%",
            trend="+5%",
            period="Este mês",
            chart_type="progress",
            progress_percent=76.0,
            insights=[
                "Atingiu 76% da meta de economia mensal.",
                "Ações em recursos ociosos podem acelerar o fechamento.",
            ],
            service_filter="finops",
            analysis_summary="Progresso da meta de redução de custos.",
            technical_conclusion="Foco em recursos subutilizados para fechar o gap.",
        ),
    ]


@router.get(
    "/widgets",
    response_model=InsightWidgetsOutput,
    status_code=status.HTTP_200_OK,
)
async def list_widgets(user: dict = Depends(require_valid_access)) -> InsightWidgetsOutput:
    # MVP: widgets iniciais para preencher a tela na primeira carga.
    # A criação por prompt já retorna dados reais quando dataset_ref estiver conectado.
    return InsightWidgetsOutput(widgets=_create_default_widgets())


@router.post(
    "/generate",
    response_model=InsightGenerateOutput,
    status_code=status.HTTP_200_OK,
)
async def generate_widget(
    payload: InsightGenerateInput,
    user: dict = Depends(require_valid_access),
) -> InsightGenerateOutput:
    pergunta = payload.prompt.strip()
    pergunta_lower = pergunta.lower()
    if not any(k in pergunta_lower for k in ["grafico", "gráfico", "barra", "linha", "dispers", "pizza", "histograma"]):
        pergunta += ". Mostre um gráfico e explique os principais insights."

    loop = asyncio.get_event_loop()
    analise_out = await loop.run_in_executor(
        None,
        _service.run,
        AnaliseEstatisticaInput(
            id_requisicao=payload.id_requisicao,
            usuario=user.get("email") or user.get("_id"),
            dataset_ref=payload.dataset_ref,
            pergunta=pergunta,
        ),
    )
    analise = analise_out.analise_estatistica or {}

    metadados = analise.get("graficos_metadados") if isinstance(analise.get("graficos_metadados"), list) else []
    dados = analise.get("graficos_dados") if isinstance(analise.get("graficos_dados"), list) else []
    chart_type, points, progress_percent, selected_meta = _extract_chart_data(metadados, dados, payload.prompt)

    insights_raw = analise.get("insights")
    insights: List[str] = []
    if isinstance(insights_raw, list):
        insights = [str(item).strip() for item in insights_raw if str(item).strip()]
    elif isinstance(insights_raw, str) and insights_raw.strip():
        insights = [insights_raw.strip()]
    if not insights:
        insights = ["Insights gerados com base nos dados disponíveis."]

    if chart_type == "progress":
        value = f"{int(progress_percent or 65)}%"
    elif points:
        value = _format_int_pt_br(int(sum(point.value for point in points)))
    else:
        quantidade = int(analise.get("quantidade_dados") or 0)
        value = _format_int_pt_br(quantidade) if quantidade > 0 else "0"

    summary = selected_meta.get("explicacao") if isinstance(selected_meta, dict) else None
    title = (selected_meta.get("titulo") if isinstance(selected_meta, dict) else None) or payload.prompt[:48]
    technical = analise.get("resposta_pergunta")
    if not isinstance(technical, str) or not technical.strip():
        technical = "Resultado gerado automaticamente com base no dataset atual."

    widget = InsightWidget(
        id=f"insight-{uuid.uuid4().hex[:10]}",
        title=title,
        value=value,
        trend="+0%",
        period="Gerado por IA",
        chart_type=chart_type,  # type: ignore[arg-type]
        progress_percent=progress_percent,
        insights=insights,
        service_filter=payload.service_filter or "data",
        custom_prompt=payload.prompt,
        analysis_summary=summary,
        technical_conclusion=technical.strip(),
        data=points,
    )
    return InsightGenerateOutput(
        id_requisicao=payload.id_requisicao,
        dataset_ref=analise_out.dataset_ref or payload.dataset_ref,
        widget=widget,
    )
