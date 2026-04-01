from fastapi import FastAPI
from typing import Dict

from RegenAI.models.regen_request import RegenRequest
from RegenAI.services.regen_orchestrator_service import RegenOrchestratorService


class RegenWorkflow:
    def __init__(self) -> None:
        self._orchestrator = RegenOrchestratorService()

    async def execute(
        self,
        execution_id: str,
        req: RegenRequest,
        app: FastAPI,
        request_headers: Dict[str, str] | None = None,
    ) -> None:
        await self._orchestrator.run(
            execution_id=execution_id,
            req=req,
            app=app,
            request_headers=request_headers or {},
        )

