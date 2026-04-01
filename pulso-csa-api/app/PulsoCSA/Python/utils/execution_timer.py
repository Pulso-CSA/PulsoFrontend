#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Timer de Execução❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Utilitário para medir e logar tempo de execução.
Uso: with execution_timer("nome_da_operacao", "source"):
         ... código ...
"""

import time
from contextlib import contextmanager
from typing import Optional

from utils.log_manager import add_log


def _format_duration(seconds: float) -> str:
    """Formata duração em formato legível (ms, s ou min)."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f}µs"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    return f"{seconds / 60:.2f}min"


@contextmanager
def execution_timer(
    operation: str,
    source: str = "execution_timer",
    log_level: str = "info",
):
    """
    Context manager que mede e loga o tempo de execução.
    Exemplo:
        with execution_timer("comprehension/run", "comprehension_router"):
            result = await run_comprehension(...)
    """
    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        msg = f"Tempo de execução: {operation} = {_format_duration(elapsed)}"
        add_log(log_level, msg, source)


def get_elapsed_ms(t0: float) -> float:
    """Retorna milissegundos desde t0 (time.perf_counter())."""
    return (time.perf_counter() - t0) * 1000


def log_elapsed(operation: str, t0: float, source: str = "execution_timer"):
    """Loga tempo decorrido desde t0."""
    elapsed = time.perf_counter() - t0
    msg = f"Tempo de execução: {operation} = {_format_duration(elapsed)}"
    add_log("info", msg, source)


def timed(operation: str, source: str = "execution_timer"):
    """Decorator que aplica execution_timer em funções sync ou async."""
    def decorator(fn):
        if callable(fn):
            import asyncio
            if asyncio.iscoroutinefunction(fn):
                async def async_wrapper(*args, **kwargs):
                    with execution_timer(operation, source):
                        return await fn(*args, **kwargs)
                return async_wrapper
            def sync_wrapper(*args, **kwargs):
                with execution_timer(operation, source):
                    return fn(*args, **kwargs)
            return sync_wrapper
        return fn
    return decorator
