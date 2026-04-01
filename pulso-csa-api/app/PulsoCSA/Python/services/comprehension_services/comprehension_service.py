#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Sistema de Compreensão (Intent Router)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import hashlib
import os
import re
import json
import time
import threading
from typing import Any, Dict, List, Literal, Set, Tuple

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client
from utils.logger import log_workflow

# Threshold de confiança: abaixo disso exibir aviso (não mudar decisão).
INTENT_CONFIDENCE_THRESHOLD = 0.75
# Cache de classificação: TTL em segundos (5–15 min).
INTENT_CACHE_TTL_SEC = int(os.getenv("COMPREHENSION_INTENT_CACHE_TTL_SEC", "300"))
INTENT_CACHE_MAX_SIZE = 500
_intent_cache: Dict[str, Tuple[float, str, float]] = {}  # key -> (timestamp, intent, confidence)
_intent_cache_lock = threading.Lock()

#━━━━━━━━━❮Constantes❯━━━━━━━━━

PROJECT_STATE_VAZIA = "ROOT_VAZIA"
PROJECT_STATE_COM_CONTEUDO = "ROOT_COM_CONTEUDO"
INTENT_ANALISAR = "ANALISAR"
INTENT_EXECUTAR = "EXECUTAR"
TARGET_GOVERNANCE = "/governance/run"
TARGET_CORRECT = "/workflow/correct/run"

# Padrões que indicam ANALISAR (perguntas, diagnóstico, recomendação) — verificados primeiro
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
]
EXECUTAR_KEYWORDS = re.compile(
    r"\b(altere|alterar|implemente|implementar|crie\s+(um|uma|o|a)|criar\s+(um|uma|o|a)|"
    r"corrija\s+(o|a|os|as)|corrigir\s+(o|a|os|as)|adicione|adicionar|remova|remover|"
    r"faça\s+(isso|isto|a\s+correção|a\s+mudança)|fazer\s+(isso|isto)|aplique|aplicar)\b",
    re.IGNORECASE,
)
EXECUTAR_VERBS_STRICT = re.compile(
    r"^(crie|implemente|corrija|adicione|remova|faça|aplique|execute|rode)\b",
    re.IGNORECASE,
)
EXECUTE_SIGNAL_KEYWORDS = re.compile(
    r"\b(faça|faca|fazer|executar|execute|aplicar|aplique|implementar|implemente|rode|rodar)\b",
    re.IGNORECASE,
)

#━━━━━━━━━❮Detecção de estado do projeto❯━━━━━━━━━


def detect_project_state(root_path: str | None) -> Literal["ROOT_VAZIA", "ROOT_COM_CONTEUDO"]:
    if not root_path or not os.path.isdir(root_path):
        return PROJECT_STATE_VAZIA
    for _root, _dirs, filenames in os.walk(root_path):
        if filenames:
            return PROJECT_STATE_COM_CONTEUDO
    return PROJECT_STATE_VAZIA


def detect_execute_signal(prompt: str) -> bool:
    """Usa comprehension_base para sinais expandidos (sim, ok, etc.)."""
    from services.comprehension_services.comprehension_base import detect_execute_signal as _detect
    return _detect(prompt)


#━━━━━━━❮Classificação de intenção (LLM + fallback)❯━━━━━━━

_INTENT_LLM_SYSTEM = """Você classifica a intenção do usuário em exatamente uma de duas opções.

ANALISAR (use quando):
- Pergunta: "o que...", "como...", "qual...", "por que...", "o que pode melhorar", "o que está errado"
- Pedido de diagnóstico, recomendação, avaliação, revisão, explicação
- Qualquer frase que termine em "?" ou que peça opinião/análise sem pedir para executar
- Exemplos: "o que pode melhorar na segurança?", "como faço X?", "analise o código", "me diga o que está errado"

EXECUTAR (use SOMENTE quando):
- O usuário pede explicitamente para FAZER/CRIAR/ALTERAR/IMPLEMENTAR/APLICAR algo com verbo imperativo
- Exemplos: "crie um projeto", "implemente a correção", "corrija o erro e faça", "adicione o endpoint"
- NÃO classifique como EXECUTAR se for pergunta ("o que pode melhorar?") ou pedido de análise

Em dúvida, classifique como ANALISAR.

Responda APENAS com um JSON válido, sem markdown, sem texto extra:
{"intent": "ANALISAR" ou "EXECUTAR", "confidence": número entre 0 e 1, "reason": "breve motivo"}"""


def _classify_intent_fallback(prompt: str) -> str:
    text = (prompt or "").strip()
    if not text:
        return INTENT_ANALISAR
    text_lower = text.lower()
    for pat in ANALISAR_PATTERNS:
        if pat.search(text):
            return INTENT_ANALISAR
    if EXECUTAR_VERBS_STRICT.match(text_lower):
        return INTENT_EXECUTAR
    if EXECUTAR_KEYWORDS.search(text_lower):
        return INTENT_EXECUTAR
    return INTENT_ANALISAR


def _parse_intent_json(raw: str) -> dict | None:
    raw = (raw or "").strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            raw = m.group(1)
    m = re.search(r"\{[^{}]*\"intent\"[^{}]*\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _looks_like_analysis(prompt: str) -> bool:
    text = (prompt or "").strip()
    if not text:
        return True
    for pat in ANALISAR_PATTERNS:
        if pat.search(text):
            return True
    return False


def _prompt_cache_key(prompt: str, usuario: str | None = None) -> str:
    """Chave de cache: hash normalizado (trim, lower, limit 1k) + usuario para isolamento."""
    text = (prompt or "").strip().lower()[:1000]
    u = (usuario or "default").strip()
    return hashlib.sha256(f"{text}|{u}".encode("utf-8")).hexdigest()


def _intent_cache_get(key: str) -> Tuple[str, float] | None:
    """Retorna (intent, confidence) se cache válido. Thread-safe."""
    with _intent_cache_lock:
        now = time.time()
        if key not in _intent_cache:
            return None
        ts, intent, confidence = _intent_cache[key]
        if now - ts > INTENT_CACHE_TTL_SEC:
            del _intent_cache[key]
            return None
        return (intent, confidence)


def _intent_cache_set(key: str, intent: str, confidence: float) -> None:
    """Thread-safe."""
    with _intent_cache_lock:
        if len(_intent_cache) >= INTENT_CACHE_MAX_SIZE:
            by_ts = sorted(_intent_cache.items(), key=lambda x: x[1][0])
            for k, _ in by_ts[: INTENT_CACHE_MAX_SIZE // 2]:
                del _intent_cache[k]
        _intent_cache[key] = (time.time(), intent, confidence)


def classify_intent(prompt: str, usuario: str | None = None) -> Tuple[Literal["ANALISAR", "EXECUTAR"], float]:
    """
    Retorna (intent, confidence). Confidence 0–1; em fallback regex usa 0.5.
    Usa cache por hash do prompt + usuario (isolamento multiusuário) com TTL curto.
    """
    if not prompt or not prompt.strip():
        return (INTENT_ANALISAR, 1.0)
    cache_key = _prompt_cache_key(prompt, usuario)
    cached = _intent_cache_get(cache_key)
    if cached is not None:
        return cached
    if _looks_like_analysis(prompt):
        return (INTENT_ANALISAR, 1.0)
    try:
        client = get_openai_client()
        user_msg = f"Prompt do usuário: \"{prompt[:500]}\"\nClassifique a intenção."
        raw = client.generate_text(
            user_msg, system_prompt=_INTENT_LLM_SYSTEM, temperature_override=0, use_fast_model=True, num_predict=128
        )
        parsed = _parse_intent_json(raw)
        if parsed and isinstance(parsed.get("intent"), str):
            intent = parsed["intent"].strip().upper()
            confidence = float(parsed.get("confidence", 0.8))
            confidence = max(0.0, min(1.0, confidence))
            if intent == INTENT_EXECUTAR:
                if _looks_like_analysis(prompt):
                    _intent_cache_set(cache_key, INTENT_ANALISAR, confidence)
                    return (INTENT_ANALISAR, confidence)
                _intent_cache_set(cache_key, INTENT_EXECUTAR, confidence)
                return (INTENT_EXECUTAR, confidence)
            if intent == INTENT_ANALISAR:
                _intent_cache_set(cache_key, INTENT_ANALISAR, confidence)
                return (INTENT_ANALISAR, confidence)
    except Exception:
        pass
    fallback_intent = _classify_intent_fallback(prompt)
    _intent_cache_set(cache_key, fallback_intent, 0.5)
    return (fallback_intent, 0.5)


def route_decision(prompt: str, root_path: str | None, usuario: str | None = None, force_execute: bool = False) -> Dict[str, Any]:
    """Compatibilidade: delega a route_decision_codigo (módulo código)."""
    from services.comprehension_services.comprehension_codigo import route_decision_codigo
    return route_decision_codigo(prompt, root_path, usuario, force_execute, None)


#━━━━━━━❮Mensagem humanizada❯━━━━━━━


def build_humanized_message(
    intent: str,
    project_state: str,
    should_execute: bool,
    target_endpoint: str | None,
    workflow_result: Dict[str, Any] | None = None,
    analysis_text: str | None = None,
    prompt: str | None = None,
) -> str:
    if intent == INTENT_ANALISAR:
        return analysis_text or "Análise concluída. Segue o plano e as recomendações acima."
    if intent == INTENT_EXECUTAR and not should_execute:
        action = "criação do projeto" if project_state == PROJECT_STATE_VAZIA else "correção do projeto"
        summary = ""
        if prompt and prompt.strip():
            summary = generate_execution_summary(prompt)
        if summary:
            return (
                f"**Resumo do que entendi:** {summary}\n\n"
                f"Para executar de fato ({action}), confirme com: \"faça\", \"executar\", \"aplicar\" ou \"implementar\"."
            )
        return (
            f"Entendi o que você quer fazer ({action}). "
            "Para executar de fato, confirme com: \"faça\", \"executar\", \"aplicar\" ou \"implementar\"."
        )
    if intent == INTENT_EXECUTAR and should_execute and workflow_result:
        if target_endpoint == TARGET_GOVERNANCE:
            id_req = workflow_result.get("id_requisicao", "")
            # Workflow JavaScript (created_files no top level)
            created = workflow_result.get("created_files") or []
            if created:
                lang = workflow_result.get("language", "javascript")
                fw = workflow_result.get("framework") or "vanilla"
                amostra = ", ".join(created[:6])
                if len(created) > 6:
                    amostra += f" e mais {len(created) - 6} arquivo(s)"
                return (
                    f"**Projeto {lang}/{fw} criado com sucesso.**\n\n"
                    f"**O que foi feito:** Estrutura base (package.json, configs) e componentes gerados. "
                    f"Total: {len(created)} arquivo(s).\n\n"
                    f"**Arquivos criados:** {amostra}\n\n"
                    f"**Próximos passos:** Execute `npm install` e `npm run dev` na pasta do projeto. "
                    f"O preview estará disponível em http://localhost:3000 após iniciar o servidor.\n\n"
                    f"Requisição: {id_req}"
                )
            # Workflow JavaScript sem root_path (estrutura planejada, arquivos não escritos)
            is_js_workflow = "project_structure" in workflow_result or (workflow_result.get("language") or "") in ("javascript", "typescript")
            if is_js_workflow:
                lang = workflow_result.get("language", "javascript")
                fw = workflow_result.get("framework") or "vanilla"
                planned = list((workflow_result.get("project_structure") or {}).keys())
                amostra = ", ".join(planned[:6]) if planned else "package.json, configs, App"
                if len(planned) > 6:
                    amostra += f" e mais {len(planned) - 6}"
                return (
                    f"**Estrutura {lang}/{fw} planejada com sucesso.**\n\n"
                    f"**O que foi feito:** Plano de projeto gerado (package.json, configs, componentes). "
                    f"Arquivos planejados: {amostra}\n\n"
                    f"**Por que:** O campo `root_path` não foi informado, então os arquivos não foram escritos em disco.\n\n"
                    f"**Próximos passos:** Informe `root_path` (pasta de destino) e execute novamente para gerar os arquivos. "
                    f"Requisição: {id_req}"
                )
            # Workflow Python
            code_manifest = workflow_result.get("code_manifest") or {}
            files_written = code_manifest.get("files_written") or []
            estrutura = workflow_result.get("estrutura_manifest") or {}
            created_py = estrutura.get("created") or {}
            num_arquivos = len(files_written) + sum(len(v) for v in created_py.values() if isinstance(v, list))
            extra = f" {num_arquivos} artefato(s) gerado(s)." if num_arquivos else ""
            return (
                f"**Projeto Python criado com sucesso.**\n\n"
                f"**O que foi feito:** Estrutura de pastas, código-fonte (rotas, services, models) e configurações. "
                f"Conforme o planejamento.{extra}\n\n"
                f"**Próximos passos:** Execute o projeto na pasta gerada. Requisição: {id_req}"
            )
        if target_endpoint == TARGET_CORRECT:
            id_req = workflow_result.get("id_requisicao", "")
            # Workflow JavaScript (corrected_files no top level)
            corrected = [p for p in (workflow_result.get("corrected_files") or []) if p != ".pulso-corrections.md"]
            if corrected:
                amostra = ", ".join(corrected[:5])
                if len(corrected) > 5:
                    amostra += f" e mais {len(corrected) - 5}"
                return (
                    f"**Correções aplicadas com sucesso.**\n\n"
                    f"**O que foi feito:** Arquivos corrigidos via LLM conforme seu pedido. "
                    f"Arquivos alterados: {amostra}\n\n"
                    f"Requisição: {id_req}"
                )
            return (
                f"Correções aplicadas com sucesso. Requisição: {id_req}. "
                "O projeto foi analisado, corrigido e validado conforme o fluxo de correção."
            )
        # Fallback: workflow com created_files/project_structure mas target_endpoint diferente
        created = workflow_result.get("created_files") or []
        if created:
            lang = workflow_result.get("language", "javascript")
            fw = workflow_result.get("framework") or "vanilla"
            amostra = ", ".join(created[:6])
            if len(created) > 6:
                amostra += f" e mais {len(created) - 6} arquivo(s)"
            return (
                f"**Projeto {lang}/{fw} criado com sucesso.**\n\n"
                f"**Arquivos criados:** {amostra}\n\n"
                f"**Próximos passos:** Execute `npm install` e `npm run dev` na pasta do projeto. "
                f"O preview estará disponível em http://localhost:3000 após iniciar o servidor."
            )
        planned = list((workflow_result.get("project_structure") or {}).keys())
        if planned:
            amostra = ", ".join(planned[:6])
            if len(planned) > 6:
                amostra += f" e mais {len(planned) - 6}"
            return (
                f"**Estrutura planejada com sucesso.**\n\n"
                f"**Arquivos planejados:** {amostra}\n\n"
                f"**Próximos passos:** Informe `root_path` e execute novamente para gerar os arquivos."
            )
    if intent == INTENT_EXECUTAR and should_execute:
        return "Execução concluída."
    return "Processado. Verifique os detalhes na resposta."


#━━━━━━━❮Contexto do projeto para análise personalizada❯━━━━━━━

_CONTEXT_KEY_FILES = [
    "requirements.txt",
    "package.json",
    "main.py",
    "app/main.py",
    "config.py",
    "settings.py",
    "app/core/pulso/config.py",
    ".env.example",
    "Dockerfile",
]
_MAX_CHARS_PER_FILE = 4000
_MAX_TOTAL_CONTEXT_CHARS = 18000
# Análise: contexto reduzido para resposta rápida (~2–3s em vez de minutos)
_ANALYSIS_MAX_CONTEXT_CHARS = int(os.getenv("COMPREHENSION_ANALYSIS_MAX_CONTEXT", "6000"))
_ANALYSIS_MAX_CHARS_PER_FILE = 1500


def _read_file_safe(path: str, max_chars: int = _MAX_CHARS_PER_FILE) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars + 1)
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... (truncado)"
        return content.strip()
    except Exception:
        return ""


def gather_project_context_for_analysis(
    root_path: str | None,
    max_total_chars: int = _MAX_TOTAL_CONTEXT_CHARS,
    max_chars_per_file: int = _MAX_CHARS_PER_FILE,
) -> str:
    if not root_path or not os.path.isdir(root_path):
        return ""
    lines: List[str] = []
    root = os.path.normpath(root_path)
    total_chars = 0
    tree_lines: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
        rel = os.path.relpath(dirpath, root)
        if rel == ".":
            rel = ""
        depth = rel.count(os.sep) + (1 if rel else 0)
        if depth > 3:
            dirnames.clear()
            continue
        folder_indent = "  " * (depth - 1) if depth else ""
        file_indent = "  " * depth
        if rel:
            tree_lines.append(folder_indent + os.path.basename(dirpath) + "/")
        for f in sorted(filenames)[:30]:
            if f.endswith(".pyc"):
                continue
            tree_lines.append(file_indent + f)
    if tree_lines:
        lines.append("--- Estrutura do projeto (árvore) ---")
        lines.append("\n".join(tree_lines[:120]))
        lines.append("")
    for rel_file in _CONTEXT_KEY_FILES:
        if total_chars >= max_total_chars:
            break
        full_path = os.path.join(root, rel_file.replace("/", os.sep))
        if not os.path.isfile(full_path):
            continue
        content = _read_file_safe(full_path, max_chars=max_chars_per_file)
        if not content:
            continue
        if ".env" in rel_file:
            vars_only = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key = line.split("=")[0].strip()
                    if key:
                        vars_only.append(key)
            content = "Variáveis (nomes apenas): " + ", ".join(vars_only) if vars_only else "(nenhuma)"
        lines.append(f"--- Arquivo: {rel_file} ---")
        lines.append(content)
        lines.append("")
        total_chars += len(content)
    if not lines:
        return ""
    return "\n".join(lines)


#━━━━━━━❮Geração de análise (ANALISAR)❯━━━━━━━

_ANALYSIS_LLM_SYSTEM = """Você é um assistente técnico elegante e profissional. O usuário pediu uma análise ou recomendação (não execução).

REGRA: Se houver "Contexto do projeto" com arquivos reais, baseie a resposta nesse projeto específico. Se não houver contexto, mencione brevemente que informar a pasta raiz melhora a precisão.

FORMATO DA RESPOSTA — limpo, legível, sem markdown excessivo (evite **asteriscos** e listas aninhadas):

1. Diagnóstico — use o emoji 📋 uma vez no título. Liste 4–6 pontos em linhas separadas, cada um começando com um hífen (-). Seja preciso e direto.

2. Plano de Ação — use o emoji 📌 uma vez no título. Liste 3–5 itens priorizados, cada um em uma linha com hífen. Para subdetalhes, use indentação ou "→" de forma sutil. Exemplo:
   - Implementar autenticação JWT → usar Flask-JWT-Extended
   - Criar rota / retornando JSON "Teste Pulso: OK"

ESTILO: Texto preciso e pontual. Profissional mas amigável. Use no máximo 2 emojis (um por seção). Não exceda 500 palavras. Evite repetições e rodeios."""


# Mensagem fixa quando LLM de análise falha (permite ao router retornar 200 + code ANALYSIS_UNAVAILABLE).
ANALYSIS_UNAVAILABLE_MESSAGE = "Análise indisponível no momento. Tente novamente."

#━━━━━━━❮Resumo para confirmação (EXECUTAR sem sinal)❯━━━━━━━

_SUMMARY_LLM_SYSTEM = """Você resume em 1-2 frases curtas o que o usuário pediu para criar, implementar ou alterar.
Seja objetivo: liste os principais itens (ex.: API Flask, login JWT, rotas X/Y/Z).
Responda APENAS com o resumo, sem prefixos como "Resumo:" ou "Entendi:". Máximo 150 palavras."""


def generate_execution_summary(prompt: str) -> str:
    """
    Gera um resumo conciso do que o usuário pediu para executar.
    Usado antes de pedir confirmação ("faça", "executar", etc.).
    Fallback: primeiros 120 caracteres do prompt.
    """
    if not prompt or not prompt.strip():
        return ""
    try:
        client = get_openai_client()
        text = client.generate_text(
            f'Pedido do usuário: "{prompt[:600]}"\n\nResuma o que será criado/implementado/alterado.',
            system_prompt=_SUMMARY_LLM_SYSTEM,
            temperature_override=0.2,
            use_fast_model=True,
            num_predict=200,
        )
        if text and "Erro ao gerar texto" not in text:
            summary = text.strip()
            if len(summary) > 300:
                summary = summary[:297] + "..."
            return summary
    except Exception:
        pass
    # Fallback: primeiros caracteres do prompt
    truncated = (prompt or "").strip()[:120]
    if len((prompt or "").strip()) > 120:
        truncated += "..."
    return truncated

# Cache de análise: TTL curto para não servir análise obsoleta (árvore pode mudar).
ANALYSIS_CACHE_TTL_SEC = int(os.getenv("COMPREHENSION_ANALYSIS_CACHE_TTL_SEC", "120"))
ANALYSIS_CACHE_MAX_SIZE = 200
# Timeout e retentativas para reduzir "Análise indisponível" (Ollama/OpenAI lentos ou instáveis).
ANALYSIS_TIMEOUT_SEC = int(os.getenv("COMPREHENSION_ANALYSIS_TIMEOUT_SEC", "120"))
ANALYSIS_MAX_RETRIES = max(1, int(os.getenv("COMPREHENSION_ANALYSIS_MAX_RETRIES", "2")))
_analysis_cache: Dict[str, Tuple[float, str]] = {}  # key -> (timestamp, text)
_analysis_cache_lock = threading.Lock()


def _analysis_cache_key(prompt: str, root_path: str | None, usuario: str | None = None) -> str:
    """Cache isolado por usuário (evita vazamento entre usuários)."""
    p = (prompt or "").strip()[:1000]
    r = (root_path or "").strip()
    u = (usuario or "default").strip()
    return hashlib.sha256(f"{p}|{r}|{u}".encode("utf-8")).hexdigest()


# Prompts indicando criação/implementação não precisam de contexto de projeto existente
_CREATION_PROMPT_PATTERN = re.compile(
    r"^(crie|criar|implemente|implementar|desenvolva|desenvolver)\s+",
    re.IGNORECASE,
)


def generate_analysis_text(prompt: str, root_path: str | None = None, usuario: str | None = None) -> Tuple[str, bool]:
    """
    Retorna (texto_da_análise, sucesso).
    Otimizado para resposta quase instantânea: num_predict limitado, contexto reduzido quando desnecessário.
    """
    if not prompt or not prompt.strip():
        return ("Nenhum pedido de análise informado.", True)
    cache_key = _analysis_cache_key(prompt, root_path, usuario)
    with _analysis_cache_lock:
        now = time.time()
        if cache_key in _analysis_cache:
            ts, text = _analysis_cache[cache_key]
            if now - ts <= ANALYSIS_CACHE_TTL_SEC:
                return (text, True)
            del _analysis_cache[cache_key]
    try:
        client = get_openai_client()
        context_block = ""
        path_note = ""
        # Pular contexto pesado quando prompt é de criação (não há projeto existente para analisar)
        skip_heavy_context = bool(_CREATION_PROMPT_PATTERN.match((prompt or "").strip()))
        if root_path and not skip_heavy_context:
            root_path = root_path.strip()
        if root_path and not skip_heavy_context:
            if not os.path.isdir(root_path):
                path_note = (
                    "[AVISO: O caminho informado não existe ou não é acessível por este servidor.]\n\n"
                )
            else:
                context_block = gather_project_context_for_analysis(
                    root_path,
                    max_total_chars=_ANALYSIS_MAX_CONTEXT_CHARS,
                    max_chars_per_file=_ANALYSIS_MAX_CHARS_PER_FILE,
                )
                if context_block:
                    context_block = (
                        "Contexto do projeto:\n\n" + context_block + "\n\n--- Fim do contexto ---\n\n"
                    )
                else:
                    path_note = "[AVISO: Nenhum arquivo chave encontrado na pasta raiz.]\n\n"
        elif not skip_heavy_context:
            path_note = "[Dica: Envie 'root_path' para análise personalizada.]\n\n"
        user_msg = path_note + context_block + f'Pedido do usuário: "{prompt[:600]}"\n\nForneça diagnóstico e plano de ação no formato limpo descrito (hífens, sem asteriscos, emojis pontuais).'
        text = ""
        for attempt in range(ANALYSIS_MAX_RETRIES):
            text = client.generate_text(
                user_msg,
                system_prompt=_ANALYSIS_LLM_SYSTEM,
                use_fast_model=True,
                num_predict=650,
                timeout_override=ANALYSIS_TIMEOUT_SEC,
            )
            if text and "Erro ao gerar texto" not in text:
                break
            if attempt < ANALYSIS_MAX_RETRIES - 1:
                time.sleep(1.5 * (attempt + 1))
        if not text or "Erro ao gerar texto" in text:
            return (ANALYSIS_UNAVAILABLE_MESSAGE, False)
        with _analysis_cache_lock:
            if len(_analysis_cache) >= ANALYSIS_CACHE_MAX_SIZE:
                by_ts = sorted(_analysis_cache.items(), key=lambda x: x[1][0])
                for k, _ in by_ts[: ANALYSIS_CACHE_MAX_SIZE // 2]:
                    del _analysis_cache[k]
            _analysis_cache[cache_key] = (time.time(), text)
        return (text, True)
    except Exception:
        return (ANALYSIS_UNAVAILABLE_MESSAGE, False)


#━━━━━━━❮Árvore de arquivos (novos com *)❯━━━━━━━


def _normalize_path_for_comparison(path: str, root_path: str) -> str:
    p = (path or "").replace("\\", "/").strip().lower()
    r = (root_path or "").replace("\\", "/").strip().lower().rstrip("/")
    if r and p.startswith(r):
        p = p[len(r) :].lstrip("/")
    return "/" + p if not p.startswith("/") else p


def extract_new_paths_from_workflow_result(
    workflow_result: Dict[str, Any] | None,
    root_path: str | None,
    target_endpoint: str | None,
) -> Set[str]:
    if not workflow_result or not root_path:
        return set()
    new_paths: Set[str] = set()
    if target_endpoint == TARGET_GOVERNANCE:
        # Workflow JavaScript (created_files no top level)
        for p in workflow_result.get("created_files") or []:
            norm = _normalize_path_for_comparison(p, root_path)
            if norm and norm != "/":
                new_paths.add(norm)
        for p in (workflow_result.get("project_structure") or {}).keys():
            norm = _normalize_path_for_comparison(p, root_path)
            if norm and norm != "/":
                new_paths.add(norm)
        # Workflow Python
        code_manifest = workflow_result.get("code_manifest") or {}
        for p in code_manifest.get("files_written") or []:
            norm = _normalize_path_for_comparison(p, root_path)
            if norm and norm != "/":
                new_paths.add(norm)
        estrutura = workflow_result.get("estrutura_manifest") or {}
        base = (estrutura.get("root_path") or "").replace("\\", "/")
        for folder, files in (estrutura.get("created") or {}).items():
            for f in files or []:
                rel = (folder.strip("/") + "/" + f).strip("/") if folder and folder != "." else f
                full = (base + "/" + rel).replace("//", "/")
                norm = _normalize_path_for_comparison(full, root_path)
                if norm and norm != "/":
                    new_paths.add(norm)
    if target_endpoint == TARGET_CORRECT:
        # Workflow JavaScript (corrected_files no top level)
        for p in workflow_result.get("corrected_files") or []:
            if p and p != ".pulso-corrections.md":
                norm = _normalize_path_for_comparison(p, root_path)
                if norm and norm != "/":
                    new_paths.add(norm)
        # Workflow Python
        execucao = workflow_result.get("execucao") or {}
        for p in execucao.get("created_files") or []:
            norm = _normalize_path_for_comparison(p, root_path)
            if norm and norm != "/":
                new_paths.add(norm)
        plano = workflow_result.get("plano_de_mudancas") or {}
        for item in plano.get("novos_arquivos") or []:
            p = item.get("path") if isinstance(item, dict) else getattr(item, "path", None)
            if p:
                norm = _normalize_path_for_comparison(p, root_path)
                if norm and norm != "/":
                    new_paths.add(norm)
    return new_paths


def build_project_file_tree(root_path: str | None, new_paths_set: Set[str] | None = None) -> str:
    if not root_path or not os.path.isdir(root_path):
        return ""
    new_paths = new_paths_set or set()
    root_norm = os.path.normpath(root_path)
    lines: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
        rel_dir = os.path.relpath(dirpath, root_norm)
        if rel_dir == ".":
            rel_dir = ""
        depth = rel_dir.count(os.sep) + (1 if rel_dir else 0)
        folder_indent = "  " * (depth - 1) if depth else ""
        file_indent = "  " * depth
        if rel_dir:
            folder_name = os.path.basename(dirpath)
            lines.append(folder_indent + folder_name + "/")
        for f in sorted(filenames):
            if f.endswith(".pyc"):
                continue
            rel_file = os.path.join(rel_dir, f).replace("\\", "/").strip("/")
            rp_lower = rel_file.lower()
            is_new = False
            for n in new_paths:
                np = n.lower().strip("/")
                if np == rp_lower or np.endswith("/" + f.lower()) or rp_lower.endswith("/" + np.split("/")[-1]):
                    is_new = True
                    break
            suffix = " *" if is_new else ""
            lines.append(file_indent + f + suffix)
    return "\n".join(lines) if lines else "(pasta vazia ou inacessível)"


def build_file_tree_from_manifest(workflow_result: Dict[str, Any] | None) -> str:
    """
    Constrói árvore de arquivos a partir do manifest do workflow (project_structure ou created_files).
    Usado quando root_path está vazio (projeto criado em memória, ex.: ROOT_VAZIA).
    Formato: indentação com 2 espaços (compatível com build_project_file_tree), pastas com /, arquivos com *.
    """
    if not workflow_result:
        return ""
    project_structure = workflow_result.get("project_structure") or {}
    created_files = workflow_result.get("created_files") or []
    paths: Set[str] = set()
    if isinstance(project_structure, dict):
        paths.update(k.replace("\\", "/").strip("/") for k in project_structure if k)
    for p in created_files:
        if p and isinstance(p, str):
            paths.add(p.replace("\\", "/").strip("/"))
    if not paths:
        return ""
    lines: List[str] = []
    root_name = "projeto"
    seen_folders: Set[str] = set()
    sorted_paths = sorted(paths)
    for rel_path in sorted_paths:
        parts = rel_path.split("/")
        for i in range(1, len(parts)):
            folder = "/".join(parts[:i])
            if folder not in seen_folders:
                seen_folders.add(folder)
                folder_indent = "  " * i
                lines.append(folder_indent + parts[i - 1] + "/")
        file_depth = len(parts)
        file_indent = "  " * file_depth
        fname = parts[-1]
        lines.append(file_indent + fname + " *")
    if not lines:
        return ""
    return root_name + "/\n" + "\n".join(lines)


#━━━━━━━❮cURL para testes do sistema criado/corrigido❯━━━━━━━

# URL base do sistema criado (Flask: 5000, FastAPI: 8000). Configurável via env.
CREATED_API_BASE_URL = os.getenv("CREATED_API_BASE_URL", "http://localhost:5000")

# Regex para extrair rotas de Flask e FastAPI
_ROUTE_FLASK = re.compile(r'@(?:app|[\w]+)\.route\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*methods\s*=\s*\[([^\]]+)\])?', re.IGNORECASE)
_ROUTE_FASTAPI = re.compile(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)


def _collect_python_files_from_workflow(
    workflow_result: Dict[str, Any] | None,
    root_path: str | None,
    target_endpoint: str | None,
) -> List[str]:
    """Coleta caminhos de arquivos .py criados/alterados pelo workflow."""
    if not workflow_result or not root_path:
        return []
    files: List[str] = []
    rp = (root_path or "").replace("\\", "/").rstrip("/")
    if target_endpoint == TARGET_GOVERNANCE:
        for p in (workflow_result.get("code_manifest") or {}).get("files_written") or []:
            if (p or "").endswith(".py"):
                files.append(p)
        estrutura = workflow_result.get("estrutura_manifest") or {}
        base = (estrutura.get("root_path") or rp).replace("\\", "/").rstrip("/")
        for folder, flist in (estrutura.get("created") or {}).items():
            for f in flist or []:
                if (f or "").endswith(".py"):
                    segs = [base, (folder or ".").strip("/"), f]
                    path = os.path.normpath(os.path.join(*segs)).replace("\\", "/")
                    files.append(path)
    elif target_endpoint == TARGET_CORRECT:
        for p in (workflow_result.get("execucao") or {}).get("created_files") or []:
            if (p or "").endswith(".py"):
                files.append(p)
        for item in (workflow_result.get("plano_de_mudancas") or {}).get("arquivos_a_alterar") or []:
            p = item.get("path") if isinstance(item, dict) else getattr(item, "path", None)
            if p and str(p).endswith(".py"):
                full = os.path.join(rp, p) if not os.path.isabs(str(p)) else p
                files.append(full)
    return list(dict.fromkeys(f for f in files if f))


def _extract_routes_from_python_file(file_path: str) -> List[Tuple[str, str]]:
    """
    Extrai (method, path) de um arquivo Python.
    Retorna lista de tuplas, ex.: [("GET", "/"), ("POST", "/login")].
    """
    routes: List[Tuple[str, str]] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []
    # FastAPI: @app.get("/path") ou @router.post("/path")
    for m in _ROUTE_FASTAPI.finditer(content):
        method = (m.group(1) or "get").upper()
        path = (m.group(2) or "/").strip()
        if not path.startswith("/"):
            path = "/" + path
        routes.append((method, path))
    # Flask: @app.route("/path") ou @app.route("/path", methods=["GET","POST"])
    for m in _ROUTE_FLASK.finditer(content):
        path = (m.group(1) or "/").strip()
        if not path.startswith("/"):
            path = "/" + path
        methods_str = (m.group(2) or "GET").upper()
        methods = [x.strip().strip('"\'') for x in methods_str.split(",")]
        if not methods:
            methods = ["GET"]
        for method in methods:
            if method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                routes.append((method, path))
                break
        else:
            routes.append(("GET", path))
    return routes


def build_curl_commands_for_created_system(
    workflow_result: Dict[str, Any] | None,
    root_path: str | None,
    target_endpoint: str | None,
    created_api_base_url: str | None = None,
) -> List[str]:
    """
    Gera comandos cURL para testar o sistema criado/corrigido (não a PulsoAPI).
    Extrai rotas dos arquivos .py gerados e monta cURLs.
    """
    if not workflow_result or not root_path or not target_endpoint:
        return []
    base = (created_api_base_url or CREATED_API_BASE_URL).rstrip("/")
    files = _collect_python_files_from_workflow(workflow_result, root_path, target_endpoint)
    seen: Set[Tuple[str, str]] = set()
    curls: List[str] = []
    for fp in files:
        if not os.path.isfile(fp):
            continue
        for method, path in _extract_routes_from_python_file(fp):
            key = (method, path)
            if key in seen:
                continue
            seen.add(key)
            path = path if path.startswith("/") else "/" + path
            if method == "GET":
                curls.append(f"curl -s -X GET {base}{path}")
            else:
                body = "{}" if method in ("POST", "PUT", "PATCH") else ""
                curls.append(f'curl -s -X {method} {base}{path} -H "Content-Type: application/json" -d \'{body}\'')
    if not curls:
        curls.append(f"# Inicie o sistema criado (ex.: python main.py) e teste: curl -s -X GET {base}/")
    return curls


def build_curl_commands(
    base_url: str,
    prompt: str,
    usuario: str,
    root_path: str | None,
    target_endpoint: str | None,
    executed: bool = False,
    workflow_result: Dict[str, Any] | None = None,
) -> List[str]:
    """
    Gera comandos cURL APENAS quando o sistema foi criado/corrigido.
    Retorna cURLs para testar o sistema requisitado pelo usuário (rotas extraídas do código gerado).
    NÃO expõe rotas da PulsoAPI. Se o workflow não foi executado, retorna lista vazia.
    """
    if workflow_result and executed and target_endpoint and root_path:
        return build_curl_commands_for_created_system(
            workflow_result=workflow_result,
            root_path=root_path,
            target_endpoint=target_endpoint,
        )
    return []


#━━━━━━━❮Contrato e sugestão frontend❯━━━━━━━


def get_route_contract() -> Dict[str, Any]:
    return {
        "route": {
            "method": "POST",
            "path": "/comprehension/run",
            "description": "Entrada principal do workflow. Classifica a intenção (ANALISAR/EXECUTAR), decide o modo do projeto e dispara ou não governance/run ou workflow/correct/run.",
            "query": {
                "async_mode": {
                    "type": "boolean",
                    "default": True,
                    "description": "Se true, criação/correção retorna HTTP 202 + job_id; consulte GET /comprehension/jobs/{job_id}. false = síncrono (pode estourar timeout de proxy).",
                },
            },
        },
        "async_poll": {
            "method": "GET",
            "path": "/comprehension/jobs/{job_id}",
            "description": "Consulta job criado quando POST /comprehension/run retornou 202. status: pending | running | completed | failed; em completed, 'response' é o JSON completo da ComprehensionResponse.",
        },
        "request": {
            "Content-Type": "application/json",
            "body": {
                "usuario": {"type": "string", "required": True, "description": "Identificação do usuário."},
                "prompt": {"type": "string", "required": True, "description": "Prompt cru / descrição do projeto (ex.: texto do chat)."},
                "root_path": {"type": "string | null", "required": False, "default": None, "description": "Caminho raiz do projeto. Obrigatório para executar fluxo de correção (ROOT_COM_CONTEUDO)."},
                "force_execute": {"type": "boolean", "required": False, "default": False, "description": "Se true, executa sem pedir confirmação."},
                "force_module": {"type": "string | null", "required": False, "default": None, "description": "Força módulo: codigo, infraestrutura ou inteligencia-dados."},
                "history": {"type": "array | null", "required": False, "default": None, "description": "Histórico de mensagens para contexto."},
            },
            "example": {
                "usuario": "usuario@email.com",
                "prompt": "Criar API REST para gestão de pedidos",
                "root_path": "C:\\Users\\pytho\\Desktop\\MeuProjeto",
            },
        },
        "response": {
            "Content-Type": "application/json",
            "body": {
                "intent": {"type": "string", "enum": ["ANALISAR", "EXECUTAR"], "description": "Intenção classificada."},
                "project_state": {"type": "string", "enum": ["ROOT_VAZIA", "ROOT_COM_CONTEUDO"], "description": "Estado da raiz do projeto."},
                "should_execute": {"type": "boolean", "description": "Se o gate de execução foi atendido."},
                "target_endpoint": {"type": "string | null", "enum": ["/governance/run", "/workflow/correct/run", None], "description": "Endpoint que seria ou foi disparado; null quando intent é ANALISAR."},
                "explanation": {"type": "string", "description": "Explicação da decisão de roteamento."},
                "next_action": {"type": "string", "description": "Próximo passo descrito."},
                "message": {"type": "string", "description": "Mensagem humanizada para exibir no frontend."},
                "file_tree": {"type": "string | null", "description": "Árvore de arquivos do projeto; novos com * ao lado do nome."},
                "system_behavior": {"type": "object | null", "description": "JSON de contrato do sistema."},
                "frontend_suggestion": {"type": "string | null", "description": "Sugestão de como exibir as mudanças na área do chat."},
                "curl_commands": {"type": "array of string", "description": "Comandos cURL em uma linha para testes (health, comprehension/run, governance ou correct)."},
                "preview_frontend_url": {"type": "string | null", "description": "URL do preview (ex.: http://localhost:3000); preenchido quando workflow executou e gerou tela de teste."},
            },
            "example": {
                "intent": "EXECUTAR",
                "project_state": "ROOT_VAZIA",
                "should_execute": True,
                "target_endpoint": "/governance/run",
                "explanation": "Intenção: EXECUTAR. Projeto: ROOT_VAZIA. Sinal de execução: sim.",
                "next_action": "Disparar fluxo: /governance/run",
                "message": "Projeto criado com sucesso. Requisição: REQ-20250202-123456. Estrutura e código foram gerados conforme o planejamento.",
                "file_tree": "REQ-20250202-123456/\n  generated_code/\n    main.py *\n    requirements.txt *",
                "system_behavior": {},
                "frontend_suggestion": "Mostre a 'message' como mensagem de sucesso no chat. Exiba a 'file_tree' em um bloco colapsável ou seção 'Árvore do projeto' (novos arquivos com *).",
            },
        },
        "errors": {
            "400": "Campo 'prompt' vazio ou, no fluxo de correção, 'root_path' ausente.",
            "500": "Erro ao executar fluxo de criação (governance) ou de correção (workflow/correct).",
        },
        "http_202_async": {
            "description": (
                "Quando async_mode=true e o fluxo dispara governance ou correct, a API responde imediatamente com job_id. "
                "Em cloud (Railway), resolved_root_path é o diretório no disco do servidor; caminhos locais do PC não são usados."
            ),
            "body_example": {
                "job_id": "uuid",
                "status": "pending",
                "message": "Workflow em execução em segundo plano…",
                "poll_path": "/comprehension/jobs/{job_id}",
                "resolved_root_path": "/app/api/app/PulsoCSA/pulso_workspace/user@example.com",
                "client_root_path_sent": "C:\\\\Users\\\\... (opcional; ignorado em cloud se fora da base)",
                "execution_host": "server",
                "cloud_workspace_note_pt": "Texto explicativo em produção (Railway) ou null em dev.",
            },
        },
    }


def get_system_behavior_spec() -> Dict[str, Any]:
    return {
        "endpoint": "POST /comprehension/run",
        "description": (
            "Entrada principal do workflow (PulsoCSA: Cursor-like sem IDE). "
            "Classifica a intenção (ANALISAR/EXECUTAR), decide o modo do projeto e dispara governance/run (criação) ou workflow/correct/run (correção). "
            "Agentes: C1 Governança → C2 Análise/Plano → C2b Code Plan → C3 Code Writer → C4 Code Implementer → C5 Testes → Pipeline autocorreção. "
            "Criação: código do zero com melhores práticas, documentação, otimização e segurança. "
            "Correção: alteração mínima do código original, otimizada para velocidade, segurança e qualidade."
        ),
        "input": {
            "usuario": "string, obrigatório — identificação do usuário",
            "prompt": "string, obrigatório — descrição do projeto ou pedido (ex.: texto do chat)",
            "root_path": "string, opcional — caminho raiz do projeto; obrigatório para executar fluxo de correção",
        },
        "output": {
            "intent": "ANALISAR | EXECUTAR",
            "project_state": "ROOT_VAZIA | ROOT_COM_CONTEUDO",
            "should_execute": "boolean",
            "target_endpoint": "string | null — /governance/run ou /workflow/correct/run quando aplicável",
            "explanation": "string",
            "next_action": "string",
            "message": "string — mensagem humanizada para exibir na UI",
            "file_tree": "string | null — árvore de arquivos do projeto; novos com * ao lado do nome",
            "system_behavior": "object — este contrato",
            "frontend_suggestion": "string — sugestão de como exibir as mudanças na área do chat/Descrição do projeto",
            "curl_commands": "string[] — comandos cURL em uma linha para testes",
            "preview_frontend_url": "string | null — URL do preview (localhost:3000) quando workflow executou",
        },
        "parameters_behavior": {
            "ROOT_VAZIA": "fluxo de criação (governance/run) se EXECUTAR e should_execute",
            "ROOT_COM_CONTEUDO": "fluxo de correção (workflow/correct/run) se EXECUTAR e should_execute",
            "ANALISAR": "nunca dispara workflow; retorna análise e plano",
            "EXECUTAR_sem_sinal": "retorna pedido de confirmação (ex.: diga 'faça' para executar)",
        },
    }


def get_frontend_suggestion(
    intent: str,
    project_state: str,
    should_execute: bool,
    has_file_tree: bool,
    target_endpoint: str | None,
) -> str:
    if intent == INTENT_ANALISAR:
        return (
            "Exiba a mensagem de análise no chat. Use o campo 'message' como conteúdo principal. "
            "Se quiser, mostre também 'explanation' em um tooltip ou texto secundário."
        )
    if intent == INTENT_EXECUTAR and not should_execute:
        return (
            "Mostre a 'message' no chat e destaque que o usuário pode confirmar com 'faça', 'executar' ou 'aplicar'. "
            "Exiba o campo 'next_action' como dica abaixo do input."
        )
    if intent == INTENT_EXECUTAR and should_execute:
        parts = [
            "Mostre a 'message' como mensagem de sucesso no chat (workflow executado: criação ou correção).",
            "Exiba a 'file_tree' em um bloco colapsável ou seção 'Árvore do projeto' (novos arquivos com *).",
        ]
        if has_file_tree:
            parts.append("Destaque a árvore de arquivos para o usuário revisar o que foi criado/alterado.")
        parts.append(
            "Se 'preview_frontend_url' estiver presente (ex.: http://localhost:3000), exiba o link e indique: "
            "execute `npm install` e `npm run dev` na pasta do projeto para ver o preview."
        )
        return " ".join(parts)
    return "Use o campo 'message' como resposta principal no chat e 'file_tree' se disponível."
