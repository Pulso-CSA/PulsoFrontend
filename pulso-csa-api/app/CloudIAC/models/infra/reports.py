#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Models Reports – Infra❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Optional
from pydantic import BaseModel, Field


class PolicyReport(BaseModel):
    """Relatório de policy-as-code."""
    passed: bool
    failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    allow_override: bool = False
    override_reason: Optional[str] = None


class CostReport(BaseModel):
    """Relatório de estimativa de custo."""
    estimated_monthly: Optional[float] = None
    currency: str = "USD"
    breakdown: list[dict] = Field(default_factory=list)
    within_budget: bool = True
    budget_max: Optional[float] = None


class ProviderDiffReport(BaseModel):
    """Diferenças entre providers (AWS vs Azure vs GCP)."""
    provider: str
    differences: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ValidationReport(BaseModel):
    """Relatório de validação Terraform."""
    fmt_ok: bool = False
    validate_ok: bool = False
    plan_ok: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PlanReport(BaseModel):
    """Resumo do terraform plan."""
    changes: int = 0
    to_add: int = 0
    to_change: int = 0
    to_destroy: int = 0
    summary: Optional[str] = None


class ApplySummary(BaseModel):
    """Resumo do terraform apply."""
    success: bool = False
    outputs_sanitized: dict = Field(default_factory=dict)
    post_deploy_steps: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
