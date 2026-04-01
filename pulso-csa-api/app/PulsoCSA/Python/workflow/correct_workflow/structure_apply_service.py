#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Builder – Estrutura Dinâmica a partir do Plano❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from storage.database.creation_analyse import database_c2 as db_c2
from storage.database.correct_analyse.autocor_database import save_autocor_snapshot

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Normalização de Nome de Módulo❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def _clean_module_name(raw_name: str) -> str:
    """Remove prefixos/sufixos comuns retornando o stem ‘limpo’."""
    name = raw_name
    for suf in (
        "_router",
        "_service",
        "_model",
        "_models",
        "_utils",
        "_test",
        "_tests",
    ):
        if name.endswith(suf):
            name = name[: -len(suf)]
            break
    for pre in ("test_", "internal_", "debug_", "tmp_", "dev_"):
        if name.startswith(pre):
            name = name[len(pre) :]
            break
    return name or raw_name


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Inferir Nome do Módulo❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def _infer_module(novos: List) -> str:
    if not novos:
        return "module"

    # 1) routers/<subpasta>/file.py  → subpasta
    for it in novos:
        p = Path(str(it.path).replace("\\", "/"))
        parts = p.parts
        if "routers" in parts:
            idx = parts.index("routers")
            if len(parts) > idx + 2:
                return parts[idx + 1]

    # 2) routers/file_router.py  → stem “limpo”
    for it in novos:
        p = Path(str(it.path).replace("\\", "/"))
        parts = p.parts
        if "routers" in parts and len(parts) == parts.index("routers") + 2:
            return _clean_module_name(p.stem)

    # 3) qualquer outro arquivo → stem limpo
    first = Path(str(novos[0].path).replace("\\", "/"))
    return _clean_module_name(first.stem)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Detectar Roles Existentes❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def _find_roles(root: str) -> Dict[str, str]:
    base = Path(root)
    roles = ["models", "services", "utils", "tests", "routers"]
    found: Dict[str, str] = {}
    for role in roles:
        for candidate in (base / "api" / "app" / role, base / role):
            if candidate.exists():
                found[role] = str(candidate)
                break
    return found


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Gerar Arquivos Complementares❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def _generate_complements(
    module: str,
    roles: Dict[str, str],
    novos: List,
    existentes: List[str],
):
    """
    Só cria stubs faltantes para *models*, *services* e *tests*:
    - evita ‘utils’ automáticos
    - não duplica versões flat/modular existentes
    - se o diretório já termina em <module>_role, não cria sub-pasta extra
    """
    generated = []
    base_paths = {n.path for n in novos}
    from models.struc_anal.struc_anal_models import PlannedFileCreation

    for role in ("models", "services", "tests"):  # utils fora
        directory = roles.get(role)
        if not directory:
            continue

        folder = f"{module}_{role}"
        file_name = f"{module}_{role}.py"

        dir_path = Path(directory)
        # Se já segue padrão module/<module>_role, use esse diretório
        if dir_path.name == folder:
            flat_candidate = dir_path / file_name
            candidate_rel = flat_candidate
        else:
            candidate_rel = dir_path / folder / file_name

        try:
            project_root = dir_path.parents[2]
            rel = candidate_rel.relative_to(project_root)
        except Exception:
            rel = candidate_rel

        rel_str = str(rel).replace("\\", "/")
        if rel_str in base_paths or rel_str in existentes:
            continue

        generated.append(
            PlannedFileCreation(
                path=rel_str,
                tipo_arquivo="python",
                descricao_conceitual=f"Auto-generated {role} for module '{module}'",
                secoes=[],
                dependencias=[],
            )
        )
    return generated


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Blueprint – mapear estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def build_structure_from_plan(
    id_requisicao: str,
    novos_arquivos: List,
    arquivos_a_alterar: List,
) -> Dict[str, List[str]]:
    estrutura: Dict[str, List[str]] = {}
    for it in [*novos_arquivos, *arquivos_a_alterar]:
        full = str(it.path).replace("\\", "/")
        folder, file = "/".join(full.split("/")[:-1]).strip(), full.split("/")[-1]
        estrutura.setdefault(folder, []).append(file)

    try:
        db_c2.upsert_blueprint(id_requisicao, estrutura)
    except Exception as exc:
        print(f"⚠️ Erro ao salvar blueprint: {exc}")

    return estrutura


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮EXPANSOR DE PLANO❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def expand_plan_with_missing_files(
    id_requisicao: str,
    root_path: str,
    novos: List,
    alterar: List,
):
    module = _infer_module(novos)
    roles = _find_roles(root_path)

    existentes_fs: List[str] = []
    for curr, _, files in os.walk(root_path):
        for f in files:
            if f.endswith(".py"):
                try:
                    rel = Path(curr, f).relative_to(root_path)
                except Exception:
                    rel = Path(curr, f)
                existentes_fs.append(str(rel).replace("\\", "/"))

    extras = _generate_complements(module, roles, novos, existentes_fs)

    save_autocor_snapshot(
        id_requisicao,
        {
            "root_path": root_path,
            "module": module,
            "roles_detected": roles,
            "original_new_files": [n.path for n in novos],
            "generated_complements": [n.path for n in extras],
        },
    )
    return novos + extras


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Alias de compatibilidade❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

apply_blueprint_tree = build_structure_from_plan
