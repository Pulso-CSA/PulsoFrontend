#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Dict, List
from pydantic import BaseModel, Field

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos - Camada 2 (Infra/CloudSec)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# 6) Análise da Infra
class AnalysisInfraRequest(BaseModel):
    id_requisicao: str = Field(..., description="ID da Camada 1")
    estrutura_arquivos: Dict[str, List[str]]
    backend: Dict

class AnalysisInfraResponse(BaseModel):
    id_requisicao: str
    infraestrutura: Dict[str, List[str]]
    mensagem: str = "Documento de infraestrutura gerado"

# 6.1) Segurança em Infra
class SecurityInfraRequest(BaseModel):
    id_requisicao: str
    infraestrutura: Dict[str, List[str]]

class SecurityInfraResponse(BaseModel):
    id_requisicao: str
    seguranca_infra: Dict[str, List[str]]
    mensagem: str = "Relatório de segurança de infra (pré-criação)"
