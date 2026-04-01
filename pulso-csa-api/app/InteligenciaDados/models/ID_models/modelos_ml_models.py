# Models para o agente de Criação de Modelos de ML (ID)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelosMLInput(BaseModel):
    id_requisicao: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    retorno_analise_estatistica: Optional[Dict[str, Any]] = Field(None, description="Saída de /analise-estatistica (opcional)")
    dataset_ref: Optional[str] = Field(None, description="Path do dataset tratado – suficiente para treinar modelo sob demanda")
    variavel_alvo: Optional[str] = Field(None, description="Coluna alvo, ex.: churn, fraude")
    tipo_problema: Optional[str] = Field(None, description="classificacao | regressao")
    versao: Optional[str] = Field(None, description="Nome da versão do modelo (ex.: v2); se omitido, gera automaticamente modelo_v1, modelo_v2...")
    acuracia_minima: Optional[float] = Field(None, description="Limiar mínimo de acurácia (padrão: 0.70 ou ML_ACURACIA_MINIMA env)")
    aplicar_balanceamento: Optional[bool] = Field(False, description="Aplicar técnicas de balanceamento de classes (SMOTE) durante o treinamento")


class ModelosMLOutput(BaseModel):
    """Saída do agente de criação de modelos ML."""
    model_config = ConfigDict(protected_namespaces=())

    id_requisicao: str
    modelo_ml: Dict[str, Any] = Field(
        ...,
        description="modelo_escolhido, motivo, resultados, constatacoes, melhorias_recomendadas, importancia_variaveis, metricas_negocio",
    )
    model_ref: Optional[str] = Field(None, description="Path do modelo salvo para uso em previsão em tempo real")
    lista_model_refs: Optional[List[str]] = Field(None, description="Todos os model_ref disponíveis para esta requisição (A/B)")
