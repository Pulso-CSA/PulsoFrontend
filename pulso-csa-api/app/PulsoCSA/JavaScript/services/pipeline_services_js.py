#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Pipeline de Autocorreção – JavaScript❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

"""
Serviços de pipeline para projetos JavaScript/TypeScript/React.
- run_analise_retorno: reutiliza o serviço Python (agnóstico de linguagem)
- run_correcao_erros_js: chama run_correct_workflow_js em vez do Python
- run_seguranca_codigo_pos_js / run_seguranca_infra_pos_js: versões simplificadas para JS
"""

from utils.log_manager import add_log

try:
    from models.pipeline_models.pipeline_models import (
        AnaliseRetornoRequest,
        AnaliseRetornoResponse,
        CorrecaoErrosRequest,
        CorrecaoErrosResponse,
        CorrecaoPayload,
        SegurancaCodigoPosRequest,
        SegurancaCodigoPosResponse,
        SegurancaCodigoPosPayload,
        SegurancaInfraPosRequest,
        SegurancaInfraPosResponse,
        SegurancaInfraPosPayload,
    )
except ImportError:
    from app.PulsoCSA.Python.models.pipeline_models.pipeline_models import (
        AnaliseRetornoRequest,
        AnaliseRetornoResponse,
        CorrecaoErrosRequest,
        CorrecaoErrosResponse,
        CorrecaoPayload,
        SegurancaCodigoPosRequest,
        SegurancaCodigoPosResponse,
        SegurancaCodigoPosPayload,
        SegurancaInfraPosRequest,
        SegurancaInfraPosResponse,
        SegurancaInfraPosPayload,
    )


def run_analise_retorno_js(req: AnaliseRetornoRequest) -> AnaliseRetornoResponse:
    """
    Reutiliza o serviço Python de análise de retorno (agnóstico de linguagem).
    """
    try:
        from app.PulsoCSA.Python.services.pipeline_services.analise_retorno_service import (
            run_analise_retorno,
        )
        return run_analise_retorno(req)
    except ImportError:
        from services.pipeline_services.analise_retorno_service import run_analise_retorno
        return run_analise_retorno(req)


def run_correcao_erros_js(
    req: CorrecaoErrosRequest,
    run_pipeline_autocorrection: bool = False,
) -> CorrecaoErrosResponse:
    """
    Correção de erros para projetos JS: chama run_correct_workflow_js
    com modo only_c4_c5 (C4 implementer + C5 teste).
    """
    add_log("info", f"[correcao-erros-js] Iniciando para id_requisicao={req.id_requisicao}", "pipeline_js")

    from app.PulsoCSA.JavaScript.workflow.correct_workflow.workflow_core_cor_js import (
        run_correct_workflow_js,
    )

    prompt_parts = [
        "Corrigir o sistema JavaScript/TypeScript/React com base na análise de retorno. "
        "REGRA: alteração mínima — altere apenas o estritamente necessário.",
        f"- Objetivo final: {req.analise_retorno.objetivo_final}.",
        "",
    ]
    if req.analise_retorno.falhas:
        prompt_parts.append("Falhas a corrigir:")
        for f in req.analise_retorno.falhas:
            prompt_parts.append(f"  • {f}")
        prompt_parts.append("")
    if req.analise_retorno.vulnerabilidades:
        prompt_parts.append("Vulnerabilidades a mitigar:")
        for v in req.analise_retorno.vulnerabilidades:
            prompt_parts.append(f"  • {v}")
        prompt_parts.append("")
    if req.analise_retorno.faltantes:
        prompt_parts.append("Itens faltantes:")
        for x in req.analise_retorno.faltantes:
            prompt_parts.append(f"  • {x}")

    prompt = "\n".join(prompt_parts)

    result = run_correct_workflow_js(
        log_type="info",
        prompt=prompt,
        usuario=req.usuario,
        root_path=req.root_path,
        run_pipeline_autocorrection=run_pipeline_autocorrection,
        only_c4_c5=True,
        id_requisicao_override=req.id_requisicao,
    )

    erros_corrigidos = list(req.analise_retorno.falhas)[:5]
    funcionalidades_atualizadas = result.get("corrected_files") or []
    estrutura_atualizada = []

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


def run_seguranca_codigo_pos_js(req: SegurancaCodigoPosRequest) -> SegurancaCodigoPosResponse:
    """
    Segurança de código pós-correção para JS.
    Versão simplificada: analisa relatório de correção e retorna payload.
    """
    add_log("info", f"[seguranca-codigo-pos-js] Iniciando para id_requisicao={req.id_requisicao}", "pipeline_js")
    corrigidas = list(req.relatorio_correcao.erros_corrigidos or [])[:5]
    payload = SegurancaCodigoPosPayload(
        corrigidas=corrigidas,
        pendentes=["Verificar boas práticas OWASP para frontend"],
        recomendacoes=["Evitar eval em input de usuário", "Validar props e sanitizar dados"],
    )
    return SegurancaCodigoPosResponse(
        id_requisicao=req.id_requisicao,
        seguranca_codigo_pos=payload,
    )


def run_seguranca_infra_pos_js(req: SegurancaInfraPosRequest) -> SegurancaInfraPosResponse:
    """
    Segurança de infra pós-correção para JS.
    Versão simplificada para projetos frontend.
    """
    add_log("info", f"[seguranca-infra-pos-js] Iniciando para id_requisicao={req.id_requisicao}", "pipeline_js")
    corrigidas = list(req.relatorio_correcao.estrutura_atualizada or [])[:5]
    payload = SegurancaInfraPosPayload(
        corrigidas=corrigidas,
        pendentes=["Verificar variáveis de ambiente e secrets"],
        recomendacoes=["Não expor API keys no frontend", "Usar HTTPS em produção"],
    )
    return SegurancaInfraPosResponse(
        id_requisicao=req.id_requisicao,
        seguranca_infra_pos=payload,
    )
