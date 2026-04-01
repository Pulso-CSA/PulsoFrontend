#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮FinOps Chat Service – Orquestrador❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
Orquestrador do chat FinOps: interpreta mensagem → comprehension → monta request → run_finops_analyze.
Sistema de compreensão exclusivo do módulo FinOps.
"""
from typing import Any

from models.finops.finops_models import (
    FinOpsAnalyzeRequest,
    AWSCredentials,
    AzureCredentials,
    GCPCredentials,
)
from models.finops.finops_chat_models import FinOpsChatInput, FinOpsChatOutput
from services.finops.comprehension_finops import (
    classify_intent_finops,
    extrair_params_finops,
    intent_to_quick_win_mode,
)
from services.finops.finops_services import run_finops_analyze


def _resolve_cloud_from_credentials(payload: FinOpsChatInput) -> str:
    """Determina cloud a partir das credenciais fornecidas."""
    if payload.aws_credentials and (payload.aws_credentials.access_key_id or payload.aws_credentials.role_arn):
        return "aws"
    if payload.azure_credentials and (payload.azure_credentials.client_id or payload.azure_credentials.subscription_id):
        return "azure"
    if payload.gcp_credentials and (payload.gcp_credentials.project_id or payload.gcp_credentials.service_account_json):
        return "gcp"
    return "aws"


def run_finops_chat(payload: FinOpsChatInput) -> FinOpsChatOutput:
    """
    Pipeline: comprehension (intent + params) → monta FinOpsAnalyzeRequest → run_finops_analyze.
    Retorna resposta em linguagem natural para o chat.
    """
    mensagem = payload.mensagem.strip()
    usuario = payload.usuario or "default"
    etapas: list[str] = ["comprehension"]

    intent, confidence = classify_intent_finops(mensagem, usuario)
    params = extrair_params_finops(mensagem, usuario)

    quick_win_mode = params.get("quick_win_mode") or intent_to_quick_win_mode(intent)
    cloud = params.get("cloud") or _resolve_cloud_from_credentials(payload)
    guardrails_mode = params.get("guardrails_mode", False)
    multi_cloud_compare = params.get("multi_cloud_compare", False)

    req = FinOpsAnalyzeRequest(
        cloud=cloud,
        aws_credentials=payload.aws_credentials,
        azure_credentials=payload.azure_credentials,
        gcp_credentials=payload.gcp_credentials,
        quick_win_mode=quick_win_mode,
        guardrails_mode=guardrails_mode,
        multi_cloud_compare=multi_cloud_compare,
    )

    result = run_finops_analyze(req)
    message = result.get("message", "")
    id_req = result.get("id_requisicao", payload.id_requisicao)
    cloud_exec = result.get("cloud", cloud)

    etapas.extend(["preflight", "billing", "inventory", "heuristics", "llm_narrative"])

    return FinOpsChatOutput(
        resposta_texto=message,
        id_requisicao=id_req,
        cloud=cloud_exec,
        etapas_executadas=etapas,
    )
