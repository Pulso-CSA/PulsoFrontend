#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from services.agents.analise_services import refine_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal – Refino com RAG❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def refine_prompt(prompt: str):
    """
    Refina o prompt utilizando RAG (busca semântica com LangChain e OpenAI).
    Carrega o prompt base de refino (base_refine.txt) e combina com contexto RAG.
    Se o RAG falhar, faz fallback para geração direta.
    """
    return service.execute_refine_prompt(prompt)
