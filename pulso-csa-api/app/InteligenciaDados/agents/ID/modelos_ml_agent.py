# Agente de Criação de Modelos de ML (ID)
from typing import Any, Dict

from app.core.openai.agent_base import BaseAgent
from app.InteligenciaDados.models.ID_models.modelos_ml_models import ModelosMLInput, ModelosMLOutput
from app.InteligenciaDados.services.ID_services.modelos_ml_service import ModelosMLService


class ModelosMLAgent(BaseAgent):
    """
    Agente ID: compara e seleciona modelos com limiar de qualidade. LLM explica resultados.
    """

    def __init__(self) -> None:
        self._service = ModelosMLService()

    def run(self, **kwargs) -> Dict[str, Any]:
        payload = ModelosMLInput(**kwargs)
        result: ModelosMLOutput = self._service.run(payload)
        return result.model_dump()
