#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Models Requests – Infra❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Literal, Optional
from pydantic import BaseModel, Field

from .core import InfraSpec


class InfraAnalyzeRequest(BaseModel):
    """Request para POST /infra/analyze."""
    root_path: str = Field(default=".", description="Caminho raiz do projeto; use '.' para diretório atual")
    tenant_id: str = Field(default="default")
    id_requisicao: str
    user_request: Optional[str] = None
    providers: Optional[list[Literal["aws", "azure", "gcp"]]] = None
    envs: Optional[list[str]] = None


class InfraGenerateRequest(BaseModel):
    """Request para POST /infra/generate."""
    infra_spec: Optional[InfraSpec] = None
    user_request: Optional[str] = None
    root_path: str = Field(default=".", description="Caminho raiz do projeto; use '.' para diretório atual")
    tenant_id: str = Field(default="default")
    id_requisicao: str


class InfraValidateRequest(BaseModel):
    """Request para POST /infra/validate."""
    root_path: str
    tenant_id: str = Field(default="default")
    id_requisicao: str
    terraform_path: Optional[str] = None


class InfraDeployRequest(BaseModel):
    """Request para POST /infra/deploy."""
    root_path: str
    tenant_id: str = Field(default="default")
    id_requisicao: str
    confirm: bool = Field(default=False)
    deploy_token: Optional[str] = None
    confirm_phrase: Optional[str] = None
    terraform_path: Optional[str] = None
    allow_policy_override: bool = False
    override_reason: Optional[str] = None
    budget_max: Optional[float] = None
    allow_budget_override: bool = False
