# Agente de Captura de Dados (ID)
from typing import Any, Dict

from app.core.openai.agent_base import BaseAgent
from app.InteligenciaDados.models.ID_models.captura_dados_models import CapturaDadosInput, CapturaDadosOutput
from app.InteligenciaDados.services.ID_services.captura_dados_service import CapturaDadosService


class CapturaDadosAgent(BaseAgent):
    """
    Agente ID: conecta à base externa, extrai estrutura e gera relatório.
    Usa LLM para descrever o teor dos dados.
    """

    def __init__(self) -> None:
        self._service = CapturaDadosService()

    def run(self, **kwargs) -> Dict[str, Any]:
        payload = CapturaDadosInput(**kwargs)
        result: CapturaDadosOutput = self._service.run(payload)
        return result.model_dump()
