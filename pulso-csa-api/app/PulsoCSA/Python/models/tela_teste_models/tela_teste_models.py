#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos: Tela Teste (itens 9 e 10)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


#━━━━━━━━━❮Item 9 – Análise de Tela Teste❯━━━━━━━━━

class AnaliseTelaTesteRequest(BaseModel):
    """Input: id_requisicao + retorno de criar-estrutura e criar-codigo."""
    id_requisicao: str = Field(..., description="ID da requisição (Camada 1).")
    root_path: Optional[str] = Field(None, description="Pasta raiz do usuário (para ler relatórios se não enviar payload).")
    estrutura_criada: Optional[Dict[str, Any]] = Field(None, description="Retorno de POST /criar-estrutura.")
    codigo_implementado: Optional[Dict[str, Any]] = Field(None, description="Retorno de POST /criar-codigo.")


class TelaTesteSpec(BaseModel):
    """Especificação da tela de teste para QA."""
    layout: str = Field(..., description="Layout ideal (ex.: dashboard em 3 colunas).")
    funcionalidades: List[str] = Field(default_factory=list, description="Funcionalidades a testar.")
    testes_cruciais: List[str] = Field(default_factory=list, description="Testes mais importantes.")
    dados_ficticios: Dict[str, Any] = Field(default_factory=dict, description="Dados de exemplo (usuarios, etc.).")


class AnaliseTelaTesteResponse(BaseModel):
    """Saída do endpoint /analise-tela-teste."""
    id_requisicao: str
    tela_teste: TelaTesteSpec


#━━━━━━━━━❮Item 10 – Criação da Tela Teste (FrontendEX)❯━━━━━━━━━

class CriarTelaTesteRequest(BaseModel):
    """Input: id_requisicao + root_path + retorno de /analise-tela-teste."""
    id_requisicao: str = Field(..., description="ID da requisição.")
    root_path: str = Field(..., description="Pasta raiz do usuário (FrontendEX será criada aqui).")
    tela_teste: TelaTesteSpec = Field(..., description="Especificação retornada por /analise-tela-teste.")
    backend_base_url: Optional[str] = Field("http://localhost:8000", description="URL base do backend do usuário.")


class CriarTelaTesteResponse(BaseModel):
    """Saída do endpoint /criar-tela-teste."""
    id_requisicao: str
    tela_teste_criada: Dict[str, Any] = Field(..., description="arquivos, framework, etc.")
    relatorio: Dict[str, Any] = Field(default_factory=dict, description="objetivo_backend, arquivos_utilizados, estrutura_tela, testes.")
