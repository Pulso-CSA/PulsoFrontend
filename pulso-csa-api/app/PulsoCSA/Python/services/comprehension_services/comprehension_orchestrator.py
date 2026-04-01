#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Orquestrador – Detecta módulo e roteia❯━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import json
import os
import re
import threading
import time
import traceback
from typing import Any, Dict, List, Optional

try:
    from utils.log_manager import add_log as _orch_log
except ImportError:
    from app.utils.log_manager import add_log as _orch_log

_LOG_ORCH = "comprehension_orchestrator"


def _log(level: str, msg: str) -> None:
    try:
        _orch_log(level, msg, _LOG_ORCH)
    except Exception:
        pass

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client

MODULE_CODIGO = "codigo"
MODULE_INFRA = "infraestrutura"
MODULE_ID = "inteligencia-dados"

# Padrões para inferir módulo (regex primeiro, LLM fallback)
INFRA_KEYWORDS = re.compile(
    r"\b(terraform|infraestrutura|infra|aws|azure|gcp|deploy|provisionar|"
    r"container|kubernetes|vpc|subnet|ec2|s3|lambda|cloud)\b",
    re.IGNORECASE,
)
ID_KEYWORDS = re.compile(
    r"\b(dados|banco|sql|consulta|query|dataset|modelo\s+ml|treinar|previsão|previsao|"
    r"churn|correlação|correlacao|estatística|estatistica|analise\s+dados|"
    r"captura\s+dados|tratamento\s+limpeza)\b",
    re.IGNORECASE,
)
# Código/PulsoCSA: blueprint de pastas/endpoints, estrutura do projeto, API, criar/corrigir código
CODIGO_KEYWORDS = re.compile(
    r"\b(projeto|código|codigo|api|backend|corrigir|implementar|criar\s+(um\s+)?projeto|"
    r"refatorar|endpoint(s)?|estrutura\s+de\s+pastas|pastas|estrutura\s+do\s+projeto|"
    r"blueprint|gerar\s+blueprint|blueprint\s+de\s+pastas|sistema|funciona|funcionamento|"
    r"educação|educacao|app|aplicação|aplicacao)\b",
    re.IGNORECASE,
)
# Desempate: "gerar blueprint (de) pastas e endpoints" → sempre código (estrutura de projeto)
CODIGO_OVERRIDE_PATTERN = re.compile(
    r"\b(gerar\s+)?blueprint\s+.*(pastas|endpoints?|estrutura)",
    re.IGNORECASE,
)

_MODULE_LLM_SYSTEM = """Você classifica em qual MÓDULO da PulsoAPI a mensagem do usuário se encaixa.

Módulos disponíveis:
- codigo: desenvolvimento de software — criar projeto, corrigir código, implementar, API, backend, ESTRUTURA DO PROJETO (blueprint de pastas, endpoints, organização de diretórios). "Gerar blueprint de pastas e endpoints" = codigo.
- infraestrutura: Terraform, AWS, Azure, GCP, deploy de infra, containers, provisionar nuvem (não estrutura de pastas de código)
- inteligencia-dados: consultas em banco, análise de dados, treinar modelo ML, previsão, estatística, churn

Regra importante: blueprint de pastas, endpoints ou estrutura do projeto/código → SEMPRE codigo. Não confundir com infraestrutura de nuvem.

Responda APENAS com JSON válido, sem markdown:
{"module": "codigo" ou "infraestrutura" ou "inteligencia-dados", "confidence": 0.0 a 1.0, "reason": "breve motivo"}"""

_MODULE_CACHE: Dict[str, tuple] = {}
_MODULE_CACHE_LOCK = threading.Lock()
_MODULE_CACHE_TTL = int(os.getenv("COMPREHENSION_MODULE_CACHE_TTL_SEC", "600"))


def _module_cache_key(prompt: str, usuario: str | None) -> str:
    import hashlib
    p = (prompt or "").strip().lower()[:500]
    u = (usuario or "default").strip()
    return hashlib.sha256(f"module|{p}|{u}".encode()).hexdigest()


def detect_module(prompt: str, usuario: str | None = None, force_module: str | None = None) -> Dict[str, Any]:
    """
    Detecta o módulo (codigo, infraestrutura, inteligencia-dados).
    Retorna {module, confidence, reason}.
    Se force_module fornecido, usa direto.
    """
    if force_module and force_module in (MODULE_CODIGO, MODULE_INFRA, MODULE_ID):
        _log("info", f"[detect_module] force_module={force_module}")
        return {"module": force_module, "confidence": 1.0, "reason": "módulo forçado pelo usuário"}

    prompt_lower = (prompt or "").strip().lower()
    if not prompt_lower:
        _log("info", "[detect_module] prompt vazio → default codigo")
        return {"module": MODULE_CODIGO, "confidence": 0.5, "reason": "prompt vazio, default código"}

    # Override: "gerar blueprint de pastas e endpoints" (estrutura de projeto) → sempre código
    if CODIGO_OVERRIDE_PATTERN.search(prompt_lower):
        _log("info", "[detect_module] override blueprint/pastas → codigo")
        return {"module": MODULE_CODIGO, "confidence": 0.95, "reason": "blueprint/pastas/endpoints = estrutura de projeto (codigo)"}

    # Cache
    cache_key = _module_cache_key(prompt, usuario)
    with _MODULE_CACHE_LOCK:
        import time
        now = time.time()
        if cache_key in _MODULE_CACHE:
            ts, m, c, r = _MODULE_CACHE[cache_key]
            if now - ts <= _MODULE_CACHE_TTL:
                _log("info", f"[detect_module] cache hit → module={m} conf={c:.2f} reason={r!r}")
                return {"module": m, "confidence": c, "reason": r}
            del _MODULE_CACHE[cache_key]

    # Heurística: múltiplos matches dão prioridade por ordem
    infra_score = len(INFRA_KEYWORDS.findall(prompt_lower))
    id_score = len(ID_KEYWORDS.findall(prompt_lower))
    codigo_score = len(CODIGO_KEYWORDS.findall(prompt_lower))

    if infra_score > id_score and infra_score > codigo_score:
        result = {"module": MODULE_INFRA, "confidence": min(0.9, 0.5 + infra_score * 0.2), "reason": "keywords infra"}
    elif id_score > infra_score and id_score > codigo_score:
        result = {"module": MODULE_ID, "confidence": min(0.9, 0.5 + id_score * 0.2), "reason": "keywords inteligência de dados"}
    elif codigo_score > 0:
        result = {"module": MODULE_CODIGO, "confidence": min(0.9, 0.5 + codigo_score * 0.2), "reason": "keywords código"}
    else:
        _log(
            "info",
            f"[detect_module] heurística empatada/zero → LLM módulo | scores infra={infra_score} id={id_score} codigo={codigo_score} | "
            f"preview={(prompt or '')[:100]!r}",
        )
        # LLM fallback
        t_llm = time.perf_counter()
        try:
            client = get_openai_client()
            raw = client.generate_text(
                f'Prompt do usuário: "{prompt[:400]}"\nQual módulo?',
                system_prompt=_MODULE_LLM_SYSTEM,
                temperature_override=0,
                use_fast_model=True,
                num_predict=128,
            )
            parsed = _parse_module_json(raw)
            if parsed:
                m = parsed.get("module", "").strip().lower()
                if m in ("codigo", "código"):
                    result = {"module": MODULE_CODIGO, "confidence": float(parsed.get("confidence", 0.8)), "reason": parsed.get("reason", "")}
                elif m in ("infraestrutura", "infra"):
                    result = {"module": MODULE_INFRA, "confidence": float(parsed.get("confidence", 0.8)), "reason": parsed.get("reason", "")}
                elif m in ("inteligencia-dados", "inteligencia_dados", "id"):
                    result = {"module": MODULE_ID, "confidence": float(parsed.get("confidence", 0.8)), "reason": parsed.get("reason", "")}
                else:
                    result = {"module": MODULE_CODIGO, "confidence": 0.5, "reason": "LLM indeciso, default código"}
            else:
                result = {"module": MODULE_CODIGO, "confidence": 0.5, "reason": "parse falhou, default código"}
            _log(
                "info",
                f"[detect_module] LLM módulo em {time.perf_counter()-t_llm:.2f}s → {result.get('module')} | "
                f"raw_trecho={(raw or '')[:200]!r}",
            )
        except Exception as e:
            _log(
                "error",
                f"[detect_module] LLM módulo exceção: {type(e).__name__}: {e}\n{traceback.format_exc()[:1200]}",
            )
            result = {"module": MODULE_CODIGO, "confidence": 0.5, "reason": "LLM falhou, default código"}

    _log(
        "info",
        f"[detect_module] resultado final module={result['module']} conf={result.get('confidence')} "
        f"reason={result.get('reason')!r} | scores infra={infra_score} id={id_score} codigo={codigo_score}",
    )
    with _MODULE_CACHE_LOCK:
        import time
        _MODULE_CACHE[cache_key] = (time.time(), result["module"], result["confidence"], result["reason"])
    return result


def _parse_module_json(raw: str) -> dict | None:
    raw = (raw or "").strip()
    if "```" in raw:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            raw = m.group(1)
    m = re.search(r"\{[^{}]*\"module\"[^{}]*\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def route_to_module(
    prompt: str,
    root_path: str | None,
    usuario: str | None,
    force_execute: bool = False,
    force_module: str | None = None,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """
    Ponto central: detecta módulo e delega ao handler específico.
    Retorna decisão completa (module, intent, target_endpoint, etc.).
    """
    t0 = time.perf_counter()
    prev = (prompt or "").strip().replace("\n", " ")[:100]
    rp = ((root_path or "")[:160] + "…") if root_path and len(root_path) > 160 else (root_path or "")
    _log(
        "info",
        f"[route_to_module] início | usuario={(usuario or '')[:48]!r} | root_path={rp!r} | force_execute={force_execute} | "
        f"force_module={force_module!r} | prompt_preview={prev!r}",
    )
    module_detection = detect_module(prompt, usuario, force_module)
    module = module_detection["module"]

    if module == MODULE_INFRA:
        from services.comprehension_services.comprehension_infra import route_decision_infra
        out = route_decision_infra(prompt, root_path, usuario, force_execute, history)
    elif module == MODULE_ID:
        from services.comprehension_services.comprehension_id import route_decision_id
        out = route_decision_id(prompt, root_path, usuario, force_execute, history)
    else:
        from services.comprehension_services.comprehension_codigo import route_decision_codigo
        out = route_decision_codigo(prompt, root_path, usuario, force_execute, history)
    _log(
        "info",
        f"[route_to_module] fim em {time.perf_counter()-t0:.2f}s | module={module} | intent={out.get('intent')} | "
        f"should_execute={out.get('should_execute')} | target={out.get('target_endpoint')}",
    )
    return out
