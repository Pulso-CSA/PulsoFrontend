#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Compreensão – Módulo Código❯━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import re
import json
import time
import traceback
from typing import Any, Dict, List, Literal, Optional, Tuple

try:
    from utils.log_manager import add_log
except ImportError:
    from app.utils.log_manager import add_log
_LOG_SOURCE = "comprehension_codigo"

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

MODULE = "codigo"
PROJECT_STATE_VAZIA = "ROOT_VAZIA"
PROJECT_STATE_COM_CONTEUDO = "ROOT_COM_CONTEUDO"
INTENT_ANALISAR = "ANALISAR"
INTENT_EXECUTAR = "EXECUTAR"
TARGET_GOVERNANCE = "/governance/run"
TARGET_CORRECT = "/workflow/correct/run"

INTENT_CONFIDENCE_THRESHOLD = 0.75

ANALISAR_PATTERNS = [
    re.compile(r"\b(o\s+que\s+(pode\s+)?melhorar|o\s+que\s+melhorar)\b", re.IGNORECASE),
    re.compile(r"\b(pode\s+melhorar|melhorar\s+na|melhorar\s+a)\b", re.IGNORECASE),
    re.compile(r"\b(o\s+que\s+está\s+errado|o\s+que\s+tem\s+de\s+errado)\b", re.IGNORECASE),
    re.compile(r"\b(qual\s+(é\s+o\s+)?problema|qual\s+o\s+problema)\b", re.IGNORECASE),
    re.compile(r"\b(como\s+(eu\s+)?faço|me\s+diga\s+como|como\s+posso)\b", re.IGNORECASE),
    re.compile(r"\b(analise|analisar|revise|revisar|diagnostique|diagnóstico)\b", re.IGNORECASE),
    re.compile(r"\b(recomende|recomendação|explique|avalie|avaliação)\b", re.IGNORECASE),
    re.compile(r"^(\s)*(o\s+que|como|qual|quais|por\s+que|porque)\b", re.IGNORECASE),
    re.compile(r"\?\s*$"),
    # Inferência: "como funciona", "o que esse sistema faz", diagnóstico de projeto
    re.compile(r"\b(como\s+(esse\s+)?(sistema|projeto|app|aplicação|aplicacao)\s+funciona)\b", re.IGNORECASE),
    re.compile(r"\b(o\s+que\s+(esse\s+)?(sistema|projeto|app)\s+faz)\b", re.IGNORECASE),
    re.compile(r"\b(como\s+funciona\s+(esse\s+)?(sistema|projeto|sistema\s+de\s+\w+))\b", re.IGNORECASE),
    re.compile(r"\b(explique\s+(como|o)\s+(funciona|sistema|projeto))\b", re.IGNORECASE),
    re.compile(r"\b(me\s+explique\s+(o\s+)?(sistema|projeto|funcionamento))\b", re.IGNORECASE),
    # Blueprint/estrutura como informação (análise), não criação de código
    re.compile(r"\bgerar\s+(o\s+)?blueprint\b", re.IGNORECASE),
    re.compile(r"\bgerar\s+estrutura\s+(de\s+)?(pastas|endpoints)", re.IGNORECASE),
    re.compile(r"\bblueprint\s+de\s+pastas\b", re.IGNORECASE),
]
EXECUTAR_KEYWORDS = re.compile(
    r"\b(altere|alterar|implemente|implementar|crie\s+(um|uma|o|a)|criar\s+(um|uma|o|a)|"
    r"corrija\s+(o|a|os|as)|corrigir\s+(o|a|os|as)|adicione|adicionar|remova|remover|"
    r"faça\s+(isso|isto|a\s+correção|a\s+mudança)|fazer\s+(isso|isto)|aplique|aplicar)\b",
    re.IGNORECASE,
)
# Confirmação ("faça") só para criar/corrigir algo no projeto. Análises (blueprint, diagnóstico) não pedem confirmação.
EXECUTAR_VERBS_STRICT = re.compile(
    r"^(crie|criar|implemente|implementar|corrija|corrigir|adicione|adicionar|"
    r"remova|remover|faça|fazer|aplique|aplicar|execute|executar|rode|rodar)\b",
    re.IGNORECASE,
)

# TEPulso: utilizador descreve o produto sem imperativo ("Sistema de gestão de pedidos") —
# evita LLM de classificação (Ollama remoto pode levar minutos e estourar timeout do cliente).
_CREATION_TITLE_PREFIX = re.compile(
    r"^(sistema|app|aplicativo|aplicação|aplicacao|api|rest\s*api|plataforma|portal|dashboard|"
    r"gestão|gestao|e-?commerce|loja\s+virtual|crm|erp|backend|frontend|"
    r"módulo|modulo|microserviço|microservico|serviço|servico|projeto|site|website)\b",
    re.IGNORECASE,
)


def _creation_title_fast_path(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text or len(text) > 280:
        return False
    if "?" in text:
        return False
    if _looks_like_analysis(prompt):
        return False
    if _CREATION_TITLE_PREFIX.search(text):
        try:
            add_log(
                "info",
                f"[_creation_title_fast_path] match=prefix | preview={_log_safe_prompt_preview(text)!r}",
                _LOG_SOURCE,
            )
        except Exception:
            pass
        return True
    words = text.split()
    if 2 <= len(words) <= 14 and not re.search(
        r"\b(como|o\s+que|qual|quais|por\s*que|porque|melhorar|analise|analisar|erro|problema|explique)\b",
        text,
        re.IGNORECASE,
    ):
        try:
            add_log(
                "info",
                f"[_creation_title_fast_path] match=short_phrase | n_words={len(words)} | preview={_log_safe_prompt_preview(text)!r}",
                _LOG_SOURCE,
            )
        except Exception:
            pass
        return True
    return False

_INTENT_LLM_SYSTEM = """Você classifica a intenção do usuário em exatamente uma de duas opções.

ANALISAR (use quando):
- Pergunta: "o que...", "como...", "qual...", "por que...", "o que pode melhorar", "o que está errado"
- Pedido de diagnóstico, recomendação, avaliação, revisão, explicação
- Qualquer frase que termine em "?" ou que peça opinião/análise sem pedir para executar
- Exemplos: "o que pode melhorar na segurança?", "como faço X?", "analise o código", "me diga o que está errado"

EXECUTAR (use SOMENTE quando):
- O usuário pede explicitamente para CRIAR ou CORRIGIR algo no projeto (código, arquivos, implementação)
- Exemplos: "crie um projeto", "implemente a correção", "corrija o erro", "adicione o endpoint"
- Pedidos de análise, blueprint, diagnóstico, "gerar blueprint de pastas" (só informação) = ANALISAR (não EXECUTAR)
- NÃO classifique como EXECUTAR se for pergunta, análise ou pedido de relatório/blueprint sem criar ou alterar código

Em dúvida, classifique como ANALISAR.

Responda APENAS com um JSON válido, sem markdown, sem texto extra:
{"intent": "ANALISAR" ou "EXECUTAR", "confidence": número entre 0 e 1, "reason": "breve motivo"}"""


def _log_safe_prompt_preview(prompt: str, max_len: int = 120) -> str:
    s = (prompt or "").strip().replace("\n", " ")
    return (s[:max_len] + "…") if len(s) > max_len else s


def detect_project_state(root_path: str | None) -> Literal["ROOT_VAZIA", "ROOT_COM_CONTEUDO"]:
    rp = (root_path or "").strip()
    if not root_path or not os.path.isdir(root_path):
        try:
            add_log(
                "info",
                f"[detect_project_state] ROOT_VAZIA | dir_missing_or_empty | root_path={rp[:200]!r}",
                _LOG_SOURCE,
            )
        except Exception:
            pass
        return PROJECT_STATE_VAZIA
    for _root, _dirs, filenames in os.walk(root_path):
        if filenames:
            try:
                add_log(
                    "info",
                    f"[detect_project_state] ROOT_COM_CONTEUDO | dir={_root[:120]!r} | n_files_here={len(filenames)} | root_path={rp[:200]!r}",
                    _LOG_SOURCE,
                )
            except Exception:
                pass
            return PROJECT_STATE_COM_CONTEUDO
    try:
        add_log(
            "info",
            f"[detect_project_state] ROOT_VAZIA | pastas_sem_arquivos | root_path={rp[:200]!r}",
            _LOG_SOURCE,
        )
    except Exception:
        pass
    return PROJECT_STATE_VAZIA


def _classify_intent_fallback(prompt: str) -> str:
    text = (prompt or "").strip()
    if not text:
        return INTENT_ANALISAR
    for pat in ANALISAR_PATTERNS:
        if pat.search(text):
            return INTENT_ANALISAR
    if EXECUTAR_VERBS_STRICT.match(text.lower()):
        return INTENT_EXECUTAR
    if EXECUTAR_KEYWORDS.search(text.lower()):
        return INTENT_EXECUTAR
    return INTENT_ANALISAR


def _looks_like_analysis(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text:
        return True
    for pat in ANALISAR_PATTERNS:
        if pat.search(text):
            return True
    return False


def classify_intent_codigo(prompt: str, usuario: str | None = None) -> Tuple[str, float]:
    t0 = time.perf_counter()
    try:
        add_log("info", "[classify_intent_codigo] início", _LOG_SOURCE)
    except Exception:
        pass
    if not prompt or not prompt.strip():
        try:
            add_log("info", "[classify_intent_codigo] prompt vazio → ANALISAR", _LOG_SOURCE)
        except Exception:
            pass
        return (INTENT_ANALISAR, 1.0)
    cache_key = prompt_cache_key(prompt, usuario, MODULE)
    cached = intent_cache_get(cache_key, MODULE)
    if cached:
        try:
            add_log("info", f"[classify_intent_codigo] cache hit → {cached[0]} ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
        except Exception:
            pass
        return cached
    if _looks_like_analysis(prompt):
        try:
            add_log(
                "info",
                f"[classify_intent_codigo] heurística ANALISAR | preview={_log_safe_prompt_preview(prompt)!r} | ({time.perf_counter()-t0:.1f}s)",
                _LOG_SOURCE,
            )
        except Exception:
            pass
        return (INTENT_ANALISAR, 1.0)
    # Fast path: verbos de execução no início (crie, implemente, etc.) → EXECUTAR sem LLM (~30s economizados)
    if EXECUTAR_VERBS_STRICT.match((prompt or "").strip()):
        intent_cache_set(cache_key, INTENT_EXECUTAR, 0.9, MODULE)
        try:
            add_log("info", f"[classify_intent_codigo] fast path EXECUTAR ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
        except Exception:
            pass
        return (INTENT_EXECUTAR, 0.9)
    if _creation_title_fast_path(prompt):
        intent_cache_set(cache_key, INTENT_EXECUTAR, 0.88, MODULE)
        try:
            add_log(
                "info",
                f"[classify_intent_codigo] fast path EXECUTAR (título/descrição de projeto, sem LLM) ({time.perf_counter()-t0:.1f}s)",
                _LOG_SOURCE,
            )
        except Exception:
            pass
        return (INTENT_EXECUTAR, 0.88)
    try:
        try:
            add_log(
                "info",
                f"[classify_intent_codigo] cache miss, chamando LLM | prompt_len={len(prompt)} | preview={_log_safe_prompt_preview(prompt)!r}",
                _LOG_SOURCE,
            )
        except Exception:
            pass
        client = get_openai_client()
        client_cls = type(client).__name__
        try:
            add_log("info", f"[classify_intent_codigo] cliente LLM={client_cls} use_fast_model=True", _LOG_SOURCE)
        except Exception:
            pass
        raw = client.generate_text(
            f'Prompt do usuário: "{prompt[:500]}"\nClassifique a intenção.',
            system_prompt=_INTENT_LLM_SYSTEM,
            temperature_override=0,
            use_fast_model=True,
            num_predict=128,
        )
        try:
            raw_preview = (raw or "")[:300].replace("\n", " ")
            add_log("info", f"[classify_intent_codigo] LLM raw (trecho): {raw_preview!r}", _LOG_SOURCE)
        except Exception:
            pass
        parsed = parse_intent_json(raw)
        if parsed and isinstance(parsed.get("intent"), str):
            intent = parsed["intent"].strip().upper()
            confidence = float(parsed.get("confidence", 0.8))
            confidence = max(0.0, min(1.0, confidence))
            if intent == INTENT_EXECUTAR:
                if _looks_like_analysis(prompt):
                    intent_cache_set(cache_key, INTENT_ANALISAR, confidence, MODULE)
                    return (INTENT_ANALISAR, confidence)
                intent_cache_set(cache_key, INTENT_EXECUTAR, confidence, MODULE)
                try:
                    add_log("info", f"[classify_intent_codigo] LLM → EXECUTAR ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
                except Exception:
                    pass
                return (INTENT_EXECUTAR, confidence)
            if intent == INTENT_ANALISAR:
                intent_cache_set(cache_key, INTENT_ANALISAR, confidence, MODULE)
                try:
                    add_log("info", f"[classify_intent_codigo] LLM → ANALISAR ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
                except Exception:
                    pass
                return (INTENT_ANALISAR, confidence)
        try:
            add_log("warning", f"[classify_intent_codigo] LLM resposta não parseável | parsed={parsed!r}", _LOG_SOURCE)
        except Exception:
            pass
    except Exception as e:
        try:
            add_log(
                "error",
                f"[classify_intent_codigo] exceção na chamada LLM: {type(e).__name__}: {e}\n{traceback.format_exc()[:1500]}",
                _LOG_SOURCE,
            )
        except Exception:
            pass
    fallback = _classify_intent_fallback(prompt)
    intent_cache_set(cache_key, fallback, 0.5, MODULE)
    try:
        add_log("info", f"[classify_intent_codigo] fallback → {fallback} ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
    except Exception:
        pass
    return (fallback, 0.5)


def route_decision_codigo(
    prompt: str,
    root_path: str | None,
    usuario: str | None = None,
    force_execute: bool = False,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    rt0 = time.perf_counter()
    u = (usuario or "")[:64]
    rp_short = ((root_path or "")[:200] + "…") if root_path and len(root_path) > 200 else (root_path or "")
    try:
        add_log(
            "info",
            f"[route_decision_codigo] início | usuario={u!r} | root_path={rp_short!r} | force_execute={force_execute} | "
            f"prompt_len={len((prompt or '').strip())} | preview={_log_safe_prompt_preview(prompt or '')!r}",
            _LOG_SOURCE,
        )
    except Exception:
        pass
    project_state = detect_project_state(root_path)
    intent, confidence = classify_intent_codigo(prompt, usuario)
    # Executa imediatamente se: force_execute, ou sinal explícito (faça/executar), ou comando direto (crie/implemente no início)
    prompt_starts_with_create = bool(EXECUTAR_VERBS_STRICT.match((prompt or "").strip()))
    # ROOT vazia + descrição tipo título de produto (ex.: "Sistema de gestão de pedidos") → executar sem pedir "faça"
    title_like_new_project = project_state == PROJECT_STATE_VAZIA and _creation_title_fast_path(prompt)
    should_execute = (
        force_execute
        or detect_execute_signal(prompt)
        or (intent == INTENT_EXECUTAR and prompt_starts_with_create)
        or (intent == INTENT_EXECUTAR and title_like_new_project)
    )

    target_endpoint = None
    if intent == INTENT_EXECUTAR:
        if project_state == PROJECT_STATE_VAZIA:
            target_endpoint = TARGET_GOVERNANCE
        else:
            target_endpoint = TARGET_CORRECT

    explanation = (
        f"Intenção: {intent}. Projeto: {project_state}."
        + (f" Sinal de execução: {'sim' if should_execute else 'não'}." if intent == INTENT_EXECUTAR else "")
    )

    if intent == INTENT_ANALISAR:
        next_action = "Responder com análise e plano, sem executar workflow."
    elif intent == INTENT_EXECUTAR and not should_execute:
        next_action = "Pedir confirmação ao usuário (ex.: diga 'faça', 'sim' ou 'executar' para executar)."
    elif intent == INTENT_EXECUTAR and should_execute:
        next_action = f"Disparar fluxo: {target_endpoint}"
    else:
        next_action = "Nenhuma ação de workflow."

    intent_warning = None
    if confidence < INTENT_CONFIDENCE_THRESHOLD:
        intent_warning = (
            "A classificação foi incerta. Se queria apenas analisar, reformule; "
            "se queria executar, confirme com 'faça', 'sim' ou 'executar'."
        )

    try:
        sig = detect_execute_signal(prompt)
        add_log(
            "info",
            f"[route_decision_codigo] decisão | project_state={project_state} | intent={intent} | conf={confidence:.2f} | "
            f"should_execute={should_execute} "
            f"[force_execute={force_execute} detect_execute_signal={sig} "
            f"verb_start={prompt_starts_with_create} title_like_root_vazia={title_like_new_project}] | "
            f"target_endpoint={target_endpoint} | elapsed={time.perf_counter()-rt0:.2f}s",
            _LOG_SOURCE,
        )
    except Exception:
        pass

    return build_module_decision(
        module=MODULE,
        intent=intent,
        target_endpoint=target_endpoint,
        should_execute=should_execute,
        explanation=explanation,
        next_action=next_action,
        extra={
            "mode": project_state,
            "intent_confidence": confidence,
            "intent_warning": intent_warning,
        },
    )
