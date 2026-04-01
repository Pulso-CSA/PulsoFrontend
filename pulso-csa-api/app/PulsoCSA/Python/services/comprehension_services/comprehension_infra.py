#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Compreensão – Módulo Infraestrutura❯━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import re
import json
from typing import Any, Dict, List, Literal, Optional

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client
from services.comprehension_services.comprehension_base import (
    detect_execute_signal,
    intent_cache_get,
    intent_cache_set,
    parse_intent_json,
    prompt_cache_key,
    build_module_decision,
)

MODULE = "infraestrutura"
TARGET_ANALYZE = "/infra/analyze"
TARGET_GENERATE = "/infra/generate"
TARGET_VALIDATE = "/infra/validate"
TARGET_DEPLOY = "/infra/deploy"

# Intents específicas do módulo infra
INTENT_ANALISAR_INFRA = "ANALISAR_INFRA"
INTENT_GERAR_TERRAFORM = "GERAR_TERRAFORM"
INTENT_VALIDAR_INFRA = "VALIDAR_INFRA"
INTENT_DEPLOY_INFRA = "DEPLOY_INFRA"

ANALISAR_INFRA_PATTERNS = [
    re.compile(r"\b(analise|analisar|revise|revisar)\s+(a\s+)?infra", re.IGNORECASE),
    re.compile(r"\b(o\s+que\s+(tem|existe)\s+na\s+infra)", re.IGNORECASE),
    re.compile(r"\b(custo|cost|estimativa)\b", re.IGNORECASE),
    re.compile(r"\b(qual\s+a\s+infra|como\s+está\s+a\s+infra)\b", re.IGNORECASE),
]
GERAR_PATTERNS = [
    re.compile(r"\b(gerar|gerar\s+terraform|gera\s+terraform)\b", re.IGNORECASE),
    re.compile(r"\b(criar\s+terraform|gerar\s+infra)\b", re.IGNORECASE),
]
VALIDAR_PATTERNS = [
    re.compile(r"\b(validar|validar\s+terraform|valida\s+infra)\b", re.IGNORECASE),
    re.compile(r"\b(terraform\s+plan|terraform\s+validate)\b", re.IGNORECASE),
]
DEPLOY_PATTERNS = [
    re.compile(r"\b(deploy|deployar|aplicar\s+terraform|terraform\s+apply)\b", re.IGNORECASE),
    re.compile(r"\b(provisionar|provisiona)\b", re.IGNORECASE),
]

_INTENT_LLM_SYSTEM = """Você classifica a intenção do usuário em relação a INFRAESTRUTURA (Terraform, AWS, Azure, GCP) em exatamente uma opção:

ANALISAR_INFRA: analisar infra existente, estimar custo, ver contexto do repo, blueprint
GERAR_TERRAFORM: gerar artefatos Terraform (arquivos .tf) a partir do projeto
VALIDAR_INFRA: validar Terraform (fmt, validate, plan), obter deploy_token
DEPLOY_INFRA: fazer deploy (terraform apply), provisionar recursos na nuvem

Responda APENAS com JSON válido, sem markdown:
{"intent": "ANALISAR_INFRA" ou "GERAR_TERRAFORM" ou "VALIDAR_INFRA" ou "DEPLOY_INFRA", "confidence": 0.0 a 1.0, "reason": "breve motivo"}"""


def _classify_intent_fallback(prompt: str) -> str:
    text = (prompt or "").strip().lower()
    if not text:
        return INTENT_ANALISAR_INFRA
    for pat in DEPLOY_PATTERNS:
        if pat.search(text):
            return INTENT_DEPLOY_INFRA
    for pat in VALIDAR_PATTERNS:
        if pat.search(text):
            return INTENT_VALIDAR_INFRA
    for pat in GERAR_PATTERNS:
        if pat.search(text):
            return INTENT_GERAR_TERRAFORM
    for pat in ANALISAR_INFRA_PATTERNS:
        if pat.search(text):
            return INTENT_ANALISAR_INFRA
    # Ter "terraform" ou "infra" sem verbo específico -> analisar
    if "terraform" in text or "infra" in text:
        return INTENT_ANALISAR_INFRA
    return INTENT_ANALISAR_INFRA


def _intent_to_target(intent: str) -> str:
    if intent == INTENT_ANALISAR_INFRA:
        return TARGET_ANALYZE
    if intent == INTENT_GERAR_TERRAFORM:
        return TARGET_GENERATE
    if intent == INTENT_VALIDAR_INFRA:
        return TARGET_VALIDATE
    if intent == INTENT_DEPLOY_INFRA:
        return TARGET_DEPLOY
    return TARGET_ANALYZE


def classify_intent_infra(prompt: str, usuario: str | None = None) -> tuple[str, float]:
    cache_key = prompt_cache_key(prompt, usuario, MODULE)
    cached = intent_cache_get(cache_key, MODULE)
    if cached:
        return cached

    # Fallback regex rápido
    fallback = _classify_intent_fallback(prompt)
    try:
        client = get_openai_client()
        raw = client.generate_text(
            f'Prompt: "{prompt[:400]}"\nClassifique a intenção de infra.',
            system_prompt=_INTENT_LLM_SYSTEM,
            temperature_override=0,
            use_fast_model=True,
            num_predict=128,
        )
        parsed = parse_intent_json(raw)
        if parsed and parsed.get("intent"):
            intent = parsed["intent"].strip().upper()
            valid = (INTENT_ANALISAR_INFRA, INTENT_GERAR_TERRAFORM, INTENT_VALIDAR_INFRA, INTENT_DEPLOY_INFRA)
            if intent in valid:
                conf = float(parsed.get("confidence", 0.8))
                conf = max(0.0, min(1.0, conf))
                intent_cache_set(cache_key, intent, conf, MODULE)
                return (intent, conf)
    except Exception:
        pass
    intent_cache_set(cache_key, fallback, 0.5, MODULE)
    return (fallback, 0.5)


def route_decision_infra(
    prompt: str,
    root_path: str | None,
    usuario: str | None = None,
    force_execute: bool = False,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    intent, confidence = classify_intent_infra(prompt, usuario)
    target = _intent_to_target(intent)
    should_execute = force_execute or detect_execute_signal(prompt)

    # Para deploy, exigir confirmação explícita (ação destrutiva)
    if intent == INTENT_DEPLOY_INFRA and not force_execute:
        should_execute = should_execute  # mantém; pode adicionar double-check no router

    explanation = f"Módulo: {MODULE}. Intenção: {intent}. Target: {target}. Sinal execução: {'sim' if should_execute else 'não'}."

    if intent == INTENT_ANALISAR_INFRA:
        next_action = "Analisar infra do projeto (repo_context, custo, blueprint)."
    elif should_execute:
        next_action = f"Executar: {target}"
    else:
        next_action = "Confirme com 'faça', 'executar' ou 'aplique' para prosseguir."

    project_state = "ROOT_COM_CONTEUDO" if root_path and os.path.isdir(root_path) else "ROOT_VAZIA"

    return build_module_decision(
        module=MODULE,
        intent=intent,
        target_endpoint=target,
        should_execute=should_execute,
        explanation=explanation,
        next_action=next_action,
        extra={
            "mode": project_state,
            "intent_confidence": confidence,
            "intent_warning": "Confiança baixa. Reformule se necessário." if confidence < 0.75 else None,
            "requires_root_path": intent != INTENT_ANALISAR_INFRA,  # generate/validate/deploy precisam
        },
    )
