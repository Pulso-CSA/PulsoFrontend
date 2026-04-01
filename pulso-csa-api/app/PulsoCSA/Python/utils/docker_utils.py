#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Funções Utilitárias Docker❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import subprocess
import os
from typing import List


def run_docker_command(command: str, project_path: str) -> List[str]:
    """Executa um comando Docker e retorna os logs da execução."""
    logs = []
    try:
        process = subprocess.Popen(
            command,
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding="utf-8",
            errors="replace"
        )

        for line in process.stdout:
            clean_line = line.strip()
            if clean_line:
                logs.append(clean_line)

        process.wait()
        if process.returncode != 0:
            logs.append(f"[ERROR] Command failed with code {process.returncode}")
    except Exception as e:
        logs.append(f"[EXCEPTION] {str(e)}")

    return logs


def check_compose_file(project_path: str) -> bool:
    """Verifica se existe o arquivo docker-compose.yml no caminho informado."""
    return os.path.exists(os.path.join(project_path, "docker-compose.yml"))
