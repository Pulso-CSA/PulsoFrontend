#!/usr/bin/env python3
"""
Pré-carrega artefactos para o primeiro request não pagar download/treino pesado.

1) tiktoken — encodings usados pela stack OpenAI (evita I/O na primeira chamada).
2) Índice RAG (FAISS) — se OPENAI_API_KEY estiver definida e USE_OLLAMA não estiver ativo,
   corre train_rag_index() durante o build da imagem.

Render (Docker): defina OPENAI_API_KEY no serviço e ative a opção de expor essa variável
durante o build (build-time / "Include during build"). Opcional: OPENAI_EMBEDDING_MODEL.

Ollama: os modelos (Mistral/Qwen) não são instalados nesta imagem; use um servidor Ollama
externo (OLLAMA_HOST) ou OpenAI em produção.
"""
from __future__ import annotations

import os
import sys


def _preload_tiktoken() -> None:
    import tiktoken

    for name in ("cl100k_base", "o200k_base"):
        try:
            tiktoken.get_encoding(name)
        except Exception:
            pass
    print("[preload_models] tiktoken: encodings carregados")


def main() -> int:
    try:
        _preload_tiktoken()
    except Exception as e:
        print(f"[preload_models] tiktoken (aviso): {e}")

    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    use_ollama = os.getenv("USE_OLLAMA", "").strip().lower() in ("1", "true", "yes")
    if not key or use_ollama:
        print(
            "[preload_models] RAG: sem pré-build (defina OPENAI_API_KEY no build e USE_OLLAMA=0 "
            "para gerar o FAISS na imagem; em runtime o índice é criado/recarregado se faltar)"
        )
        return 0

    try:
        from app.core.openai.rag_trainer import train_rag_index

        train_rag_index()
        print("[preload_models] RAG: índice FAISS gerado no build")
    except Exception as e:
        print(f"[preload_models] RAG falhou no build: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
