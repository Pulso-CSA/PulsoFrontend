# Agente de Análise Estatística (ID)
from typing import Any, Dict

from app.core.openai.agent_base import BaseAgent
from app.InteligenciaDados.models.ID_models.analise_estatistica_models import (
    AnaliseEstatisticaInput,
    AnaliseEstatisticaOutput,
)
from app.InteligenciaDados.services.ID_services.analise_estatistica_service import AnaliseEstatisticaService


class AnaliseEstatisticaAgent(BaseAgent):
    """
    Agente ID: métricas, insights e sugestão de modelos ML. Usa LLM para narrativa.
    """

    def __init__(self) -> None:
        self._service = AnaliseEstatisticaService()

    def run(self, **kwargs) -> Dict[str, Any]:
        payload = AnaliseEstatisticaInput(**kwargs)
        result: AnaliseEstatisticaOutput = self._service.run(payload)
        return result.model_dump()
