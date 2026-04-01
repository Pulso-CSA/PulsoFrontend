#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Recebimento de Prompt Inicial❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from datetime import datetime
import uuid
from storage.database import database_c1 as db_c1


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal do Serviço❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def register_input(
    prompt: str,
    usuario: str,
    root_path: str = None,
    id_requisicao: str | None = None,
):
    """
    Recebe o prompt inicial, gera um ID de requisição e salva no MongoDB.
    Agora inclui o campo opcional root_path para armazenar o caminho base de execução.
    Se id_requisicao for passado (ex.: camada 1 já gerou REQ-...), usa o mesmo em todo o pipeline.
    Retorna um dicionário padronizado com os dados do input.
    """
    if not id_requisicao or not str(id_requisicao).strip():
        id_requisicao = f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    else:
        id_requisicao = str(id_requisicao).strip()
    summary = prompt[:80] + "..." if len(prompt) > 80 else prompt

    input_doc = {
        "id_requisicao": id_requisicao,
        "prompt": prompt,
        "usuario": usuario,
        "status": "recebido",
        "content_summary": summary,
        "timestamp": datetime.utcnow().isoformat(),
        "root_path": root_path  # ✅ Novo campo adicionado
    }

    #━━━━━━━━━❮Persistência❯━━━━━━━━━
    db_c1.upsert_input(id_requisicao, input_doc)

    #━━━━━━━━━❮Retorno Padronizado❯━━━━━━━━━
    return input_doc
