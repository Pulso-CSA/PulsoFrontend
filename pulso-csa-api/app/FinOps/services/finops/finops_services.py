#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮FinOps Orchestration Service❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
Orquestra: conectores → normalização → heurísticas → LLM → narrativa.
Retorna texto final para chat (sem PDF, sem anexos).
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from app.core.openai.openai_client import get_openai_client
from models.finops.finops_models import FinOpsAnalyzeRequest
from app.prompts.loader import load_prompt
from services.finops.connectors.factory import CloudConnectorFactory
from services.finops.connectors.base import ConnectorResult
from services.finops.heuristics_engine import run_heuristics, build_guardrails_recommendations
from app.utils.log_manager import add_log

SOURCE = "finops_service"
FINOPS_TIMEOUT = 360
FALLBACK_MESSAGE = (
    "Análise FinOps indisponível no momento. Verifique credenciais e permissões. "
    "Em ambiente de desenvolvimento, instale boto3 (AWS), azure-identity (Azure) ou google-cloud-billing (GCP)."
)


def _default_dates() -> tuple[str, str]:
    end = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    return start, end


def _normalize_for_prompt(result: ConnectorResult) -> dict[str, Any]:
    """Prepara dados para o prompt (evita vazamento de credenciais)."""
    return {
        "billing": result.billing,
        "inventory": result.inventory,
        "metrics": result.metrics,
        "provider": result.provider,
        "errors": result.errors,
        "data_quality": result.data_quality,
    }


def _build_prompt_payload(
    billing: dict[str, Any],
    inventory: dict[str, Any],
    heuristics: list[dict[str, Any]],
    metrics: dict[str, Any],
    quick_win_mode: str,
    guardrails_mode: bool,
    multi_cloud: bool,
) -> str:
    """Monta o prompt com os placeholders preenchidos."""
    template = load_prompt("finops/finops_prompt")
    billing_str = json.dumps(billing, ensure_ascii=False, indent=2)[:3000]
    inv_str = json.dumps(inventory, ensure_ascii=False, indent=2)[:3000]
    heur_str = json.dumps(heuristics, ensure_ascii=False, indent=2)[:4000]
    metrics_str = json.dumps(metrics, ensure_ascii=False, indent=2)[:1500]
    return template.replace("{billing_aggregated}", billing_str).replace(
        "{inventario_resumido}", inv_str
    ).replace("{heuristica_candidatos}", heur_str).replace(
        "{metricas_resumo}", metrics_str
    ).replace("{quick_win_mode}", quick_win_mode).replace(
        "{guardrails_mode}", "sim" if guardrails_mode else "não"
    ).replace("{multi_cloud_compare}", "sim" if multi_cloud else "não")


def run_finops_analyze(req: FinOpsAnalyzeRequest) -> dict[str, str]:
    """
    Pipeline principal: conecta → coleta → heurísticas → LLM → texto.
    Retorna {"message": "<texto>"} para o chat.
    """
    id_req = f"FINOP-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    add_log("info", f"FinOps analyze iniciada | id={id_req} cloud={req.cloud}", SOURCE)

    cloud = req.cloud
    if cloud == "multi":
        cloud = "aws"
        if req.aws_credentials:
            cloud = "aws"
        elif req.azure_credentials:
            cloud = "azure"
        elif req.gcp_credentials:
            cloud = "gcp"
        else:
            return {
                "message": "Para cloud=multi, forneça credenciais de pelo menos um provedor (aws, azure ou gcp).",
                "id_requisicao": id_req,
            }

    connector = CloudConnectorFactory.create(
        cloud=cloud,
        aws_creds=req.aws_credentials,
        azure_creds=req.azure_credentials,
        gcp_creds=req.gcp_credentials,
    )
    if not connector:
        msg = f"Credenciais ausentes para {cloud}. Forneça aws_credentials, azure_credentials ou gcp_credentials conforme o provider."
        add_log("error", f"FinOps: {msg}", SOURCE)
        return {"message": msg, "id_requisicao": id_req}

    ok, preflight_msg = connector.preflight()
    if not ok:
        add_log("error", f"FinOps preflight falhou: {preflight_msg}", SOURCE)
        return {"message": f"Falha na validação: {preflight_msg}", "id_requisicao": id_req}

    start, end = req.start_date or _default_dates()[0], req.end_date or _default_dates()[1]
    try:
        result = connector.collect_all(start_date=start, end_date=end)
    except Exception as e:
        add_log("error", f"FinOps coleta falhou: {type(e).__name__}", SOURCE)
        from app.utils.path_validation import is_production
        msg = "Erro na coleta de dados." if is_production() else f"Erro na coleta de dados: {str(e)[:200]}"
        return {"message": msg, "id_requisicao": id_req}

    heuristics = run_heuristics(
        billing=result.billing,
        inventory=result.inventory,
        metrics=result.metrics,
        provider=result.provider,
        quick_win_mode=req.quick_win_mode,
        guardrails_mode=req.guardrails_mode,
    )

    prompt_body = _build_prompt_payload(
        billing=result.billing,
        inventory=result.inventory,
        heuristics=heuristics,
        metrics=result.metrics,
        quick_win_mode=req.quick_win_mode,
        guardrails_mode=req.guardrails_mode,
        multi_cloud=req.multi_cloud_compare and req.cloud == "multi",
    )

    try:
        client = get_openai_client()
        narrative = client.generate_text(
            prompt_body,
            system_prompt="Você é um Staff+ FinOps Engineer. Responda APENAS em texto natural, seguindo o formato do prompt. Use EXCLUSIVAMENTE os dados fornecidos; nunca invente preços.",
            use_fast_model=False,
            timeout_override=FINOPS_TIMEOUT,
        )
        if not narrative or "Erro ao gerar texto" in narrative:
            narrative = _fallback_narrative(result, heuristics, req)
    except Exception as e:
        add_log("error", f"FinOps LLM falhou: {type(e).__name__}", SOURCE)
        narrative = _fallback_narrative(result, heuristics, req)

    add_log("info", f"FinOps analyze concluída | id={id_req}", SOURCE)
    return {"message": narrative, "id_requisicao": id_req, "cloud": result.provider}


def _fallback_narrative(
    result: ConnectorResult,
    heuristics: list[dict[str, Any]],
    req: FinOpsAnalyzeRequest,
) -> str:
    """Fallback determinístico quando LLM falha."""
    parts = ["## Resumo executivo (fallback determinístico)\n"]
    parts.append(f"Provider: {result.provider}. Qualidade dos dados: {result.data_quality}.\n")
    if result.errors:
        parts.append(f"Erros na coleta: {'; '.join(result.errors[:3])}.\n")
    total = result.billing.get("total_cost_usd") or result.billing.get("total_cost")
    if total is not None:
        parts.append(f"Custo total no período: ${total:.2f} USD.\n")
    parts.append("\n## Candidatos de ação (heurísticas)\n")
    for h in heuristics[:10]:
        parts.append(f"- [{h.get('eixo', '')}] {h.get('acao', '')}: {h.get('evidencia', '')} (confiança: {h.get('confianca', 'N/A')})\n")
    if req.guardrails_mode:
        guard = build_guardrails_recommendations(result.billing, req.anomaly_threshold_pct, req.anomaly_window_days)
        parts.append("\n## Guardrails recomendados\n")
        for g in guard:
            parts.append(f"- {g.get('tipo', '')}: {g.get('descricao', '')}\n")
    parts.append("\n## Lacunas de dados\n")
    parts.append("Para análise completa, habilite Cost Explorer (AWS), Cost Management (Azure) ou Billing Export (GCP) e colete métricas de CloudWatch/Azure Monitor/Cloud Monitoring.")
    return "".join(parts)
