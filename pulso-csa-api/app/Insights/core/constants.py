from typing import Final, List

SUPPORTED_CHART_TYPES: Final[List[str]] = ["line", "bar", "pie", "area", "kpi_card"]

# IDs estáveis para API e persistência (alinhados ao produto)
SUPPORTED_SERVICES: Final[List[str]] = ["pulso_csa", "cloud_iac", "finops", "dados_ia"]

SERVICE_LABELS: Final[dict] = {
    "pulso_csa": "PulsoCSA",
    "cloud_iac": "CloudIaC",
    "finops": "FinOps",
    "dados_ia": "Dados & IA",
}

MIN_LLM_CONFIDENCE: Final[float] = 0.45
