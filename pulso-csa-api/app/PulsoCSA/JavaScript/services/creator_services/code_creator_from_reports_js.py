#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Geração de Código JS a partir de relatórios (equivalente ao Python C3.2)❯━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Any, List, Tuple

try:
    from utils.logger import log_workflow
    from utils.path_validation import is_path_under_base
except ImportError:
    from app.PulsoCSA.Python.utils.logger import log_workflow
    from app.PulsoCSA.Python.utils.path_validation import is_path_under_base

from app.prompts.loader import set_request_stack
from app.PulsoCSA.JavaScript.services.code_creator_service_js import generate_file_js

# Arquivos que mantêm stub (não passam por LLM) — evita chamadas desnecessárias ao Ollama
_SKIP_LLM = {
    "package.json", "tsconfig.json", "tsconfig.app.json",
    "vite.config.ts", "vite.config.js", "index.html",
    ".env", ".env.example", ".gitignore", "README.md",
    "angular.json", "__init__.py",
    # Frontend/base fullstack mantido por stub determinístico
    "App.tsx", "App.jsx", "LoginPage.tsx", "LoginPage.jsx",
    "LoginForm.tsx", "LoginForm.jsx", "AuthContext.tsx", "AuthContext.jsx",
    "authService.ts", "authService.js", "useAuth.ts", "useAuth.js",
    # Backend fullstack JS
    "server.js", "auth.routes.js", "auth.service.js", "users.js",
}


def _css_stub(filename: str) -> str:
    """Stub para CSS — App.css recebe estilos base; outros mínimo."""
    name = os.path.splitext(filename)[0]
    if name.lower() == "app":
        return (
            ".app { text-align: center; }\n"
            ".app-header { background-color: #282c34; padding: 20px; color: white; }\n"
            ".app-header h1 { margin: 0; }\n"
            "main { padding: 20px; min-height: 200px; }\n"
            ".form-stub { max-width: 320px; margin: 20px auto; padding: 16px; }\n"
            ".form-stub .field { margin-bottom: 12px; }\n"
            ".form-stub label { display: block; margin-bottom: 4px; }\n"
            ".form-stub input { width: 100%; padding: 8px; box-sizing: border-box; }\n"
            ".form-stub button { margin-top: 8px; padding: 8px 16px; }\n"
            ".login-success { padding: 20px; text-align: left; }\n"
        )
    return f"/* {name} */\n"


def _test_stub(filename: str) -> str:
    """Stub mínimo para arquivos de teste — não usa LLM."""
    return "// TODO: adicione testes\nimport { describe, it, expect } from 'vitest'\n\ndescribe('placeholder', () => {\n  it('placeholder', () => {\n    expect(true).toBe(true)\n  })\n})\n"


def create_code_from_reports_js(root_path: str, id_requisicao: str, language: str = "javascript", framework: str = "react") -> Dict[str, Any]:
    """
    Lê structure_manifest, backend e security reports, gera código via LLM para cada arquivo.
    Equivalente ao Python create_code_from_reports para stack JavaScript.
    """
    set_request_stack("javascript")
    try:
        reports_dir = os.path.join(root_path, "reports", id_requisicao)
        structure_manifest_path = os.path.join(root_path, id_requisicao, "generated_code", "structure_manifest.json")
        backend_report_path = os.path.join(reports_dir, "02_backend_report.json")
        security_report_path = os.path.join(reports_dir, "04_code_security_report.json")
        summary_path = os.path.join(reports_dir, "summary_pipeline.json")

        if not os.path.exists(structure_manifest_path):
            raise FileNotFoundError(f"Structure manifest não encontrado: {structure_manifest_path}")

        with open(structure_manifest_path, "r", encoding="utf-8") as f:
            structure_manifest = json.load(f)

        base_dir = structure_manifest.get("root_path")
        if not base_dir or not os.path.isdir(base_dir):
            raise FileNotFoundError(f"Diretório gerado não encontrado: {base_dir}")
        base_dir_abs = os.path.abspath(base_dir)

        backend_report = {}
        if os.path.exists(backend_report_path):
            with open(backend_report_path, "r", encoding="utf-8") as f:
                backend_report = json.load(f)
        security_report = {}
        if os.path.exists(security_report_path):
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

        backend_str = json.dumps(backend_report, ensure_ascii=False)[:1500]
        security_str = json.dumps(security_report, ensure_ascii=False)[:800]
        structure_str = json.dumps(structure_manifest.get("created", {}), ensure_ascii=False, indent=2)[:2000]
        refined = refined_prompt or "criar sistema de login"

        created_files: List[str] = []
        created_dict = structure_manifest.get("created", {})
        tasks_llm: List[Tuple[str, str, str, str, str]] = []

        for folder_key, files in created_dict.items():
            if not isinstance(files, list):
                continue
            folder_path = base_dir if folder_key in (".", "", None) else os.path.join(base_dir, str(folder_key).strip())
            if not is_path_under_base(os.path.abspath(folder_path), base_dir_abs):
                continue
            for filename in files:
                if not isinstance(filename, str) or not filename or ".." in filename:
                    continue
                file_path = os.path.join(folder_path, filename)
                if not is_path_under_base(os.path.abspath(file_path), base_dir_abs):
                    continue
                if filename.lower() in _SKIP_LLM:
                    created_files.append(file_path)
                    continue
                # CSS não precisa de LLM — stub é suficiente
                if filename.lower().endswith(".css"):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(_css_stub(filename))
                    created_files.append(file_path)
                    continue
                # Test/spec — stub mínimo (LLM pode gerar depois se necessário)
                fn_lower = filename.lower()
                if fn_lower.endswith(".test.ts") or fn_lower.endswith(".test.tsx") or fn_lower.endswith(".spec.ts") or fn_lower.endswith(".spec.tsx"):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(_test_stub(filename))
                    created_files.append(file_path)
                    continue
                # Declarações TypeScript (.d.ts)
                if fn_lower.endswith(".d.ts"):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("// Type declarations\n")
                    created_files.append(file_path)
                    continue

                rel_path = f"{folder_key}/{filename}".lstrip("/") if folder_key and folder_key != "." else filename
                file_context = f"Arquivo {rel_path}"
                if "component" in rel_path.lower() or rel_path.endswith((".tsx", ".jsx")):
                    file_context = f"Componente React {filename}"
                elif "service" in rel_path.lower():
                    file_context = f"Serviço {filename}"
                elif "hook" in rel_path.lower():
                    file_context = f"Hook {filename}"
                elif "page" in rel_path.lower():
                    file_context = f"Página {filename}"
                tasks_llm.append((file_path, rel_path, file_context, structure_str, refined))

        def _generate_one_file(args: Tuple[str, str, str, str, str]) -> str:
            file_path, rel_path, file_context, struct, ref = args
            try:
                content = generate_file_js(
                    filename=rel_path,
                    refined_prompt=ref,
                    structure=struct,
                    file_context=file_context,
                    backend=backend_str,
                    security=security_str,
                    language=language,
                    framework=framework,
                )
                if content and len(content.strip()) > 30:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return file_path
            except Exception as e:
                log_workflow(id_requisicao, f"[JS] LLM skip {rel_path}: {e}")
            return ""

        use_ollama = os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes")
        default_workers = 2 if use_ollama else 4
        max_workers = int(os.getenv("CODEGEN_JS_MAX_WORKERS", str(default_workers)))
        max_workers = min(max(1, max_workers), max(1, len(tasks_llm)))

        if tasks_llm:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(_generate_one_file, t): t for t in tasks_llm}
                for fut in as_completed(futures):
                    try:
                        fp = fut.result()
                        if fp:
                            created_files.append(fp)
                    except Exception as file_err:
                        task = futures.get(fut)
                        file_info = f" (arquivo: {task[1]})" if task else ""
                        log_workflow(id_requisicao, f"[JS] Erro ao gerar {file_info}: {file_err}")

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

        log_workflow(id_requisicao, "[JS] Código gerado com sucesso")
        return code_manifest

    except Exception as e:
        import traceback
        log_workflow(id_requisicao, f"[JS] Erro ao gerar código: {e}\n{traceback.format_exc()}")
        return {"erro": str(e).strip()[:500] if str(e) else "Erro ao gerar código.", "status": "falha"}
