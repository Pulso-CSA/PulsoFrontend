#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Iniciar Preview (npm run dev / streamlit run)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from utils.log_manager import add_log

# Evita colisão com o frontend principal, que costuma usar 3000.
PREVIEW_PORT_JS = int(os.getenv("PREVIEW_FRONTEND_PORT", "3100"))
PREVIEW_PORT_STREAMLIT = int(os.getenv("PREVIEW_STREAMLIT_PORT", "8501"))
SOURCE = "preview"


def _find_available_port(start_port: int, host: str = "127.0.0.1", max_tries: int = 50) -> Optional[int]:
    """
    Encontra uma porta TCP livre a partir de `start_port`.
    Evita conflito quando a porta padrão (ex.: 3000) já está ocupada pelo app principal.
    """
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    return None


def _wait_for_port(host: str, port: int, timeout_seconds: float = 20.0) -> bool:
    """
    Aguarda o servidor abrir a porta.
    Evita retornar sucesso quando o processo morre logo após o spawn.
    """
    end_time = time.time() + timeout_seconds
    while time.time() < end_time:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.35)
    return False


def _resolve_project_path(root_path: str) -> Tuple[Optional[Path], Optional[str]]:
    """
    Resolve o caminho efetivo do projeto.
    Se a raiz não tem package.json/app.py, busca em REQ-*/generated_code (projetos gerados pelo PulsoCSA).
    Retorna (path_efetivo, tipo) ou (None, None).
    """
    root = Path(root_path)
    if not root.is_dir():
        return None, None
    # JavaScript: package.json na raiz
    if (root / "package.json").is_file():
        return root, "javascript"
    # Python: FrontendEX ou app.py + streamlit
    frontendex_app = root / "FrontendEX" / "app.py"
    if frontendex_app.is_file():
        return root, "python"
    app_py = root / "app.py"
    req_txt = root / "requirements.txt"
    if app_py.is_file() and req_txt.is_file():
        try:
            if "streamlit" in req_txt.read_text(encoding="utf-8", errors="ignore").lower():
                return root, "python"
        except Exception:
            pass
    # Fallback: buscar em subpastas REQ-*/generated_code (projetos JS gerados pelo workflow)
    try:
        req_dirs = sorted(
            [d for d in root.iterdir() if d.is_dir() and d.name.startswith("REQ-")],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        for req_dir in req_dirs:
            gen = req_dir / "generated_code"
            if gen.is_dir() and (gen / "package.json").is_file():
                return gen, "javascript"
    except (OSError, PermissionError):
        pass
    return None, None


def _detect_project_type(root_path: str) -> Optional[str]:
    """
    Detecta o tipo do projeto: 'javascript' (package.json) ou 'python' (FrontendEX/app.py ou streamlit).
    Considera subpastas REQ-*/generated_code quando a raiz não tem projeto.
    """
    _, project_type = _resolve_project_path(root_path)
    return project_type


def _run_background(cmd: str, cwd: str, log_prefix: str = "") -> Tuple[bool, str]:
    """
    Inicia processo em background (detachado). Retorna (sucesso, mensagem).
    """
    try:
        kwargs = {
            "cwd": cwd,
            "shell": True,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "stdin": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            CREATE_NO_WINDOW = 0x08000000
            kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS
                | CREATE_NO_WINDOW
            )
        else:
            kwargs["start_new_session"] = True
        proc = subprocess.Popen(cmd, **kwargs)
        add_log("info", f"{log_prefix} Processo iniciado em background (PID={proc.pid})", SOURCE)
        return True, f"Processo iniciado (PID={proc.pid})"
    except Exception as e:
        add_log("error", f"{log_prefix} Erro ao iniciar: {e}", SOURCE)
        return False, str(e)


def _run_sync(cmd: str, cwd: str, timeout: int = 120) -> Tuple[int, str, str]:
    """Executa comando de forma síncrona. Retorna (exit_code, stdout, stderr)."""
    kwargs = {
        "cwd": cwd,
        "shell": True,
        "capture_output": True,
        "text": True,
        "timeout": timeout,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        result = subprocess.run(cmd, **kwargs)
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout ao executar comando"
    except Exception as e:
        return -1, "", str(e)


def start_preview_javascript(root_path: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Para projeto JS/React/Vue: npm install (sync) + autocorrect (evita erros) + npm run dev (background).
    Retorna (success, message, preview_url, details).
    """
    root = Path(root_path)
    package_json = root / "package.json"
    if not package_json.is_file():
        return False, "package.json não encontrado.", None, None
    # npm install (pode demorar)
    add_log("info", f"[preview] Executando npm install em {root_path}", SOURCE)
    code, out, err = _run_sync("npm install", str(root), timeout=180)
    if code != 0:
        details = (out + "\n" + err).strip()[:500]
        return False, "npm install falhou.", None, details
    # Auto-correção antes do dev (como no workflow de criação): evita erros de imports/deps
    try:
        from app.PulsoCSA.JavaScript.services.autocorrect_creator_service_js import run_autocorrect_creator_js
        workflow_log: list = []
        run_autocorrect_creator_js(root_path, "", workflow_log, "javascript", "react")
    except Exception as e:
        add_log("info", f"[preview] Auto-correção skip: {e}", SOURCE)
    # Seleciona porta livre para evitar colisão com o frontend principal do Pulso.
    preview_port = _find_available_port(PREVIEW_PORT_JS)
    if preview_port is None:
        return False, "Nenhuma porta livre disponível para o preview JavaScript.", None, None
    add_log("info", f"[preview] Porta selecionada para JS: {preview_port}", SOURCE)

    # npm run dev em background
    add_log("info", f"[preview] Iniciando npm run dev em {root_path}", SOURCE)
    ok, msg = _run_background(
        f"npm run dev -- --host 127.0.0.1 --port {preview_port} --strictPort",
        str(root),
        "[preview] ",
    )
    if not ok:
        return False, f"Falha ao iniciar npm run dev: {msg}", None, msg
    if not _wait_for_port("127.0.0.1", preview_port, timeout_seconds=20):
        return (
            False,
            "npm run dev não ficou disponível na porta esperada. Verifique logs e dependências do projeto gerado.",
            None,
            f"Porta {preview_port} não respondeu a tempo.",
        )
    url = f"http://127.0.0.1:{preview_port}"
    return True, "Servidor de desenvolvimento iniciado. O preview estará disponível em breve.", url, None


def start_preview_python(root_path: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Para projeto Python/Streamlit: streamlit run (background).
    Procura FrontendEX/app.py ou app.py na raiz.
    Retorna (success, message, preview_url, details).
    """
    root = Path(root_path)
    streamlit_script = None
    cwd = str(root)
    # Prioridade: FrontendEX/app.py (tela teste) — rodar de dentro de FrontendEX
    frontendex_app = root / "FrontendEX" / "app.py"
    if frontendex_app.is_file():
        streamlit_script = "app.py"
        cwd = str(root / "FrontendEX")
    else:
        app_py = root / "app.py"
        if app_py.is_file():
            streamlit_script = str(app_py)
    preview_port = _find_available_port(PREVIEW_PORT_STREAMLIT)
    if preview_port is None:
        return False, "Nenhuma porta livre disponível para o preview Streamlit.", None, None
    add_log("info", f"[preview] Porta selecionada para Streamlit: {preview_port}", SOURCE)

    if not streamlit_script:
        return False, "Nenhum app Streamlit encontrado (FrontendEX/app.py ou app.py).", None, None
    cmd = f'streamlit run "{streamlit_script}" --server.port {preview_port} --server.address 127.0.0.1 --server.headless true'
    add_log("info", f"[preview] Iniciando streamlit em {streamlit_script}", SOURCE)
    ok, msg = _run_background(cmd, cwd, "[preview] ")
    if not ok:
        return False, f"Falha ao iniciar Streamlit: {msg}", None, msg
    if not _wait_for_port("127.0.0.1", preview_port, timeout_seconds=20):
        return (
            False,
            "Streamlit não ficou disponível na porta esperada. Verifique logs e dependências do projeto gerado.",
            None,
            f"Porta {preview_port} não respondeu a tempo.",
        )
    url = f"http://127.0.0.1:{preview_port}"
    return True, "Streamlit iniciado. O preview estará disponível em breve.", url, None


def start_preview(root_path: str, project_type: str = "auto") -> dict:
    """
    Inicia o servidor de preview conforme o tipo do projeto.
    project_type: 'javascript', 'python' ou 'auto'.
    Busca em REQ-*/generated_code quando a raiz não tem package.json.
    Retorna dict com success, preview_url, message, project_type, details.
    """
    if not root_path or not os.path.isdir(root_path):
        return {
            "success": False,
            "preview_url": None,
            "message": "root_path inválido ou diretório não encontrado.",
            "project_type": None,
            "details": None,
            "preview_auto_open": False,
        }
    resolved_path, detected = _resolve_project_path(root_path)
    effective_type = project_type.lower() if project_type and project_type != "auto" else (detected or "")
    if not effective_type and detected:
        effective_type = detected
    if not effective_type or not resolved_path:
        return {
            "success": False,
            "preview_url": None,
            "message": "Tipo do projeto não detectado. Informe 'javascript' ou 'python' ou verifique se o projeto tem package.json (JS) ou FrontendEX/app.py / app.py com streamlit (Python).",
            "project_type": None,
            "details": None,
            "preview_auto_open": False,
        }
    effective_root = str(resolved_path)
    if effective_root != root_path:
        add_log("info", f"[preview] Projeto detectado em subpasta: {effective_root}", SOURCE)
    if effective_type == "javascript":
        ok, msg, url, details = start_preview_javascript(effective_root)
    elif effective_type == "python":
        ok, msg, url, details = start_preview_python(effective_root)
    else:
        return {
            "success": False,
            "preview_url": None,
            "message": f"Tipo '{effective_type}' não suportado. Use 'javascript' ou 'python'.",
            "project_type": effective_type,
            "details": None,
            "preview_auto_open": False,
        }
    return {
        "success": ok,
        "preview_url": url,
        "message": msg,
        "project_type": effective_type,
        "details": details,
        "preview_auto_open": False,
    }
