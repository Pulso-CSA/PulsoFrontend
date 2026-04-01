#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Models Core – InfraSpec❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ProviderTarget(BaseModel):
    """Provider cloud (AWS, Azure, GCP)."""
    provider: Literal["aws", "azure", "gcp"]
    region: Optional[str] = None
    env: Optional[str] = Field(None, description="dev, staging, prod")


class SecurityConstraints(BaseModel):
    """Restrições de segurança."""
    no_public_ip_default: bool = True
    no_0_0_0_0_ports: bool = True
    encryption_at_rest: bool = True
    network_segmentation: bool = True
    required_tags: list[str] = Field(default_factory=lambda: ["Environment", "Project", "ManagedBy"])


class CostConstraints(BaseModel):
    """Restrições de custo."""
    budget_max: Optional[float] = None
    prefer_right_sizing: bool = True
    prefer_spot_preemptible: bool = False
    regions_suggested: list[str] = Field(default_factory=list)


class GoldenModuleRef(BaseModel):
    """Referência a módulo golden no catálogo."""
    provider: Literal["aws", "azure", "gcp"]
    module_name: str
    module_path: str
    version: Optional[str] = None


class Blueprint(BaseModel):
    """Blueprint sugerido (ex.: api-rest-python, webapp-react)."""
    blueprint_id: str
    name: str
    description: Optional[str] = None
    stack_pattern: list[str] = Field(default_factory=list)


class InfraSpec(BaseModel):
    """Especificação de infraestrutura multi-cloud."""
    tenant_id: str
    id_requisicao: str
    providers: list[ProviderTarget] = Field(default_factory=list)
    envs: list[str] = Field(default_factory=lambda: ["dev"])
    resources: list[str] = Field(default_factory=list)
    blueprint: Optional[Blueprint] = None
    golden_modules: list[GoldenModuleRef] = Field(default_factory=list)
    security: SecurityConstraints = Field(default_factory=SecurityConstraints)
    cost: CostConstraints = Field(default_factory=CostConstraints)
    user_request: Optional[str] = None
    backend_context: Optional[dict] = None
    structure_context: Optional[dict] = None
