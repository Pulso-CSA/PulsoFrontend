#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Golden Module Selector – lookup sem LLM❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Literal

from app.CloudIAC.models.infra.core import GoldenModuleRef, InfraSpec, ProviderTarget

# Catálogo de golden modules (terraform/modules/<provider>/...)
GOLDEN_MODULES: dict[str, dict[str, GoldenModuleRef]] = {
    "networking": {
        "aws": GoldenModuleRef(provider="aws", module_name="networking", module_path="terraform/modules/aws/networking"),
        "azure": GoldenModuleRef(provider="azure", module_name="networking", module_path="terraform/modules/azure/networking"),
        "gcp": GoldenModuleRef(provider="gcp", module_name="networking", module_path="terraform/modules/gcp/networking"),
    },
    "compute": {
        "aws": GoldenModuleRef(provider="aws", module_name="compute", module_path="terraform/modules/aws/compute"),
        "azure": GoldenModuleRef(provider="azure", module_name="compute", module_path="terraform/modules/azure/compute"),
        "gcp": GoldenModuleRef(provider="gcp", module_name="compute", module_path="terraform/modules/gcp/compute"),
    },
    "container": {
        "aws": GoldenModuleRef(provider="aws", module_name="container", module_path="terraform/modules/aws/container"),
        "azure": GoldenModuleRef(provider="azure", module_name="container", module_path="terraform/modules/azure/container"),
        "gcp": GoldenModuleRef(provider="gcp", module_name="container", module_path="terraform/modules/gcp/container"),
    },
    "storage": {
        "aws": GoldenModuleRef(provider="aws", module_name="storage", module_path="terraform/modules/aws/storage"),
        "azure": GoldenModuleRef(provider="azure", module_name="storage", module_path="terraform/modules/azure/storage"),
        "gcp": GoldenModuleRef(provider="gcp", module_name="storage", module_path="terraform/modules/gcp/storage"),
    },
    "iam": {
        "aws": GoldenModuleRef(provider="aws", module_name="iam", module_path="terraform/modules/aws/iam"),
        "azure": GoldenModuleRef(provider="azure", module_name="iam", module_path="terraform/modules/azure/iam"),
        "gcp": GoldenModuleRef(provider="gcp", module_name="iam", module_path="terraform/modules/gcp/iam"),
    },
    "observability": {
        "aws": GoldenModuleRef(provider="aws", module_name="observability", module_path="terraform/modules/aws/observability"),
        "azure": GoldenModuleRef(provider="azure", module_name="observability", module_path="terraform/modules/azure/observability"),
        "gcp": GoldenModuleRef(provider="gcp", module_name="observability", module_path="terraform/modules/gcp/observability"),
    },
}


def select_golden_modules(spec: InfraSpec) -> list[GoldenModuleRef]:
    """
    Seleciona módulos golden a partir da InfraSpec.
    Sem LLM: lookup direto por recursos e providers.
    """
    providers = [p.provider if isinstance(p, ProviderTarget) else p for p in spec.providers]
    if not providers:
        providers = ["aws"]

    resources = spec.resources or ["networking", "compute", "storage", "iam", "observability"]
    selected: list[GoldenModuleRef] = []

    for res in resources:
        res_lower = res.lower().replace(" ", "_")
        if res_lower in GOLDEN_MODULES:
            for prov in providers:
                ref = GOLDEN_MODULES[res_lower].get(prov)
                if ref:
                    selected.append(ref)
        elif res_lower in ("ec2", "vm", "gce"):
            for prov in providers:
                ref = GOLDEN_MODULES["compute"].get(prov)
                if ref:
                    selected.append(ref)
        elif res_lower in ("ecs", "eks", "aks", "gke"):
            for prov in providers:
                ref = GOLDEN_MODULES["container"].get(prov)
                if ref:
                    selected.append(ref)

    seen: set[str] = set()
    unique: list[GoldenModuleRef] = []
    for m in selected:
        key = f"{m.provider}:{m.module_path}"
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return unique
