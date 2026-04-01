#━━━━━━━━━❮Allowlist de Comandos Venv❯━━━━━━━━━
# Lista de comandos permitidos para execução no venv (evita RCE).
import re
from typing import List, Optional

# Comandos permitidos (whitelist)
ALLOWED_VENV_COMMANDS = [
    r"^pip\s+(install|uninstall|list|show|freeze|check|search)\s+",
    r"^python\s+-m\s+(pytest|unittest|pip|pipenv|venv|virtualenv)\s+",
    r"^python\s+-m\s+pytest\s+",
    r"^python\s+.*\.py$",  # Executar scripts Python
    r"^python\s+-c\s+",  # Comandos Python inline (limitado)
    r"^pipenv\s+(install|uninstall|lock|sync|run)\s+",
    r"^npm\s+(install|run|test|build)\s+",  # Se projeto usar Node
    r"^npm\s+run\s+",
    r"^yarn\s+(install|test|build)\s+",
]

# Padrões proibidos (blacklist adicional)
FORBIDDEN_PATTERNS = [
    r"rm\s+-rf",
    r"del\s+/[sf]",
    r"format\s+[cd]:",
    r"shutdown",
    r"reboot",
    r"sudo\s+",
    r"su\s+",
    r"chmod\s+777",
    r"chown\s+",
    r">\s*/dev/",
    r"curl\s+.*\s+\|",
    r"wget\s+.*\s+\|",
    r"nc\s+",
    r"netcat\s+",
    r"python\s+-c\s+.*(__import__|eval|exec|compile)",
]


def validar_comando_venv(comando: str) -> tuple[bool, Optional[str]]:
    """
    Valida se comando é permitido na execução do venv.
    Retorna (is_valid, error_message).
    """
    if not comando or not comando.strip():
        return False, "Comando vazio"
    comando = comando.strip()
    # Verificar blacklist primeiro
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, comando, re.IGNORECASE):
            return False, f"Comando proibido detectado: {pattern}"
    # Verificar whitelist
    for pattern in ALLOWED_VENV_COMMANDS:
        if re.match(pattern, comando, re.IGNORECASE):
            return True, None
    # Se não match em nenhum padrão permitido, negar
    return False, f"Comando '{comando[:50]}' não está na allowlist de comandos permitidos"


def is_comando_permitido(comando: str) -> bool:
    """Wrapper simples: retorna True se comando é permitido."""
    is_valid, _ = validar_comando_venv(comando)
    return is_valid
