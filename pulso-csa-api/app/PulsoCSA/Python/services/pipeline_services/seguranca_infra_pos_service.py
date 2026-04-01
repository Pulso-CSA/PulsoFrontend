#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮13.2 – Segurança Infra (pós-correção)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from utils.log_manager import add_log
from agents.architecture.planning.agent_sec_infra import analyze_infra_security
from storage.database.creation_analyse import database_c2 as db_c2
from models.pipeline_models.pipeline_models import (
    SegurancaInfraPosRequest,
    SegurancaInfraPosResponse,
    SegurancaInfraPosPayload,
)


def run_seguranca_infra_pos(req: SegurancaInfraPosRequest) -> SegurancaInfraPosResponse:
    """
    Revalida infraestrutura após correções. Reutiliza agent_sec_infra.
    """
    add_log("info", f"[seguranca-infra-pos] Iniciando para id_requisicao={req.id_requisicao}", "pipeline")
    infra_doc = req.analise_infra
    if not infra_doc:
        doc = db_c2.get_architecture_doc(req.id_requisicao)
        if doc:
            infra_doc = doc.get("infra_doc") or doc.get("estrutura_arquivos") or {}
        else:
            infra_doc = {}

    report = analyze_infra_security(req.id_requisicao, infra_doc)
    corrigidas: list[str] = []
    pendentes: list[str] = []
    recomendacoes: list[str] = []

    if isinstance(report, dict):
        riscos = report.get("riscos") or []
        rec = report.get("recomendacoes") or []
        for r in riscos[:10]:
            if isinstance(r, dict):
                pendentes.append(r.get("titulo") or r.get("descricao") or r.get("id") or str(r)[:200])
            else:
                pendentes.append(str(r)[:200])
        for r in rec[:10]:
            if isinstance(r, dict):
                recomendacoes.append(r.get("acao") or str(r)[:200])
            else:
                recomendacoes.append(str(r)[:200])
        for item in (req.relatorio_correcao.erros_corrigidos or [])[:5]:
            corrigidas.append(item)

    payload = SegurancaInfraPosPayload(
        corrigidas=corrigidas,
        pendentes=pendentes if pendentes else ["Nenhum risco pendente identificado"],
        recomendacoes=recomendacoes if recomendacoes else ["Seguir CIS Benchmarks e Zero Trust"],
    )
    return SegurancaInfraPosResponse(
        id_requisicao=req.id_requisicao,
        seguranca_infra_pos=payload,
    )
