#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
from abc import ABC, abstractmethod
from typing import Any, Dict

#━━━━━━━━━❮Classe Base dos Agentes❯━━━━━━━━━
class BaseAgent(ABC):
    """
    Classe base abstrata para todos os agentes do sistema.
    """

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """Executa a ação principal do agente"""
        pass

    @staticmethod
    def _safe_print(msg: str):
        print(f"[AGENT] {msg}")
