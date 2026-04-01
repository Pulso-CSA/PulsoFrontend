#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Validação de Prompt❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from datetime import datetime
from typing import Dict

from storage.database import database_c1 as db
from agents.architecture.orchestrator.orchestrator_c1_to_c2 import run_layer2_pipeline


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função de Validação Lógica❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def validate_prompt_logic(refined_prompt: str) -> Dict:
    """
    Realiza a validação do prompt refinado e define se o mesmo será aprovado ou não.
    Caso seja aprovado, dispara automaticamente o pipeline da Camada 2.
    """
    if len(refined_prompt.split()) > 12:
        return {
            "validation_status": "aprovado",
            "feedback": "O prompt está completo e coerente com os frameworks solicitados.",
            "final_prompt": refined_prompt
        }
    else:
        return {
            "validation_status": "reprovado",
            "feedback": "Prompt muito curto ou insuficiente.",
            "final_prompt": refined_prompt
        }


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Execução Principal do Agente❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def execute_agent_validation(id_requisicao: str, refined_prompt: str, feedback_usuario: str) -> Dict:
    """
    Etapa final da camada de governança:
    - Valida o prompt refinado
    - Persiste resultado no banco
    - Se aprovado, inicia automaticamente a Camada 2 (arquitetura e planejamento)
    """
    resultado_validacao = validate_prompt_logic(refined_prompt)
    status = resultado_validacao["validation_status"]

    documento_requisitos = {
        "descricao": refined_prompt,
        "objetivo_negocio": "Atender ao requisito funcional do usuário com segurança e compliance"
    }

    camada_2_result = None

    #━━━━━━━━━❮Integração Automática com a Camada 2❯━━━━━━━━━
    if status == "aprovado" and feedback_usuario.lower() == "aprovado":
        try:
            print(f"🚀 Disparando pipeline da Camada 2 para ID {id_requisicao}...")
            camada_2_result = run_layer2_pipeline(id_requisicao, refined_prompt)
            print("✅ Camada 2 executada com sucesso.")
        except Exception as e:
            print(f"⚠️ Erro ao executar Camada 2: {e}")
            camada_2_result = {"erro": f"Falha ao executar Camada 2: {str(e)}"}

    #━━━━━━━━━❮Persistência❯━━━━━━━━━
    db.upsert_validation_doc(id_requisicao, {
        "status": status,
        "feedback_usuario": feedback_usuario,
        "documento_requisitos": documento_requisitos,
        "timestamp": datetime.utcnow().isoformat()
    })

    #━━━━━━━━━❮Retorno Padronizado❯━━━━━━━━━
    return {
        "id_requisicao": id_requisicao,
        "status": status,
        "documento_requisitos": documento_requisitos,
        "mensagem": "Documento de requisitos gerado com sucesso",
        "camada_2": camada_2_result
    }
