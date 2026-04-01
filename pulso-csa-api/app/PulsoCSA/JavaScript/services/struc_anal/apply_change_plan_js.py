#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Aplicar Plano de Mudanças – JavaScript/TypeScript/React❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any

try:
    from models.struc_anal.struc_anal_models import PlannedFileCreation, PlannedFileSection
except ImportError:
    from app.PulsoCSA.Python.models.struc_anal.struc_anal_models import (
        PlannedFileCreation,
        PlannedFileSection,
    )
from utils.log_manager import add_log

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Stub para arquivos JS/TS/React❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


def _build_file_stub_js(item: PlannedFileCreation, request_id: str) -> str:
    """Gera stub inicial para arquivo JavaScript/TypeScript/React."""
    header = f"// Auto-generated file for {item.path} (request {request_id})\n\n"
    deps = f"// dependencies: {', '.join(item.dependencias)}\n\n" if item.dependencias else ""
    sections = []
    for sec in item.secoes:
        if isinstance(sec, PlannedFileSection):
            sections.append(f"// section: {sec.name} -> {sec.description}")
        else:
            sections.append(f"// section: {sec.get('name')} -> {sec.get('description')}")
    sections_str = "\n".join(sections) + ("\n" if sections else "")

    ext = Path(item.path).suffix.lower()
    if ext in (".tsx", ".jsx"):
        return header + deps + sections_str + "\n// TODO: implementar componente conforme descrição\n"
    if ext == ".ts":
        return header + deps + sections_str + "\n// TODO: implementar conforme descrição\n"
    if ext == ".vue":
        return header + deps + sections_str + "\n<template>\n  <div></div>\n</template>\n<script>\n// TODO: implementar\n</script>\n"
    return header + deps + sections_str + "\n// TODO: implementar conforme descrição\n"


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Aplicar plano ao filesystem❯━━━━━━━━━
#━━━━━━━━━━━━━━


def apply_change_plan_to_filesystem_js(
    root_path: str,
    id_requisicao: str,
    novos_arquivos: List[PlannedFileCreation],
) -> Dict[str, Any]:
    """
    Aplica o plano de mudanças ao filesystem para projetos JavaScript/TypeScript/React.
    Cria arquivos stub (não cria __init__.py).
    """
    try:
        project_root = Path(root_path)
        created_files: List[str] = []
        skipped: List[str] = []
        touched: set = set()

        add_log("info", f"[apply_change_plan_js] Aplicando plano para {id_requisicao}", "apply_change_plan_js")

        for item in novos_arquivos:
            rel = Path(item.path.replace("\\", "/").lstrip("/"))
            final_path = project_root / rel
            final_folder = final_path.parent

            final_folder.mkdir(parents=True, exist_ok=True)
            touched.add(str(final_folder))

            if final_path.exists():
                skipped.append(str(final_path))
                continue

            content = _build_file_stub_js(item, id_requisicao)
            final_path.write_text(content, encoding="utf-8")
            created_files.append(str(final_path))

        add_log(
            "info",
            f"[apply_change_plan_js] Concluído. Criados={len(created_files)} ignorados={len(skipped)}",
            "apply_change_plan_js",
        )

        return {
            "root_path": root_path,
            "created_files": created_files,
            "skipped_existing_files": skipped,
            "touched_dirs": list(touched),
            "message": "Estrutura JS aplicada com sucesso.",
        }
    except Exception as e:
        add_log("error", f"[apply_change_plan_js] Erro: {e}", "apply_change_plan_js")
        return {"erro": str(e), "status": "falha"}
