#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import json
from datetime import datetime
from pathlib import Path

# 🔎 Import opcional do Mongo para recuperar root_path se não vier por parâmetro/ambiente
# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection
except ImportError:
    try:
        from app.storage.database.database_core import get_collection
    except Exception:
        get_collection = None
except Exception:
    get_collection = None

try:
    from utils.path_validation import get_app_package_dir
except ImportError:
    def get_app_package_dir() -> str:
        return str(Path(__file__).resolve().parents[2])

  
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função de Salvar Relatório❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def save_agent_report(id_requisicao: str, step_name: str, data: dict, root_path: str = None):
    """
    Salva o relatório JSON em <root_path>/reports/<id_requisicao>/<step_name>.json.
    root_path deve ser passado explicitamente pelo fluxo (multi-usuário seguro).
    Se root_path não for informado: tenta Mongo (C1) por id_requisicao; fallback app/reports/.
    Não use PULSOCSA_ROOT_PATH em ambiente concorrente (foi removido do fluxo).
    """

    app_package_dir = get_app_package_dir()

    try:
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        #━━━━━━━━━❮Definição do Caminho Base❯━━━━━━━━━
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

        # ✅ 1) Parâmetro → 2) Mongo (Camada 1) por id_requisicao → fallback sob api/app/reports/
        # Não usar PULSOCSA_ROOT_PATH (multi-usuário: env é compartilhado).
        resolved_root = (str(root_path).strip() if root_path is not None else "") or None

        # 🔄 Tentativa de recuperar do Mongo se ainda não tivermos root_path
        if not resolved_root and get_collection is not None:
            try:
                coll = get_collection()
                # root_path na raiz (database_c1) + input.root_path
                doc = coll.find_one(
                    {"id_requisicao": id_requisicao},
                    {"input.root_path": 1, "root_path": 1}
                )
                mongo_root = None
                if doc:
                    top_s = str(doc.get("root_path") or "").strip()
                    inp_s = ""
                    if isinstance(doc.get("input"), dict):
                        inp_s = str((doc["input"].get("root_path") or "")).strip()
                    merged = top_s or inp_s
                    mongo_root = merged or None

                if mongo_root:
                    resolved_root = mongo_root
            except Exception as e_mongo:
                pass

        # 🧭 Base final — sempre gravar sob <root>/reports/<id>/ (igual structure_creator / code_creator)
        if resolved_root:
            base_dir = os.path.normpath(os.path.abspath(resolved_root))
        else:
            base_dir = app_package_dir

        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        #━━━━━━━━━❮Criação dos Diretórios❯━━━━━━━━━
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        reports_dir = os.path.join(base_dir, "reports", id_requisicao)
        os.makedirs(reports_dir, exist_ok=True)

        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        #━━━━━━━━━❮Criação do Arquivo JSON❯━━━━━━━━━
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        path = os.path.join(reports_dir, f"{step_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return path

    except Exception as e:
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        #━━━━━━━━━❮Tratamento de Erros❯━━━━━━━━━
        #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
        logs_dir = os.path.join(app_package_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        error_log = os.path.join(logs_dir, "report_error.log")

        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] Erro ao salvar {step_name} ({id_requisicao}): {e}\n")

        return None
