#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, List
from services.agents.analise_services import structure_service as service

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente – Análise da Estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def analyze_structure(id_requisicao: str) -> Dict[str, List[str]]:
    """
    Gera blueprint detalhado de estrutura de pastas/arquivos
    e persiste no MongoDB.
    """
    return service.generate_structure_blueprint(id_requisicao)
