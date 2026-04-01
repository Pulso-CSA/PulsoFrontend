#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮13 – Correção de Erros❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from utils.log_manager import add_log
from models.pipeline_models.pipeline_models import (
    CorrecaoErrosRequest,
    CorrecaoErrosResponse,
    CorrecaoPayload,
    AnaliseRetornoPayload,
)


def _build_prompt_from_analise(analise: AnaliseRetornoPayload) -> str:
    """Monta prompt técnico para o workflow de correção a partir da análise de retorno."""
    parts = [
        "Corrigir o sistema com base na análise de retorno. REGRA: alteração mínima — altere apenas o estritamente necessário; preserve ao máximo o código original (estilo, estrutura).",
        f"- Objetivo final: {analise.objetivo_final}.",
        "",
    ]
    if analise.falhas:
        parts.append("Falhas a corrigir:")
        for f in analise.falhas:
            parts.append(f"  • {f}")
        parts.append("")
    if analise.vulnerabilidades:
        parts.append("Vulnerabilidades a mitigar:")
        for v in analise.vulnerabilidades:
            parts.append(f"  • {v}")
        parts.append("")
    if analise.faltantes:
        parts.append("Itens faltantes a implementar ou ajustar:")
        for x in analise.faltantes:
            parts.append(f"  • {x}")
    return "\n".join(parts)


def run_correcao_erros(
    req: CorrecaoErrosRequest,
    run_pipeline_autocorrection: bool = False,
) -> CorrecaoErrosResponse:
    """
    Ajusta falhas identificadas: chama o workflow de correção com prompt
    gerado a partir do relatório de /analise-retorno. Reutiliza run_correct_workflow.
    run_pipeline_autocorrection=False evita recursão quando chamado de dentro do workflow.
    """
    add_log("info", f"[correcao-erros] Iniciando para id_requisicao={req.id_requisicao}", "pipeline")
    prompt = _build_prompt_from_analise(req.analise_retorno)

    # Import aqui para evitar import circular (workflow_core_cor → pipeline_services → correcao_erros → workflow_core_cor)
    from workflow.correct_workflow.workflow_core_cor import run_correct_workflow

    # Retry barato: só C4 (implementer) + C5 (teste), reutilizando code plan existente.
    result = run_correct_workflow(
        log_type="info",
        prompt=prompt,
        usuario=req.usuario,
        root_path=req.root_path,
        run_pipeline_autocorrection=run_pipeline_autocorrection,
        only_c4_c5=True,
        id_requisicao_override=req.id_requisicao,
    )

    # Mapeia resultado do workflow para o payload de correção
    erros_corrigidos = list(req.analise_retorno.falhas)[:5]  # itens que foram alvo da correção
    funcionalidades_atualizadas = []
    estrutura_atualizada = []
    if result.get("execucao"):
        execucao = result["execucao"]
        if isinstance(execucao, dict):
            funcionalidades_atualizadas = execucao.get("created_files") or []
            estrutura_atualizada = execucao.get("touched_dirs") or []

    correcao = CorrecaoPayload(
        erros_corrigidos=erros_corrigidos,
        funcionalidades_atualizadas=funcionalidades_atualizadas,
        estrutura_atualizada=estrutura_atualizada,
        status="corrigido e aguardando validação",
    )
    return CorrecaoErrosResponse(
        id_requisicao=req.id_requisicao,
        correcao=correcao,
        workflow_result=result,
    )
