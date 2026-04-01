# Models para o agente de Tratamento e Limpeza de Dados (ID)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TratamentoLimpezaInput(BaseModel):
    id_requisicao: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    retorno_analise_inicial: Optional[Dict[str, Any]] = Field(None, description="Saída de /analise-dados-inicial (opcional)")
    dataset_ref: Optional[str] = Field(None, description="Path do dataset – suficiente para rodar ETL sob demanda")


class TratamentoLimpezaOutput(BaseModel):
    id_requisicao: str
    tratamento_limpeza: Dict[str, Any] = Field(
        ...,
        description="acoes, justificativas, dataset_pronto",
    )
