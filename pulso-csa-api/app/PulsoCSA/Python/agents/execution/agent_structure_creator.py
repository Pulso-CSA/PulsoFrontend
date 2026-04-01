#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente de Criação de Estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from services.agents.creator_services import structure_creator_service as service


def create_structure_from_report(root_path: str, id_requisicao: str):
    """
    Lê o relatório da camada 2 e cria fisicamente as pastas e arquivos
    dentro do root_path informado pelo usuário.
    """
    return service.generate_structure_from_report(root_path, id_requisicao)
