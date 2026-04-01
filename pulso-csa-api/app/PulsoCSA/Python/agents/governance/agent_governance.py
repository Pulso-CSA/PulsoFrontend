#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, Any
from services.agents.analise_services import governance_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente Coordenador❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class GovernanceAgent:
    """
    Agente Coordenador das Camadas 1 e 2.
    Responsável por orquestrar o ciclo completo:
    input → refine → validate → arquitetura → segurança.
    """

    def __init__(self):
        self.logs = []

    #━━━━━━━━━❮Workflow da Camada 1❯━━━━━━━━━#
    def run_workflow(self, prompt: str, usuario: str = "desconhecido", root_path: str = None):
        """Executa o fluxo básico de governança (Camada 1)."""
        return service.execute_layer1_workflow(prompt, usuario, root_path, self.logs)

    #━━━━━━━━━❮Workflow Completo (Camadas 1 + 2)❯━━━━━━━━━#
    def run_full_workflow(self, prompt: str, usuario: str, root_path: str = None) -> Dict[str, Any]:
        """Executa automaticamente o pipeline completo (Camada 1 + Camada 2)."""
        return service.execute_full_workflow(prompt, usuario, root_path)
