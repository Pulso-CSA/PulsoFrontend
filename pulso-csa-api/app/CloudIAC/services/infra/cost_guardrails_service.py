#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Cost Guardrails – estimativa sem LLM❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Optional

from app.CloudIAC.models.infra.reports import CostReport


# Estimativas aproximadas mensais (USD) por recurso
ESTIMATE_PER_RESOURCE: dict[str, float] = {
    "networking": 20.0,
    "compute": 50.0,
    "container": 80.0,
    "storage": 10.0,
    "iam": 0.0,
    "observability": 10.0,
}


def estimate_cost(
    resources: list[str],
    providers: list[str],
    budget_max: Optional[float] = None,
) -> CostReport:
    """
    Estima custo mensal a partir dos recursos.
    Sem LLM: lookup em tabela.
    """
    total = 0.0
    breakdown: list[dict] = []
    for res in resources:
        res_lower = res.lower().replace(" ", "_")
        if res_lower in ESTIMATE_PER_RESOURCE:
            cost = ESTIMATE_PER_RESOURCE[res_lower]
        elif res_lower in ("ec2", "vm", "gce"):
            cost = ESTIMATE_PER_RESOURCE["compute"]
        elif res_lower in ("ecs", "eks", "aks", "gke"):
            cost = ESTIMATE_PER_RESOURCE["container"]
        else:
            cost = 10.0
        per_provider = cost / max(len(providers), 1)
        total += per_provider * len(providers)
        breakdown.append({"resource": res, "estimate_usd_monthly": cost})

    within_budget = budget_max is None or total <= budget_max
    return CostReport(
        estimated_monthly=round(total, 2),
        currency="USD",
        breakdown=breakdown,
        within_budget=within_budget,
        budget_max=budget_max,
    )
