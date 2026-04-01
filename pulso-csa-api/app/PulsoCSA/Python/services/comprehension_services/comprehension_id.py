#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Compreensão – Módulo Inteligência de Dados❯━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import re
from typing import Any, Dict, List, Optional

from services.comprehension_services.comprehension_base import (
    detect_execute_signal,
    build_module_decision,
)

MODULE = "inteligencia-dados"
TARGET_CHAT = "/inteligencia-dados/chat"
TARGET_QUERY = "/inteligencia-dados/query"
TARGET_CAPTURA = "/inteligencia-dados/captura-dados"
TARGET_ANALISE_ESTATISTICA = "/inteligencia-dados/analise-estatistica"
TARGET_CRIAR_MODELO = "/inteligencia-dados/criar-modelo-ml"
TARGET_PREVER = "/inteligencia-dados/prever"

# Intents do módulo ID (o chat ID já interpreta internamente; aqui categorizamos para UX)
INTENT_CHAT_ID = "CHAT_ID"
INTENT_QUERY = "QUERY"
INTENT_CAPTURA = "CAPTURA"
INTENT_ESTATISTICA = "ESTATISTICA"
INTENT_CRIAR_MODELO = "CRIAR_MODELO"
INTENT_PREVER = "PREVER"

# Padrões para sub-rotas (opcional; o chat é o orquestrador principal)
QUERY_PATTERNS = [
    re.compile(r"\b(consulta|query|pergunta)\s+(em|no)\s+(linguagem\s+natural|sql)\b", re.IGNORECASE),
    re.compile(r"\b(qual|quantos|quanto)\s+.*\s+(no|na)\s+banco\b", re.IGNORECASE),
]
CAPTURA_PATTERNS = [
    re.compile(r"\b(conecta|conectar|captura|capturar)\s+(no\s+)?(banco|mysql|mongo)\b", re.IGNORECASE),
    re.compile(r"\b(extrai|extrair)\s+os\s+dados\b", re.IGNORECASE),
]
ESTATISTICA_PATTERNS = [
    re.compile(r"\b(correlação|correlacao|média|mediana|estatística|estatistica)\b", re.IGNORECASE),
    re.compile(r"\b(analise\s+estatística|análise\s+estatística)\b", re.IGNORECASE),
]
MODELO_PATTERNS = [
    re.compile(r"\b(treinar|treina)\s+(modelo|modelo\s+ml)\b", re.IGNORECASE),
    re.compile(r"\b(criar\s+modelo|criar\s+modelo\s+ml)\b", re.IGNORECASE),
    re.compile(r"\b(modelo\s+de\s+churn|churn)\b", re.IGNORECASE),
]
PREVER_PATTERNS = [
    re.compile(r"\b(prever|previsão|previsao|predição|predicao)\b", re.IGNORECASE),
    re.compile(r"\b(quem\s+vai\s+churnar|quantos\s+vão\s+churnar)\b", re.IGNORECASE),
]


def _classify_subintent(prompt: str) -> str:
    """Sub-intent para sugerir endpoint; o chat ID é o orquestrador principal."""
    text = (prompt or "").strip().lower()
    if not text:
        return INTENT_CHAT_ID
    for pat in QUERY_PATTERNS:
        if pat.search(text):
            return INTENT_QUERY
    for pat in CAPTURA_PATTERNS:
        if pat.search(text):
            return INTENT_CAPTURA
    for pat in ESTATISTICA_PATTERNS:
        if pat.search(text):
            return INTENT_ESTATISTICA
    for pat in MODELO_PATTERNS:
        if pat.search(text):
            return INTENT_CRIAR_MODELO
    for pat in PREVER_PATTERNS:
        if pat.search(text):
            return INTENT_PREVER
    return INTENT_CHAT_ID


def _subintent_to_target(subintent: str) -> str:
    if subintent == INTENT_QUERY:
        return TARGET_QUERY
    if subintent == INTENT_CAPTURA:
        return TARGET_CAPTURA
    if subintent == INTENT_ESTATISTICA:
        return TARGET_ANALISE_ESTATISTICA
    if subintent == INTENT_CRIAR_MODELO:
        return TARGET_CRIAR_MODELO
    if subintent == INTENT_PREVER:
        return TARGET_PREVER
    return TARGET_CHAT


def route_decision_id(
    prompt: str,
    root_path: str | None,
    usuario: str | None = None,
    force_execute: bool = False,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """
    Roteamento para Inteligência de Dados.
    O endpoint principal é /inteligencia-dados/chat que orquestra tudo.
    Sub-intent serve para sugerir ao frontend.
    """
    subintent = _classify_subintent(prompt)
    target = _subintent_to_target(subintent)
    should_execute = force_execute or detect_execute_signal(prompt)

    # Para ID, "executar" geralmente significa rodar o chat (não precisa de confirmação explícita para muitas operações)
    # Mas perguntas como "qual a correlação entre X e Y" são executadas direto
    if not should_execute and not prompt.strip().endswith("?"):
        # Frases imperativas sem confirmação
        should_execute = bool(re.search(r"\b(me\s+mostre|mostre|diga|quero|preciso)\b", prompt, re.IGNORECASE))

    explanation = f"Módulo: {MODULE}. Sub-intent: {subintent}. Target: {target}. Execução: {'sim' if should_execute else 'não'}."

    next_action = "Executar chat de Inteligência de Dados. O orquestrador interpreta a mensagem e executa captura, tratamento, estatística, treino ou previsão conforme necessário."

    return build_module_decision(
        module=MODULE,
        intent=subintent,
        target_endpoint=target,
        should_execute=should_execute,
        explanation=explanation,
        next_action=next_action,
        extra={
            "mode": "N/A",  # ID não usa project_state
            "intent_confidence": 0.9,
            "intent_warning": None,
            "suggested_endpoint": TARGET_CHAT,  # Sempre chat como orquestrador
        },
    )
