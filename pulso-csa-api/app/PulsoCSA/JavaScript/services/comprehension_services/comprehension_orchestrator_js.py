#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Orquestrador JavaScript – Detecta módulo e roteia❯━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import json
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional

try:
    from utils.log_manager import add_log
except ImportError:
    from app.utils.log_manager import add_log
_LOG_SOURCE = "comprehension_js"

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
    t0 = time.perf_counter()
    try:
        add_log("info", "[detect_module] início", _LOG_SOURCE)
    except Exception:
        pass

    if force_module and force_module in (MODULE_CODIGO, MODULE_INFRA, MODULE_ID):
        try:
            add_log("info", f"[detect_module] force_module={force_module} ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
        except Exception:
            pass
        return {"module": force_module, "confidence": 1.0, "reason": "módulo forçado pelo usuário"}

    prompt_lower = (prompt or "").strip().lower()
    if not prompt_lower:
        try:
            add_log("info", f"[detect_module] prompt vazio, default codigo ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
        except Exception:
            pass
        return {"module": MODULE_CODIGO, "confidence": 0.5, "reason": "prompt vazio, default código"}

    # Override: "gerar blueprint de pastas e endpoints" (estrutura de projeto) → sempre código
    if CODIGO_OVERRIDE_PATTERN.search(prompt_lower):
        try:
            add_log("info", f"[detect_module] override blueprint → codigo ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
        except Exception:
            pass
        return {"module": MODULE_CODIGO, "confidence": 0.95, "reason": "blueprint/pastas/endpoints = estrutura de projeto (codigo)"}

    # Cache
    cache_key = _module_cache_key(prompt, usuario)
    with _MODULE_CACHE_LOCK:
        now = time.time()
        if cache_key in _MODULE_CACHE:
            ts, m, c, r = _MODULE_CACHE[cache_key]
            if now - ts <= _MODULE_CACHE_TTL:
                try:
                    add_log("info", f"[detect_module] cache hit → {m} ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
                except Exception:
                    pass
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
        # LLM fallback
        try:
            add_log("info", "[detect_module] cache miss, chamando LLM (interpretação)", _LOG_SOURCE)
        except Exception:
            pass
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
        except Exception:
            result = {"module": MODULE_CODIGO, "confidence": 0.5, "reason": "LLM falhou, default código"}

    with _MODULE_CACHE_LOCK:
        _MODULE_CACHE[cache_key] = (time.time(), result["module"], result["confidence"], result["reason"])
    try:
        add_log("info", f"[detect_module] fim → {result.get('module')} ({time.perf_counter()-t0:.1f}s)", _LOG_SOURCE)
    except Exception:
        pass
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


def detect_language(
    use_python: bool, 
    use_javascript: bool, 
    use_typescript: bool, 
    use_react: bool,
    use_vue: bool = False,
    use_angular: bool = False,
) -> Dict[str, Any]:
    """
    Detecta a linguagem e framework baseado nas flags.
    Retorna {language, framework}.
    """
    if use_python and not use_javascript:
        return {"language": "python", "framework": None}
    elif use_javascript:
        framework_parts = []
        if use_typescript:
            framework_parts.append("typescript")
        if use_react:
            framework_parts.append("react")
        if use_vue:
            framework_parts.append("vue")
        if use_angular:
            framework_parts.append("angular")
        
        if framework_parts:
            framework = "+".join(framework_parts)
        else:
            framework = "vanilla"
        
        return {"language": "javascript", "framework": framework}
    else:
        # Default: JavaScript vanilla se nenhuma flag estiver marcada
        return {"language": "javascript", "framework": "vanilla"}


def route_to_module_js(
    prompt: str,
    root_path: str | None,
    usuario: str | None,
    use_python: bool = False,
    use_javascript: bool = False,
    use_typescript: bool = False,
    use_react: bool = False,
    use_vue: bool = False,
    use_angular: bool = False,
    force_execute: bool = False,
    force_module: str | None = None,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """
    Ponto central JavaScript: detecta módulo e linguagem, delega ao handler específico.
    Retorna decisão completa (module, intent, target_endpoint, language, framework, etc.).
    """
    module_detection = detect_module(prompt, usuario, force_module)
    module = module_detection["module"]
    
    language_info = detect_language(use_python, use_javascript, use_typescript, use_react, use_vue, use_angular)
    language = language_info["language"]
    framework = language_info["framework"]

    # Para JavaScript, sempre usa o módulo código (desenvolvimento de software)
    if module == MODULE_INFRA:
        # Infraestrutura pode usar qualquer linguagem, mas mantém o módulo
        from app.PulsoCSA.Python.services.comprehension_services.comprehension_infra import route_decision_infra
        result = route_decision_infra(prompt, root_path, usuario, force_execute, history)
        result["language"] = language
        result["framework"] = framework
        return result
    elif module == MODULE_ID:
        # Inteligência de dados pode usar qualquer linguagem, mas mantém o módulo
        from app.PulsoCSA.Python.services.comprehension_services.comprehension_id import route_decision_id
        result = route_decision_id(prompt, root_path, usuario, force_execute, history)
        result["language"] = language
        result["framework"] = framework
        return result
    else:
        # Módulo código: usa serviços JavaScript específicos
        from app.PulsoCSA.JavaScript.services.comprehension_services.comprehension_codigo_js import route_decision_codigo_js
        return route_decision_codigo_js(
            prompt, 
            root_path, 
            usuario, 
            language,
            framework,
            force_execute, 
            history
        )
