from __future__ import annotations

from typing import Any, Dict, List

from app.PulsoCSA.Python.models.pipeline_models.pipeline_models import (
    AnaliseRetornoRequest,
    CorrecaoErrosRequest,
    RelatorioTestes,
)
from app.PulsoCSA.Python.services.pipeline_services.analise_retorno_service import run_analise_retorno
from app.PulsoCSA.Python.services.pipeline_services.correcao_erros_service import run_correcao_erros


class CorrectionBridgeService:
    def apply_minimal_correction(
        self,
        execution_id: str,
        round_number: int,
        scope_root_paths: Dict[str, str],
        usuario: str,
        failures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not failures:
            return {
                "round": round_number,
                "applied": False,
                "reason": "sem falhas para correcao",
                "results_by_scope": [],
            }

        failure_msgs = self._to_failure_messages(failures)
        failures_by_scope: Dict[str, List[Dict[str, Any]]] = {}
        for failure in failures:
            scope = failure.get("scope", "unknown")
            failures_by_scope.setdefault(scope, []).append(failure)

        results_by_scope: List[Dict[str, Any]] = []
        any_applied = False
        for scope, scope_failures in failures_by_scope.items():
            root_path = scope_root_paths.get(scope)
            if not root_path:
                results_by_scope.append(
                    {
                        "scope": scope,
                        "applied": False,
                        "reason": "scope sem mapeamento de diretorio",
                    }
                )
                continue

            scope_msgs = self._to_failure_messages(scope_failures)
            relatorio = RelatorioTestes(
                status="parcialmente aprovado",
                erros=scope_msgs,
                vulnerabilidades=[],
                logs=scope_msgs,
            )
            id_requisicao = f"{execution_id}-r{round_number}-{scope.lower().replace('/', '-')}"
            analise = run_analise_retorno(
                AnaliseRetornoRequest(
                    id_requisicao=id_requisicao,
                    relatorio_testes=relatorio,
                    root_path=root_path,
                )
            )

            if analise.analise_retorno.objetivo_final == "atingido":
                results_by_scope.append(
                    {
                        "scope": scope,
                        "applied": False,
                        "reason": "analise-retorno ja marcou objetivo como atingido",
                        "analise_retorno": analise.model_dump(),
                        "correcao": None,
                    }
                )
                continue

            correcao = run_correcao_erros(
                CorrecaoErrosRequest(
                    id_requisicao=id_requisicao,
                    analise_retorno=analise.analise_retorno.model_dump(),
                    root_path=root_path,
                    usuario=usuario,
                ),
                run_pipeline_autocorrection=False,
            )
            correcao_dump = correcao.model_dump()
            code_implementer_status = (
                ((correcao_dump.get("workflow_result") or {}).get("code_implementer") or {}).get("status")
            )
            code_implementer_errors = (
                ((correcao_dump.get("workflow_result") or {}).get("code_implementer") or {}).get("errors") or []
            )
            has_effective_change = code_implementer_status in {"success", "partial"}
            code_plan_missing = any("Code-plan not found" in str(err) for err in code_implementer_errors)
            if code_plan_missing:
                has_effective_change = False
                # Fallback: executar fluxo completo (C1..C5) para gerar code-plan quando nao existir.
                from app.PulsoCSA.Python.workflow.correct_workflow.workflow_core_cor import run_correct_workflow

                fallback_result = run_correct_workflow(
                    log_type="info",
                    prompt="RegenAI fallback: gerar plano e aplicar correcao minima para as falhas reportadas.",
                    usuario=usuario,
                    root_path=root_path,
                    run_pipeline_autocorrection=False,
                    only_c4_c5=False,
                    id_requisicao_override=id_requisicao,
                )
                correcao_dump["workflow_result_fallback"] = fallback_result
                fallback_impl = (fallback_result or {}).get("code_implementer") or {}
                fallback_status = fallback_impl.get("status")
                has_effective_change = fallback_status in {"success", "partial"}

            if has_effective_change:
                any_applied = True
            results_by_scope.append(
                {
                    "scope": scope,
                    "applied": has_effective_change,
                    "analise_retorno": analise.model_dump(),
                    "correcao": correcao_dump,
                    "reason": None if has_effective_change else "autocorrecao sem mudanca efetiva",
                    "correction_status": correcao.correcao.status,
                }
            )

        return {
            "round": round_number,
            "applied": any_applied,
            "failures_received": len(failure_msgs),
            "results_by_scope": results_by_scope,
        }

    @staticmethod
    def _to_failure_messages(failures: List[Dict[str, Any]]) -> List[str]:
        output: List[str] = []
        for failure in failures:
            method = failure.get("method", "UNKNOWN")
            path = failure.get("path", "/")
            if failure.get("error"):
                output.append(f"{method} {path}: {failure['error']}")
            else:
                output.append(f"{method} {path}: status={failure.get('status_code')}")
        return output[:50]

