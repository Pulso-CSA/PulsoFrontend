#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Comprehension – Exclusivo FinOps❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
Sistema de compreensão exclusivo do módulo FinOps.
Classifica intent e extrai parâmetros (cloud, quick_win_mode, guardrails) a partir da mensagem.
"""
import json
import os
import re
from typing import Any, Optional

from app.core.openai.openai_client import get_openai_client
from services.comprehension_services.comprehension_base import (
    prompt_cache_key,
    intent_cache_get,
    intent_cache_set,
)

NAMESPACE = "finops"
INTENT_CACHE_TTL = int(os.getenv("FINOPS_INTENT_CACHE_TTL_SEC", "300"))

# Intents
INTENT_ANALISAR_FINOPS = "ANALISAR_FINOPS"
INTENT_QUICK_WINS = "QUICK_WINS"
INTENT_COMPARAR_REGIOES = "COMPARAR_REGIOES"
INTENT_POLITICAS_DESLIGAMENTO = "POLITICAS_DESLIGAMENTO"
INTENT_GUARDRAILS = "GUARDRAILS"

# Padrões regex (prioridade: mais específico primeiro)
QUICK_WINS_PATTERNS = [
    re.compile(r"\b(quick\s+win|quick\s+wins|oportunidades\s+imediatas)\b", re.IGNORECASE),
    re.compile(r"\b(ganhos\s+rápidos|ganhos\s+rapidos)\b", re.IGNORECASE),
]
COMPARAR_REGIOES_PATTERNS = [
    re.compile(r"\b(comparar\s+(custos\s+)?por\s+região|comparar\s+regiões)\b", re.IGNORECASE),
    re.compile(r"\b(custo\s+por\s+região|regiões\s+mais\s+caras)\b", re.IGNORECASE),
]
POLITICAS_PATTERNS = [
    re.compile(r"\b(políticas?\s+de\s+desligamento|auto\s+shutdown)\b", re.IGNORECASE),
    re.compile(r"\b(desligar\s+fora\s+do\s+horário|scale\s+to\s+zero)\b", re.IGNORECASE),
]
GUARDRAILS_PATTERNS = [
    re.compile(r"\b(guardrails|budgets?|alertas?|thresholds?)\b", re.IGNORECASE),
    re.compile(r"\b(recomende\s+budgets?|anomalias?)\b", re.IGNORECASE),
]

_LLM_INTENT_SYSTEM = """Você classifica a intenção do usuário em relação a FinOps (custos cloud, otimização) em exatamente uma opção:

ANALISAR_FINOPS: análise completa de custos, performance e segurança na cloud
QUICK_WINS: quick wins, oportunidades imediatas, ganhos rápidos
COMPARAR_REGIOES: comparar custos por região, sugerir realocação
POLITICAS_DESLIGAMENTO: políticas de desligamento automático, scale-to-zero, dev/test
GUARDRAILS: budgets, alertas, thresholds de anomalia

Responda APENAS com JSON válido, sem markdown:
{"intent": "ANALISAR_FINOPS" ou "QUICK_WINS" ou "COMPARAR_REGIOES" ou "POLITICAS_DESLIGAMENTO" ou "GUARDRAILS", "confidence": 0.0 a 1.0, "reason": "breve motivo"}"""

_LLM_PARAMS_SYSTEM = """Você extrai parâmetros de uma mensagem sobre FinOps. Retorne JSON válido:

- cloud: "aws" | "azure" | "gcp" | "multi" (inferir de "minha AWS", "Azure", "GCP", "multi-cloud")
- quick_win_mode: "quick_wins" | "compare_regions" | "auto_shutdown_policies" | "none"
- guardrails_mode: true | false
- multi_cloud_compare: true | false (apenas se mencionar comparação multi-cloud)

Responda APENAS JSON, sem markdown."""


def _classify_intent_fallback(mensagem: str) -> str:
    text = (mensagem or "").strip().lower()
    if not text:
        return INTENT_ANALISAR_FINOPS
    for pat in QUICK_WINS_PATTERNS:
        if pat.search(text):
            return INTENT_QUICK_WINS
    for pat in COMPARAR_REGIOES_PATTERNS:
        if pat.search(text):
            return INTENT_COMPARAR_REGIOES
    for pat in POLITICAS_PATTERNS:
        if pat.search(text):
            return INTENT_POLITICAS_DESLIGAMENTO
    for pat in GUARDRAILS_PATTERNS:
        if pat.search(text):
            return INTENT_GUARDRAILS
    return INTENT_ANALISAR_FINOPS


def _parse_json(raw: str) -> dict | None:
    raw = (raw or "").strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            raw = m.group(1)
    start = raw.find("{")
    if start < 0:
        return None
    depth = 0
    for i, c in enumerate(raw[start:], start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start : i + 1])
                except Exception:
                    return None
    return None


def classify_intent_finops(mensagem: str, usuario: str | None = None) -> tuple[str, float]:
    """Classifica intent da mensagem. Retorna (intent, confidence). Usa cache isolado por usuário."""
    cache_key = prompt_cache_key(mensagem, usuario, NAMESPACE)
    cached = intent_cache_get(cache_key, NAMESPACE)
    if cached:
        return cached

    fallback = _classify_intent_fallback(mensagem)
    try:
        client = get_openai_client()
        raw = client.generate_text(
            f'Mensagem: "{mensagem[:400]}"\nClassifique a intenção FinOps.',
            system_prompt=_LLM_INTENT_SYSTEM,
            temperature_override=0,
            use_fast_model=True,
        )
        parsed = _parse_json(raw)
        if parsed and parsed.get("intent"):
            intent = parsed["intent"].strip().upper()
            valid = (INTENT_ANALISAR_FINOPS, INTENT_QUICK_WINS, INTENT_COMPARAR_REGIOES, INTENT_POLITICAS_DESLIGAMENTO, INTENT_GUARDRAILS)
            if intent in valid:
                conf = float(parsed.get("confidence", 0.8))
                conf = max(0.0, min(1.0, conf))
                intent_cache_set(cache_key, intent, conf, NAMESPACE)
                return (intent, conf)
    except Exception:
        pass
    intent_cache_set(cache_key, fallback, 0.5, NAMESPACE)
    return (fallback, 0.5)


def intent_to_quick_win_mode(intent: str) -> str:
    """Mapeia intent para quick_win_mode."""
    if intent == INTENT_QUICK_WINS:
        return "quick_wins"
    if intent == INTENT_COMPARAR_REGIOES:
        return "compare_regions"
    if intent == INTENT_POLITICAS_DESLIGAMENTO:
        return "auto_shutdown_policies"
    return "none"


def extrair_params_finops(mensagem: str, usuario: str | None = None) -> dict[str, Any]:
    """
    Extrai cloud, quick_win_mode, guardrails_mode, multi_cloud_compare da mensagem.
    Usa LLM + fallback heurístico.
    """
    text = (mensagem or "").strip().lower()
    params: dict[str, Any] = {
        "cloud": "aws",
        "quick_win_mode": "none",
        "guardrails_mode": False,
        "multi_cloud_compare": False,
    }

    # Heurística: cloud
    if "azure" in text or "microsoft" in text:
        params["cloud"] = "azure"
    elif "gcp" in text or "google" in text or "gcloud" in text:
        params["cloud"] = "gcp"
    elif "multi" in text or "multicloud" in text or "todas" in text:
        params["cloud"] = "multi"
    elif "aws" in text or "amazon" in text:
        params["cloud"] = "aws"

    # Heurística: guardrails
    if any(p.search(text) for p in GUARDRAILS_PATTERNS):
        params["guardrails_mode"] = True

    # LLM para refinar (opcional)
    try:
        client = get_openai_client()
        raw = client.generate_text(
            f'Mensagem: "{mensagem[:400]}"\nExtraia cloud, quick_win_mode, guardrails_mode, multi_cloud_compare.',
            system_prompt=_LLM_PARAMS_SYSTEM,
            temperature_override=0,
            use_fast_model=True,
        )
        parsed = _parse_json(raw)
        if parsed:
            if parsed.get("cloud") in ("aws", "azure", "gcp", "multi"):
                params["cloud"] = parsed["cloud"]
            if parsed.get("guardrails_mode") is True:
                params["guardrails_mode"] = True
            if parsed.get("multi_cloud_compare") is True:
                params["multi_cloud_compare"] = True
            if parsed.get("quick_win_mode") in ("quick_wins", "compare_regions", "auto_shutdown_policies", "none"):
                params["quick_win_mode"] = parsed["quick_win_mode"]
    except Exception:
        pass

    return params
