from Insights.core.constants import SERVICE_LABELS, SUPPORTED_SERVICES
from Insights.models.insights_schemas import CatalogChartTypeInfo, CatalogResponse, CatalogServiceInfo


def build_catalog_response() -> CatalogResponse:
    chart_infos = [
        CatalogChartTypeInfo(
            id="line",
            label="Linha",
            description="Séries temporais (evolução ao longo do tempo).",
        ),
        CatalogChartTypeInfo(
            id="bar",
            label="Barras",
            description="Comparação entre categorias ou módulos.",
        ),
        CatalogChartTypeInfo(
            id="pie",
            label="Pizza",
            description="Proporções de um total.",
        ),
        CatalogChartTypeInfo(
            id="area",
            label="Área",
            description="Volume acumulado ou tendência preenchida.",
        ),
        CatalogChartTypeInfo(
            id="kpi_card",
            label="KPI",
            description="Métrica única com meta / delta (cartão, sem layout imposto).",
        ),
    ]
    services = [
        CatalogServiceInfo(
            id=sid,
            label=SERVICE_LABELS.get(sid, sid),
            description=_service_desc(sid),
        )
        for sid in SUPPORTED_SERVICES
    ]
    capabilities = [
        "Interpretação de pedidos em português (Ollama quando USE_OLLAMA=1).",
        "Fallback heurístico quando o modelo falha ou tem baixa confiança.",
        "Payload neutro para Recharts, Chart.js ou outro renderer no frontend.",
        "Sessões e histórico persistidos em MongoDB (coleções insights_*).",
        "v1: dados de referência determinísticos por serviço — pronto para conectar fontes reais.",
    ]
    examples = [
        "Me mostre a evolução semanal de custos",
        "Gere um gráfico de barras com conversões por serviço",
        "Quero comparar desempenho entre PulsoCSA e CloudIaC",
        "Me traga um KPI com a meta de economia do mês",
        "Distribuição de gastos por categoria na cloud",
        "Tendência de acurácia do modelo em Dados & IA",
    ]
    return CatalogResponse(
        chart_types=chart_infos,
        services=services,
        capabilities=capabilities,
        example_prompts=examples,
    )


def _service_desc(sid: str) -> str:
    return {
        "pulso_csa": "Governança, análise de código e pipelines PulsoCSA.",
        "cloud_iac": "Infra como código, Terraform e estimativas de recurso.",
        "finops": "Custos multi-cloud, economia e metas.",
        "dados_ia": "Datasets, ML e indicadores analíticos.",
    }.get(sid, "")
