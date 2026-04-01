#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
from datetime import datetime

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Constantes❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# 🔥 CORREÇÃO MINIMA: logs passam a ir para /tmp (permitido no Railway)
LOG_DIR = "/tmp/pulso_logs"
os.makedirs(LOG_DIR, exist_ok=True)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Funções❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _write_log(filename: str, message: str) -> None:
    path = os.path.join(LOG_DIR, filename)
    timestamp = datetime.utcnow().isoformat()
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_input(id_req: str, usuario: str) -> None:
    _write_log("input.log", f"[{id_req}] input recebido | usuario={usuario}")

def log_refine(id_req: str, versao: str) -> None:
    _write_log("refine.log", f"[{id_req}] refinamento criado | versao={versao}")

def log_validate(id_req: str, status: str) -> None:
    _write_log("validate.log", f"[{id_req}] validado | status={status}")

def log_workflow(id_req: str, status: str) -> None:
    _write_log("workflow.log", f"[{id_req}] workflow | status={status}")
