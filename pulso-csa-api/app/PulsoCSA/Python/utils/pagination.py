#━━━━━━━━━❮Paginação Consistente❯━━━━━━━━━
# Limites globais para paginação e queries grandes.
import os

# Limites padrão (configuráveis via env)
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "1000"))
MAX_QUERY_ROWS = int(os.getenv("MAX_QUERY_ROWS", "10000"))  # Para queries SQL/ID
MAX_SAMPLE_ROWS = int(os.getenv("MAX_SAMPLE_ROWS", "5000"))  # Para amostras de dados


def validar_pagina(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> tuple[int, int]:
    """
    Valida e normaliza parâmetros de paginação.
    Retorna (page_validado, page_size_validado).
    """
    page = max(1, int(page))
    page_size = min(max(1, int(page_size)), MAX_PAGE_SIZE)
    return page, page_size


def validar_limite_query(limit: int = None) -> int:
    """
    Valida limite de linhas para queries.
    Retorna limite válido (máx MAX_QUERY_ROWS).
    """
    if limit is None:
        return MAX_QUERY_ROWS
    return min(max(1, int(limit)), MAX_QUERY_ROWS)


def validar_limite_amostra(limit: int = None) -> int:
    """
    Valida limite de linhas para amostras.
    Retorna limite válido (máx MAX_SAMPLE_ROWS).
    """
    if limit is None:
        return MAX_SAMPLE_ROWS
    return min(max(1, int(limit)), MAX_SAMPLE_ROWS)
