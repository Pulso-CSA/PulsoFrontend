#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Dict
from services.agents.analise_services import validate_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função de Validação do Prompt❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def validate_prompt(refined_prompt: str) -> Dict:
    """
    Realiza a validação do prompt refinado e define se o mesmo será aprovado ou não.
    Caso seja aprovado, dispara automaticamente o pipeline da Camada 2.
    """
    return service.validate_prompt_logic(refined_prompt)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente Principal de Validação❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def agent_validate(id_requisicao: str, refined_prompt: str, feedback_usuario: str) -> Dict:
    """
    Etapa final da camada de governança:
    - Valida o prompt refinado
    - Persiste resultado no banco
    - Se aprovado, inicia automaticamente a Camada 2 (arquitetura e planejamento)
    """
    return service.execute_agent_validation(id_requisicao, refined_prompt, feedback_usuario)
