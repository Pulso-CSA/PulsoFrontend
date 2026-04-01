#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Refino de Prompt com RAG (SAFE MODE)❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

# openai está em api/app/core/openai/ (compartilhado)
try:
    from core.openai.openai_client import get_openai_client
    from core.openai.rag_trainer import load_rag_index
except ImportError:
    from app.core.openai.openai_client import get_openai_client
    from app.core.openai.rag_trainer import load_rag_index
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from app.prompts.loader import load_prompt

import hashlib
import os
import re
import threading
import time
from typing import Dict, Tuple

# Prompts de criação claros: pular RAG+LLM (economia ~10–12 min no fluxo JS)
_CREATION_PROMPT_PATTERN = re.compile(
    r"^(crie|criar|implemente|implementar|desenvolva|desenvolver|gerar|faça|fazer|faça um|me crie|me faça)\s+",
    re.IGNORECASE,
)
_CREATION_SKIP_MIN_LEN = 10

REFINE_CACHE_TTL_SEC = int(os.environ.get("REFINE_CACHE_TTL_SEC", "300"))
REFINE_CACHE_MAX_SIZE = 200
_refine_cache: Dict[str, Tuple[float, str]] = {}
_refine_cache_lock = threading.Lock()


def _refine_cache_key(prompt: str) -> str:
    return hashlib.sha256((prompt or "").strip().encode("utf-8")).hexdigest()


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Execução Principal❯━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def execute_refine_prompt(prompt: str):
    """
    Refina o prompt de forma segura:
      - melhora clareza,
      - remove ambiguidades,
      - preserva 100% da intenção original,
      - NÃO altera a tecnologia informada,
      - NÃO adiciona requisitos novos,
      - NÃO converte para outro framework/language,
      - NÃO cria escopo adicional.

    O objetivo aqui é apenas melhorar comunicação técnica,
    mantendo o pedido exatamente como foi feito.
    """
    cache_key = _refine_cache_key(prompt)
    with _refine_cache_lock:
        now = time.time()
        if cache_key in _refine_cache:
            ts, cached_refined = _refine_cache[cache_key]
            if now - ts <= REFINE_CACHE_TTL_SEC:
                return {"refined_prompt": cached_refined, "refinement_quality": "safe"}
            del _refine_cache[cache_key]

    #━━━━━━━━━❮Skip refine para prompts de criação claros (otimização)❯━━━━━━━━━
    p = (prompt or "").strip()
    if len(p) >= _CREATION_SKIP_MIN_LEN and _CREATION_PROMPT_PATTERN.match(p):
        with _refine_cache_lock:
            if len(_refine_cache) >= REFINE_CACHE_MAX_SIZE:
                by_ts = sorted(_refine_cache.items(), key=lambda x: x[1][0])
                for k, _ in by_ts[: REFINE_CACHE_MAX_SIZE // 2]:
                    del _refine_cache[k]
            _refine_cache[cache_key] = (time.time(), p)
        return {"refined_prompt": p, "refinement_quality": "safe"}

    #━━━━━━━━━❮Carregar prompts de arquivos .txt❯━━━━━━━━━
    base_refine = load_prompt("analyse/base_refine")
    template_suffix = load_prompt("analyse/refine_template_suffix")
    instructions = load_prompt("analyse/refine_instructions")

    # O chain "stuff" do RetrievalQA passa a pergunta na chave "question", não "query".
    safe_template = PromptTemplate(
        template=f"{base_refine}\n\n{template_suffix}\n\n{instructions}",
        input_variables=["context", "question"],
    )

    try:
        #━━━━━━━━━❮Construir RAG❯━━━━━━━━━
        db = load_rag_index()
        retriever = db.as_retriever(search_kwargs={"k": 4})

        client = get_openai_client()
        qa_chain = RetrievalQA.from_chain_type(
            llm=client.llm_fast,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": safe_template},
            return_source_documents=False
        )

        # LangChain pode usar "query", "input" ou "question" conforme a versão.
        # Enviar todos evita "Missing some input keys: {'query'}" ao invocar a chain.
        inp = {"query": prompt, "input": prompt, "question": prompt}
        result = qa_chain.invoke(inp)
        refined_prompt = (
            result["result"].strip()
            if isinstance(result, dict)
            else str(result).strip()
        )

    except Exception as e:
        print(f"⚠️ Erro no RAG (fallback ativado): {e}")
        try:
            fallback_instruction = load_prompt("analyse/refine_fallback")
            client = get_openai_client()
            refined_prompt = client.generate_text(
                f"{fallback_instruction}\n\n{prompt}",
                use_fast_model=True,
                num_predict=512,
            )
        except Exception:
            refined_prompt = prompt

    with _refine_cache_lock:
        if len(_refine_cache) >= REFINE_CACHE_MAX_SIZE:
            by_ts = sorted(_refine_cache.items(), key=lambda x: x[1][0])
            for k, _ in by_ts[: REFINE_CACHE_MAX_SIZE // 2]:
                del _refine_cache[k]
        _refine_cache[cache_key] = (time.time(), refined_prompt)

    return {
        "refined_prompt": refined_prompt,
        "refinement_quality": "safe"
    }
