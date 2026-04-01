# Test runner para projetos JavaScript/TypeScript
import os
import subprocess
import sys

# Windows: evita abrir janela de terminal
_SUBPROCESS_FLAGS = {"creationflags": 0x08000000} if sys.platform == "win32" else {}


def run_automated_test_js(root_path: str, log_type: str = "info"):
    if not root_path or not os.path.isdir(root_path):
        return {"success": False, "message": "Diretório inválido", "method_used": None, "logs": []}
    pkg = os.path.join(root_path, "package.json")
    if not os.path.isfile(pkg):
        return {"success": True, "message": "Sem package.json - skip", "method_used": "skip", "logs": []}
    try:
        r = subprocess.run(
            ["npm", "test"],
            cwd=root_path,
            capture_output=True,
            text=True,
            timeout=120,
            **_SUBPROCESS_FLAGS,
        )
        logs = (r.stdout or "").splitlines() + (r.stderr or "").splitlines()
        return {"success": r.returncode == 0, "message": "npm test concluído", "method_used": "npm", "logs": logs}
    except Exception as e:
        return {"success": False, "message": str(e), "method_used": "npm", "logs": []}
