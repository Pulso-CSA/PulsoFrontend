#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow Core JavaScript❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import json
import os
from datetime import datetime
from typing import Dict, Any

from utils.logger import log_workflow
from utils.execution_timer import execution_timer
from utils.path_validation import resolve_project_root_for_workflow
from app.prompts.loader import set_request_stack

# Camadas 1 e 2 (Governança + Arquitetura) – pipeline igual ao Python
try:
    from app.PulsoCSA.JavaScript.workflow.creator_workflow.workflow_steps_js import (
        execute_layer1_js,
        execute_layer2_js,
    )
    _HAS_FULL_PIPELINE = True
except ImportError:
    execute_layer1_js = None
    execute_layer2_js = None
    _HAS_FULL_PIPELINE = False

# Camada 3 e 3.2 – Estrutura e Código (mesmo pipeline que Python)
try:
    from app.PulsoCSA.JavaScript.services.creator_services import (
        create_structure_from_report_js,
        create_code_from_reports_js,
    )
    _HAS_CREATOR_AGENTS = True
except ImportError:
    create_structure_from_report_js = None
    create_code_from_reports_js = None
    _HAS_CREATOR_AGENTS = False

try:
    from app.PulsoCSA.JavaScript.services.test_runner_service_js import run_automated_test_js
    _HAS_TEST_RUNNER = True
except ImportError:
    run_automated_test_js = None
    _HAS_TEST_RUNNER = False

try:
    from app.PulsoCSA.JavaScript.services.autocorrect_creator_service_js import run_autocorrect_creator_js
    _HAS_AUTOCORRECT = True
except ImportError:
    run_autocorrect_creator_js = None
    _HAS_AUTOCORRECT = False


def run_workflow_pipeline_js(
    prompt: str, 
    usuario: str, 
    root_path: str = None,
    language: str = "javascript",
    framework: str | None = None,
) -> Dict[str, Any]:
    """
    Orquestra a execução do workflow JavaScript/TypeScript/React.
    Retorna o documento consolidado final.
    """
    with execution_timer("workflow/creator-js (governance)", "workflow_core_js"):
        return _run_workflow_pipeline_js_impl(prompt, usuario, root_path, language, framework)


def _run_workflow_pipeline_js_impl(
    prompt: str, 
    usuario: str, 
    root_path: str = None,
    language: str = "javascript",
    framework: str | None = None,
) -> Dict[str, Any]:
    """
    Implementação do workflow JavaScript.
    Pipeline igual ao Python: C1 (Governança) → C2 (Arquitetura) → C3 (Estrutura) → C3.2 (Código/LLM).
    """
    workflow_log = []
    layer1_result = None
    layer2_result = None
    test_result = None
    
    try:
        workflow_log.append(f"🚀 Iniciando workflow JavaScript ({language}/{framework})...")
        
        #━━━━━━━━━❮Camada 1 – Governança (Input → Refine → Validate)❯━━━━━━━━━
        if _HAS_FULL_PIPELINE and execute_layer1_js:
            set_request_stack("javascript")
            workflow_log.append("⚙️ C1 – Governança...")
            layer1_result = execute_layer1_js(prompt, usuario, root_path)
            id_requisicao = layer1_result["id_requisicao"]
            refined_prompt = layer1_result["final_prompt"]
            root_path = layer1_result.get("root_path") or root_path
            workflow_log.append(f"✅ C1 concluída: {id_requisicao}")
        else:
            id_requisicao = f"js-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(prompt + usuario) % 10000}"
            refined_prompt = prompt
        
        #━━━━━━━━━❮Mesmo destino que Python: workspace por utilizador ou pulso_workspace_dev (dev)❯━━━━━━━━━
        root_path = resolve_project_root_for_workflow(usuario, root_path)
        workflow_log.append(f"📁 root_path efetivo: {root_path}")
        
        #━━━━━━━━━❮Camada 2 – Arquitetura (Structure → Backend → Infra → Sec) – igual ao Python❯━━━━━━━━━
        if _HAS_FULL_PIPELINE and execute_layer2_js:
            set_request_stack("javascript")
            workflow_log.append("⚙️ C2 – Arquitetura...")
            layer2_result = execute_layer2_js(id_requisicao, refined_prompt, root_path)
            workflow_log.append("✅ C2 concluída")
        
        #━━━━━━━━━❮Camada 3 – Estrutura (igual ao Python: create_structure_from_report)❯━━━━━━━━━
        estrutura_manifest = None
        code_manifest = None
        base_dir = None
        created_files = []
        
        if _HAS_CREATOR_AGENTS and create_structure_from_report_js and root_path:
            workflow_log.append("⚙️ C3 – Criação de Estrutura...")
            estrutura_manifest = create_structure_from_report_js(root_path, id_requisicao)
            if estrutura_manifest.get("status") == "falha" or estrutura_manifest.get("erro"):
                raise ValueError(estrutura_manifest.get("erro", "Falha ao criar estrutura"))
            workflow_log.append("✅ C3 – Estrutura criada com sucesso.")
            base_dir = estrutura_manifest.get("root_path")
        else:
            workflow_log.append("⚠️ C3 skip (agentes não disponíveis ou root_path inválido)")
        
        #━━━━━━━━━❮Camada 3.2 – Código (igual ao Python: create_code_from_reports)❯━━━━━━━━━
        if base_dir and os.path.isdir(base_dir) and _HAS_CREATOR_AGENTS and create_code_from_reports_js:
            workflow_log.append("⚙️ C3.2 – Gerando código-fonte via LLM...")
            fw = (framework or "react").lower()
            lang = (language or "javascript").lower()
            code_manifest = create_code_from_reports_js(root_path, id_requisicao, lang, fw)
            if code_manifest.get("status") == "falha":
                workflow_log.append(f"⚠️ C3.2 – {code_manifest.get('erro', 'Falha ao gerar código')}")
            else:
                created_files = code_manifest.get("files_written") or []
                workflow_log.append("✅ C3.2 – Código gerado com sucesso.")
        
        #━━━━━━━━━❮Auto-correção (valida build, corrige imports) – como Python❯━━━━━━━━━
        if base_dir and _HAS_AUTOCORRECT and run_autocorrect_creator_js:
            try:
                run_autocorrect_creator_js(base_dir, refined_prompt, workflow_log, language or "javascript", framework)
            except Exception as e:
                workflow_log.append(f"⚠️ Auto-correção skip: {e}")

        #━━━━━━━━━❮C5 – Teste automatizado (npm test) – como Python❯━━━━━━━━━
        test_result = None
        if base_dir and _HAS_TEST_RUNNER and run_automated_test_js:
            try:
                workflow_log.append("⚙️ C5 – Teste automatizado...")
                test_result = run_automated_test_js(base_dir, "info")
                if test_result.get("success"):
                    workflow_log.append("✅ C5 – Testes passaram")
                else:
                    workflow_log.append(f"⚠️ C5 – {test_result.get('message', 'Testes falharam ou skip')}")
            except Exception as e:
                workflow_log.append(f"⚠️ C5 skip: {e}")
        
        # Resultado alinhado ao contrato do Python (extract_new_paths, build_file_tree)
        result = {
            "id_requisicao": id_requisicao,
            "status": "sucesso",
            "language": language,
            "framework": framework,
            "created_files": created_files,
            "root_path": root_path,
            "workflow_log": workflow_log,
            "test_run": test_result,
            "estrutura_manifest": estrutura_manifest,
            "code_manifest": code_manifest,
            "estrutura": layer2_result.get("estrutura") if layer2_result else None,
            "backend": layer2_result.get("backend") if layer2_result else None,
        }
        
        log_workflow("workflow.log", f"[workflow-js] Concluído: {id_requisicao} ({language}/{framework})")
        return result
        
    except Exception as e:
        error_msg = f"Erro no workflow JavaScript: {str(e)}"
        workflow_log.append(f"❌ {error_msg}")
        log_workflow("workflow.log", f"[workflow-js] ERRO: {error_msg}")
        return {
            "id_requisicao": id_requisicao if 'id_requisicao' in locals() else "unknown",
            "status": "falha",
            "erro": error_msg,
            "workflow_log": workflow_log,
        }


def _stub_content_for_file(file_path: str, framework: str, is_ts: bool) -> str:
    """Gera conteúdo stub mínimo e válido para arquivo do blueprint (dinâmico, organizado, buildável)."""
    path_lower = file_path.lower().replace("\\", "/")
    name = file_path.split("/")[-1].split(".")[0] if "/" in file_path else file_path.split(".")[0]
    ext = ".tsx" if path_lower.endswith(".tsx") else ".jsx" if path_lower.endswith(".jsx") else ".ts" if path_lower.endswith(".ts") else ".js"
    is_react = "react" in (framework or "").lower()
    is_vue = "vue" in (framework or "").lower()

    # Estilos
    if path_lower.endswith(".css"):
        return "/* " + name + " */\n"

    # LoginForm.tsx / componentes de login em React
    if path_lower.endswith((".tsx", ".jsx")) and is_react and "login" in path_lower:
        # Preferir TypeScript quando indicado, mas sem depender de recursos avançados
        header = "import React, { useState } from 'react'\n\n"
        if ext == ".tsx":
            body = (
                "interface LoginFormProps {\n"
                "  onSuccess: (profile: any) => void\n"
                "}\n\n"
                "const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {\n"
                "  const [email, setEmail] = useState('')\n"
                "  const [password, setPassword] = useState('')\n"
                "  const [loading, setLoading] = useState(false)\n"
                "  const [error, setError] = useState<string | null>(null)\n\n"
                "  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {\n"
                "    e.preventDefault()\n"
                "    setLoading(true)\n"
                "    setError(null)\n"
                "    try {\n"
                "      const baseUrl = import.meta.env.VITE_API_URL || ''\n"
                "      const resp = await fetch(`${baseUrl}/auth/login`, {\n"
                "        method: 'POST',\n"
                "        headers: { 'Content-Type': 'application/json' },\n"
                "        body: JSON.stringify({ email, password }),\n"
                "      })\n"
                "      if (!resp.ok) {\n"
                "        const data = await resp.json().catch(() => ({}))\n"
                "        throw new Error((data && (data.detail || data.message)) || 'Falha no login')\n"
                "      }\n"
                "      const data = await resp.json().catch(() => ({}))\n"
                "      onSuccess(data)\n"
                "    } catch (err: any) {\n"
                "      setError(err?.message || 'Erro inesperado ao autenticar')\n"
                "    } finally {\n"
                "      setLoading(false)\n"
                "    }\n"
                "  }\n\n"
                "  return (\n"
                "    <form onSubmit={handleSubmit} className=\"login-form\">\n"
                "      <div className=\"field\">\n"
                "        <label htmlFor=\"email\">E-mail</label>\n"
                "        <input\n"
                "          id=\"email\"\n"
                "          type=\"email\"\n"
                "          value={email}\n"
                "          onChange={e => setEmail(e.target.value)}\n"
                "          required\n"
                "        />\n"
                "      </div>\n"
                "      <div className=\"field\">\n"
                "        <label htmlFor=\"password\">Senha</label>\n"
                "        <input\n"
                "          id=\"password\"\n"
                "          type=\"password\"\n"
                "          value={password}\n"
                "          onChange={e => setPassword(e.target.value)}\n"
                "          required\n"
                "        />\n"
                "      </div>\n"
                "      {error && <p className=\"error\">{error}</p>}\n"
                "      <button type=\"submit\" disabled={loading}>\n"
                "        {loading ? 'Entrando...' : 'Entrar'}\n"
                "      </button>\n"
                "    </form>\n"
                "  )\n"
                "}\n\n"
                "export default LoginForm\n"
            )
        else:
            body = (
                "const LoginForm = ({ onSuccess }) => {\n"
                "  const [email, setEmail] = useState('')\n"
                "  const [password, setPassword] = useState('')\n"
                "  const [loading, setLoading] = useState(false)\n"
                "  const [error, setError] = useState(null)\n\n"
                "  const handleSubmit = async (e) => {\n"
                "    e.preventDefault()\n"
                "    setLoading(true)\n"
                "    setError(null)\n"
                "    try {\n"
                "      const baseUrl = import.meta.env.VITE_API_URL || ''\n"
                "      const resp = await fetch(`${baseUrl}/auth/login`, {\n"
                "        method: 'POST',\n"
                "        headers: { 'Content-Type': 'application/json' },\n"
                "        body: JSON.stringify({ email, password }),\n"
                "      })\n"
                "      if (!resp.ok) {\n"
                "        const data = await resp.json().catch(() => ({}))\n"
                "        throw new Error((data && (data.detail || data.message)) || 'Falha no login')\n"
                "      }\n"
                "      const data = await resp.json().catch(() => ({}))\n"
                "      onSuccess(data)\n"
                "    } catch (err) {\n"
                "      setError(err?.message || 'Erro inesperado ao autenticar')\n"
                "    } finally {\n"
                "      setLoading(false)\n"
                "    }\n"
                "  }\n\n"
                "  return (\n"
                "    <form onSubmit={handleSubmit} className=\"login-form\">\n"
                "      <div className=\"field\">\n"
                "        <label htmlFor=\"email\">E-mail</label>\n"
                "        <input\n"
                "          id=\"email\"\n"
                "          type=\"email\"\n"
                "          value={email}\n"
                "          onChange={e => setEmail(e.target.value)}\n"
                "          required\n"
                "        />\n"
                "      </div>\n"
                "      <div className=\"field\">\n"
                "        <label htmlFor=\"password\">Senha</label>\n"
                "        <input\n"
                "          id=\"password\"\n"
                "          type=\"password\"\n"
                "          value={password}\n"
                "          onChange={e => setPassword(e.target.value)}\n"
                "          required\n"
                "        />\n"
                "      </div>\n"
                "      {error && <p className=\"error\">{error}</p>}\n"
                "      <button type=\"submit\" disabled={loading}>\n"
                "        {loading ? 'Entrando...' : 'Entrar'}\n"
                "      </button>\n"
                "    </form>\n"
                "  )\n"
                "}\n\n"
                "export default LoginForm\n"
            )
        return header + body

    # Componentes React genéricos
    if path_lower.endswith((".tsx", ".jsx")) and is_react:
        comp = name.replace("-", "") if "-" in name else name
        comp = comp[0].upper() + (comp[1:] if len(comp) > 1 else "")
        return (
            f"import React from 'react'\n\n"
            f"const {comp}: React.FC = () => {{\n  return <div>{comp}</div>\n}}\n\nexport default {comp}\n"
        )

    # Serviços / hooks em TS/JS
    if path_lower.endswith((".ts", ".js")):
        lower_name = name.lower()
        if "authservice" in lower_name or ("auth" in path_lower and "service" in path_lower):
            return (
                "const API_URL = import.meta.env.VITE_API_URL || ''\n\n"
                "export interface LoginResponse {\n"
                "  access_token: string\n"
                "  refresh_token?: string\n"
                "  [key: string]: any\n"
                "}\n\n"
                "export async function login(email: string, password: string): Promise<LoginResponse> {\n"
                "  const resp = await fetch(`${API_URL}/auth/login`, {\n"
                "    method: 'POST',\n"
                "    headers: { 'Content-Type': 'application/json' },\n"
                "    body: JSON.stringify({ email, password }),\n"
                "  })\n"
                "  if (!resp.ok) {\n"
                "    const data = await resp.json().catch(() => ({}))\n"
                "    throw new Error((data as any).detail || (data as any).message || 'Falha no login')\n"
                "  }\n"
                "  return (await resp.json()) as LoginResponse\n"
                "}\n"
            )
        if "hook" in path_lower:
            return (
                "import { useState } from 'react'\n\n"
                f"export function {name}() {{\n"
                "  const [loading, setLoading] = useState(false)\n"
                "  return { loading, setLoading }\n"
                "}\n"
            )
        return f"// {name}\nexport {{}}\n"

    # Vue SFC
    if path_lower.endswith(".vue") and is_vue:
        return f"<template><div>{name}</div></template>\n<script setup>\n</script>\n"

    return ""


def _merge_blueprint_into_structure(
    project_structure: Dict[str, str],
    estrutura_arquivos: Dict[str, list],
    framework: str,
    is_typescript: bool,
) -> Dict[str, str]:
    """Adiciona stubs para arquivos do blueprint que ainda não existem (dinâmico por prompt)."""
    if not estrutura_arquivos or not isinstance(estrutura_arquivos, dict):
        return project_structure
    out = dict(project_structure)
    is_ts = is_typescript or "typescript" in (framework or "").lower()
    for folder, files in estrutura_arquivos.items():
        if not isinstance(files, list):
            continue
        prefix = (folder.strip("/") + "/") if folder and folder != "." else ""
        for f in files:
            if not isinstance(f, str) or not f.strip():
                continue
            path = (prefix + f.strip()).replace("\\", "/").lstrip("/")
            if path in out:
                continue
            stub = _stub_content_for_file(path, framework, is_ts)
            if stub:
                out[path] = stub
    return out


def _generate_project_structure(language: str, framework: str | None, prompt: str) -> Dict[str, str]:
    """
    Gera estrutura completa de projeto baseada na linguagem e framework.
    Suporta: React, Vue, Angular, TypeScript, JavaScript vanilla.
    """
    structure = {}
    
    if not framework:
        framework = "vanilla"
    
    framework_lower = framework.lower()
    is_typescript = "typescript" in framework_lower
    is_react = "react" in framework_lower
    is_vue = "vue" in framework_lower
    is_angular = "angular" in framework_lower
    
    # Determina extensão de arquivo
    if is_angular:
        ext = ".ts"  # Angular sempre usa TypeScript
        is_typescript = True
    elif is_vue:
        ext = ".vue"
        if is_typescript:
            ext = ".vue"  # Vue pode ter TypeScript dentro
    elif is_react:
        ext = ".tsx" if is_typescript else ".jsx"
    elif is_typescript:
        ext = ".ts"
    else:
        ext = ".js"
    
    # package.json
    package_json = {
        "name": "pulso-project",
        "version": "1.0.0",
        "description": prompt[:100],
        "main": f"src/index{ext}" if not is_angular else "src/main.ts",
        "scripts": {},
        "dependencies": {},
        "devDependencies": {},
    }
    
    # Configura scripts e dependências baseado no framework
    if is_angular:
        package_json["scripts"] = {
            "ng": "ng",
            "start": "ng serve",
            "build": "ng build",
            "watch": "ng build --watch --configuration development",
            "test": "ng test",
        }
        package_json["dependencies"] = {
            "@angular/animations": "^17.0.0",
            "@angular/common": "^17.0.0",
            "@angular/compiler": "^17.0.0",
            "@angular/core": "^17.0.0",
            "@angular/forms": "^17.0.0",
            "@angular/platform-browser": "^17.0.0",
            "@angular/platform-browser-dynamic": "^17.0.0",
            "@angular/router": "^17.0.0",
            "rxjs": "~7.8.0",
            "tslib": "^2.3.0",
            "zone.js": "~0.14.0",
        }
        package_json["devDependencies"] = {
            "@angular-devkit/build-angular": "^17.0.0",
            "@angular/cli": "^17.0.0",
            "@angular/compiler-cli": "^17.0.0",
            "@types/jasmine": "~5.1.0",
            "jasmine-core": "~5.1.0",
            "karma": "~6.4.0",
            "karma-chrome-launcher": "~3.2.0",
            "karma-coverage": "~2.2.0",
            "karma-jasmine": "~5.1.0",
            "karma-jasmine-html-reporter": "~2.1.0",
            "typescript": "~5.2.0",
        }
    elif is_vue:
        package_json["scripts"] = {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
        }
        package_json["dependencies"] = {
            "vue": "^3.4.0",
        }
        package_json["devDependencies"] = {
            "@vitejs/plugin-vue": "^5.0.0",
            "vite": "^5.0.0",
        }
        if is_typescript:
            package_json["devDependencies"]["typescript"] = "^5.3.0"
            package_json["devDependencies"]["vue-tsc"] = "^1.8.0"
    elif is_react:
        package_json["scripts"] = {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
            "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
        }
        package_json["dependencies"] = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
        }
        package_json["devDependencies"] = {
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "@vitejs/plugin-react": "^4.2.0",
            "eslint": "^8.57.0",
            "eslint-plugin-react": "^7.33.0",
            "eslint-plugin-react-hooks": "^4.6.0",
            "eslint-plugin-react-refresh": "^0.4.5",
            "vite": "^5.0.0",
        }
        if is_typescript:
            package_json["devDependencies"]["typescript"] = "^5.3.0"
    else:
        # JavaScript vanilla ou Node.js
        package_json["scripts"] = {
            "dev": "node src/index.js",
            "start": "node src/index.js",
            "build": "tsc" if is_typescript else "echo 'Build script'",
        }
        if is_typescript:
            package_json["devDependencies"]["typescript"] = "^5.3.0"
            package_json["devDependencies"]["@types/node"] = "^20.10.0"
    
    structure["package.json"] = json.dumps(package_json, indent=2, ensure_ascii=False)
    
    # tsconfig.json (se TypeScript e não Angular)
    if is_typescript and not is_angular:
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "ESNext",
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "jsx": "react-jsx" if is_react else ("preserve" if is_vue else "preserve"),
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
            },
            "include": ["src"],
        }
        structure["tsconfig.json"] = json.dumps(tsconfig, indent=2)
    elif is_angular:
        # Angular tem múltiplos arquivos tsconfig
        tsconfig_base = {
            "compileOnSave": False,
            "compilerOptions": {
                "outDir": "./dist/out-tsc",
                "forceConsistentCasingInFileNames": True,
                "strict": True,
                "noImplicitOverride": True,
                "noPropertyAccessFromIndexSignature": True,
                "noImplicitReturns": True,
                "noFallthroughCasesInSwitch": True,
            },
        }
        structure["tsconfig.json"] = json.dumps(tsconfig_base, indent=2)
        
        tsconfig_app = {
            "extends": "./tsconfig.json",
            "compilerOptions": {
                "outDir": "./out-tsc/app",
                "types": [],
            },
            "files": ["src/main.ts"],
            "include": ["src/**/*.d.ts"],
        }
        structure["tsconfig.app.json"] = json.dumps(tsconfig_app, indent=2)
    
    # vite.config (se React ou Vue)
    if is_react:
        vite_config = f"""import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({{
  plugins: [react()],
  server: {{
    port: 3000,
    open: false,
  }},
}})"""
        structure[f"vite.config.{'ts' if is_typescript else 'js'}"] = vite_config
    elif is_vue:
        vite_config = f"""import {{ defineConfig }} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({{
  plugins: [vue()],
  server: {{
    port: 3000,
    open: false,
  }},
}})"""
        structure[f"vite.config.{'ts' if is_typescript else 'js'}"] = vite_config
    
    # angular.json (se Angular)
    if is_angular:
        angular_json = {
            "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
            "version": 1,
            "newProjectRoot": "projects",
            "projects": {
                "pulso-project": {
                    "projectType": "application",
                    "schematics": {},
                    "root": "",
                    "sourceRoot": "src",
                    "prefix": "app",
                    "architect": {
                        "build": {
                            "builder": "@angular-devkit/build-angular:browser",
                            "options": {
                                "outputPath": "dist/pulso-project",
                                "index": "src/index.html",
                                "main": "src/main.ts",
                                "polyfills": ["zone.js"],
                                "tsConfig": "tsconfig.app.json",
                                "assets": ["src/favicon.ico", "src/assets"],
                                "styles": ["src/styles.css"],
                                "scripts": [],
                            },
                        },
                        "serve": {
                            "builder": "@angular-devkit/build-angular:dev-server",
                            "options": {
                                "port": 4200,
                            },
                        },
                    },
                },
            },
        }
        structure["angular.json"] = json.dumps(angular_json, indent=2, ensure_ascii=False)
    
    # src/index ou src/main
    if is_angular:
        main_content = f"""import {{ platformBrowserDynamic }} from '@angular/platform-browser-dynamic';
import {{ AppModule }} from './app/app.module';

platformBrowserDynamic().bootstrapModule(AppModule)
  .catch(err => console.error(err));
"""
        structure["src/main.ts"] = main_content
    elif is_vue:
        index_content = """import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

createApp(App).mount('#app')
"""
        structure["src/main.js"] = index_content
        if is_typescript:
            structure["src/main.ts"] = index_content
        structure["src/style.css"] = """* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
"""
    elif is_react:
        index_content = f"""import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App{ext}'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""
    else:
        index_content = f"""// {prompt[:200]}

console.log('Hello, Pulso!')
"""
    
    structure[f"src/index{ext}"] = index_content
    
    # src/App (se React ou Vue)
    if is_react:
        prompt_lower = (prompt or "").lower()
        is_login_project = any(kw in prompt_lower for kw in ("login", "sistema de login", "autenticação", "autenticacao"))
        if is_login_project:
            app_content = f"""import React, {{ useState }} from 'react'
import './App.css'
import LoginForm from './components/LoginForm'

function App() {{
  const [user, setUser] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSuccess = (profile: any) => {{
    setUser(profile)
    setError(null)
  }}

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sistema de Login</h1>
        <p>{prompt[:200]}</p>
      </header>
      <main>
        {{!user ? (
          <LoginForm onSuccess={handleSuccess} />
        ) : (
          <div className="login-success">
            <h2>Bem-vindo</h2>
            <pre>{'{'}JSON.stringify(user, null, 2){'}'}</pre>
          </div>
        )}}
        {{error && <p className="error">{{error}}</p>}}
      </main>
    </div>
  )
}}

export default App
"""
        else:
            app_content = f"""import React from 'react'
import './App.css'

function App() {{
  return (
    <div className="app">
      <header className="app-header">
        <h1>Pulso Project</h1>
        <p>{prompt[:200]}</p>
      </header>
      <main>
        <p>Comece editando <code>src/App{ext}</code></p>
      </main>
    </div>
  )
}}

export default App
"""
        structure[f"src/App{ext}"] = app_content
        structure["src/App.css"] = """.app {
  text-align: center;
}

.app-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
}

.app-header h1 {
  margin: 0;
  font-size: 2rem;
}
"""
    elif is_vue:
        app_content = f"""<template>
  <div class="app">
    <header class="app-header">
      <h1>Pulso Project</h1>
      <p>{{ description }}</p>
    </header>
    <main>
      <p>Comece editando <code>src/App.vue</code></p>
    </main>
  </div>
</template>

<script{' setup lang="ts"' if is_typescript else ' setup'}>
const description = `{prompt[:200]}`
</script>

<style scoped>
.app {{
  text-align: center;
}}

.app-header {{
  background-color: #282c34;
  padding: 20px;
  color: white;
}}

.app-header h1 {{
  margin: 0;
  font-size: 2rem;
}}
</style>
"""
        structure["src/App.vue"] = app_content
    elif is_angular:
        app_component_ts = f"""import {{ Component }} from '@angular/core';

@Component({{
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
}})
export class AppComponent {{
  title = 'Pulso Project';
  description = `{prompt[:200]}`;
}}
"""
        app_component_html = """<div class="app">
  <header class="app-header">
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
  </header>
  <main>
    <p>Comece editando <code>src/app/app.component.ts</code></p>
  </main>
</div>
"""
        app_component_css = """.app {
  text-align: center;
}

.app-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
}

.app-header h1 {
  margin: 0;
  font-size: 2rem;
}
"""
        structure["src/app/app.component.ts"] = app_component_ts
        structure["src/app/app.component.html"] = app_component_html
        structure["src/app/app.component.css"] = app_component_css
        
        app_module = """import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
"""
        structure["src/app/app.module.ts"] = app_module
    
    # index.html (se React ou Vue)
    if is_react or is_vue:
        script_src = "/src/index.tsx" if (is_react and is_typescript) else "/src/index.jsx" if is_react else "/src/main.js"
        html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Pulso Project</title>
  </head>
  <body>
    <div id="{'root' if is_react else 'app'}"></div>
    <script type="module" src="{script_src}"></script>
  </body>
</html>"""
        structure["index.html"] = html_content
    elif is_angular:
        html_content = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Pulso Project</title>
  <base href="/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/x-icon" href="favicon.ico">
</head>
<body>
  <app-root></app-root>
</body>
</html>
"""
        structure["src/index.html"] = html_content
    
    # README.md
    readme = f"""# Pulso Project

## Descrição
{prompt[:500]}

## Tecnologias
- Linguagem: {language}
- Framework: {framework or 'Nenhum'}

## Instalação
\`\`\`bash
npm install
\`\`\`

## Execução
\`\`\`bash
npm run dev
\`\`\`
"""
    structure["README.md"] = readme
    
    # .gitignore
    gitignore = """node_modules/
dist/
build/
*.log
.env
.DS_Store
"""
    structure[".gitignore"] = gitignore
    
    # .env.example (referência segura para variáveis de ambiente — qualidade empresarial)
    if is_react or is_vue:
        structure[".env.example"] = "# API (Vite usa prefixo VITE_)\nVITE_API_URL=\n"
    
    return structure
