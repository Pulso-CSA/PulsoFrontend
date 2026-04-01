#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Models – FinOps Chat❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
Pydantic para POST /finops/chat (entrada única do chat FinOps).
"""
from typing import Optional

from pydantic import BaseModel, Field

from models.finops.finops_models import AWSCredentials, AzureCredentials, GCPCredentials


class FinOpsChatInput(BaseModel):
    """Entrada do chat FinOps: mensagem em linguagem natural + credenciais."""
    mensagem: str = Field(..., min_length=1, description="Pergunta ou comando em linguagem natural")
    id_requisicao: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    aws_credentials: Optional[AWSCredentials] = Field(None, description="Credenciais AWS")
    azure_credentials: Optional[AzureCredentials] = Field(None, description="Credenciais Azure")
    gcp_credentials: Optional[GCPCredentials] = Field(None, description="Credenciais GCP")


class FinOpsChatOutput(BaseModel):
    """Resposta do chat FinOps: texto narrativo + metadados."""
    resposta_texto: str = Field(..., description="Resposta em linguagem natural para o chat")
    id_requisicao: str = Field(..., description="ID da requisição para rastreio")
    cloud: Optional[str] = Field(None, description="Provedor executado")
    etapas_executadas: list[str] = Field(default_factory=list, description="Ex.: [comprehension, preflight, billing, heuristics, llm_narrative]")
