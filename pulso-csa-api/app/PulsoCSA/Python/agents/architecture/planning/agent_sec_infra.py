#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Dict
from services.agents.analise_services import sec_infra_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente – Segurança de Infraestrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def analyze_infra_security(id_requisicao: str, infra_doc: Dict) -> Dict:
    """Analisa segurança da infraestrutura planejada e gera relatório JSON com riscos, recomendações e checklist."""
    return service.generate_infra_security_report(id_requisicao, infra_doc)
