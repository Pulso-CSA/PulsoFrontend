# Models para o agente de Análise Inicial dos Dados (ID)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnaliseDadosInicialInput(BaseModel):
    id_requisicao: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    retorno_captura: Optional[Dict[str, Any]] = Field(None, description="Saída de /captura-dados (opcional; chamada sob demanda)")
    dataset_ref: Optional[str] = Field(None, description="Path do dataset quando não vier de retorno_captura")
    objetivo_analise: Optional[str] = Field(None, description="Pergunta do usuário, ex.: churn, fraude, correlação entre x e y")


class AnaliseDadosInicialOutput(BaseModel):
    id_requisicao: str
    analise_inicial: Dict[str, Any] = Field(
        ...,
        description="objetivo_analise, analises_recomendadas, tratamentos_necessarios, variaveis_alvo",
    )
    dataset_ref: Optional[str] = Field(None, description="Path do dataset (repasse da captura para próxima etapa)")
