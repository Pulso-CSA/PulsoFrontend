"""
Extrai texto e sinais de gráficos de respostas JSON para validação RegenAI (testes como usuário).
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, List, Tuple


def _fold_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

_CHART_EXPECTATION_HINTS = (
    "gráfico",
    "grafico",
    "histograma",
    "dispersão",
    "dispersao",
    "scatter",
    "barras",
    "pizza",
    "matriz",
    "visualização",
    "visualizacao",
    "plot",
    "chart",
)


def expects_chart_or_visualization(expected_output: str) -> bool:
    e = (expected_output or "").lower()
    return any(h in e for h in _CHART_EXPECTATION_HINTS)


def has_chart_signals(obj: Any) -> bool:
    """Detecta estruturas típicas de gráficos nas respostas (ID insights, análise estatística, widgets)."""
    if isinstance(obj, dict):
        if obj.get("graficos_metadados"):
            return True
        gd = obj.get("graficos_dados")
        if isinstance(gd, list) and len(gd) > 0:
            return True
        w = obj.get("widget")
        if isinstance(w, dict):
            ct = (w.get("chart_type") or "").lower()
            if ct and ct != "progress":
                data = w.get("data")
                if isinstance(data, list) and len(data) > 0:
                    return True
            if w.get("data"):
                return True
        ct = obj.get("chart_type")
        if ct and str(ct).lower() not in ("", "progress", "none"):
            if obj.get("data"):
                return True
        for v in obj.values():
            if has_chart_signals(v):
                return True
    if isinstance(obj, list):
        for item in obj:
            if has_chart_signals(item):
                return True
    return False


def extract_semantic_text_from_parsed(parsed: Any) -> str:
    """Junta strings relevantes do JSON para matching com saída esperada."""
    parts: List[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                lk = str(k).lower()
                if lk in ("password", "secret", "token", "authorization"):
                    continue
                if isinstance(v, (str, int, float, bool)):
                    parts.append(str(v))
                else:
                    walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, (str, int, float)):
            parts.append(str(x))

    walk(parsed)
    return " ".join(parts)


def build_semantic_test_string(body_text: str, parsed: Any | None) -> str:
    """
    Texto único usado para comparar com expected_output: corpo textual + conteúdo achatado do JSON.
    """
    chunks: List[str] = [body_text or ""]
    if parsed is not None:
        chunks.append(extract_semantic_text_from_parsed(parsed))
        if has_chart_signals(parsed):
            chunks.append(
                " regenai_chart_evidence chart_type widget graficos_dados graficos_metadados "
            )
    return " ".join(chunks)


def _normalize(s: str) -> str:
    return " ".join((s or "").lower().split())


def soft_match_expected(semantic_text: str, expected_output: str) -> bool:
    """
    Correspondência com saída esperada: substring completa ou fragmentos / sobreposição de palavras-chave.
    """
    exp = _normalize(expected_output)
    if not exp:
        return True
    text = _normalize(semantic_text)
    text_fold = _fold_accents(semantic_text)
    if exp in text:
        return True
    if _fold_accents(expected_output) in text_fold:
        return True

    # Fragmentos (seções separadas por pontuação ou "ou")
    raw_fragments = re.split(r"[\n;|]| ou ", expected_output)
    fragments = [_normalize(f) for f in raw_fragments if len(_normalize(f)) >= 10]
    for frag in fragments:
        if frag and frag in text:
            return True
        if frag and _fold_accents(frag) in text_fold:
            return True

    # Palavras significativas na expectativa (pt/en)
    words = [w for w in re.findall(r"[a-zA-ZáàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ]{4,}", expected_output.lower())]
    if len(words) >= 2:
        hits = sum(1 for w in words if w in text or _fold_accents(w) in text_fold)
        need = max(2, min(len(words), int(len(words) * 0.45) + 1))
        if hits >= need:
            return True

    return False


def evaluate_expected_output(
    *,
    semantic_text: str,
    expected_output: str,
    parsed_body: Any | None,
) -> Tuple[bool, str]:
    """
    Valida saída esperada considerando texto e presença de gráficos quando a pergunta exige visualização.
    Retorna (ok, motivo_curto).
    """
    exp = (expected_output or "").strip()
    if not exp:
        return True, ""

    text = semantic_text
    if soft_match_expected(text, exp):
        return True, ""

    if expects_chart_or_visualization(exp) and parsed_body is not None and has_chart_signals(parsed_body):
        words = [w for w in re.findall(r"[a-zA-ZáàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ]{4,}", exp.lower())]
        text_l = _normalize(text)
        text_fold = _fold_accents(text)
        hits = sum(1 for w in words if w in text_l or _fold_accents(w) in text_fold)
        if hits >= max(1, min(3, len(words) // 2 or 1)):
            return True, "grafico_ok_termos_parciais"

    return False, "nao_bate_com_saida_esperada"


def parse_json_safe(raw: str) -> Any | None:
    if not raw or not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None
