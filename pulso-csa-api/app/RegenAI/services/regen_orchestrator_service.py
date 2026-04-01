from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI

from app.PulsoCSA.Python.services.test_runner_service.test_runner_service import run_automated_test
from app.PulsoCSA.Python.utils.log_manager import add_log

from RegenAI.models.regen_request import RegenRequest, SCOPE_DIRECTORY_MAP
from RegenAI.services.correction_bridge_service import CorrectionBridgeService
from RegenAI.services.input_generation_service import InputGenerationService
from RegenAI.services.log_analysis_service import LogAnalysisService
from RegenAI.services.report_service import ReportService
from RegenAI.services.route_discovery_service import RouteDiscoveryService
from RegenAI.services.test_execution_service import TestExecutionService
from RegenAI.storage.execution_cache import execution_cache


class RegenOrchestratorService:
    def __init__(self) -> None:
        self.route_discovery = RouteDiscoveryService()
        self.input_generation = InputGenerationService()
        self.test_execution = TestExecutionService()
        self.log_analysis = LogAnalysisService()
        self.correction_bridge = CorrectionBridgeService()
        self.report_service = ReportService()

    async def run(
        self,
        execution_id: str,
        req: RegenRequest,
        app: FastAPI,
        request_headers: Dict[str, str],
    ) -> None:
        rounds_data: List[Dict[str, Any]] = []
        corrections: List[Dict[str, Any]] = []
        all_failures: List[str] = []
        evidences: List[str] = []
        all_input_validation_gaps: List[Dict[str, Any]] = []
        scope_root_paths = {
            scope: self._resolve_scope_root_path(SCOPE_DIRECTORY_MAP[scope]) for scope in req.scopes
        }
        questions_by_scope = self.input_generation.load_questions_for_scopes(req.scopes)

        execution_cache.update_status(execution_id, status="running")
        self._log(
            execution_id,
            "info",
            f"Execucao iniciada com max_rounds={req.max_rounds} e scopes={', '.join(req.scopes)}",
        )

        try:
            openapi_schema = app.openapi()
            routes = self.route_discovery.discover(app, req)
            execution_cache.update_status(execution_id, total_routes=len(routes))
            self._log(execution_id, "info", f"Rotas relevantes descobertas: {len(routes)}")

            for round_number in range(1, req.max_rounds + 1):
                execution_cache.update_status(execution_id, current_round=round_number)
                self._log(execution_id, "info", f"Rodada {round_number} iniciada")

                generated_inputs = self.input_generation.generate(
                    routes=routes,
                    req=req,
                    round_number=round_number,
                    questions_by_scope=questions_by_scope,
                    openapi_schema=openapi_schema,
                )
                for item in generated_inputs:
                    question = item.get("question")
                    if not question:
                        continue
                    execution_cache.add_exception_question(
                        execution_id,
                        {
                            "question": question,
                            "scope": item.get("scope"),
                            "source_file": item.get("question_source_file"),
                            "category": item.get("question_category"),
                            "expected_output": item.get("question_expected_output"),
                        },
                    )
                execution_cache.update_status(execution_id, total_inputs=len(generated_inputs))

                results = await self.test_execution.execute(
                    app=app,
                    test_inputs=generated_inputs,
                    max_concurrency=req.max_concurrency,
                    request_headers=request_headers,
                    on_log=lambda level, message: self._log(execution_id, level, message),
                    on_result=lambda result: execution_cache.append_live_result(execution_id, result),
                )
                baseline_results = await self._run_baseline_tests(scope_root_paths)
                for baseline_item in baseline_results:
                    execution_cache.append_live_result(execution_id, baseline_item)
                results.extend(baseline_results)

                analysis = self.log_analysis.analyze_round(results)
                round_record = {
                    "round": round_number,
                    "inputs": len(generated_inputs),
                    "input_sources": [
                        {
                            "question": item.get("question"),
                            "scope": item.get("scope"),
                            "source_file": item.get("question_source_file"),
                            "category": item.get("question_category"),
                        }
                        for item in generated_inputs
                    ],
                    "failures": analysis["failure_count"],
                    "correction_candidates": len(analysis.get("correction_candidates", [])),
                    "input_validation_gaps": analysis.get("input_validation_gaps", []),
                    "results": results,
                }
                rounds_data.append(round_record)
                execution_cache.add_round(execution_id, round_record)

                evidences.extend(analysis["evidences"])
                all_failures.extend(analysis["evidences"])
                all_input_validation_gaps.extend(analysis.get("input_validation_gaps", []))
                execution_cache.update_status(
                    execution_id,
                    total_failures=len(all_failures),
                )

                if not analysis["has_failures"]:
                    self._log(execution_id, "info", f"Rodada {round_number} finalizada sem falhas")
                    break

                if not analysis.get("has_correction_candidates"):
                    self._log(
                        execution_id,
                        "warning",
                        "Somente falhas nao-corrigiveis automaticamente (ex.: 422/Baseline); encerrando ciclos.",
                    )
                    break

                self._log(
                    execution_id,
                    "warning",
                    f"Rodada {round_number} encontrou {analysis['failure_count']} falhas ({len(analysis.get('correction_candidates', []))} corrigiveis); iniciando autocorrecao",
                )
                correction_result = self.correction_bridge.apply_minimal_correction(
                    execution_id=execution_id,
                    round_number=round_number,
                    scope_root_paths=scope_root_paths,
                    usuario=req.usuario,
                    failures=analysis.get("correction_candidates", []),
                )
                corrections.append(correction_result)
                self._log(
                    execution_id,
                    "info",
                    f"Autocorrecao rodada {round_number} concluida (applied={correction_result.get('applied')})",
                )
                if not correction_result.get("applied"):
                    self._log(
                        execution_id,
                        "warning",
                        "Autocorrecao nao aplicou mudanca efetiva; encerrando execucao para evitar loop inutil.",
                    )
                    break

            final_status = "completed"
            if rounds_data:
                last_round = rounds_data[-1]
                has_corrigiveis_pendentes = last_round.get("correction_candidates", 0) > 0
                if has_corrigiveis_pendentes and len(rounds_data) >= req.max_rounds:
                    final_status = "failed"

            report = self.report_service.build_report(
                execution_id=execution_id,
                objective=req.objective,
                scopes=req.scopes,
                routes=routes,
                questions_by_scope=questions_by_scope,
                generated_inputs=self.input_generation.generate(
                    routes=routes,
                    req=req,
                    round_number=1,
                    questions_by_scope=questions_by_scope,
                    openapi_schema=openapi_schema,
                ),
                rounds=rounds_data,
                corrections=corrections,
                failures_detected=all_failures,
                input_validation_gaps=all_input_validation_gaps,
                evidences=evidences,
                final_status=final_status,
            )
            report_json_path, report_md_path = self.report_service.persist_reports(report)
            report = report.model_copy(
                update={
                    "report_json_path": report_json_path,
                    "report_md_path": report_md_path,
                }
            )
            execution_cache.set_report(execution_id, report)
            execution_cache.update_status(
                execution_id,
                status=final_status,
                completed_at=report.generated_at,
                report_json_path=report_json_path,
                report_md_path=report_md_path,
            )
            self._log(execution_id, "info", f"Execucao finalizada com status={final_status}")
        except Exception as exc:  # pragma: no cover
            execution_cache.update_status(execution_id, status="failed", error=str(exc))
            self._log(execution_id, "error", f"Falha inesperada na execucao: {exc}")

    @staticmethod
    def _log(execution_id: str, level: str, message: str) -> None:
        execution_cache.append_log(execution_id, level, message, source="regenai")
        add_log(level, f"[regenai:{execution_id}] {message}", "regenai")

    async def _run_baseline_tests(self, scope_root_paths: Dict[str, str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for scope, root_path in scope_root_paths.items():
            test_resp = await asyncio.to_thread(
                run_automated_test,
                root_path=root_path,
                log_type="info",
                prefer_docker=False,
            )
            results.append(
                {
                    "method": "BASELINE",
                    "path": root_path,
                    "scope": scope,
                    "status_code": 200 if test_resp.success else 500,
                    "success": test_resp.success,
                    "elapsed_ms": 0,
                    "body_preview": test_resp.message,
                    "error": None if test_resp.success else test_resp.details or test_resp.message,
                }
            )
        return results

    @staticmethod
    def _resolve_scope_root_path(configured_path: str) -> str:
        """
        Resolve caminho configurado para um path existente e estável.
        Evita cenários como `<repo>/api/api/app/...` quando o cwd já é `api/`.
        """
        raw = Path(configured_path)
        candidates = []
        if raw.is_absolute():
            candidates.append(raw)
        else:
            here = Path(__file__).resolve()
            repo_root = here.parents[4]
            api_root = here.parents[3]
            candidates.extend(
                [
                    Path.cwd() / raw,
                    repo_root / raw,
                    api_root / str(raw).removeprefix("api/"),
                ]
            )
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return configured_path

