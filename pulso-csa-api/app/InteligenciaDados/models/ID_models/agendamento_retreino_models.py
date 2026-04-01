# Models para agendamento de retreino (ID)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgendamentoRetreinoInput(BaseModel):
    """Registra intenção de retreino periódico."""
    id_requisicao: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    dataset_ref: str = Field(..., description="Path do dataset para retreino")
    variavel_alvo: str = Field(..., description="Coluna alvo")
    tipo_problema: Optional[str] = Field("classificacao", description="classificacao | regressao")
    proxima_execucao_em_minutos: Optional[int] = Field(None, description="Executar retreino daqui a N minutos (para teste)")
    cron_expr: Optional[str] = Field(None, description="Expressão cron (ex.: 0 9 * * 1 = toda segunda 9h); uso depende do executor externo")


class AgendamentoRetreinoOutput(BaseModel):
    """Confirmação do agendamento."""
    id_requisicao: str
    agendamento_id: str = Field(..., description="ID do agendamento registrado")
    mensagem: str = Field(..., description="Instruções para executar retreino (chamar POST /executar-retreino-agendado)")


class ExecutarRetreinoOutput(BaseModel):
    """Resultado da execução de um retreino agendado."""
    model_config = ConfigDict(protected_namespaces=())
    agendamento_id: str
    executado: bool
    model_ref_novo: Optional[str] = None
    modelo_ml: Optional[Dict[str, Any]] = None
    erro: Optional[str] = None
