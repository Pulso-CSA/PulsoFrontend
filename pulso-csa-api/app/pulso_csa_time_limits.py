# -*- coding: utf-8 -*-
"""
Limites de tempo Pulso CSA: geração de código e fluxo de compreensão.

Orçamento padrão: 5 minutos (300 s) por pedido síncrono ou por job assíncrono.
Override: PULSO_CSA_WORKFLOW_MAX_SEC, PULSO_CSA_LLM_CALL_TIMEOUT_SEC
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Callable, TypeVar

T = TypeVar("T")

CSA_WORKFLOW_WALL_CLOCK_SEC = float(os.getenv("PULSO_CSA_WORKFLOW_MAX_SEC", "300"))

CSA_LLM_CALL_TIMEOUT_SEC = int(os.getenv("PULSO_CSA_LLM_CALL_TIMEOUT_SEC", "120"))


def csa_timeout_user_message() -> str:
    mins = max(1, int(CSA_WORKFLOW_WALL_CLOCK_SEC // 60))
    return (
        f"O tempo máximo de {mins} minuto(s) para esta operação foi excedido. "
        "Tente um pedido mais específico ou divida em passos menores."
    )


def csa_timeout_http_detail() -> dict:
    return {
        "code": "CSA_TIME_BUDGET_EXCEEDED",
        "message": csa_timeout_user_message(),
    }


class CsaRequestBudget:
    """
    Orçamento monotónico partilhado (ex.: route_to_module + análise + workflow)
    num único POST de compreensão em modo síncrono.
    """

    def __init__(self, total_sec: float | None = None):
        sec = float(total_sec if total_sec is not None else CSA_WORKFLOW_WALL_CLOCK_SEC)
        self._end = time.monotonic() + max(1.0, sec)

    def remaining(self) -> float:
        r = self._end - time.monotonic()
        if r <= 0:
            raise asyncio.TimeoutError()
        return r

    async def run_in_executor(
        self,
        loop: asyncio.AbstractEventLoop,
        fn: Callable[[], T],
    ) -> T:
        return await asyncio.wait_for(
            loop.run_in_executor(None, fn),
            timeout=self.remaining(),
        )
