#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Auto-correção no Creator Workflow JS❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
# Valida o build após criação e corrige imports/deps quebrados (como no Python).

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from utils.log_manager import add_log

SOURCE = "autocorrect_creator_js"

# Windows: evita abrir janela de terminal ao rodar npm
_SUBPROCESS_FLAGS = {}
if sys.platform == "win32":
    _SUBPROCESS_FLAGS["creationflags"] = 0x08000000  # CREATE_NO_WINDOW


def _run_build(root_path: str, timeout: int = 120) -> Tuple[int, str, str]:
    """Executa npm run build. Retorna (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=root_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            **_SUBPROCESS_FLAGS,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout ao executar build"
    except Exception as e:
        return -1, "", str(e)


def _parse_build_errors(stdout: str, stderr: str) -> Dict[str, List[str]]:
    """
    Extrai erros de build do Vite/npm.
    Retorna {"missing_packages": [...], "missing_imports": [(arquivo, import_path), ...], "app_missing_default_export": [path]}
    """
    combined = stdout + "\n" + stderr
    combined_lower = combined.lower()
    missing_packages: List[str] = []
    missing_imports: List[Tuple[str, str]] = []
    app_missing_default_export: List[str] = []

    # "No matching export in ... for import \"default\"" (index importa App como default)
    no_export = re.findall(
        r"no matching export\s+in\s+[\"']([^\"']+)[\"']\s+for import\s+[\"']default[\"']",
        combined_lower,
        re.IGNORECASE,
    )
    for file_path in no_export:
        file_path = file_path.strip().replace("\\", "/")
        if "src" in file_path:
            file_path = "src/" + file_path.split("src")[-1].lstrip("/")
        if file_path and file_path not in app_missing_default_export:
            app_missing_default_export.append(file_path)

    # "Failed to resolve import X from Y"
    imp_match = re.findall(
        r"failed to resolve import\s+[\"']([^\"']+)[\"']\s+from\s+[\"']([^\"']+)[\"']",
        combined_lower,
        re.IGNORECASE,
    )
    for imp_path, file_path in imp_match:
        imp_path = imp_path.strip()
        file_path = file_path.strip()
        # Normaliza file_path para relativo (ex: src/App.tsx)
        if "src" in file_path:
            file_path = "src/" + file_path.split("src")[-1].lstrip("/\\")
        if imp_path.startswith(".") or imp_path.startswith("/"):
            missing_imports.append((file_path, imp_path))
        else:
            if imp_path not in missing_packages:
                missing_packages.append(imp_path)

    # "react-router-dom (imported by X)" ou "The following dependencies... X"
    pkg_match = re.findall(
        r"([a-z0-9@/_.-]+)\s*\(imported by",
        combined_lower,
        re.IGNORECASE,
    )
    for p in pkg_match:
        pkg = p.strip()
        if pkg and pkg not in missing_packages and not pkg.startswith(".") and "node_modules" not in pkg:
            missing_packages.append(pkg)

    # Lista explícita de pacotes comuns que o LLM usa mas não estão no template
    for known in ["react-router-dom", "react-router", "react-hook-form", "zod", "yup", "@hookform/resolvers"]:
        if known in combined_lower and ("could not be resolved" in combined_lower or "are they installed" in combined_lower):
            if known not in missing_packages:
                missing_packages.append(known)

    return {
        "missing_packages": list(dict.fromkeys(missing_packages)),
        "missing_imports": missing_imports,
        "app_missing_default_export": app_missing_default_export,
    }


def _fix_app_default_export(root_path: str, app_path: str, workflow_log: List[str]) -> bool:
    """Corrige App.tsx/App.jsx: remove ReactDOM.render e garante export default (primeira versão funcional)."""
    full_path = Path(root_path) / app_path
    if not full_path.is_file():
        return False
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False
    # Remove prefixo 'typescript' ou 'javascript' na primeira linha
    lines = content.split("\n")
    if lines and (lines[0].strip().lower() in ("typescript", "javascript")):
        lines = lines[1:]
    content = "\n".join(lines).lstrip()
    # Remove linhas com ReactDOM.render (ponto de entrada é index.tsx)
    content = "\n".join(line for line in content.split("\n") if "ReactDOM.render" not in line)
    content = content.rstrip()
    if "export default" not in content:
        component_name = "App"
        if content and not content.endswith(";"):
            content += "\n"
        content += f"\nexport default {component_name}\n"
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        workflow_log.append(f"✅ Auto-correção: {app_path} — export default aplicado")
        add_log("info", f"[{SOURCE}] Corrigido export default em {app_path}", SOURCE)
        return True
    except Exception:
        return False


def _add_dependencies(root_path: str, packages: List[str], workflow_log: List[str]) -> bool:
    """Adiciona dependências ao package.json e executa npm install."""
    if not packages:
        return True
    pkg_path = Path(root_path) / "package.json"
    if not pkg_path.is_file():
        return False
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        deps = data.get("dependencies", {})
        added = []
        VERSIONS = {
            "react-router-dom": "^6.4.0",
            "react-router": "^6.4.0",
            "react-hook-form": "^6.25.0",  # v6: compatível com ref={register}; v7 usa {...register('field')}
            "zod": "^3.22.0",
            "yup": "^1.3.0",
            "@hookform/resolvers": "^3.3.0",
        }
        for pkg in packages:
            if pkg not in deps:
                version = VERSIONS.get(pkg)
                if not version:
                    version = "^6.0.0" if "react-router" in pkg else "^7.0.0" if "react" in pkg else "^3.0.0"
                deps[pkg] = version
                added.append(pkg)
        if added:
            data["dependencies"] = deps
            with open(pkg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            add_log("info", f"[{SOURCE}] Dependências adicionadas: {added}", SOURCE)
            workflow_log.append(f"📦 Auto-correção: dependências adicionadas {added}")
            code, _, err = _run_npm_install(root_path)
            if code != 0:
                workflow_log.append(f"⚠️ npm install falhou: {err[:200]}")
                return False
        return True
    except Exception as e:
        add_log("error", f"[{SOURCE}] Erro ao atualizar package.json: {e}", SOURCE)
        return False


def _run_npm_install(root_path: str, timeout: int = 180) -> Tuple[int, str, str]:
    """Executa npm install."""
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=root_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            **_SUBPROCESS_FLAGS,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except Exception as e:
        return -1, "", str(e)


def _fix_file_with_missing_imports(
    root_path: str,
    file_path: str,
    missing_imports: List[Tuple[str, str]],
    prompt: str,
    workflow_log: List[str],
) -> bool:
    """
    Corrige arquivo que importa módulos inexistentes usando correct_file_js.
    Pede ao LLM para remover/substituir os imports quebrados.
    """
    try:
        from app.PulsoCSA.JavaScript.services.code_implementer_service_js import correct_file_js
    except ImportError:
        return False

    full_path = Path(root_path) / file_path
    if not full_path.is_file():
        return False

    rel_path = file_path.replace("\\", "/")
    imports_str = ", ".join(f"{imp} (em {f})" for f, imp in missing_imports if f == file_path or file_path in f)
    if not imports_str:
        imports_str = ", ".join(imp for _, imp in missing_imports)

    reason = (
        f"O build falhou porque estes imports não existem: {imports_str}. "
        "Remova ou substitua por implementação local. Para hooks (useAuth etc): use useState no componente. "
        "Para react-router-dom/Link: remova e use botões ou links <a>. Mantenha a funcionalidade principal."
    )

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    corrected = correct_file_js(
        file_path=rel_path,
        existing_source=content,
        prompt=reason,
        project_root=root_path,
        language="javascript",
        framework="react",
    )
    if corrected and corrected != content:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(corrected)
        workflow_log.append(f"✅ Auto-correção: {rel_path} corrigido (imports inexistentes)")
        return True
    return False


def run_autocorrect_creator_js(
    root_path: str,
    prompt: str,
    workflow_log: List[str],
    language: str = "javascript",
    framework: Optional[str] = None,
) -> Dict:
    """
    Executa validação de build e auto-correção após criação do projeto.
    Similar ao pipeline de autocorreção do Python.
    Retorna {"success": bool, "corrected": bool, "message": str}.
    """
    result: Dict = {"success": False, "corrected": False, "message": ""}
    if not root_path or not Path(root_path).is_dir():
        result["message"] = "root_path inválido"
        return result

    pkg_path = Path(root_path) / "package.json"
    if not pkg_path.is_file():
        result["success"] = True
        result["message"] = "Sem package.json, skip validação"
        return result

    # Verifica se tem script build
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        if "build" not in (pkg.get("scripts") or {}):
            result["success"] = True
            result["message"] = "Sem script build, skip validação"
            return result
    except Exception:
        result["message"] = "Erro ao ler package.json"
        return result

    add_log("info", f"[{SOURCE}] Validando build em {root_path}", SOURCE)
    workflow_log.append("🔧 Auto-correção: validando build...")

    # Garante node_modules antes do build
    if not (Path(root_path) / "node_modules").exists():
        workflow_log.append("📦 Auto-correção: npm install...")
        code_install, _, _ = _run_npm_install(root_path)
        if code_install != 0:
            result["message"] = "npm install falhou"
            return result

    code, out, err = _run_build(root_path)
    if code == 0:
        result["success"] = True
        result["message"] = "Build OK"
        workflow_log.append("✅ Auto-correção: build OK")
        return result

    parsed = _parse_build_errors(out, err)
    missing_packages = parsed.get("missing_packages", [])
    missing_imports = parsed.get("missing_imports", [])
    app_missing_default_export = parsed.get("app_missing_default_export", [])

    # 0. Corrigir App sem export default (primeira versão funcional)
    for app_path in app_missing_default_export[:2]:
        _fix_app_default_export(root_path, app_path, workflow_log)
    if app_missing_default_export:
        code0, _, _ = _run_build(root_path)
        if code0 == 0:
            result["success"] = True
            result["corrected"] = True
            result["message"] = "Build OK após correção de export default"
            workflow_log.append("✅ Auto-correção: build OK após export default")
            return result

    if not missing_packages and not missing_imports:
        result["message"] = f"Build falhou (código {code}), sem erros parseáveis"
        workflow_log.append(f"⚠️ Build falhou: {err[:150]}...")
        return result

    # 1. Adiciona dependências faltantes
    if missing_packages:
        _add_dependencies(root_path, missing_packages, workflow_log)

    # 2. Corrige arquivos com imports locais inexistentes
    files_to_fix = list(dict.fromkeys(f for f, _ in missing_imports))
    for file_path in files_to_fix[:3]:  # Limita a 3 arquivos
        _fix_file_with_missing_imports(root_path, file_path, missing_imports, prompt, workflow_log)

    # 3. Se adicionou pacotes, precisa npm install antes de corrigir imports de pacotes
    # (já feito em _add_dependencies)

    # 4. Retry build
    code2, _, _ = _run_build(root_path)
    if code2 == 0:
        result["success"] = True
        result["corrected"] = True
        result["message"] = "Build OK após auto-correção"
        workflow_log.append("✅ Auto-correção: build OK após correções")
    else:
        result["message"] = "Build ainda falha após auto-correção"
        workflow_log.append("⚠️ Auto-correção: build ainda falha")

    return result
