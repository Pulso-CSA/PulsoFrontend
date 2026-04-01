# Agente de Análise Inicial dos Dados (ID)
from typing import Any, Dict

from app.core.openai.agent_base import BaseAgent
from app.InteligenciaDados.models.ID_models.analise_dados_models import AnaliseDadosInicialInput, AnaliseDadosInicialOutput
from app.InteligenciaDados.services.ID_services.analise_dados_service import AnaliseDadosService


class AnaliseDadosAgent(BaseAgent):
    """
    Agente ID: interpreta captura, propõe objetivos e variáveis alvo. Usa LLM.
    """

    def __init__(self) -> None:
        self._service = AnaliseDadosService()

    def run(self, **kwargs) -> Dict[str, Any]:
        payload = AnaliseDadosInicialInput(**kwargs)
        result: AnaliseDadosInicialOutput = self._service.run(payload)
        return result.model_dump()
