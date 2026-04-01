from typing import Any, Dict

from app.core.openai.agent_base import BaseAgent
from app.InteligenciaDados.models.ID_models.query_get_models import (
    QueryGetInput,
    QueryGetOutput,
)
from app.InteligenciaDados.services.ID_services.query_get_service import QueryGetService


class QueryGetAgent(BaseAgent):
    """
    Agente de Inteligência de Dados (NL -> SQL -> DB -> NL).

    Pode ser utilizado por:
    - Routers (HTTP)
    - Workflows internos
    - Orquestradores de agentes
    """

    def __init__(self) -> None:
        self._service = QueryGetService()

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Executa o agente.

        Espera receber os mesmos campos definidos em QueryGetInput.
        """
        self._safe_print("QueryGetAgent iniciado")

        try:
            payload = QueryGetInput(**kwargs)
        except Exception as e:
            raise ValueError(f"Payload inválido para QueryGetAgent: {e}")

        result: QueryGetOutput = self._service.run(payload)

        self._safe_print("QueryGetAgent finalizado")

        # BaseAgent exige Dict[str, Any]
        return result.model_dump()