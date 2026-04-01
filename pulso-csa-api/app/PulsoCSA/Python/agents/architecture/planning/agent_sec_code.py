#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Dict
from services.agents.analise_services import sec_code_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente – Segurança de Código❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def analyze_code_security(id_requisicao: str, backend_doc: Dict) -> Dict:
    """
    Analisa segurança do backend com base em padrões OWASP, NIST e DevSecOps.
    Retorna relatório de vulnerabilidades e recomendações.
    """
    return service.generate_code_security_report(id_requisicao, backend_doc)
