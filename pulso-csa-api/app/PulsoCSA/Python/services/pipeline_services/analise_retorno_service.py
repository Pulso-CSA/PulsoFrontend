#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮12 – Análise de Retorno❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from utils.log_manager import add_log
from models.pipeline_models.pipeline_models import (
    AnaliseRetornoRequest,
    AnaliseRetornoResponse,
    AnaliseRetornoPayload,
    RelatorioTestes,
)


def run_analise_retorno(req: AnaliseRetornoRequest) -> AnaliseRetornoResponse:
    """
    Analisa resultado dos testes e verifica se objetivos foram atingidos.
    Cruza relatório de /teste-automatizado + contexto (estrutura/backend/tela);
    retorna objetivo_final, falhas, vulnerabilidades, faltantes, relatorio_logs.
    """
    add_log("info", f"[analise-retorno] Iniciando para id_requisicao={req.id_requisicao}", "pipeline")
    rt: RelatorioTestes = req.relatorio_testes

    falhas = list(rt.erros)
    vulnerabilidades = list(rt.vulnerabilidades)
    relatorio_logs = "\n".join(rt.logs) if rt.logs else None

    # Objetivo: atingido só se aprovado e sem erros/vulnerabilidades
    if rt.status == "aprovado" and not rt.erros and not rt.vulnerabilidades:
        objetivo_final = "atingido"
    else:
        objetivo_final = "não atingido"

    # Faltantes: inferido a partir de erros comuns (pode ser expandido com LLM depois)
    faltantes: list[str] = []
    for e in rt.erros:
        e_lower = e.lower()
        if "docker" in e_lower or "compose" in e_lower:
            faltantes.append("configuração docker-compose ou containers")
        elif "venv" in e_lower or "requirements" in e_lower:
            faltantes.append("ambiente virtual ou requirements.txt")
        elif "import" in e_lower or "module" in e_lower:
            faltantes.append("dependências ou imports corretos")

    payload = AnaliseRetornoPayload(
        objetivo_final=objetivo_final,
        falhas=falhas,
        vulnerabilidades=vulnerabilidades,
        faltantes=faltantes if faltantes else ["verificar logs para detalhes"],
        relatorio_logs=relatorio_logs,
    )
    return AnaliseRetornoResponse(
        id_requisicao=req.id_requisicao,
        analise_retorno=payload,
    )
