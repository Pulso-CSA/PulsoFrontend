#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente de Criação de Código❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from services.agents.creator_services import code_creator_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def create_code_from_reports(root_path: str, id_requisicao: str):
    """
    Lê os relatórios da camada 2 e o manifesto da estrutura (C3.1),
    e gera os arquivos de código-fonte dentro da pasta 'generated_code',
    utilizando LLM + contexto RAG para geração inteligente.
    """
    return service.generate_code_from_reports(root_path, id_requisicao)
