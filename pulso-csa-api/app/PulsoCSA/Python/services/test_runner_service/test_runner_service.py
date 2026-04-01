#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço de Teste Automatizado (Venv + Docker)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
from typing import List

from utils.log_manager import add_log
from utils.docker_utils import check_compose_file, run_docker_command
from utils.venv_utils import run_cmd, venv_exists
from models.test_models.test_models import TestRunResponse
from services.deploy.deploy_service import start_compose
from services.venv_service.venv_service import create_venv


#━━━━━━━━━❮Helpers❯━━━━━━━━━

def _venv_python_path(project_path: str) -> str:
    """Retorna o caminho do interpretador Python do venv (Windows ou Linux)."""
    subdir = "Scripts" if os.name == "nt" else "bin"
    base = os.path.join(project_path, "venv", subdir, "python")
    # Windows cria python.exe; Linux/Mac usa python sem extensão.
    if os.name == "nt" and not os.path.isfile(base) and os.path.isfile(base + ".exe"):
        return base + ".exe"
    return base


def _run_test_via_docker(project_path: str, log_type: str) -> TestRunResponse:
    """
    Sobe os containers e verifica se estão rodando (teste básico).
    Não faz rebuild para ser rápido; apenas start + ps.
    """
    add_log(log_type, f"[test_runner] Tentando teste via Docker em {project_path}", "test_runner")
    if not check_compose_file(project_path):
        return TestRunResponse(
            success=False,
            message="docker-compose.yml não encontrado.",
            method_used=None,
            logs=[],
        )
    response = start_compose(project_path, project_path)
    logs: List[str] = list(response.logs or [])
    if not response.success:
        return TestRunResponse(
            success=False,
            message=response.message,
            method_used="docker",
            logs=logs,
            details=response.message,
        )
    # Verifica se há containers em execução
    ps_logs = run_docker_command("docker-compose ps -q", project_path)
    logs.extend(ps_logs)
    has_containers = any(line.strip() for line in ps_logs if line.strip() and not line.strip().startswith("[ERROR]"))
    if not has_containers:
        return TestRunResponse(
            success=False,
            message="Containers não estão rodando após start.",
            method_used="docker",
            logs=logs,
            details="docker-compose ps -q não retornou IDs.",
        )
    return TestRunResponse(
        success=True,
        message="Teste via Docker concluído: containers em execução.",
        method_used="docker",
        logs=logs,
    )


def _run_test_via_venv(project_path: str, log_type: str) -> TestRunResponse:
    """
    Garante venv existente, instala deps se houver requirements.txt,
    e executa um check (import sys; sys.exit(0)) como teste básico.
    """
    add_log(log_type, f"[test_runner] Tentando teste via Venv em {project_path}", "test_runner")
    logs: List[str] = []
    if not venv_exists(project_path):
        create_resp = create_venv(log_type, project_path)
        if create_resp.status == "error":
            return TestRunResponse(
                success=False,
                message=create_resp.message,
                method_used="venv",
                logs=logs,
                details=create_resp.details,
            )
        logs.append(create_resp.message)
        if create_resp.details:
            logs.append(create_resp.details)
    python_bin = _venv_python_path(project_path)
    # Normalizar path e checar .exe no Windows (venv cria python.exe).
    if not os.path.isfile(python_bin) and os.name == "nt" and os.path.isfile(python_bin + ".exe"):
        python_bin = python_bin + ".exe"
    if not os.path.isfile(python_bin):
        return TestRunResponse(
            success=False,
            message="Venv não encontrado após criação.",
            method_used="venv",
            logs=logs,
            details=f"Esperado: {python_bin}",
        )
    # Teste: executar Python e sair com 0
    cmd = f'"{python_bin}" -c "import sys; print(\"ok\"); sys.exit(0)"'
    out, err, code = run_cmd(log_type, cmd, cwd=project_path)
    logs.append(out or "(stdout vazio)")
    if err:
        logs.append(f"stderr: {err}")
    if code != 0:
        return TestRunResponse(
            success=False,
            message="Execução no venv falhou.",
            method_used="venv",
            logs=logs,
            details=err or out,
        )
    return TestRunResponse(
        success=True,
        message="Teste via Venv concluído: execução ok.",
        method_used="venv",
        logs=logs,
        details=(out or "").strip(),
    )


#━━━━━━━━━❮API Pública❯━━━━━━━━━

def run_automated_test(
    root_path: str,
    log_type: str = "info",
    prefer_docker: bool = True,
) -> TestRunResponse:
    """
    Executa teste automatizado no projeto em root_path.
    - Se prefer_docker e existir docker-compose.yml: sobe containers e valida (Docker).
    - Caso contrário (ou se Docker falhar): usa venv (cria se necessário, instala deps, roda check).

    Usado pela rota POST /test/run e como último passo do workflow de correção.
    """
    add_log(log_type, f"[test_runner] Iniciando teste automatizado em {root_path}", "test_runner")
    if prefer_docker and check_compose_file(root_path):
        result = _run_test_via_docker(root_path, log_type)
        if result.success:
            return result
        add_log(log_type, f"[test_runner] Docker falhou, tentando venv: {result.message}", "test_runner")
    # Venv: se tem requirements.txt ou venv já existe
    has_venv = venv_exists(root_path)
    has_req = os.path.isfile(os.path.join(root_path, "requirements.txt"))
    if has_venv or has_req:
        return _run_test_via_venv(root_path, log_type)
    # Nenhum método disponível
    return TestRunResponse(
        success=False,
        message="Nenhum método de teste disponível (sem docker-compose.yml e sem requirements.txt/venv).",
        method_used=None,
        logs=[],
        details=None,
    )
