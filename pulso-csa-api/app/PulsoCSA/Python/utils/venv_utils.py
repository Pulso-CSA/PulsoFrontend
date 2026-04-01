#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Venv Utility Functions❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import shlex
import subprocess

from utils.log_manager import add_log
from utils.venv_allowlist import validar_comando_venv


def run_cmd(log, cmd: str, cwd: str = None, validate: bool = True):
    """
    Run system command and return output.
    Se validate=True, valida comando contra allowlist antes de executar.
    Usa shell=False para evitar RCE via injeção de comandos.
    """
    if validate:
        is_valid, error_msg = validar_comando_venv(cmd)
        if not is_valid:
            add_log(log, f"Comando bloqueado: {error_msg}", "venv")
            return "", f"Comando bloqueado por segurança: {error_msg}", 1
    add_log(log, f"Running command: {cmd}", "venv")
    try:
        # shell=False evita RCE; shlex.split preserva argumentos com espaços
        args = shlex.split(cmd, posix=(os.name != "nt"))
        process = subprocess.Popen(
            args,
            shell=False,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        return stdout.decode(), stderr.decode(), process.returncode
    except Exception as e:
        add_log(log, f"Erro ao executar comando: {e}", "venv")
        return "", str(e), 1


def venv_exists(path: str) -> bool:
    """Check if venv folder already exists."""
    return os.path.isdir(os.path.join(path, "venv"))
