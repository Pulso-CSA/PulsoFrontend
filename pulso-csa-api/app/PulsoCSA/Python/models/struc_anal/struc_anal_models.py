#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import List, Dict, Any
from pydantic import BaseModel, Field

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos de Requisição❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
class StructurePlanRequest(BaseModel):
    usuario: str = Field(..., description="Identificação do usuário.")
    root_path: str = Field(..., description="Caminho absoluto do projeto.")
    prompt: str = Field(..., description="Prompt do usuário descrevendo o que deseja criar/alterar.")
    id_requisicao: str = Field(..., description="ID único da requisição.")


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelo ScannedFile❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
class ScannedFile(BaseModel):
    path: str
    linhas: int
    tamanho_bytes: int
    conteudo: str
    papel: str   # ← ESTE CAMPO É OBRIGATÓRIO


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelo ScannedProject❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
class ScannedProject(BaseModel):
    id_requisicao: str
    root_path: str
    arquivos: List[ScannedFile]
    resumo_sistema: str



#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos de Plano do LLM❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
class PlannedFileSection(BaseModel):
    name: str
    description: str


class PlannedFileCreation(BaseModel):
    path: str
    tipo_arquivo: str
    descricao_conceitual: str
    secoes: List[PlannedFileSection]
    dependencias: List[str]


class PlannedFileUpdate(BaseModel):
    path: str
    trechos_atuais_relevantes: str
    descricao_mudanca: str
    impacto: str


class StructurePlanResponse(BaseModel):
    id_requisicao: str
    resumo_sistema: str
    novos_arquivos: List[PlannedFileCreation]
    arquivos_a_alterar: List[PlannedFileUpdate]
