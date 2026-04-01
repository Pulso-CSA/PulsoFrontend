#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço de Deploy Docker❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from utils.docker_utils import run_docker_command, check_compose_file
from utils.log_manager import add_log
from models.deploy_models.deploy_models import DeployResponse
import time
import os


def start_compose(project_path: str, root_path: str | None = None) -> DeployResponse:
    """Inicia os containers via docker-compose."""
    target_path = root_path or project_path

    if not check_compose_file(target_path):
        add_log("error", f"Arquivo docker-compose.yml não encontrado em {target_path}.", "docker")
        return DeployResponse(message="❌ docker-compose.yml não encontrado!", success=False)

    add_log("info", f"Iniciando containers no caminho: {target_path}", "docker")
    logs = [f"🚀 Subindo containers com docker-compose up -d em {target_path}..."]
    logs += run_docker_command("docker-compose up -d", target_path)
    logs.append("✅ Containers iniciados com sucesso.")
    add_log("info", "Containers iniciados.", "docker")
    return DeployResponse(message="Containers iniciados.", logs=logs)


def rebuild_compose(project_path: str, root_path: str | None = None) -> DeployResponse:
    """Recria todos os containers."""
    target_path = root_path or project_path

    if not check_compose_file(target_path):
        add_log("error", f"Arquivo docker-compose.yml não encontrado em {target_path}.", "docker")
        return DeployResponse(message="❌ docker-compose.yml não encontrado!", success=False)

    add_log("warning", f"Recriando containers no caminho: {target_path}", "docker")
    logs = [
        "🛑 Encerrando containers existentes...",
        *run_docker_command("docker-compose down", target_path),
        "🧹 Limpando imagens antigas...",
        *run_docker_command("docker system prune -af --volumes", target_path),
        "🏗️  Reconstruindo containers...",
        *run_docker_command("docker-compose up --build -d", target_path),
        f"✅ Rebuild finalizado às {time.strftime('%H:%M:%S')}."
    ]
    add_log("info", "Containers reconstruídos com sucesso.", "docker")
    return DeployResponse(message="Rebuild concluído.", logs=logs)


def stop_compose(project_path: str, root_path: str | None = None) -> DeployResponse:
    """Desliga os containers via docker-compose down."""
    target_path = root_path or project_path

    if not check_compose_file(target_path):
        add_log("error", f"Arquivo docker-compose.yml não encontrado em {target_path}.", "docker")
        return DeployResponse(message="❌ docker-compose.yml não encontrado!", success=False)

    add_log("info", f"Desligando containers no caminho: {target_path}", "docker")
    logs = ["🛑 Encerrando containers...", *run_docker_command("docker-compose down", target_path)]
    logs.append("✅ Containers desligados.")
    add_log("info", "Containers desligados.", "docker")
    return DeployResponse(message="Containers desligados.", logs=logs)
