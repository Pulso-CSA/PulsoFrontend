#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from services.agents.analise_services import input_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def receive_prompt(
    prompt: str,
    usuario: str,
    root_path: str = None,
    id_requisicao: str | None = None,
):
    """
    Recebe o prompt inicial, gera um ID de requisição e salva no MongoDB.
    Agora inclui o campo opcional root_path para armazenar o caminho base de execução.
    id_requisicao opcional: quando definido (ex.: REQ-... da camada 1), evita dois IDs diferentes no Mongo.
    Retorna um dicionário padronizado com os dados do input.
    """
    return service.register_input(prompt, usuario, root_path, id_requisicao=id_requisicao)
