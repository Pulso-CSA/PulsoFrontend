"""
Fallback semântico: normalização leve + heurísticas quando o LLM falha ou confidence é baixa.
Não falha silenciosamente: sempre produz estrutura mínima utilizável.
"""
import re
from typing import Any, Dict, List, Tuple

from Insights.core.constants import SUPPORTED_SERVICES
from Insights.models.insights_schemas import validate_chart_type, validate_services_list

# (regex ou palavras, chart_type, metric_key, services padrão, comparison)
_HEURISTICS: List[Tuple[str, str, str, List[str], bool]] = [
    (r"meta.*econom|econom.*meta|kpi.*econom|percent.*econom", "kpi_card", "savings_goal_month", ["finops"], False),
    (r"evolu[cç][aã]o.*seman|semanal.*cust|custo.*seman", "line", "weekly_cost_evolution", ["finops"], False),
    (r"custo|custos|finops|cloud bill|fatura", "line", "weekly_cost_evolution", ["finops"], False),
    (r"gr[aá]fico.*barr|barras.*serv|convers[oõ]es.*serv", "bar", "conversions_by_service", ["dados_ia", "pulso_csa"], False),
    (r"compar.*pulso|pulso.*cloud|cloud.*pulso|versus| vs ", "bar", "service_comparison", ["pulso_csa", "cloud_iac"], True),
    (r"compar.*finops|finops.*dados|dados.*finops", "bar", "cross_module_comparison", ["finops", "dados_ia"], True),
    (r"pizza|propor[cç][aã]o|distribui", "pie", "share_by_category", ["finops"], False),
    (r"[áa]rea|area|preench", "area", "volume_trend", ["dados_ia"], False),
    (r"linha|tend[eê]ncia|evolu", "line", "generic_trend", ["finops"], False),
    (r"pulsocsa|pulso csa|govern", "bar", "governance_activity", ["pulso_csa"], False),
    (r"terraform|iac|infra.*c[oó]d", "bar", "iac_resource_mix", ["cloud_iac"], False),
    (r"modelo|ml|dataset|trein|dados\s*&\s*ia", "line", "ml_pipeline_metric", ["dados_ia"], False),
]


def _lower(s: str) -> str:
    return (s or "").lower()


def normalize_prompt_text(prompt: str) -> str:
    """Segunda passagem de normalização (antes das heurísticas)."""
    t = prompt.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def heuristic_classify(prompt: str) -> Dict[str, Any]:
    n = _lower(normalize_prompt_text(prompt))
    for pattern, chart, metric, services, comparison in _HEURISTICS:
        if re.search(pattern, n, re.IGNORECASE):
            return {
                "chart_type": chart,
                "services": list(services),
                "metric_key": metric,
                "confidence": 0.55,
                "title_hint": _title_from_prompt(prompt),
                "comparison": comparison,
                "time_grain": "week" if "seman" in n else ("month" if "mês" in n or "mes" in n else "none"),
                "notes": "heuristic_fallback",
            }
    # Default seguro: FinOps linha genérica (custos são o caso mais comum em analytics corporativo)
    return {
        "chart_type": "line",
        "services": ["finops"],
        "metric_key": "weekly_cost_evolution",
        "confidence": 0.4,
        "title_hint": _title_from_prompt(prompt),
        "comparison": False,
        "time_grain": "week",
        "notes": "default_fallback",
    }


def merge_intent(llm: Dict[str, Any] | None, prompt: str) -> Tuple[Dict[str, Any], str]:
    """
    Combina saída LLM com heurística. Retorna (intent_dict, source_label).
    source_label: ollama | normalized_heuristic | hybrid
    """
    heur = heuristic_classify(prompt)
    if not llm:
        return heur, "normalized_heuristic"

    try:
        conf = float(llm.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0

    merged: Dict[str, Any] = {
        "chart_type": llm.get("chart_type") or heur["chart_type"],
        "metric_key": llm.get("metric_key") or heur["metric_key"],
        "title_hint": (llm.get("title_hint") or heur["title_hint"] or "")[:120],
        "comparison": bool(llm.get("comparison", heur["comparison"])),
        "time_grain": llm.get("time_grain") or heur["time_grain"],
        "notes": llm.get("notes"),
    }

    raw_services = llm.get("services")
    if isinstance(raw_services, list):
        sv = validate_services_list([str(x) for x in raw_services])
    else:
        sv = []
    if not sv:
        sv = heur["services"]
    merged["services"] = [s for s in sv if s in SUPPORTED_SERVICES] or heur["services"]

    # chart_type válido
    try:
        merged["chart_type"] = validate_chart_type(str(merged["chart_type"]))
    except ValueError:
        merged["chart_type"] = heur["chart_type"]

    if conf < 0.45:
        # Híbrido: preferir heurística em tipo e métrica se LLM fraco
        merged["chart_type"] = heur["chart_type"]
        merged["metric_key"] = heur["metric_key"]
        merged["services"] = heur["services"]
        merged["confidence"] = max(conf, 0.35)
        return merged, "hybrid_low_confidence"

    merged["confidence"] = conf
    return merged, "ollama" if conf >= 0.65 else "hybrid"


def ambiguity_suggestions(prompt: str) -> Dict[str, Any]:
    """Opções controladas para o frontend quando status=ambiguity."""
    return {
        "message": "Não foi possível identificar com precisão o tipo de análise. Escolha um dos focos abaixo ou refine o pedido.",
        "suggested_prompts": [
            "Mostre a evolução semanal de custos (FinOps)",
            "Gráfico de barras com conversões por serviço (Dados & IA)",
            "Compare desempenho entre PulsoCSA e CloudIaC",
            "KPI com a meta de economia do mês (FinOps)",
        ],
        "valid_options": [
            {"chart_type": "line", "services": ["finops"], "label": "Custos ao longo do tempo"},
            {"chart_type": "bar", "services": ["pulso_csa", "cloud_iac"], "label": "Comparativo PulsoCSA × CloudIaC"},
            {"chart_type": "kpi_card", "services": ["finops"], "label": "Meta de economia"},
            {"chart_type": "pie", "services": ["finops"], "label": "Distribuição de gastos por categoria"},
        ],
    }


def _title_from_prompt(prompt: str) -> str:
    p = prompt.strip()
    return (p[:72] + "…") if len(p) > 72 else p or "Insight"
