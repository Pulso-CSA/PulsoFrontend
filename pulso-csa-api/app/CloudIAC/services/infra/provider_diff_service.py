#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Provider Diff – docs pré-geradas (sem LLM)❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from app.CloudIAC.models.infra.reports import ProviderDiffReport

# Diferenças documentadas entre providers (lookup sem LLM)
PROVIDER_DIFFS: dict[str, list[str]] = {
    "aws": [
        "VPC usa security groups e NACLs",
        "IAM com políticas JSON",
        "Regiões: us-east-1, us-west-2, etc.",
    ],
    "azure": [
        "VNet com NSGs",
        "RBAC com Azure AD",
        "Regiões: eastus, westeurope, etc.",
    ],
    "gcp": [
        "VPC nativa com firewall rules",
        "IAM com roles e bindings",
        "Regiões: us-central1, europe-west1, etc.",
    ],
}


def get_provider_diff_report(providers: list[str]) -> list[ProviderDiffReport]:
    """Retorna relatório de diferenças entre providers. Sem LLM."""
    return [
        ProviderDiffReport(
            provider=p,
            differences=PROVIDER_DIFFS.get(p, [f"Provider {p} sem documentação pré-definida"]),
            notes=f"Especificidades do {p.upper()}",
        )
        for p in providers
    ]
