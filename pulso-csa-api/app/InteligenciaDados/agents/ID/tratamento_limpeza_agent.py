# Agente de Tratamento e Limpeza (ID)
from typing import Any, Dict

from app.core.openai.agent_base import BaseAgent
from app.InteligenciaDados.models.ID_models.tratamento_limpeza_models import TratamentoLimpezaInput, TratamentoLimpezaOutput
from app.InteligenciaDados.services.ID_services.tratamento_limpeza_service import TratamentoLimpezaService


class TratamentoLimpezaAgent(BaseAgent):
    """
    Agente ID: pipeline de ETL e limpeza. Modular e configurável.
    """

    def __init__(self) -> None:
        self._service = TratamentoLimpezaService()

    def run(self, **kwargs) -> Dict[str, Any]:
        payload = TratamentoLimpezaInput(**kwargs)
        result: TratamentoLimpezaOutput = self._service.run(payload)
        return result.model_dump()
