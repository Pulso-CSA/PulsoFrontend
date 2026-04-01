#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, List
from services.agents.analise_services import backend_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente – Análise do Backend❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def analyze_backend(
    id_requisicao: str,
    estrutura_arquivos: Dict[str, List[str]],
    refined_prompt: str = "",
) -> Dict:
    """
    Gera o documento de backend:
      - define conteúdo por arquivo
      - lista funcionalidades e conexões
      - propõe otimizações de performance e segurança
    Persiste o resultado no MongoDB.
    refined_prompt: pedido do usuário (CLI, API, Streamlit, etc.) para análise contextual.
    """
    return service.generate_backend_doc(id_requisicao, estrutura_arquivos, refined_prompt)
