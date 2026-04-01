#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Venv Service❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from utils.log_manager import add_log
from utils.venv_utils import run_cmd, venv_exists
from models.venv_models.venv_models import VenvResponse
import os
import shutil


#━━━━━━━━━❮Create Venv (Executor)❯━━━━━━━━━
def create_venv(log, project_path: str) -> VenvResponse:
    """Create a Python virtual environment and install dependencies."""

    add_log(log, f"Starting venv creation in {project_path}", "venv")

    if venv_exists(project_path):
        return VenvResponse(
            status="warning",
            message="Venv already exists.",
            details="Use /venv/recreate to rebuild it."
        )

    cmd = "python -m venv venv"
    out, err, code = run_cmd(log, cmd, cwd=project_path)

    if code != 0:
        return VenvResponse(status="error", message="Failed to create venv.", details=err)

    req_file = os.path.join(project_path, "requirements.txt")

    if not os.path.isfile(req_file):
        return VenvResponse(
            status="success",
            message="Venv created, but requirements.txt not found.",
            details=None
        )

    subdir = "Scripts" if os.name == "nt" else "bin"
    venv_python = os.path.join(project_path, "venv", subdir, "python")
    if os.name == "nt" and not os.path.isfile(venv_python) and os.path.isfile(venv_python + ".exe"):
        venv_python = venv_python + ".exe"
    pip_cmd = f'"{venv_python}" -m pip install -r requirements.txt'
    out, err, code = run_cmd(log, pip_cmd, cwd=project_path)

    if code != 0:
        return VenvResponse(status="error", message="Venv created but requirements failed.", details=err)

    return VenvResponse(status="success", message="Venv created successfully.", details=out)


#━━━━━━━━━❮Recreate Venv (Executor)❯━━━━━━━━━
def recreate_venv(log, project_path: str) -> VenvResponse:
    """Delete and recreate the virtual environment."""

    add_log(log, f"Recreating venv in {project_path}", "venv")

    venv_path = os.path.join(project_path, "venv")

    if os.path.isdir(venv_path):
        shutil.rmtree(venv_path)

    return create_venv(log, project_path)


#━━━━━━━━━❮Execute Venv Check (Executor)❯━━━━━━━━━
def activate_venv(log, project_path: str) -> VenvResponse:
    """
    Executes code using the venv Python interpreter.
    This DOES NOT activate shell environment — it executes code directly.
    """

    add_log(log, "Executing venv python check.", "venv")

    python_bin = os.path.join(project_path, "venv", "Scripts", "python")

    if not os.path.isfile(python_bin):
        return VenvResponse(
            status="error",
            message="Venv not found.",
            details="Create the venv before executing."
        )

    cmd = f"{python_bin} --version"
    out, err, code = run_cmd(log, cmd, cwd=project_path)

    if code != 0:
        return VenvResponse(status="error", message="Failed to execute venv python.", details=err)

    return VenvResponse(
        status="success",
        message="Venv executor ran successfully.",
        details=out.strip()
    )


#━━━━━━━━━❮Deactivate (No-op Executor)❯━━━━━━━━━
def deactivate_venv(log, project_path: str) -> VenvResponse:
    """
    No-op executor.
    Venv deactivation has no meaning in persistent API processes.
    """

    add_log(log, "Venv deactivation requested (no-op).", "venv")

    return VenvResponse(
        status="success",
        message="Venv deactivation is a no-op in API context.",
        details=None
    )
