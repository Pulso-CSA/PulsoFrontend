# Models para previsão em tempo real com modelo treinado (ID)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PrevisaoInput(BaseModel):
    """Entrada para aplicar modelo e obter previsões."""
    model_config = ConfigDict(protected_namespaces=())
    id_requisicao: str = Field(..., min_length=1)
    model_ref: str = Field(..., description="Path do modelo salvo (retornado por criar-modelo-ml)")
    dataset_ref: Optional[str] = Field(None, description="Path do dataset (Parquet) para prever em lote")
    dados: Optional[List[Dict[str, Any]]] = Field(None, description="Linhas para previsão em tempo real (ex.: um registro no chat)")
    usuario: Optional[str] = None


class PrevisaoOutput(BaseModel):
    """Saída com previsões e metadados."""
    id_requisicao: str
    previsoes: List[Any] = Field(..., description="Valores previstos (um por linha de entrada)")
    dataset_com_previsao_ref: Optional[str] = Field(None, description="Path do dataset com coluna de previsão salva (quando dataset_ref foi usado)")
    total_previsto: int = Field(..., description="Quantidade de previsões retornadas")
    modelo_usado: Optional[str] = Field(None, description="Nome do modelo aplicado")
    metricas_negocio: Optional[Dict[str, Any]] = Field(None, description="Ex.: quantidade_por_classe, valor_em_risco")
    intervalos_confianca: Optional[List[Dict[str, Any]]] = Field(None, description="Para regressão: [{'lower': x, 'upper': y}, ...]")
    erro_validacao: Optional[str] = Field(None, description="Mensagem se dados não batem com o schema do modelo")
