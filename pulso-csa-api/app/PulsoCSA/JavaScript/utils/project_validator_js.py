#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Validador de Projetos JavaScript❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path


def validate_js_project(root_path: str) -> Dict[str, any]:
    """
    Valida um projeto JavaScript existente e detecta sua estrutura.
    Retorna informações sobre o projeto: tipo, framework, estrutura de pastas, etc.
    """
    if not root_path or not os.path.isdir(root_path):
        return {
            "valid": False,
            "error": "Diretório não encontrado",
            "project_type": None,
            "framework": None,
            "has_typescript": False,
            "has_package_json": False,
            "structure": {},
        }
    
    root = Path(root_path)
    result = {
        "valid": True,
        "project_type": "unknown",
        "framework": None,
        "has_typescript": False,
        "has_package_json": False,
        "has_node_modules": False,
        "structure": {},
        "files": [],
        "dependencies": {},
        "dev_dependencies": {},
    }
    
    # Verifica package.json
    package_json_path = root / "package.json"
    if package_json_path.exists():
        result["has_package_json"] = True
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            result["dependencies"] = package_data.get("dependencies", {})
            result["dev_dependencies"] = package_data.get("devDependencies", {})
            
            # Detecta framework
            deps = {**result["dependencies"], **result["dev_dependencies"]}
            
            if "react" in deps or "react-dom" in deps:
                result["framework"] = "react"
                result["project_type"] = "react-app"
            elif "vue" in deps or "@vue/cli-service" in deps:
                result["framework"] = "vue"
                result["project_type"] = "vue-app"
            elif "@angular/core" in deps or "@angular/cli" in deps:
                result["framework"] = "angular"
                result["project_type"] = "angular-app"
            elif "next" in deps:
                result["framework"] = "next"
                result["project_type"] = "next-app"
            elif "svelte" in deps:
                result["framework"] = "svelte"
                result["project_type"] = "svelte-app"
            else:
                result["project_type"] = "node-app"
            
            # Detecta TypeScript
            if "typescript" in deps or "ts-node" in deps:
                result["has_typescript"] = True
            
        except Exception as e:
            result["error"] = f"Erro ao ler package.json: {str(e)}"
    
    # Verifica node_modules
    if (root / "node_modules").exists():
        result["has_node_modules"] = True
    
    # Verifica tsconfig.json
    if (root / "tsconfig.json").exists():
        result["has_typescript"] = True
    
    # Analisa estrutura de pastas
    structure = {
        "src": False,
        "public": False,
        "components": False,
        "pages": False,
        "routes": False,
        "utils": False,
        "services": False,
        "hooks": False,
        "styles": False,
    }
    
    for item in root.iterdir():
        if item.is_dir():
            name = item.name.lower()
            if name == "src":
                structure["src"] = True
            elif name == "public":
                structure["public"] = True
            elif name in ["components", "component"]:
                structure["components"] = True
            elif name in ["pages", "page", "views", "view"]:
                structure["pages"] = True
            elif name in ["routes", "router", "routers"]:
                structure["routes"] = True
            elif name in ["utils", "util", "helpers", "helper"]:
                structure["utils"] = True
            elif name in ["services", "service", "api"]:
                structure["services"] = True
            elif name in ["hooks", "hook"]:
                structure["hooks"] = True
            elif name in ["styles", "style", "css", "scss"]:
                structure["styles"] = True
    
    result["structure"] = structure
    
    # Lista arquivos principais
    main_files = []
    for ext in [".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte"]:
        for file_path in root.rglob(f"*{ext}"):
            if "node_modules" not in str(file_path):
                rel_path = str(file_path.relative_to(root))
                main_files.append(rel_path)
                if len(main_files) >= 50:  # Limita a 50 arquivos
                    break
        if len(main_files) >= 50:
            break
    
    result["files"] = main_files[:50]
    
    return result


def detect_project_needs(root_path: str, prompt: str) -> List[str]:
    """
    Analisa o projeto e o prompt para detectar o que precisa ser criado/corrigido.
    Retorna lista de necessidades detectadas.
    """
    needs = []
    
    validation = validate_js_project(root_path)
    
    if not validation["valid"]:
        needs.append("criar-estrutura-base")
        return needs
    
    # Verifica se tem package.json
    if not validation["has_package_json"]:
        needs.append("criar-package-json")
    
    # Verifica estrutura básica
    if not validation["structure"]["src"]:
        needs.append("criar-pasta-src")
    
    # Analisa prompt para necessidades específicas
    prompt_lower = prompt.lower()
    
    if "componente" in prompt_lower or "component" in prompt_lower:
        needs.append("criar-componente")
    
    if "rota" in prompt_lower or "route" in prompt_lower or "endpoint" in prompt_lower:
        needs.append("criar-rotas")
    
    if "api" in prompt_lower or "serviço" in prompt_lower or "service" in prompt_lower:
        needs.append("criar-servico")
    
    if "hook" in prompt_lower or "custom hook" in prompt_lower:
        needs.append("criar-hook")
    
    if "estilo" in prompt_lower or "style" in prompt_lower or "css" in prompt_lower:
        needs.append("criar-estilos")
    
    if "teste" in prompt_lower or "test" in prompt_lower:
        needs.append("criar-testes")
    
    if "corrigir" in prompt_lower or "corrige" in prompt_lower or "fix" in prompt_lower:
        needs.append("corrigir-codigo")
    
    if "adicionar" in prompt_lower or "adiciona" in prompt_lower or "add" in prompt_lower:
        needs.append("adicionar-funcionalidade")
    
    return needs
