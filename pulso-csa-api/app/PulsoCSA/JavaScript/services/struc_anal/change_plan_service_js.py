#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Change Plan para JavaScript/TypeScript/React❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

try:
    from core.openai.openai_client import get_openai_client, OpenAIClient
except ImportError:
    from app.core.openai.openai_client import get_openai_client, OpenAIClient

try:
    from models.struc_anal.struc_anal_models import (
        ScannedProject,
        PlannedFileCreation,
        PlannedFileUpdate,
        PlannedFileSection,
    )
except ImportError:
    from app.PulsoCSA.Python.models.struc_anal.struc_anal_models import (
        ScannedProject,
        PlannedFileCreation,
        PlannedFileUpdate,
        PlannedFileSection,
    )

from utils.log_manager import add_log

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Configurações❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

MAX_CHARS_PER_CHUNK = 4000
MAX_PREVIEW_LINES = 80
OUTPUT_HARD_LIMIT = (
    "⚠ IMPORTANTE: Sua resposta DEVE ter no máximo 200 palavras. "
    "SEMPRE respeite esse limite. NUNCA ultrapasse."
)

RELEVANT_ROLES_JS = {
    "component", "page", "router", "service", "hook", "store", "utils", "core", "test",
}

MAX_STRUCTURE_FILES = 80
MAX_FILES_PER_DIR_IN_CONTEXT = 3
MAX_RESUMO_CHARS = 2800
MAX_ESTRUTURA_CONTEXT_CHARS = 2400

CHANGE_PLAN_CACHE_TTL_SEC = int(os.environ.get("CHANGE_PLAN_CACHE_TTL_SEC", "45"))
CHANGE_PLAN_CACHE_MAX = 100
_change_plan_cache: Dict[str, Tuple[float, str, List, List]] = {}
_change_plan_cache_lock = threading.Lock()


def _change_plan_cache_key(prompt: str, root_path: str, num_files: int) -> str:
    return hashlib.sha256(f"{(prompt or '').strip()}|{root_path}|{num_files}".encode()).hexdigest()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Chunking e Contexto❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def build_llm_chunks_from_project_js(scanned: ScannedProject) -> List[str]:
    """Monta chunks para o LLM a partir do projeto escaneado."""
    arquivos_relevantes = [f for f in scanned.arquivos if f.papel in RELEVANT_ROLES_JS]
    if not arquivos_relevantes:
        arquivos_relevantes = scanned.arquivos

    chunks: List[str] = []
    current_chunk = ""

    for f in arquivos_relevantes:
        preview_lines = f.conteudo.splitlines()[:MAX_PREVIEW_LINES]
        preview = "\n".join(preview_lines)
        entry = (
            f"# FILE: {f.path}\n"
            f"# papel_detectado: {f.papel}\n"
            f"{preview}\n\n"
        )
        if len(entry) > MAX_CHARS_PER_CHUNK:
            entry = entry[:MAX_CHARS_PER_CHUNK]
        if len(current_chunk) + len(entry) > MAX_CHARS_PER_CHUNK and current_chunk:
            chunks.append(current_chunk)
            current_chunk = entry
        else:
            current_chunk += entry

    if current_chunk.strip():
        chunks.append(current_chunk)
    return chunks


def build_existing_paths_context_js(scanned: ScannedProject) -> str:
    """Snapshot dinâmico da estrutura existente (diretórios e arquivos)."""
    dirs_map = {}
    total_files_counted = 0

    for f in scanned.arquivos:
        rel = os.path.relpath(f.path, scanned.root_path).replace("\\", "/")
        dir_name = os.path.dirname(rel) or "."
        file_name = os.path.basename(rel)
        if dir_name not in dirs_map:
            dirs_map[dir_name] = []
        if len(dirs_map[dir_name]) < MAX_FILES_PER_DIR_IN_CONTEXT:
            dirs_map[dir_name].append(file_name)
            total_files_counted += 1
        if total_files_counted >= MAX_STRUCTURE_FILES:
            break

    lines = ["Estrutura atual (amostra de diretórios e arquivos):"]
    for dir_name in sorted(dirs_map.keys()):
        files_sample = ", ".join(dirs_map[dir_name])
        lines.append(f"- {dir_name}: {files_sample}")
    return "\n".join(lines)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Chamada LLM❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def safe_llm_call_js(
    client: OpenAIClient,
    user_prompt: str,
    system_prompt: str,
    use_fast_model: bool = False,
) -> str:
    """Chamada LLM com retry."""
    retries = 3
    delay = 1
    final_prompt = f"{user_prompt}\n\n{OUTPUT_HARD_LIMIT}"
    timeout_sec = int(os.getenv("CHANGE_PLAN_LLM_TIMEOUT_SEC", "120"))

    for _ in range(retries):
        resp = client.generate_text(
            final_prompt, system_prompt, use_fast_model=use_fast_model, timeout_override=timeout_sec
        )
        if "Erro ao gerar texto" not in resp:
            return resp
        time.sleep(delay)
        delay *= 2
    return "Erro ao gerar texto com OpenAI após múltiplas tentativas."


def consolidate_chunks_js(
    chunks_analysis: List[str], prompt: str, resumo_base: str
) -> str:
    """Consolida resumos parciais em um resumo global."""
    client = get_openai_client()
    if not chunks_analysis:
        return resumo_base
    if all("Erro ao gerar texto com OpenAI" in r for r in chunks_analysis):
        return resumo_base

    system_prompt = (
        "Você é um analista sênior de arquitetura de software JavaScript/TypeScript/React. "
        "Receberá resumos parciais de trechos do sistema e deve consolidar em um ÚNICO RESUMO FINAL curto."
    )
    joined = "\n\n---\n".join(chunks_analysis)
    question = (
        f"Resumos parciais:\n{joined}\n\n"
        f"Objetivo do usuário:\n{prompt}\n\n"
        f"Produza um ÚNICO RESUMO FINAL do sistema, sem bullets, em texto corrido."
    )
    resumo = safe_llm_call_js(client, question, system_prompt, use_fast_model=True)
    if "Erro ao gerar texto com OpenAI" in resumo:
        return resumo_base
    return resumo.strip()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Parse JSON do Plano❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def parse_plan_json_js(raw: str) -> Tuple[List[PlannedFileCreation], List[PlannedFileUpdate]]:
    """Converte JSON do LLM em modelos Pydantic."""
    try:
        data = json.loads(raw)
    except Exception as e:
        add_log("error", f"[change_plan_js] Falha ao parsear JSON: {e}", "change_plan_js")
        return [], []

    novos_raw = data.get("novos_arquivos", []) or []
    alterar_raw = data.get("arquivos_a_alterar", []) or []
    novos: List[PlannedFileCreation] = []
    alterar: List[PlannedFileUpdate] = []

    for item in novos_raw:
        try:
            if "secoes" not in item:
                item["secoes"] = []
            item["secoes"] = [
                PlannedFileSection(**sec).model_dump() if not isinstance(sec, dict) else sec
                for sec in item["secoes"]
            ]
            novos.append(PlannedFileCreation(**item))
        except Exception as e:
            add_log("error", f"[change_plan_js] PlannedFileCreation: {e}", "change_plan_js")

    for item in alterar_raw:
        try:
            alterar.append(PlannedFileUpdate(**item))
        except Exception as e:
            add_log("error", f"[change_plan_js] PlannedFileUpdate: {e}", "change_plan_js")

    return novos, alterar


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Filtro de Paths (permite src/ para projetos JS)❯━━━━━━━━━
#━━━━━━━━━━━━━━

def filter_plan_with_existing_paths_js(
    scanned: ScannedProject,
    novos: List[PlannedFileCreation],
    alterar: List[PlannedFileUpdate],
) -> Tuple[List[PlannedFileCreation], List[PlannedFileUpdate]]:
    """
    Filtra sugestões do LLM.
    Para novos: permite diretórios existentes OU src/ (comum em projetos JS).
    Para alterar: arquivo deve existir.
    """
    existing_files = set()
    existing_dirs = set()

    for f in scanned.arquivos:
        rel = os.path.relpath(f.path, scanned.root_path).replace("\\", "/")
        existing_files.add(rel)
        dir_name = os.path.dirname(rel) or "."
        existing_dirs.add(dir_name)

    root_path = scanned.root_path
    if os.path.isdir(os.path.join(root_path, "src")):
        existing_dirs.add("src")
        existing_dirs.add(".")
    if os.path.isdir(root_path):
        existing_dirs.add(".")

    filtered_new: List[PlannedFileCreation] = []
    for item in novos:
        rel = item.path.replace("\\", "/")
        parent_dir = os.path.dirname(rel) or "."
        allowed = parent_dir in existing_dirs
        if not allowed and parent_dir:
            parts = parent_dir.split("/")
            for i in range(1, len(parts) + 1):
                prefix = "/".join(parts[:i])
                if prefix in existing_dirs:
                    allowed = True
                    break
        if allowed or parent_dir == ".":
            filtered_new.append(item)
        else:
            add_log("warning", f"[change_plan_js] Ignorando novo arquivo fora de dirs existentes: {item.path}", "change_plan_js")

    filtered_update: List[PlannedFileUpdate] = []
    for item in alterar:
        rel = item.path.replace("\\", "/")
        if rel in existing_files:
            filtered_update.append(item)
        else:
            add_log("warning", f"[change_plan_js] Ignorando alteração em arquivo inexistente: {item.path}", "change_plan_js")

    return filtered_new, filtered_update


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Geração do Plano❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def generate_change_plan_js(
    log_type: str,
    scanned: ScannedProject,
    prompt: str,
) -> Tuple[str, List[PlannedFileCreation], List[PlannedFileUpdate]]:
    """
    Gera resumo do sistema e plano de mudanças (novos arquivos / alterar)
    para projetos JavaScript/TypeScript/React.
    """

    add_log(log_type, f"[change_plan_js] Gerando plano para {scanned.id_requisicao}", "change_plan_js")

    cache_key = _change_plan_cache_key(prompt, scanned.root_path, len(scanned.arquivos))
    with _change_plan_cache_lock:
        now = time.time()
        if cache_key in _change_plan_cache:
            ts, c_resumo, c_novos, c_alterar = _change_plan_cache[cache_key]
            if now - ts <= CHANGE_PLAN_CACHE_TTL_SEC:
                return c_resumo, c_novos, c_alterar
            del _change_plan_cache[cache_key]

    client = get_openai_client()

    chunks = build_llm_chunks_from_project_js(scanned)
    system_prompt_chunk = (
        "Você está analisando um trecho de um sistema JavaScript/TypeScript/React. "
        "Descreva de forma concisa QUAL PAPEL esse trecho cumpre "
        "(ex: componente React, página, rota, serviço, hook, store, utilitário)."
    )

    def _analyze_chunk(ch: str) -> str:
        return safe_llm_call_js(client, ch, system_prompt_chunk, use_fast_model=True)

    max_workers = min(len(chunks), 8) if chunks else 1
    if max_workers <= 1:
        partial_results = [safe_llm_call_js(client, ch, system_prompt_chunk, use_fast_model=True) for ch in chunks]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_analyze_chunk, ch): i for i, ch in enumerate(chunks)}
            results = [None] * len(chunks)
            for fut in as_completed(futures):
                i = futures[fut]
                try:
                    results[i] = fut.result()
                except Exception:
                    results[i] = "Erro ao gerar texto com OpenAI após múltiplas tentativas."
            partial_results = results

    resumo_base = scanned.resumo_sistema or ""
    resumo_sistema = consolidate_chunks_js(partial_results, prompt, resumo_base)

    estrutura_context = build_existing_paths_context_js(scanned)

    system_prompt_plan = (
        "Você é um arquiteto de software especialista em JavaScript/TypeScript/React. "
        "Com base no resumo do sistema, na estrutura atual e no objetivo do usuário, "
        "retorne APENAS um JSON VÁLIDO com dois campos de nível raiz:\n"
        "  - 'novos_arquivos': lista de objetos com:\n"
        "      path (string, ex: src/components/MeuComponente.tsx),\n"
        "      tipo_arquivo (string, ex: component, page, service, hook),\n"
        "      descricao_conceitual (string),\n"
        "      secoes (lista de { name, description }),\n"
        "      dependencias (lista de strings)\n"
        "  - 'arquivos_a_alterar': lista de objetos com:\n"
        "      path (string),\n"
        "      trechos_atuais_relevantes (string),\n"
        "      descricao_mudanca (string),\n"
        "      impacto (string)\n"
        "Regras:\n"
        "1) Use SOMENTE diretórios existentes na estrutura fornecida (ex: src, src/components).\n"
        "2) Para arquivos_a_alterar, use apenas caminhos que JÁ EXISTEM.\n"
        "3) Responda SOMENTE o JSON, sem explicações."
    )

    resumo_trunc = resumo_sistema[:MAX_RESUMO_CHARS] + ("..." if len(resumo_sistema) > MAX_RESUMO_CHARS else "")
    estrutura_trunc = estrutura_context[:MAX_ESTRUTURA_CONTEXT_CHARS] + ("..." if len(estrutura_context) > MAX_ESTRUTURA_CONTEXT_CHARS else "")
    plan_prompt = (
        f"RESUMO DO SISTEMA:\n{resumo_trunc}\n\n"
        f"OBJETIVO DO USUÁRIO:\n{prompt}\n\n"
        f"ESTRUTURA ATUAL:\n{estrutura_trunc}\n\n"
        f"Gere o JSON solicitado."
    )

    plan_raw = safe_llm_call_js(client, plan_prompt, system_prompt_plan)

    if "Erro ao gerar texto com OpenAI" in plan_raw:
        add_log("error", "[change_plan_js] LLM falhou ao gerar JSON, retornando listas vazias.", "change_plan_js")
        return resumo_sistema, [], []

    novos, alterar = parse_plan_json_js(plan_raw)
    novos_filtrados, alterar_filtrados = filter_plan_with_existing_paths_js(
        scanned=scanned, novos=novos, alterar=alterar
    )

    with _change_plan_cache_lock:
        if len(_change_plan_cache) >= CHANGE_PLAN_CACHE_MAX:
            by_ts = sorted(_change_plan_cache.items(), key=lambda x: x[1][0])
            for k, _ in by_ts[: CHANGE_PLAN_CACHE_MAX // 2]:
                del _change_plan_cache[k]
        _change_plan_cache[cache_key] = (time.time(), resumo_sistema, novos_filtrados, alterar_filtrados)

    add_log(log_type, f"[change_plan_js] Plano: {len(novos_filtrados)} novos, {len(alterar_filtrados)} a alterar", "change_plan_js")
    return resumo_sistema, novos_filtrados, alterar_filtrados
