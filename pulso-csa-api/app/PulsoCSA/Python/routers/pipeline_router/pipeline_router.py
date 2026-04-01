#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Rotas do Pipeline (11 → 13.2)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter, Depends, HTTPException
from core.auth import auth_and_rate_limit
from core.entitlement.deps import require_valid_access
from utils.log_manager import add_log
from utils.path_validation import sanitize_root_path, is_production
from utils.idempotency import gerar_run_id, gerar_correlation_id, verificar_idempotency_key, registrar_idempotency_key

from models.pipeline_models.pipeline_models import (
    TesteAutomatizadoRequest,
    TesteAutomatizadoResponse,
    AnaliseRetornoRequest,
    AnaliseRetornoResponse,
    CorrecaoErrosRequest,
    CorrecaoErrosResponse,
    SegurancaCodigoPosRequest,
    SegurancaCodigoPosResponse,
    SegurancaInfraPosRequest,
    SegurancaInfraPosResponse,
)
from services.pipeline_services import (
    run_teste_automatizado,
    run_analise_retorno,
    run_correcao_erros,
    run_seguranca_codigo_pos,
    run_seguranca_infra_pos,
)

router = APIRouter(prefix="/pipeline", tags=["Pipeline (11–13.2)"])
SOURCE = "pipeline"


#━━━━━━━━━❮11 – Teste Automatizado Local❯━━━━━━━━━
def _sanitize_payload_root_path(payload, path_attr="root_path"):
    """Se payload tiver root_path, sanitiza e retorna payload atualizado ou 400."""
    rp = getattr(payload, path_attr, None)
    if not rp:
        return payload
    safe = sanitize_root_path(rp)
    if not safe:
        raise HTTPException(status_code=400, detail={"code": "ROOT_PATH_INVALID", "message": "root_path inválido ou fora do permitido."})
    return payload.model_copy(update={path_attr: safe})


@router.post("/teste-automatizado", response_model=TesteAutomatizadoResponse)
async def endpoint_teste_automatizado(payload: TesteAutomatizadoRequest, user: dict = Depends(require_valid_access)):
    """Executa testes no backend/ambiente (venv ou docker). Requer autenticação."""
    # Idempotência
    if payload.idempotency_key:
        is_new, cached_response = verificar_idempotency_key(payload.idempotency_key)
        if not is_new:
            return TesteAutomatizadoResponse(**cached_response)
    # Correlation ID
    correlation_id = payload.correlation_id or gerar_correlation_id(payload.id_requisicao, "teste-automatizado")
    run_id = gerar_run_id("test")
    payload = _sanitize_payload_root_path(payload)
    add_log("info", f"teste-automatizado iniciado | id_requisicao={payload.id_requisicao} run_id={run_id}", SOURCE)
    try:
        out = run_teste_automatizado(payload)
        out.run_id = run_id
        out.correlation_id = correlation_id
        add_log("info", f"teste-automatizado concluído | id_requisicao={payload.id_requisicao} status={out.relatorio_testes.status}", SOURCE)
        # Registrar idempotência
        if payload.idempotency_key:
            registrar_idempotency_key(payload.idempotency_key, out.model_dump())
        return out
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"teste-automatizado falhou: {type(e).__name__}", SOURCE)
        msg = "Erro no teste automatizado." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "TESTE_AUTOMATIZADO_FAILED", "message": msg})


#━━━━━━━━━❮12 – Análise de Retorno❯━━━━━━━━━
@router.post("/analise-retorno", response_model=AnaliseRetornoResponse)
async def endpoint_analise_retorno(payload: AnaliseRetornoRequest, user: dict = Depends(require_valid_access)):
    """Analisa resultado dos testes. Retorna objetivo_final, falhas, vulnerabilidades, faltantes."""
    add_log("info", f"analise-retorno iniciada | id_requisicao={payload.id_requisicao}", SOURCE)
    try:
        out = run_analise_retorno(payload)
        add_log("info", f"analise-retorno concluída | id_requisicao={payload.id_requisicao} objetivo={out.analise_retorno.objetivo_final}", SOURCE)
        return out
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"analise-retorno falhou: {type(e).__name__}", SOURCE)
        msg = "Erro na análise de retorno." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "ANALISE_RETORNO_FAILED", "message": msg})


#━━━━━━━━━❮13 – Correção de Erros❯━━━━━━━━━
@router.post("/correcao-erros", response_model=CorrecaoErrosResponse)
async def endpoint_correcao_erros(payload: CorrecaoErrosRequest, user: dict = Depends(require_valid_access)):
    """
    Ajusta falhas identificadas. Input: id_requisicao + analise_retorno + root_path.
    Chama workflow de correção e retorna correcao + workflow_result.
    """
    payload = _sanitize_payload_root_path(payload)
    try:
        return run_correcao_erros(payload)
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"correcao-erros falhou: {type(e).__name__}", SOURCE)
        msg = "Erro na correção de erros." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "CORRECAO_ERROS_FAILED", "message": msg})


#━━━━━━━━━❮13.1 – Segurança Código (pós-correção)❯━━━━━━━━━
@router.post("/seguranca-codigo-pos", response_model=SegurancaCodigoPosResponse)
async def endpoint_seguranca_codigo_pos(payload: SegurancaCodigoPosRequest, user: dict = Depends(require_valid_access)):
    """Revalida código após correções. Retorna corrigidas, pendentes, recomendacoes."""
    add_log("info", f"seguranca-codigo-pos iniciada | id_requisicao={payload.id_requisicao}", SOURCE)
    try:
        out = run_seguranca_codigo_pos(payload)
        add_log("info", f"seguranca-codigo-pos concluída | id_requisicao={payload.id_requisicao}", SOURCE)
        return out
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"seguranca-codigo-pos falhou: {type(e).__name__}", SOURCE)
        msg = "Erro em seguranca-codigo-pos." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SEGURANCA_CODIGO_POS_FAILED", "message": msg})


#━━━━━━━━━❮13.2 – Segurança Infra (pós-correção)❯━━━━━━━━━
@router.post("/seguranca-infra-pos", response_model=SegurancaInfraPosResponse)
async def endpoint_seguranca_infra_pos(payload: SegurancaInfraPosRequest, user: dict = Depends(require_valid_access)):
    """Revalida infra após correções. Retorna corrigidas, pendentes, recomendacoes."""
    add_log("info", f"seguranca-infra-pos iniciada | id_requisicao={payload.id_requisicao}", SOURCE)
    try:
        out = run_seguranca_infra_pos(payload)
        add_log("info", f"seguranca-infra-pos concluída | id_requisicao={payload.id_requisicao}", SOURCE)
        return out
    except HTTPException:
        raise
    except Exception as e:
        add_log("error", f"seguranca-infra-pos falhou: {type(e).__name__}", SOURCE)
        msg = "Erro em seguranca-infra-pos." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "SEGURANCA_INFRA_POS_FAILED", "message": msg})
