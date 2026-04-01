#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import Dict
from services.agents.analise_services import infra_service as service


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agente – Infraestrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def analyze_infra(id_requisicao: str, estrutura_arquivos: Dict, backend_doc: Dict) -> Dict:
    """
    Analisa a infraestrutura ideal para o projeto (servidores, bancos, pipelines, etc.)
    e aplica boas práticas de segurança baseadas em OWASP, NIST e CIS Benchmarks.
    """
    return service.generate_infra_doc(id_requisicao, estrutura_arquivos, backend_doc)
