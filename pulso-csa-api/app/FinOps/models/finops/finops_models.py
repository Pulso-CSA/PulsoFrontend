#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Models – FinOps Analyze❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Pydantic request/response para POST /finops/analyze.
Credenciais por provider, janela, escopos, quick_win_mode, guardrails_mode.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


#━━━━━━━━━❮Credenciais por provider❯━━━━━━━━━

class AWSCredentials(BaseModel):
    """Credenciais AWS: AssumeRole (preferencial) ou AccessKey/Secret."""
    role_arn: Optional[str] = Field(None, description="ARN para AssumeRole (opcional)")
    external_id: Optional[str] = Field(None, description="External ID para AssumeRole")
    access_key_id: Optional[str] = Field(None, description="Fallback: Access Key")
    secret_access_key: Optional[str] = Field(None, description="Fallback: Secret Key")
    session_token: Optional[str] = Field(None, description="Fallback: temporário")
    region: Optional[str] = Field(None, description="Região principal (ex.: us-east-1)")


class AzureCredentials(BaseModel):
    """Credenciais Azure: service principal ou managed identity."""
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    client_id: Optional[str] = Field(None, description="Application (client) ID")
    client_secret: Optional[str] = Field(None, description="Client secret")
    subscription_id: Optional[str] = Field(None, description="Subscription ID")


class GCPCredentials(BaseModel):
    """Credenciais GCP: service account JSON ou ADC."""
    service_account_json: Optional[dict[str, Any]] = Field(None, description="JSON da service account")
    project_id: Optional[str] = Field(None, description="Project ID")


#━━━━━━━━━❮Request principal❯━━━━━━━━━

class FinOpsAnalyzeRequest(BaseModel):
    """Request para POST /finops/analyze."""
    cloud: Literal["aws", "azure", "gcp", "multi"] = Field(
        ...,
        description="Provedor ou 'multi' para comparação multi-cloud"
    )
    aws_credentials: Optional[AWSCredentials] = Field(None, description="Credenciais AWS (quando cloud=aws ou multi)")
    azure_credentials: Optional[AzureCredentials] = Field(None, description="Credenciais Azure (quando cloud=azure ou multi)")
    gcp_credentials: Optional[GCPCredentials] = Field(None, description="Credenciais GCP (quando cloud=gcp ou multi)")
    start_date: Optional[str] = Field(None, description="Início da janela (YYYY-MM-DD). Default: 30 dias atrás")
    end_date: Optional[str] = Field(None, description="Fim da janela (YYYY-MM-DD). Default: ontem")
    scopes: Optional[list[str]] = Field(
        default_factory=lambda: ["all"],
        description="Escopos: all, compute, storage, network, managed, kubernetes"
    )
    quick_win_mode: Literal["quick_wins", "compare_regions", "auto_shutdown_policies", "none"] = Field(
        "none",
        description="Modo de quick wins: quick_wins, compare_regions, auto_shutdown_policies ou none"
    )
    multi_cloud_compare: bool = Field(
        False,
        description="Se true e cloud=multi, inclui comparação de drivers de custo"
    )
    guardrails_mode: bool = Field(
        False,
        description="Se true, inclui seção Guardrails recomendados (budgets, anomalias, alertas)"
    )
    anomaly_threshold_pct: Optional[float] = Field(
        None,
        description="Threshold de anomalia (% desvio vs média). Default: 30"
    )
    anomaly_window_days: Optional[int] = Field(
        None,
        description="Janela para anomalia (dias). Default: 7 ou 30"
    )


#━━━━━━━━━❮Response principal❯━━━━━━━━━

class FinOpsAnalyzeResponse(BaseModel):
    """Response com texto final para chat (sem anexos)."""
    message: str = Field(..., description="Resposta em linguagem natural para o chat")
    cloud: Optional[str] = Field(None, description="Provedor executado")
    id_requisicao: Optional[str] = Field(None, description="ID da requisição para rastreio")
