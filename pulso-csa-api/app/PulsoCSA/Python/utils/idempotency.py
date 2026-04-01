#━━━━━━━━━❮Idempotência❯━━━━━━━━━
# Geração de run_id e validação de idempotency keys para pipelines/workflows.
import hashlib
import time
import uuid
from typing import Optional, Dict, Any
from collections import defaultdict

# Cache simples de idempotency keys (em produção usar Redis)
_IDEMPOTENCY_CACHE: Dict[str, Dict[str, Any]] = {}
_IDEMPOTENCY_MAX_AGE_SECONDS = 3600  # 1 hora


def gerar_run_id(prefix: str = "run") -> str:
    """Gera um run_id único para rastreabilidade de execuções."""
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def gerar_correlation_id(id_requisicao: str, etapa: Optional[str] = None) -> str:
    """Gera um correlation_id para rastreabilidade entre etapas."""
    base = f"{id_requisicao}_{etapa or 'main'}"
    return hashlib.sha256(base.encode()).hexdigest()[:16]


def verificar_idempotency_key(key: str) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Verifica se uma idempotency key já foi usada.
    Retorna (is_new, cached_response).
    """
    if not key:
        return True, None
    cached = _IDEMPOTENCY_CACHE.get(key)
    if cached:
        age = time.time() - cached.get("timestamp", 0)
        if age < _IDEMPOTENCY_MAX_AGE_SECONDS:
            return False, cached.get("response")
        else:
            del _IDEMPOTENCY_CACHE[key]
    return True, None


def registrar_idempotency_key(key: str, response: Dict[str, Any]):
    """Registra uma idempotency key com sua resposta."""
    if key:
        _IDEMPOTENCY_CACHE[key] = {
            "timestamp": time.time(),
            "response": response,
        }
        # Limpar entradas antigas periodicamente
        if len(_IDEMPOTENCY_CACHE) > 1000:
            now = time.time()
            _IDEMPOTENCY_CACHE.clear()  # Simplificado: em produção usar TTL
