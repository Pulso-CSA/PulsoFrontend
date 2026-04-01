#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Sistema de Compreensão❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


#━━━━━━━━━❮Request❯━━━━━━━━━


# Limites de validação (segurança e custo)
PROMPT_MAX_LENGTH = 8192
USER_MAX_LENGTH = 512


class ComprehensionRequest(BaseModel):
    """Payload da entrada principal do workflow (Sistema de Compreensão)."""

    usuario: str = Field(..., max_length=USER_MAX_LENGTH, description="Identificação do usuário.")
    prompt: str = Field(..., max_length=PROMPT_MAX_LENGTH, description="Prompt cru informado pelo usuário.")
    root_path: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Caminho raiz do projeto. Obrigatório quando for executar governance ou correct.",
    )
    force_execute: Optional[bool] = Field(
        default=False,
        description="Se True, executa sem pedir confirmação (ex.: botão 'Executar' no frontend).",
    )
    force_module: Optional[str] = Field(
        default=None,
        description="Força módulo: 'codigo', 'infraestrutura' ou 'inteligencia-dados'. Se omitido, detecta automaticamente.",
    )
    history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Histórico de mensagens [{role, content}] para contexto conversacional.",
    )
    id_requisicao: Optional[str] = Field(
        default=None,
        max_length=128,
        description="ID da requisição (para módulo Inteligência de Dados).",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="Chave OpenAI do usuário (plano BYOK, 15% desconto). Nunca armazenada; reenviar a cada request.",
    )


#━━━━━━━━━❮Response❯━━━━━━━━━


class ComprehensionResponse(BaseModel):
    """
    Resposta do Sistema de Compreensão.
    Inclui campos técnicos e message humanizada para o frontend exibir direto.
    """

    intent: str = Field(..., description="ANALISAR ou EXECUTAR.")
    project_state: str = Field(..., description="ROOT_VAZIA ou ROOT_COM_CONTEUDO.")
    should_execute: bool = Field(..., description="Se o gate de execução foi atendido.")
    target_endpoint: Optional[str] = Field(
        default=None,
        description="Endpoint que seria ou foi disparado: /governance/run ou /workflow/correct/run.",
    )
    explanation: str = Field(..., description="Explicação da decisão de roteamento.")
    next_action: str = Field(..., description="Próximo passo descrito.")
    message: str = Field(
        ...,
        description="Mensagem humanizada para exibir no frontend (sucesso, análise ou pedido de confirmação).",
    )
    file_tree: Optional[str] = Field(
        default=None,
        description="Árvore de arquivos do projeto; arquivos criados neste run têm * ao lado do nome.",
    )
    system_behavior: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON de contrato do sistema: input, output, parâmetros (como o endpoint se comporta).",
    )
    frontend_suggestion: Optional[str] = Field(
        default=None,
        description="Sugestão de como exibir as mudanças na área do chat / Descrição do projeto.",
    )
    intent_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confiança da classificação de intenção (0–1). Quando < threshold, ver intent_warning.",
    )
    intent_warning: Optional[str] = Field(
        default=None,
        description="Aviso quando a classificação foi incerta (ex.: sugerir reformular ou confirmar).",
    )
    processing_time_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Tempo de processamento em milissegundos.",
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Código de erro estruturado quando aplicável (ex.: ANALYSIS_UNAVAILABLE, GOVERNANCE_RUN_FAILED).",
    )
    module: Optional[str] = Field(
        default=None,
        description="Módulo detectado: codigo, infraestrutura ou inteligencia-dados.",
    )
    curl_commands: Optional[List[str]] = Field(
        default=None,
        description="Comandos cURL em uma linha para testes (ex.: Health, Compreensão, Governance/Correct).",
    )
    preview_frontend_url: Optional[str] = Field(
        default=None,
        description="URL do preview do frontend (Streamlit localhost:3000) quando tela foi criada.",
    )
