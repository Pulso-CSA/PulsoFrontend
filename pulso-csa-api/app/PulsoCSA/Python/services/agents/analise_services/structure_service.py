#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Análise da Estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, List, Any, Set
import json
import re
from pathlib import Path

from utils.log_manager import add_log
from app.prompts.loader import load_prompt, get_request_stack
from storage.database.creation_analyse import database_c1 as db_c1
from storage.database.creation_analyse import database_c2 as db_c2


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Funções auxiliares internas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _safe_load_json(raw: str) -> Any:
    """
    Safely loads a JSON string.
    Returns None if not a valid JSON.
    """
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        # Esperado quando raw_data é prompt refinado (texto), não JSON
        return None


def _extract_paths_from_plan_files(plan: Dict[str, Any]) -> Set[str]:
    """
    Extracts file paths from known structural plan keys, such as:
    - novos_arquivos: [{ path: "..." }, ...]
    - arquivos_a_alterar: [{ path: "..." }, ...]
    """
    paths: Set[str] = set()

    for key in ("novos_arquivos", "arquivos_a_alterar"):
        items = plan.get(key) or []
        if not isinstance(items, list):
            continue

        for item in items:
            if isinstance(item, dict) and "path" in item:
                value = str(item["path"]).strip()
                if value:
                    paths.add(value)

    return paths


def _extract_paths_generic(node: Any) -> Set[str]:
    """
    Recursively scans any JSON-like structure looking for values
    that look like file paths.
    """
    paths: Set[str] = set()

    if isinstance(node, dict):
        for value in node.values():
            paths |= _extract_paths_generic(value)
    elif isinstance(node, list):
        for value in node:
            paths |= _extract_paths_generic(value)
    elif isinstance(node, str):
        value = node.strip()
        if not value:
            return paths

        # Heurística mínima para “parece um path”
        if (
            "/" in value
            or "\\" in value
            or value.endswith(
                (
                    ".py",
                    ".js",
                    ".ts",
                    ".tsx",
                    ".jsx",
                    ".json",
                    ".yml",
                    ".yaml",
                    ".toml",
                    ".md",
                    ".txt",
                    ".html",
                    ".css",
                    ".sql",
                )
            )
        ):
            paths.add(value)

    return paths


def _flatten_tree(tree: Dict[str, Any], parent: str = "") -> Dict[str, List[str]]:
    """
    Flattens a nested tree structure into { 'dir': [files...] }.
    Accepts nodes in two general shapes:
      - { "dir": ["file1.py", "file2.py"] }
      - { "dir": { "subdir": ["file.py"] } }
      - { "dir": { "file.py": [], "subdir/": ["file.py"] } }  (file com [] = arquivo no dir)
    """
    flattened: Dict[str, List[str]] = {}

    for key, value in tree.items():
        path = f"{parent}/{key}".strip("/")
        dir_path = path.rstrip("/") or "."

        if isinstance(value, list):
            files = [str(v) for v in value if isinstance(v, str)]
            if files:
                flattened.setdefault(dir_path, [])
                for f in files:
                    if f not in flattened[dir_path]:
                        flattened[dir_path].append(f)
            # lista vazia com key que parece arquivo → arquivo no parent
            elif key and not key.endswith("/") and ("." in key or key == "__init__.py"):
                parent_dir = parent.strip("/") or "."
                flattened.setdefault(parent_dir, [])
                if key not in flattened[parent_dir]:
                    flattened[parent_dir].append(key)

        elif isinstance(value, dict):
            sub_flat = _flatten_tree(value, dir_path)
            for d, files in sub_flat.items():
                flattened.setdefault(d, [])
                for f in files:
                    if f not in flattened[d]:
                        flattened[d].append(f)

        else:
            # Se for um valor simples, assume-se que é um arquivo no diretório "parent"
            if isinstance(value, str):
                file_name = value.strip()
                if file_name:
                    dir_path = path or "."
                    flattened.setdefault(dir_path, [])
                    if file_name not in flattened[dir_path]:
                        flattened[dir_path].append(file_name)

    # Ordena arquivos por diretório para consistência
    for dir_path in flattened:
        flattened[dir_path].sort()

    return flattened


def _normalize_structure_mapping(tree: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Normaliza um mapeamento de estrutura já em forma de árvore
    (estrutura_arquivos) para o formato achatado final:
        { "dir": ["file1.py", "file2.py"] }
    Sem impor pastas fixas, sem forçar 'app/' ou arquivos obrigatórios.
    """
    if not isinstance(tree, dict):
        return {}

    # Caso simples: já esteja no formato { "dir": [files...] }
    if all(isinstance(v, list) for v in tree.values()):
        normalized: Dict[str, List[str]] = {}
        for dir_path, files in tree.items():
            dir_key = str(dir_path).strip() or "."
            file_list = [str(f) for f in files if isinstance(f, str)]
            if file_list:
                # Remove duplicados mantendo ordem
                seen = set()
                filtered: List[str] = []
                for f in file_list:
                    if f not in seen:
                        seen.add(f)
                        filtered.append(f)
                normalized[dir_key] = filtered
        return normalized

    # Caso geral: árvore aninhada
    return _flatten_tree(tree)


def _paths_to_structure(paths: Set[str]) -> Dict[str, List[str]]:
    """
    Converte um conjunto de paths arbitrários em um blueprint plano:
        { "dir": ["file1.py", "file2.py"] }
    """
    estrutura: Dict[str, List[str]] = {}

    for raw in paths:
        if not raw:
            continue

        normalized = raw.replace("\\", "/").strip()
        if not normalized:
            continue

        path_obj = Path(normalized)
        file_name = path_obj.name
        if not file_name:
            continue

        dir_path = str(path_obj.parent).replace("\\", "/") or "."
        estrutura.setdefault(dir_path, [])
        if file_name not in estrutura[dir_path]:
            estrutura[dir_path].append(file_name)

    # Ordena arquivos em cada diretório
    for dir_path in estrutura:
        estrutura[dir_path].sort()

    return estrutura


def _extract_json_from_llm_response(raw: str) -> Any:
    """Extrai e tenta parsear JSON de resposta LLM (markdown, texto misto, JSON malformado)."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    # 1) Bloco markdown ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    # 2) Primeiro bloco { ... } (balanceado)
    brace = text.find("{")
    if brace >= 0:
        depth = 0
        end = -1
        for i in range(brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end >= 0:
            text = text[brace : end + 1]
    # 3) Tenta parsear
    plan = _safe_load_json(text)
    if plan is not None:
        return plan
    # 4) Tenta corrigir vírgulas finais e aspas
    fixed = re.sub(r",\s*}", "}", text)
    fixed = re.sub(r",\s*]", "]", fixed)
    return _safe_load_json(fixed)


def _default_structure_from_prompt(prompt: str) -> Dict[str, List[str]]:
    """Fallback quando o LLM falha. Para API, retorna estrutura corporativa."""
    if _is_api_project(prompt):
        return {
            "models": ["__init__.py", "user_model.py"],
            "services": ["__init__.py", "auth_service.py", "calculator_service.py"],
            "routers": ["__init__.py", "auth_router.py", "calculator_router.py"],
            "tests": ["__init__.py", "test_auth.py", "test_calculator.py"],
            "config": ["__init__.py", "settings.py"],
            ".": ["main.py", "requirements.txt", ".env", "README.md"],
        }
    return {
        ".": ["main.py", "requirements.txt", ".env", "README.md"],
    }


def _is_api_project(refined_prompt: str) -> bool:
    """Detecta se o pedido é para API (Flask, FastAPI, REST)."""
    if not refined_prompt or not refined_prompt.strip():
        return False
    text = refined_prompt.lower()
    return any(kw in text for kw in ("api", "flask", "fastapi", "rest", "rota", "rotas", "login", "endpoint"))


def _ensure_complete_api_structure(
    estrutura: Dict[str, List[str]], refined_prompt: str
) -> Dict[str, List[str]]:
    """
    Para API com login+calculator: garante que a estrutura tenha TODOS os arquivos
    necessários. Mescla com _default_structure_from_prompt para nunca faltar.
    """
    if not _is_api_project(refined_prompt):
        return estrutura
    default = _default_structure_from_prompt(refined_prompt)
    merged: Dict[str, List[str]] = {}
    all_keys = set(estrutura.keys()) | set(default.keys())
    for k in all_keys:
        current = list(estrutura.get(k, []) or [])
        extra = [f for f in (default.get(k, []) or []) if f not in current]
        merged[k] = list(dict.fromkeys(current + extra))
    return merged


def _enforce_corporate_structure(
    estrutura: Dict[str, List[str]], refined_prompt: str
) -> Dict[str, List[str]]:
    """
    Quando a estrutura está flat (só ".") e o projeto é API, transforma para
    models/, services/, routers/, tests/, config/ — padrão corporativo.
    """
    if not _is_api_project(refined_prompt):
        return estrutura
    has_corporate = any(k in estrutura for k in ("models", "services", "routers", "routes"))
    prompt_lower = refined_prompt.lower()
    has_auth_in_prompt = any(k in prompt_lower for k in ("login", "criação de conta", "create_account", "cadastro", "auth"))
    has_calc_in_prompt = any(k in prompt_lower for k in ("bhaskara", "pitagoras", "pitágoras", "operações", "operacoes"))
    # Mesmo com estrutura corporativa, garantir arquivos de auth e calculator quando o prompt pedir
    if has_corporate:
        updated = dict(estrutura)
        if has_auth_in_prompt:
            routers = list(updated.get("routers", []) or [])
            if "auth_router.py" not in routers:
                routers.append("auth_router.py")
                updated["routers"] = routers
            services = list(updated.get("services", []) or [])
            if "auth_service.py" not in services:
                services.append("auth_service.py")
                updated["services"] = services
            models = list(updated.get("models", []) or [])
            if "user_model.py" not in models:
                models.append("user_model.py")
                updated["models"] = models
            config = list(updated.get("config", []) or [])
            if "settings.py" not in config:
                config.append("settings.py")
                updated["config"] = config
        if has_calc_in_prompt:
            routers = list(updated.get("routers", []) or [])
            if "calculator_router.py" not in routers:
                routers.append("calculator_router.py")
                updated["routers"] = routers
            services = list(updated.get("services", []) or [])
            if "calculator_service.py" not in services:
                services.append("calculator_service.py")
                updated["services"] = services
        return updated
    root_files = list(estrutura.get(".", []) or estrutura.get("", []))
    # Se tem "app" mas não corporate, coletar arquivos de app/ e . para redistribuir
    if "app" in estrutura and isinstance(estrutura.get("app"), list):
        root_files = list(estrutura.get("app", [])) + root_files
    if not root_files:
        root_files = ["main.py", "requirements.txt", ".env", "README.md"]
    # Mapear arquivos flat para pastas corporativas
    models_files = ["__init__.py"]
    services_files = ["__init__.py"]
    routers_files = ["__init__.py"]
    tests_files = ["__init__.py"]
    config_files = ["__init__.py"]
    root_keep = []
    for f in root_files:
        if f in ("__init__.py", "README.md", ".env", "docker-compose.yml", "Dockerfile"):
            if f == "__init__.py":
                continue
            root_keep.append(f)
        elif "model" in f.lower() or "schema" in f.lower():
            models_files.append(f)
        elif "service" in f.lower() or "auth" in f.lower() and "router" not in f.lower():
            services_files.append(f)
        elif "router" in f.lower() or "route" in f.lower() or "auth" in f.lower():
            routers_files.append(f)
        elif f.startswith("test_") or "test" in f.lower():
            tests_files.append(f)
        elif "setting" in f.lower() or "config" in f.lower():
            config_files.append(f)
        elif f in ("main.py", "requirements.txt", "app.py"):
            root_keep.append(f)
        else:
            services_files.append(f)
    # Garantir routers e services separados (não colocar router em services)
    to_move = [f for f in services_files if "router" in f.lower() or "route" in f.lower()]
    for f in to_move:
        services_files.remove(f)
        routers_files.append(f)
    # Para API com auth + cálculos: garantir auth_router e calculator_router
    has_auth = any("auth" in f.lower() for f in services_files + root_files)
    has_calc = any("calc" in f.lower() or "bhaskara" in refined_prompt.lower() or "pitagoras" in refined_prompt.lower() for f in services_files + root_files)
    if has_auth and "auth_router.py" not in routers_files:
        routers_files.append("auth_router.py")
    if (has_calc or any("calc" in f.lower() for f in services_files)) and "calculator_router.py" not in routers_files:
        routers_files.append("calculator_router.py")
    if has_auth and "user_model.py" not in models_files:
        models_files.append("user_model.py")
    result = {
        "models": list(dict.fromkeys(models_files)),
        "services": list(dict.fromkeys(services_files)),
        "routers": list(dict.fromkeys(routers_files)),
        "tests": list(dict.fromkeys(tests_files)),
        "config": list(dict.fromkeys(config_files)),
        ".": list(dict.fromkeys(root_keep)) or ["main.py", "requirements.txt", ".env", "README.md"],
    }
    return {k: v for k, v in result.items() if v}


def _default_structure_js(refined_prompt: str) -> Dict[str, List[str]]:
    """Fallback para projetos JavaScript/TypeScript/React quando o LLM falha."""
    return {
        "src": ["index.tsx", "App.tsx", "App.css"],
        "src/components": ["LoginForm.tsx", "AuthContext.tsx"],
        "src/pages": ["LoginPage.tsx"],
        "src/services": ["authService.ts"],
        "src/hooks": ["useAuth.ts"],
        ".": ["package.json", "vite.config.ts", "tsconfig.json", "index.html", ".env", ".gitignore", "README.md"],
    }


def _generate_structure_via_llm(id_requisicao: str, refined_prompt: str) -> Dict[str, List[str]]:
    """
    Gera blueprint de estrutura via LLM quando a pasta está vazia ou não há JSON de plano.
    Usa o prompt structure_blueprint para criar estrutura modular, organizada, documentada e testada.
    Fallback: estrutura padrão quando JSON inválido.
    Respeita stack (javascript) para gerar estrutura JS/React em vez de Python.
    """
    from app.prompts.loader import get_request_stack
    stack = get_request_stack() or "python"
    is_js = stack == "javascript"

    if not refined_prompt or not refined_prompt.strip():
        return _default_structure_js("") if is_js else _default_structure_from_prompt("")

    # Fast path JS: prompts curtos ou com keywords de criação usam estrutura padrão sem LLM (~2–3 min economizados)
    lower = refined_prompt.strip().lower()
    js_fast_keywords = ("criar", "implementar", "desenvolver", "gerar", "sistema de login", "sistema", "login", "app", "formulário", "formulario", "página", "pagina", "dashboard", "crud", "cadastro", "autenticação", "autenticacao")
    if is_js and (len(refined_prompt.strip()) < 500 and any(kw in lower for kw in js_fast_keywords)):
        add_log("info", "generate_structure_blueprint: fast path JS, usando estrutura padrão", "structure_blueprint")
        return _default_structure_js(refined_prompt)

    # openai está em api/app/core/openai/ (compartilhado)
    try:
        from core.openai.openai_client import get_openai_client
    except ImportError:
        from app.core.openai.openai_client import get_openai_client
    
    sys_prompt_js = (
        "Responda SOMENTE com um objeto JSON válido. "
        "Formato: {\"src\": [\"App.tsx\", \"index.tsx\"], \"src/components\": [\"LoginForm.tsx\"], \".\": [\"package.json\", \"vite.config.ts\", \".env\"]}. "
        "Use .tsx, .ts, .jsx, .js, .vue. NUNCA use main.py, requirements.txt ou estrutura Python. Sem markdown."
    )
    sys_prompt_py = (
        "Responda SOMENTE com um objeto JSON válido. "
        "Formato: {\"app\": [\"main.py\", ...], \".\": [\"requirements.txt\", \".env\"]}. Sem markdown."
    )
    system_prompt = sys_prompt_js if is_js else sys_prompt_py

    try:
        template = load_prompt("analyse/structure_blueprint")
        prompt_text = template.replace("{context}", "Pasta vazia – criar projeto do zero conforme pedido do usuário.")
        prompt_text = prompt_text.replace("{input}", refined_prompt.strip())

        client = get_openai_client()
        raw = client.generate_text(
            prompt_text,
            system_prompt=system_prompt,
            use_fast_model=True,
            num_predict=1024,
        )
        default_fn = _default_structure_js if is_js else _default_structure_from_prompt
        enforce_fn = (lambda e, p: e) if is_js else _enforce_corporate_structure

        if not raw:
            add_log("warning", "generate_structure_blueprint: LLM retornou vazio, usando estrutura padrão", "structure_blueprint")
            return enforce_fn(default_fn(refined_prompt), refined_prompt)

        plan = _extract_json_from_llm_response(raw)
        if plan is None:
            add_log("warning", "generate_structure_blueprint: JSON inválido do LLM, usando estrutura padrão", "structure_blueprint")
            return enforce_fn(default_fn(refined_prompt), refined_prompt)
        result = _plan_to_structure(plan)
        if not result:
            return enforce_fn(default_fn(refined_prompt), refined_prompt)
        return enforce_fn(result, refined_prompt)
    except Exception as exc:
        add_log(
            "error",
            f"generate_structure_blueprint: falha ao gerar estrutura via LLM ({exc}), usando padrão",
            "structure_blueprint",
        )
        default_fn = _default_structure_js if is_js else _default_structure_from_prompt
        enforce_fn = (lambda e, p: e) if is_js else _enforce_corporate_structure
        return enforce_fn(default_fn(refined_prompt), refined_prompt)


def _plan_to_structure(plan: Any) -> Dict[str, List[str]]:
    """
    Converte um JSON arbitrário em blueprint de estrutura.

    Suporta, dinamicamente:
    1) JSON com 'estrutura_arquivos' já pronto:
       { "estrutura_arquivos": { "dir": ["file1.py"] } }

    2) JSON do agente estrutural:
       {
         "novos_arquivos": [{ "path": "..." }, ...],
         "arquivos_a_alterar": [{ "path": "..." }, ...]
       }

    3) JSON genérico com paths embutidos em campos arbitrários.
    """
    if not isinstance(plan, dict):
        return {}

    # 1) estrutura_arquivos explícito
    if "estrutura_arquivos" in plan and isinstance(plan["estrutura_arquivos"], dict):
        return _normalize_structure_mapping(plan["estrutura_arquivos"])

    # 2) planos com paths explícitos
    paths = _extract_paths_from_plan_files(plan)

    # 3) se ainda vazio, vasculha todo o JSON
    if not paths:
        paths = _extract_paths_generic(plan)

    if not paths:
        return {}

    return _paths_to_structure(paths)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Função Principal do Serviço❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def generate_structure_blueprint(id_requisicao: str) -> Dict[str, List[str]]:
    """
    Gera o blueprint de estrutura de arquivos de forma 100% dinâmica,
    sem uso de LLM.

    Fluxo:
    1. Busca no C1 um JSON bruto associado à id_requisicao.
       (agente anterior deve persistir o plano/estrutura nesse campo).
    2. Interpreta esse JSON em um dos formatos suportados (1, 2 ou 3).
    3. Converte para o formato plano final:
           { "dir": ["file1.py", "file2.py"] }
    4. Persiste o blueprint em C2 via upsert_blueprint.
    5. Retorna o blueprint para consumo pelos próximos agentes.

    Se o JSON não existir ou não for interpretável, retorna estrutura vazia.
    """

    add_log(
        "info",
        f"generate_structure_blueprint: iniciando criação de blueprint para id_requisicao={id_requisicao}",
        "structure_blueprint",
    )

    # 1) Recupera dado base do C1 (pode ser JSON de plano ou prompt refinado em texto)
    raw_data = db_c1.get_refined_prompt(id_requisicao)
    if not raw_data:
        add_log(
            "warning",
            f"generate_structure_blueprint: nenhum dado base encontrado em C1 para id_requisicao={id_requisicao}",
            "structure_blueprint",
        )
        estrutura_arquivos: Dict[str, List[str]] = {}
    else:
        plan = _safe_load_json(raw_data)
        if plan is not None:
            estrutura_arquivos = _plan_to_structure(plan)
        else:
            stack = get_request_stack() or "python"
            # Fast path: JS + prompt original curto de criação -> usa estrutura padrão sem LLM (~2–3 min mais rápido)
            original_prompt = db_c1.get_original_prompt(id_requisicao) if hasattr(db_c1, "get_original_prompt") else ""
            prompt_para_fast = (original_prompt or str(raw_data))[:500]
            prompt_lower = prompt_para_fast.strip().lower()
            js_fast_keywords = ("criar", "implementar", "desenvolver", "gerar", "sistema", "login", "app", "formulário", "formulario", "página", "pagina", "dashboard", "crud", "cadastro", "autenticação", "autenticacao")
            if stack == "javascript" and prompt_para_fast and len(prompt_para_fast.strip()) < 450:
                if any(kw in prompt_lower for kw in js_fast_keywords) or re.match(r"^(criar|implementar|desenvolver|gerar|faça|fazer)\s+", prompt_lower):
                    add_log("info", "generate_structure_blueprint: fast path JS (prompt criação curto), usando estrutura padrão", "structure_blueprint")
                    estrutura_arquivos = _default_structure_js(str(raw_data)[:500])
                else:
                    add_log("info", "generate_structure_blueprint: gerando estrutura dinâmica via LLM", "structure_blueprint")
                    estrutura_arquivos = _generate_structure_via_llm(id_requisicao, raw_data)
            else:
                add_log("info", "generate_structure_blueprint: gerando estrutura dinâmica via LLM", "structure_blueprint")
                estrutura_arquivos = _generate_structure_via_llm(id_requisicao, raw_data)

    # 2) Persistência no C2
    try:
        db_c2.upsert_blueprint(id_requisicao, estrutura_arquivos)
    except Exception as exc:
        add_log(
            "error",
            f"generate_structure_blueprint: falha ao salvar blueprint no banco ({exc})",
            "structure_blueprint",
        )

    # Garantir estrutura completa (Python API ou JS/React)
    stack = get_request_stack() or "python"
    refined_prompt_text = raw_data if raw_data and _safe_load_json(raw_data) is None else ""
    if stack == "javascript":
        if not estrutura_arquivos and raw_data:
            estrutura_arquivos = _default_structure_js(str(raw_data)[:500])
    elif refined_prompt_text and _is_api_project(refined_prompt_text):
        estrutura_arquivos = _ensure_complete_api_structure(estrutura_arquivos, refined_prompt_text)
    elif not estrutura_arquivos and raw_data:
        estrutura_arquivos = _ensure_complete_api_structure({}, str(raw_data)[:500])

    mensagem = (
        "Blueprint de estrutura criado dinamicamente a partir de JSON de plano."
        if estrutura_arquivos
        else "Nenhum blueprint pôde ser derivado do JSON de plano; estrutura vazia retornada."
    )

    return {
        "id_requisicao": id_requisicao,
        "estrutura_arquivos": estrutura_arquivos,
        "mensagem": mensagem,
    }
