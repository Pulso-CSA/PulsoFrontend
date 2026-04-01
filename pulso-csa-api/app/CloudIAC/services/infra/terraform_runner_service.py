#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Terraform Runner – allowlist + workdir isolado❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os
import subprocess
from pathlib import Path
from typing import Optional

from app.utils.log_sanitizer import sanitizar_log

# Allowlist de comandos Terraform permitidos
ALLOWED_TERRAFORM_COMMANDS = ["init", "fmt", "validate", "plan", "apply"]
TERRAFORM_TIMEOUT_SEC = int(os.getenv("INFRA_TERRAFORM_TIMEOUT_SEC", "360"))


def run_terraform(
    workdir: str,
    command: str,
    extra_args: Optional[list[str]] = None,
    auto_approve: bool = False,
) -> tuple[int, str, str]:
    """
    Executa comando terraform no workdir.
    Retorna (returncode, stdout, stderr).
    stdout/stderr sanitizados (sem secrets).
    """
    cmd = command.strip().lower()
    if cmd not in ALLOWED_TERRAFORM_COMMANDS:
        return -1, "", f"Comando '{command}' não permitido. Allowlist: {ALLOWED_TERRAFORM_COMMANDS}"

    workdir_resolved = str(Path(workdir).resolve())
    if not os.path.isdir(workdir_resolved):
        return -1, "", f"Workdir inválido: {workdir_resolved}"

    args = ["terraform", cmd]
    if extra_args:
        args.extend(extra_args)
    if cmd == "apply" and auto_approve:
        args.append("-auto-approve")

    try:
        result = subprocess.run(
            args,
            cwd=workdir_resolved,
            capture_output=True,
            text=True,
            timeout=TERRAFORM_TIMEOUT_SEC,
            env={**os.environ},
        )
        out = sanitizar_log(result.stdout or "")
        err = sanitizar_log(result.stderr or "")
        return result.returncode, out, err
    except subprocess.TimeoutExpired:
        return -1, "", f"Timeout após {TERRAFORM_TIMEOUT_SEC}s"
    except subprocess.SubprocessError as e:
        return -1, "", sanitizar_log(str(e))
    except Exception as e:
        return -1, "", sanitizar_log(str(e))
