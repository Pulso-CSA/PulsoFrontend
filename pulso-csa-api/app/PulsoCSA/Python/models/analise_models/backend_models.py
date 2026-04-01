#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos - Camada 2 (Backend/Arquitetura)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# 4) Análise da Estrutura
class AnalysisStructureRequest(BaseModel):
    id_requisicao: str = Field(..., description="ID gerado na Camada 1")

class AnalysisStructureResponse(BaseModel):
    id_requisicao: str
    estrutura_arquivos: Dict[str, List[str]]
    mensagem: str = "Blueprint de estrutura criado"

# 5) Análise do Backend
class AnalysisBackendRequest(BaseModel):
    id_requisicao: str
    estrutura_arquivos: Dict[str, List[str]]

class AnalysisBackendDoc(BaseModel):
    arquivos: Dict[str, List[str]]
    funcionalidades: List[str]
    conexoes: List[str]
    otimizacoes: List[str]

class AnalysisBackendResponse(BaseModel):
    id_requisicao: str
    backend: AnalysisBackendDoc
    mensagem: str = "Documento de backend gerado"

# 6.2) Segurança de Código (pré-criação)
class SecurityCodeRequest(BaseModel):
    id_requisicao: str
    backend: AnalysisBackendDoc

class SecurityCodeResponse(BaseModel):
    id_requisicao: str
    seguranca_codigo: Dict[str, List[str]]
    mensagem: str = "Relatório de segurança de código (pré-criação)"
