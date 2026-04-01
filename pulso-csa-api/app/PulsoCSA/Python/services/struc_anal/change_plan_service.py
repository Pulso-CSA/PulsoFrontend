#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client, OpenAIClient
except ImportError:
    from app.core.openai.openai_client import get_openai_client, OpenAIClient
from models.struc_anal.struc_anal_models import (
    ScannedProject,
    PlannedFileCreation,
    PlannedFileUpdate,
    PlannedFileSection,
)
from utils.log_manager import add_log

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Configurações❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# Tamanho máximo de um chunk enviado ao LLM (em caracteres)
MAX_CHARS_PER_CHUNK = 4000

# Número máximo de linhas por arquivo utilizadas no contexto do LLM
MAX_PREVIEW_LINES = 80

# Limite duro de palavras para forçar respostas compactas
OUTPUT_HARD_LIMIT = (
    "⚠ IMPORTANTE: Sua resposta DEVE ter no máximo 200 palavras. "
    "SEMPRE respeite esse limite. NUNCA ultrapasse."
)

# Papéis considerados estruturais para o LLM
RELEVANT_ROLES = {
    "router",
    "service",
    "model",
    "agent",
    "workflow",
    "database",
    "core",
}

# Limites para amostragem de estrutura (para continuar dinâmico sem estourar tokens)
MAX_STRUCTURE_FILES = 80
MAX_FILES_PER_DIR_IN_CONTEXT = 3
# Limites de contexto enviado ao LLM no plano final (menos tokens = mais rápido e barato)
MAX_RESUMO_CHARS = 2800
MAX_ESTRUTURA_CONTEXT_CHARS = 2400

# Cache do plano de mudanças: (timestamp, (resumo, novos, alterar)). TTL 45s.
CHANGE_PLAN_CACHE_TTL_SEC = int(os.environ.get("CHANGE_PLAN_CACHE_TTL_SEC", "45"))
CHANGE_PLAN_CACHE_MAX = 100
_change_plan_cache: Dict[str, Tuple[float, str, List, List]] = {}
_change_plan_cache_lock = threading.Lock()


def _change_plan_cache_key(prompt: str, root_path: str, num_files: int) -> str:
    return hashlib.sha256(f"{ (prompt or '').strip() }|{ root_path }|{ num_files }".encode()).hexdigest()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Chunking de Arquivos❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def build_llm_chunks_from_project(scanned: ScannedProject) -> List[str]:
    """
    Build textual chunks for the LLM from the scanned project.
    Each chunk contains metadata + preview of several files,
    respecting the max chars per chunk.
    """
    arquivos_relevantes = [f for f in scanned.arquivos if f.papel in RELEVANT_ROLES]
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


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Snapshot Dinâmico da Estrutura❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def build_existing_paths_context(scanned: ScannedProject) -> str:
    """
    Build a dynamic, project-specific snapshot of existing directories and files.
    This is used ONLY as context for the LLM to avoid inventing non-existent paths.
    Completely dynamic: works for any project layout.
    """
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

    lines = ["Estrutura atual (amostra dinâmica de diretórios e arquivos):"]
    for dir_name in sorted(dirs_map.keys()):
        files_sample = ", ".join(dirs_map[dir_name])
        lines.append(f"- {dir_name}: {files_sample}")

    return "\n".join(lines)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Chamada LLM com Retry❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def safe_llm_call(
    client: OpenAIClient,
    user_prompt: str,
    system_prompt: str,
    use_fast_model: bool = False,
) -> str:
    """
    Wraps LLM calls with small retry and stable error message.
    use_fast_model: usa OPENAI_MODEL_FAST para economia (chunks, consolidação).
    """
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


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Consolidação dos Chunks❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def consolidate_chunks(chunks_analysis: List[str], prompt: str, resumo_base: str) -> str:
    """
    Consolidates partial summaries into a single global system summary.
    In case of error, returns the programmatic summary as fallback.
    """
    client = get_openai_client()

    if not chunks_analysis:
        return resumo_base

    if all("Erro ao gerar texto com OpenAI" in r for r in chunks_analysis):
        return resumo_base

    system_prompt = (
        "Você é um analista sênior de arquitetura de software. "
        "Receberá resumos parciais de vários trechos do sistema "
        "e deve consolidar tudo em um único RESUMO FINAL curto e objetivo "
        "sobre o funcionamento do sistema como um todo."
    )

    joined = "\n\n---\n".join(chunks_analysis)

    question = (
        f"A seguir estão resumos parciais de trechos estruturais do sistema:\n{joined}\n\n"
        f"Objetivo atual do usuário:\n{prompt}\n\n"
        f"Produza um ÚNICO RESUMO FINAL do sistema, sem bullets, em texto corrido."
    )

    resumo = safe_llm_call(client, question, system_prompt, use_fast_model=True)

    if "Erro ao gerar texto com OpenAI" in resumo:
        return resumo_base

    return resumo.strip()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Parse do JSON de Plano❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def parse_plan_json(raw: str) -> Tuple[List[PlannedFileCreation], List[PlannedFileUpdate]]:
    """
    Converts raw JSON from LLM into Pydantic models.
    Any error → returns empty lists.
    """
    try:
        data = json.loads(raw)
    except Exception as e:
        add_log("error", f"Failed to parse plan JSON: {e}", "struc_anal_plan")
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
            add_log("error", f"Failed to parse PlannedFileCreation: {e}", "struc_anal_plan")

    for item in alterar_raw:
        try:
            alterar.append(PlannedFileUpdate(**item))
        except Exception as e:
            add_log("error", f"Failed to parse PlannedFileUpdate: {e}", "struc_anal_plan")

    return novos, alterar


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Filtro Dinâmico de Paths❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def filter_plan_with_existing_paths(
    scanned: ScannedProject,
    novos: List[PlannedFileCreation],
    alterar: List[PlannedFileUpdate],
) -> Tuple[List[PlannedFileCreation], List[PlannedFileUpdate]]:
    """
    Filters LLM suggestions so that:
    - new files are only allowed inside directories that already exist in the project;
    - files to update must already exist in the scanned project.

    This keeps the behavior 100% dynamic, based on the scanned structure,
    and avoids inventing non-existent directories or files.
    """
    existing_files = set()
    existing_dirs = set()

    for f in scanned.arquivos:
        rel = os.path.relpath(f.path, scanned.root_path).replace("\\", "/")
        existing_files.add(rel)
        dir_name = os.path.dirname(rel) or "."
        existing_dirs.add(dir_name)

    filtered_new: List[PlannedFileCreation] = []
    for item in novos:
        rel = item.path.replace("\\", "/")
        parent_dir = os.path.dirname(rel) or "."
        if parent_dir in existing_dirs:
            filtered_new.append(item)
        else:
            add_log(
                "warning",
                f"Dropping suggested new file outside existing dirs: {item.path}",
                "struc_anal_plan",
            )

    filtered_update: List[PlannedFileUpdate] = []
    for item in alterar:
        rel = item.path.replace("\\", "/")
        if rel in existing_files:
            filtered_update.append(item)
        else:
            add_log(
                "warning",
                f"Dropping suggested update for non-existing file: {item.path}",
                "struc_anal_plan",
            )

    return filtered_new, filtered_update


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Geração do Plano (arquivos + mudanças)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
def generate_change_plan(
    log_type: str,
    scanned: ScannedProject,
    prompt: str,
) -> Tuple[str, List[PlannedFileCreation], List[PlannedFileUpdate]]:
    """
    Generate, in a fully dynamic way, a global system summary and a structural
    impact plan (files to create and files to update) based on ALL scanned files,
    respecting model token limits via chunking.

    This function:
    - DOES NOT create or modify any file;
    - only returns analysis (JSON) for future agents to implement.
    """

    add_log(
        log_type,
        f"Generating change plan for request {scanned.id_requisicao}",
        "struc_anal_plan",
    )

    cache_key = _change_plan_cache_key(prompt, scanned.root_path, len(scanned.arquivos))
    with _change_plan_cache_lock:
        now = time.time()
        if cache_key in _change_plan_cache:
            ts, c_resumo, c_novos, c_alterar = _change_plan_cache[cache_key]
            if now - ts <= CHANGE_PLAN_CACHE_TTL_SEC:
                return c_resumo, c_novos, c_alterar
            del _change_plan_cache[cache_key]

    client = get_openai_client()

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━❮1. Chunks a partir do projeto escaneado (paralelo + modelo fast)❯━━━━━━━━━
    chunks = build_llm_chunks_from_project(scanned)

    system_prompt_chunk = (
        "Você está analisando um trecho estrutural de um sistema existente. "
        "Descreva, de forma extremamente concisa, QUAL PAPEL esse trecho cumpre "
        "na arquitetura (ex: endpoints HTTP, camada de serviço, persistência, "
        "orquestração de workflows, utilitários, etc.). Não repita código."
    )

    def _analyze_chunk(ch: str) -> str:
        return safe_llm_call(client, ch, system_prompt_chunk, use_fast_model=True)

    partial_results: List[str] = []
    max_workers = min(len(chunks), 8) if chunks else 1
    if max_workers <= 1:
        partial_results = [safe_llm_call(client, ch, system_prompt_chunk, use_fast_model=True) for ch in chunks]
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

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━❮2. Consolida resumos em um resumo global❯━━━━━━━━━
    resumo_base = scanned.resumo_sistema or ""
    resumo_sistema = consolidate_chunks(partial_results, prompt, resumo_base)

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━❮3. Snapshot dinâmico da estrutura existente❯━━━━━━━━━
    estrutura_context = build_existing_paths_context(scanned)

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━❮4. Pede ao LLM o plano JSON❯━━━━━━━━━
    system_prompt_plan = (
        "Você é um arquiteto de software especialista em refatoração incremental. "
        "Com base no resumo do sistema, na estrutura atual e no objetivo do usuário, "
        "retorne APENAS um JSON VÁLIDO com dois campos de nível raiz:\n"
        "  - 'novos_arquivos': lista de objetos com os campos:\n"
        "      path (string),\n"
        "      tipo_arquivo (string),\n"
        "      descricao_conceitual (string),\n"
        "      secoes (lista de objetos { name, description }),\n"
        "      dependencias (lista de strings)\n"
        "  - 'arquivos_a_alterar': lista de objetos com os campos:\n"
        "      path (string),\n"
        "      trechos_atuais_relevantes (string),\n"
        "      descricao_mudanca (string),\n"
        "      impacto (string)\n"
        "Regras OBRIGATÓRIAS:\n"
        "1) Todos os 'path' devem usar SOMENTE diretórios já existentes na estrutura atual fornecida.\n"
        "2) Não invente diretórios raiz novos; se algo não se encaixar, escolha o diretório existente mais coerente.\n"
        "3) Para 'arquivos_a_alterar', use apenas caminhos de arquivos que JÁ EXISTEM.\n"
        "4) Não escreva nenhuma explicação fora do JSON. Responda SOMENTE o JSON."
    )

    resumo_trunc = resumo_sistema[:MAX_RESUMO_CHARS] + ("..." if len(resumo_sistema) > MAX_RESUMO_CHARS else "")
    estrutura_trunc = estrutura_context[:MAX_ESTRUTURA_CONTEXT_CHARS] + ("..." if len(estrutura_context) > MAX_ESTRUTURA_CONTEXT_CHARS else "")
    plan_prompt = (
        f"RESUMO GLOBAL DO SISTEMA:\n{resumo_trunc}\n\n"
        f"OBJETIVO DO USUÁRIO (em linguagem natural):\n{prompt}\n\n"
        f"ESTRUTURA ATUAL (amostra dinâmica de diretórios e arquivos):\n{estrutura_trunc}\n\n"
        f"Com base nisso, gere o JSON solicitado."
    )

    plan_raw = safe_llm_call(client, plan_prompt, system_prompt_plan)

    if "Erro ao gerar texto com OpenAI" in plan_raw:
        add_log(
            "error",
            "LLM failed to generate change plan JSON, returning empty lists.",
            "struc_anal_plan",
        )
        return resumo_sistema, [], []

    novos, alterar = parse_plan_json(plan_raw)

    #━━━━━━━━━━━━━━❮◆❯━━━━━━━━━❮5. Filtro dinâmico com base na estrutura real❯━━━━━━━━━
    novos_filtrados, alterar_filtrados = filter_plan_with_existing_paths(
        scanned=scanned,
        novos=novos,
        alterar=alterar,
    )

    with _change_plan_cache_lock:
        if len(_change_plan_cache) >= CHANGE_PLAN_CACHE_MAX:
            by_ts = sorted(_change_plan_cache.items(), key=lambda x: x[1][0])
            for k, _ in by_ts[: CHANGE_PLAN_CACHE_MAX // 2]:
                del _change_plan_cache[k]
        _change_plan_cache[cache_key] = (time.time(), resumo_sistema, novos_filtrados, alterar_filtrados)

    return resumo_sistema, novos_filtrados, alterar_filtrados
