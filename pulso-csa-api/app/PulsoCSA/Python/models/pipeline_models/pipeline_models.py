#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos do Pipeline (11 → 13.2)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


#━━━━━━━━━❮11 – Teste Automatizado❯━━━━━━━━━
class TesteAutomatizadoRequest(BaseModel):
    id_requisicao: str = Field(..., description="ID da requisição.")
    root_path: str = Field(..., description="Caminho raiz do projeto (para run venv/docker).")
    criar_estrutura: Optional[Dict[str, Any]] = Field(None, description="Retorno de criar-estrutura / analise-estrutura.")
    criar_codigo: Optional[Dict[str, Any]] = Field(None, description="Retorno de criar-codigo / workflow.")
    criar_tela_teste: Optional[Dict[str, Any]] = Field(None, description="Retorno de criar-tela-teste.")
    prefer_docker: bool = Field(True, description="Tentar Docker antes de Venv.")
    idempotency_key: Optional[str] = Field(None, description="Chave de idempotência para evitar execução duplicada.")
    correlation_id: Optional[str] = Field(None, description="ID de correlação para rastreabilidade.")


class RelatorioTestes(BaseModel):
    status: str = Field(..., description="aprovado | parcialmente aprovado | reprovado")
    erros: List[str] = Field(default_factory=list)
    vulnerabilidades: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)


class TesteAutomatizadoResponse(BaseModel):
    id_requisicao: str
    relatorio_testes: RelatorioTestes
    run_id: Optional[str] = Field(None, description="ID único da execução.")
    correlation_id: Optional[str] = Field(None, description="ID de correlação para rastreabilidade.")


#━━━━━━━━━❮12 – Análise de Retorno❯━━━━━━━━━
class AnaliseRetornoRequest(BaseModel):
    id_requisicao: str = Field(..., description="ID da requisição.")
    relatorio_testes: RelatorioTestes = Field(..., description="Saída de /teste-automatizado.")
    estrutura: Optional[Dict[str, Any]] = Field(None, description="Contexto: estrutura/backend/tela.")
    root_path: Optional[str] = Field(None)
    idempotency_key: Optional[str] = Field(None, description="Chave de idempotência.")
    correlation_id: Optional[str] = Field(None, description="ID de correlação.")


class AnaliseRetornoPayload(BaseModel):
    objetivo_final: str = Field(..., description="atingido | não atingido")
    falhas: List[str] = Field(default_factory=list)
    vulnerabilidades: List[str] = Field(default_factory=list)
    faltantes: List[str] = Field(default_factory=list)
    relatorio_logs: Optional[str] = Field(None)


class AnaliseRetornoResponse(BaseModel):
    id_requisicao: str
    analise_retorno: AnaliseRetornoPayload
    run_id: Optional[str] = Field(None, description="ID único da execução.")
    correlation_id: Optional[str] = Field(None, description="ID de correlação.")


#━━━━━━━━━❮13 – Correção de Erros❯━━━━━━━━━
class CorrecaoErrosRequest(BaseModel):
    id_requisicao: str = Field(..., description="ID da requisição.")
    analise_retorno: AnaliseRetornoPayload = Field(..., description="Saída de /analise-retorno.")
    root_path: str = Field(..., description="Caminho raiz do projeto.")
    usuario: str = Field(default="pipeline", description="Usuário para o workflow de correção.")
    idempotency_key: Optional[str] = Field(None, description="Chave de idempotência.")
    correlation_id: Optional[str] = Field(None, description="ID de correlação.")


class CorrecaoPayload(BaseModel):
    erros_corrigidos: List[str] = Field(default_factory=list)
    funcionalidades_atualizadas: List[str] = Field(default_factory=list)
    estrutura_atualizada: List[str] = Field(default_factory=list)
    status: str = Field(..., description="ex.: corrigido e aguardando validação")
    deve_reexecutar_teste: bool = Field(
        True,
        description="Indica se o cliente deve reexecutar teste e análise até aprovação.",
    )
    proximo_passo: str = Field(
        "Reexecutar POST /teste-automatizado e em seguida POST /analise-retorno para validar se o objetivo foi atingido.",
        description="Próximo passo no ciclo refino → análise → criação → testes.",
    )


class CorrecaoErrosResponse(BaseModel):
    id_requisicao: str
    correcao: CorrecaoPayload
    workflow_result: Optional[Dict[str, Any]] = Field(None, description="Retorno bruto do correct_workflow.")
    run_id: Optional[str] = Field(None, description="ID único da execução.")
    correlation_id: Optional[str] = Field(None, description="ID de correlação.")


#━━━━━━━━━❮13.1 – Segurança Código (pós-correção)❯━━━━━━━━━
class SegurancaCodigoPosRequest(BaseModel):
    id_requisicao: str = Field(..., description="ID da requisição.")
    relatorio_correcao: CorrecaoPayload = Field(..., description="Saída de /correcao-erros.")
    backend_doc: Optional[Dict[str, Any]] = Field(None, description="Backend atual (ou carregado do DB).")


class SegurancaCodigoPosPayload(BaseModel):
    corrigidas: List[str] = Field(default_factory=list)
    pendentes: List[str] = Field(default_factory=list)
    recomendacoes: List[str] = Field(default_factory=list)


class SegurancaCodigoPosResponse(BaseModel):
    id_requisicao: str
    seguranca_codigo_pos: SegurancaCodigoPosPayload


#━━━━━━━━━❮13.2 – Segurança Infra (pós-correção)❯━━━━━━━━━
class SegurancaInfraPosRequest(BaseModel):
    id_requisicao: str = Field(..., description="ID da requisição.")
    relatorio_correcao: CorrecaoPayload = Field(..., description="Saída de /correcao-erros.")
    analise_infra: Optional[Dict[str, Any]] = Field(None, description="Contexto de análise de infra (ou do DB).")


class SegurancaInfraPosPayload(BaseModel):
    corrigidas: List[str] = Field(default_factory=list)
    pendentes: List[str] = Field(default_factory=list)
    recomendacoes: List[str] = Field(default_factory=list)


class SegurancaInfraPosResponse(BaseModel):
    id_requisicao: str
    seguranca_infra_pos: SegurancaInfraPosPayload
