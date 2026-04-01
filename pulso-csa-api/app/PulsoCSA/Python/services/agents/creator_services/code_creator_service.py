#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Geração de Código (LLM + RAG)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

CODEGEN_MAX_RETRIES = int(os.getenv("CODEGEN_MAX_RETRIES", "4"))
CODEGEN_RETRY_DELAY_SEC = float(os.getenv("CODEGEN_RETRY_DELAY_SEC", "2"))
from langchain.prompts import PromptTemplate
from utils.logger import log_workflow
from utils.path_validation import is_path_under_base
from storage.database import database_c3 as db_c3
# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Localização dos Prompts❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from app.prompts.loader import load_prompt


#━━━━━━━━━❮Fallback quando LLM falha❯━━━━━━━━━
def _get_fallback_stub(filename: str, refined_prompt: str = "") -> str:
    """Fallback mínimo quando LLM falha — stub genérico, não assume API."""
    fn = filename.lower()
    prompt_lower = (refined_prompt or "").lower()
    use_flask = "flask" in prompt_lower
    if fn == "main.py":
        if use_flask:
            return '''"""Ponto de entrada da API Flask."""
from flask import Flask, jsonify
from routers.auth_router import auth_bp
from routers.calculator_router import calculator_bp

app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(calculator_bp, url_prefix="/calc")

@app.route("/")
def index():
    return jsonify({"Teste Pulso 1.0": "OK"})

if __name__ == "__main__":
    app.run(debug=True)
'''
        return '''"""Ponto de entrada da API."""
from fastapi import FastAPI
from routers.auth_router import router as auth_router
from routers.calculator_router import router as calculator_router

app = FastAPI()
app.include_router(auth_router, prefix="/auth")
app.include_router(calculator_router, prefix="/calc")

@app.get("/")
def index():
    return {"Teste Pulso 1.0": "OK"}
'''
    if fn == "settings.py":
        return '''"""Configurações da aplicação."""
import os

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
'''
    if fn == "user_model.py":
        return '''"""Modelo de usuário."""
from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str
'''
    if fn.endswith(".py"):
        return f'"""Módulo {filename}."""\n\n# TODO: implementar conforme contexto do projeto\n'
    if fn == "requirements.txt":
        return "python-dotenv>=1.0.0\n"
    if fn == "readme.md":
        return f"# {filename}\n\nProjeto gerado pelo Pulso.\n"
    if fn == ".env":
        return "DEBUG=false\n"
    if fn == "dockerfile":
        return "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"main.py\"]\n"
    if fn.endswith(".yml") or fn.endswith(".yaml"):
        return "services:\n  app:\n    build: .\n"
    return ""


#━━━━━━━━━❮Detecção de erro Ollama❯━━━━━━━━━
def _is_ollama_error(text: str) -> bool:
    """Retorna True se a resposta for mensagem de erro ou artefato inválido do Ollama."""
    if not text or not text.strip():
        return True
    t = text.strip()
    if t.startswith("Erro ao gerar texto com Ollama") or "ReadTimeout" in t or "timed out" in t.lower():
        return True
    if t in ("<|fim_middle|>", "🧠", "�") or t.startswith("<|") and "|>" in t and len(t) < 50:
        return True
    return False


#━━━━━━━━━❮Sanitização via módulo dedicado❯━━━━━━━━━
from utils.code_sanitizer import sanitize_generated_code


def _is_valid_for_file(content: str, filename: str) -> bool:
    """Verifica se o conteúdo é apropriado para o arquivo (genérico, não assume API)."""
    if not content or len(content.strip()) < 25:
        return False
    if "<|fim_middle|>" in content or "<|im_end|>" in content:
        return False
    fn = filename.lower()
    c = content.lower()
    if fn.endswith(".py"):
        return "import " in c or "from " in c or "def " in c or "class " in c
    if fn == "requirements.txt":
        return "\n" in c or len(c) > 10
    if fn == "readme.md":
        return len(c) > 20
    if fn in (".env", "dockerfile") or fn.endswith(".yml") or fn.endswith(".yaml"):
        return len(c) > 15
    return True


def _fix_placeholder_imports(text: str) -> str:
    """Remove ou comenta imports fictícios ('your_project.*', '2fa', etc.) mantendo o código válido."""
    if not text:
        return text
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("from your_project") or stripped.startswith("import your_project"):
            lines.append(f"# TODO: import removido: {stripped}")
            continue
        if ".2fa" in stripped or "2fa." in stripped:
            lines.append(f"# TODO: import inválido removido: {stripped}")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal do Serviço❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def generate_code_from_reports(root_path: str, id_requisicao: str):
    """
    Lê os relatórios da camada 2 e o manifesto da estrutura (C3.1),
    e gera os arquivos de código-fonte dentro da pasta 'generated_code',
    utilizando LLM + contexto RAG para geração inteligente.
    """
    try:
        reports_dir = os.path.join(root_path, "reports", id_requisicao)
        structure_manifest_path = os.path.join(root_path, id_requisicao, "generated_code", "structure_manifest.json")
        backend_report_path = os.path.join(reports_dir, "02_backend_report.json")
        security_report_path = os.path.join(reports_dir, "04_code_security_report.json")
        summary_path = os.path.join(reports_dir, "summary_pipeline.json")

        #━━━━━━━━━❮Validação de Arquivos❯━━━━━━━━━
        if not all(os.path.exists(p) for p in [structure_manifest_path, backend_report_path, security_report_path]):
            raise FileNotFoundError("Um ou mais relatórios da camada 2 não foram encontrados.")

        #━━━━━━━━━❮Carregamento de Dados❯━━━━━━━━━
        with open(structure_manifest_path, "r", encoding="utf-8") as f:
            structure_manifest = json.load(f)
        with open(backend_report_path, "r", encoding="utf-8") as f:
            backend_report = json.load(f)
        with open(security_report_path, "r", encoding="utf-8") as f:
            security_report = json.load(f)
        refined_prompt = ""
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary = json.load(f)
                refined_prompt = (summary.get("refined_prompt") or "").strip()[:800]
            except Exception:
                pass

        base_dir = structure_manifest.get("root_path") or os.path.join(
            root_path, id_requisicao, "generated_code"
        )
        base_dir_abs = os.path.abspath(base_dir)
        created_files = []
        use_ollama = os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes")

        client = get_openai_client()
        system_prompt = load_prompt("creation/system")

        tasks_llm = []
        for folder, files in structure_manifest.get("created", {}).items():
            folder_path = base_dir if folder in (".", "", None) else os.path.join(base_dir, folder)
            if not is_path_under_base(os.path.abspath(folder_path), base_dir_abs):
                continue
            for filename in files:
                if not isinstance(filename, str) or not filename or ".." in filename or filename.startswith("/"):
                    continue
                file_path = os.path.join(folder_path, filename)
                if not is_path_under_base(os.path.abspath(file_path), base_dir_abs):
                    continue
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                if filename == "__init__.py":
                    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                        f.write('"""Inicialização do pacote."""\n')
                    created_files.append(file_path)
                else:
                    tasks_llm.append((file_path, folder_path, filename, folder or "."))

        #━━━━━━━━━❮Geração paralela (apenas arquivos customizados)❯━━━━━━━━━
        max_workers = 2 if use_ollama else min(4, max(1, len(tasks_llm)))

        structure_str = json.dumps(structure_manifest.get("created", {}), ensure_ascii=False, indent=2)

        def _generate_one_file(args):
            file_path, folder_path, filename, folder_key = args
            folder = str(folder_key or ".").strip()
            if folder and folder != ".":
                if "routers" in folder.lower() or "routes" in folder.lower():
                    if "auth" in filename.lower():
                        file_context = "Arquivo auth_router — APENAS rotas POST /login e POST /create_account. Chame auth_service. Blueprint (Flask) ou APIRouter (FastAPI). NUNCA bhaskara/pitagoras aqui."
                    elif "calculator" in filename.lower():
                        file_context = "Arquivo calculator_router — APENAS rotas bhaskara, pitagoras, add, subtract, multiply, divide. Chame calculator_service. NUNCA login/create_account aqui."
                    else:
                        file_context = "Arquivo em routers/ — use APIRouter (FastAPI) ou Blueprint (Flask). Rotas com @router.get/post. NUNCA app aqui."
                elif "services" in folder.lower():
                    file_context = "Arquivo em services/ — GERE CÓDIGO com funções puras. auth_service: login(username,password), create_account. calculator_service: bhaskara(a,b,c), pitagoras(a,b), add, subtract, multiply, divide. Sem rotas."
                elif "models" in folder.lower():
                    file_context = "Arquivo em models/ — GERE CÓDIGO com classes Pydantic (BaseModel) ou SQLAlchemy. user_model.py: classe User com username, password. Sem rotas."
                elif "config" in folder.lower() or "settings" in filename.lower():
                    file_context = "Arquivo de configuração — GERE CÓDIGO com import os, os.getenv('DEBUG'), os.getenv('SECRET_KEY'). Variáveis DEBUG, SECRET_KEY. NUNCA apenas __init__ vazio."
                elif "tests" in folder.lower():
                    file_context = "Arquivo de teste — pytest, fixtures. Teste as funções dos services e rotas dos routers."
                elif "main" in filename.lower():
                    file_context = "Ponto de entrada — GERE CÓDIGO PYTHON COMPLETO. Comece com 'from flask import' ou 'from fastapi import'. Crie app, registre routers/blueprints. IMPORTS: from routers.xxx_router import router ou auth_bp. Rota GET / retorna JSON. NUNCA retorne instruções ou listas."
                else:
                    file_context = f"Arquivo em {folder}/."
            else:
                if "main" in filename.lower():
                    file_context = "Ponto de entrada — GERE CÓDIGO PYTHON COMPLETO. Comece com 'from flask import' ou 'from fastapi import'. Crie app, registre routers/blueprints. Rota GET / retorna JSON. NUNCA retorne instruções."
                else:
                    file_context = "Arquivo na raiz — main.py ou config. NUNCA misture rotas com lógica de negócio."
            if filename.lower() == "requirements.txt":
                file_context = "APENAS linhas de dependências (package==versão). NUNCA inclua código Python."
            # Contexto reduzido por arquivo para evitar overflow e confusão da LLM
            backend_str = json.dumps(backend_report, ensure_ascii=False, indent=2)
            if len(backend_str) > 2500:
                backend_str = backend_str[:2500] + "\n... (resumido)"
            security_str = json.dumps(security_report, ensure_ascii=False, indent=2)
            if len(security_str) > 800:
                security_str = security_str[:800] + "\n... (resumido)"

            prompt_template = PromptTemplate(
                template=load_prompt("creation/code_creation"),
                input_variables=["backend", "security", "filename", "structure", "file_context", "refined_prompt"]
            )
            code_prompt = prompt_template.format(
                backend=backend_str,
                security=security_str,
                filename=filename,
                structure=structure_str,
                file_context=file_context,
                refined_prompt=refined_prompt or "(use o contexto do backend e estrutura)",
            )
            # Reforço de framework — colocar NO INÍCIO do prompt para máxima prioridade
            if refined_prompt and "flask" in refined_prompt.lower():
                code_prompt = (
                    "[OBRIGATÓRIO: O usuário pediu FLASK. Use Flask, Blueprint, register_blueprint. "
                    "NUNCA use FastAPI, APIRouter, uvicorn, Depends, OAuth2PasswordBearer.]\n\n"
                    + code_prompt
                )
            elif refined_prompt and "fastapi" in refined_prompt.lower():
                code_prompt = (
                    "[OBRIGATÓRIO: O usuário pediu FastAPI. Use FastAPI, APIRouter, include_router, uvicorn.]\n\n"
                    + code_prompt
                )
            fn_lower = filename.lower()
            if fn_lower == "requirements.txt" or fn_lower == ".env":
                num_pred = 256
            elif fn_lower.startswith("test_"):
                num_pred = 768
            else:
                num_pred = 1536
            generated_code = ""
            for attempt in range(CODEGEN_MAX_RETRIES):
                try:
                    raw = client.generate_text(
                        code_prompt,
                        system_prompt=system_prompt,
                        use_fast_model=False,
                        num_predict=num_pred,
                    )
                    if not _is_ollama_error(raw) and raw and raw.strip():
                        generated_code = sanitize_generated_code(raw, filename)
                        generated_code = _fix_placeholder_imports(generated_code)
                        if generated_code.strip() and _is_valid_for_file(generated_code, filename):
                            break
                    if attempt < CODEGEN_MAX_RETRIES - 1:
                        time.sleep(CODEGEN_RETRY_DELAY_SEC * (attempt + 1))
                except Exception:
                    if attempt < CODEGEN_MAX_RETRIES - 1:
                        time.sleep(CODEGEN_RETRY_DELAY_SEC * (attempt + 1))
                    continue
            if not generated_code or not generated_code.strip() or not _is_valid_for_file(generated_code, filename):
                generated_code = _get_fallback_stub(filename, refined_prompt) or f'"""Arquivo {filename}."""\n'
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(generated_code + "\n")
            return (file_path, None)

        max_workers = min(max_workers, max(1, len(tasks_llm)))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_generate_one_file, t): t for t in tasks_llm}
            for fut in as_completed(futures):
                try:
                    fp, _ = fut.result()
                    created_files.append(fp)
                except Exception as file_err:
                    task = futures.get(fut)
                    file_info = f" (arquivo: {task[2]})" if task else ""
                    raise RuntimeError(f"Erro ao gerar {file_info}: {file_err}") from file_err

        #━━━━━━━━━❮Manifesto e Persistência❯━━━━━━━━━
        code_manifest = {
            "id_requisicao": id_requisicao,
            "root_path": base_dir,
            "files_written": created_files,
            "timestamp": datetime.now().isoformat(),
            "status": "sucesso",
        }

        manifest_path = os.path.join(base_dir, "code_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(code_manifest, f, indent=4, ensure_ascii=False)

        db_c3.upsert_code_manifest(id_requisicao, code_manifest)
        log_workflow(id_requisicao, "[LLM-CODEGEN] Código gerado com sucesso")
        return code_manifest

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        log_workflow(id_requisicao, f"[LLM-CODEGEN] Erro geral ao gerar código: {type(e).__name__}: {e}\n{tb}")
        from utils.path_validation import is_production
        err_msg = str(e).strip()[:500] if str(e) else "Erro ao gerar código."
        if is_production():
            err_msg = "Erro ao gerar código."
        return {"erro": err_msg, "status": "falha"}
