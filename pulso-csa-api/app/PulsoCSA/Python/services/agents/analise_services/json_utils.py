#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Utilitários JSON para respostas LLM/RAG❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import json
import re
from typing import Any


def extract_json_from_response(raw: str) -> dict | None:
    """
    Extrai JSON de resposta LLM (markdown, texto misto, vazio).
    Retorna dict ou None.
    """
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    brace = text.find("{")
    if brace >= 0:
        depth, end = 0, -1
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
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        try:
            fixed = re.sub(r",\s*}", "}", text)
            fixed = re.sub(r",\s*]", "]", fixed)
            parsed = json.loads(fixed)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None


def is_js_structure(estrutura_arquivos: dict) -> bool:
    """Detecta se a estrutura é de projeto JS/TS/React."""
    if not estrutura_arquivos:
        return False
    js_ext = (".tsx", ".jsx", ".ts", ".js", ".vue")
    for folder, files in estrutura_arquivos.items():
        for f in (files or []) if isinstance(files, list) else []:
            if isinstance(f, str) and any(f.lower().endswith(ext) for ext in js_ext):
                return True
            if f == "package.json" or "src" in str(folder):
                return True
    return False


def is_js_backend(backend_doc: dict) -> bool:
    """Detecta se o backend doc é de projeto JS (pelas chaves em arquivos)."""
    if not backend_doc:
        return False
    arquivos = backend_doc.get("arquivos") or {}
    if not isinstance(arquivos, dict):
        return False
    js_ext = (".tsx", ".jsx", ".ts", ".js", ".vue")
    for key in arquivos:
        if isinstance(key, str) and any(key.lower().endswith(ext) for ext in js_ext):
            return True
    return False
