#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮FinOps Agent – Orquestrador❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
Agente orquestrador com fallback determinístico.
Delega ao service; em caso de falha, retorna análise básica.
"""
from models.finops.finops_models import FinOpsAnalyzeRequest
from services.finops.finops_services import run_finops_analyze


def run_finops_agent(req: FinOpsAnalyzeRequest) -> dict[str, str]:
    """
    Executa análise FinOps. O service já contém fallback determinístico
    quando o LLM falha; o agent apenas delega.
    """
    return run_finops_analyze(req)
