# Models para o agente de Análise Estatística (ID)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnaliseEstatisticaInput(BaseModel):
    id_requisicao: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    retorno_tratamento: Optional[Dict[str, Any]] = Field(None, description="Saída de /tratamento-limpeza (opcional)")
    dataset_ref: Optional[str] = Field(None, description="Path do dataset – suficiente para correlações/estatísticas sob demanda")
    pergunta: Optional[str] = Field(None, description="Pergunta do usuário, ex.: 'qual a correlação entre x e y?'")


class AnaliseEstatisticaOutput(BaseModel):
    id_requisicao: str
    analise_estatistica: Dict[str, Any] = Field(
        ...,
        description="quantidade_dados, resultados, insights, modelos_sugeridos, requisitos_modelos, graficos_metadados",
    )
    dataset_ref: Optional[str] = Field(None, description="Path do dataset tratado para uso no ML")
