#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮13.1 – Segurança Código (pós-correção)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from utils.log_manager import add_log
from agents.architecture.planning.agent_sec_code import analyze_code_security
from storage.database.creation_analyse import database_c2 as db_c2
from models.pipeline_models.pipeline_models import (
    SegurancaCodigoPosRequest,
    SegurancaCodigoPosResponse,
    SegurancaCodigoPosPayload,
)


def run_seguranca_codigo_pos(req: SegurancaCodigoPosRequest) -> SegurancaCodigoPosResponse:
    """
    Revalida o código após correções. Reutiliza agent_sec_code (análise estática/dinâmica).
    """
    add_log("info", f"[seguranca-codigo-pos] Iniciando para id_requisicao={req.id_requisicao}", "pipeline")
    backend_doc = req.backend_doc
    if not backend_doc:
        doc = db_c2.get_architecture_doc(req.id_requisicao)
        if doc:
            backend_doc = doc.get("backend_doc") or {}
        else:
            backend_doc = {}

    report = analyze_code_security(req.id_requisicao, backend_doc)
    corrigidas: list[str] = []
    pendentes: list[str] = []
    recomendacoes: list[str] = []

    if isinstance(report, dict):
        vuln = report.get("vulnerabilidades_potenciais") or report.get("vulnerabilidades") or []
        rec = report.get("recomendacoes") or []
        for v in vuln[:10]:
            if isinstance(v, dict):
                pendentes.append(v.get("descricao") or v.get("id") or str(v)[:200])
            else:
                pendentes.append(str(v)[:200])
        for r in rec[:10]:
            if isinstance(r, dict):
                recomendacoes.append(r.get("acao") or r.get("justificativa") or str(r)[:200])
            else:
                recomendacoes.append(str(r)[:200])
        # Corrigidas: itens do relatório de correção que tocam segurança
        for item in (req.relatorio_correcao.erros_corrigidos or [])[:5]:
            corrigidas.append(item)

    payload = SegurancaCodigoPosPayload(
        corrigidas=corrigidas,
        pendentes=pendentes if pendentes else ["Nenhuma vulnerabilidade pendente identificada"],
        recomendacoes=recomendacoes if recomendacoes else ["Manter boas práticas OWASP"],
    )
    return SegurancaCodigoPosResponse(
        id_requisicao=req.id_requisicao,
        seguranca_codigo_pos=payload,
    )
