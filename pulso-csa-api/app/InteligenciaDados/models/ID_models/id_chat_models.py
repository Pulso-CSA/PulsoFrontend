# Models para Chat ID – orquestrador de alto nível (captura → análise → modelo → previsão)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IDChatInput(BaseModel):
    """Entrada do chat: mensagem em linguagem natural + contexto opcional."""
    model_config = ConfigDict(protected_namespaces=())
    mensagem: str = Field(..., min_length=1, max_length=4096, description="Pergunta ou comando em linguagem natural")
    id_requisicao: str = Field(..., min_length=1, max_length=128)
    usuario: Optional[str] = Field(None, max_length=256)
    dataset_ref: Optional[str] = Field(None, max_length=2048, description="Dataset já disponível (ex.: após captura/tratamento)")
    model_ref: Optional[str] = Field(None, max_length=2048, description="Modelo já treinado (para só prever)")
    retorno_captura: Optional[Dict[str, Any]] = Field(None, description="Saída anterior de captura (opcional)")
    dados_para_prever: Optional[List[Dict[str, Any]]] = Field(None, description="Registros para previsão em tempo real")
    db_config: Optional[Dict[str, Any]] = Field(None, description="Conexão ao banco (MySQL/MongoDB) para captura no chat")


class IDChatOutput(BaseModel):
    """Resposta unificada: texto + etapas executadas + previsões quando houver."""
    model_config = ConfigDict(protected_namespaces=())
    id_requisicao: str
    resposta_texto: str = Field(..., description="Resposta em linguagem natural para o usuário")
    etapas_executadas: List[str] = Field(default_factory=list, description="Ex.: ['analise_estatistica','criar_modelo_ml','prever']")
    previsoes: Optional[List[Any]] = Field(None, description="Previsões quando a mensagem pediu previsão")
    distribuicao_previsoes: Optional[Dict[str, int]] = Field(None, description="Contagem por classe (ex.: {Yes: 120, No: 380})")
    metricas_modelo_previsao: Optional[Dict[str, Any]] = Field(None, description="Métricas do modelo usado (acuracia, auc, etc.) quando disponíveis")
    exemplos_previsao: Optional[List[Dict[str, Any]]] = Field(None, description="Amostra de previsões com índice (ex.: [{indice: 0, previsao: Yes}, ...])")
    analise_estatistica: Optional[Dict[str, Any]] = Field(None, description="Resultado de análise estatística quando aplicável")
    modelo_ml: Optional[Dict[str, Any]] = Field(None, description="Resultado do treino quando aplicável")
    dataset_ref: Optional[str] = Field(None, description="Path do dataset atualizado/gerado")
    model_ref: Optional[str] = Field(None, description="Path do modelo treinado (para próximas previsões)")
    sugestao_proximo_passo: Optional[str] = Field(None, description="Sugestão do assistente para o próximo passo")
