#━━━━━━━━━❮Sanitização de Logs❯━━━━━━━━━
# Remove secrets, tokens e informações sensíveis dos logs.
import re
from typing import Any, Dict, List

# Padrões de secrets comuns
SECRET_PATTERNS = [
    r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(token|secret|auth[_-]?token)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(bearer)\s+([a-zA-Z0-9\-_\.]+)",
    r"(?i)(jwt)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(access[_-]?token)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(refresh[_-]?token)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(private[_-]?key)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(secret[_-]?key)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    # FinOps: credenciais cloud
    r"(?i)(access[_-]?key[_-]?id|aws_access_key)\s*[:=]\s*['\"]?([A-Z0-9]{20})['\"]?",
    r"(?i)(secret[_-]?access[_-]?key|aws_secret_key)\s*[:=]\s*['\"]?([^'\"]{40})['\"]?",
    r"(?i)(client[_-]?secret)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
    r"(?i)(service[_-]?account[_-]?json|private_key)\s*[:=]\s*['\"]?([^'\"]+)['\"]?",
]


def sanitizar_log(texto: str) -> str:
    """
    Remove secrets e tokens de strings de log.
    Substitui por '[REDACTED]'.
    """
    if not texto:
        return texto
    resultado = texto
    for pattern in SECRET_PATTERNS:
        resultado = re.sub(pattern, r'\1=[REDACTED]', resultado)
    return resultado


def sanitizar_dict(d: Dict[str, Any], campos_sensiveis: List[str] = None) -> Dict[str, Any]:
    """
    Remove campos sensíveis de um dict.
    campos_sensiveis: lista de chaves a remover/sanitizar.
    """
    if campos_sensiveis is None:
        campos_sensiveis = ["password", "token", "api_key", "secret", "authorization"]
    resultado = {}
    for k, v in d.items():
        if k.lower() in [c.lower() for c in campos_sensiveis]:
            resultado[k] = "[REDACTED]"
        elif isinstance(v, dict):
            resultado[k] = sanitizar_dict(v, campos_sensiveis)
        elif isinstance(v, str):
            resultado[k] = sanitizar_log(v)
        else:
            resultado[k] = v
    return resultado
