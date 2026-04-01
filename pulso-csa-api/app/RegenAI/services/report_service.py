from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from RegenAI.models.regen_report import RegenReport


class ReportService:
    def build_report(
        self,
        execution_id: str,
        objective: str,
        scopes: List[str],
        routes: List[Dict[str, str]],
        questions_by_scope: Dict[str, List[Dict[str, str]]],
        generated_inputs: List[Dict[str, Any]],
        rounds: List[Dict[str, Any]],
        corrections: List[Dict[str, Any]],
        failures_detected: List[str],
        input_validation_gaps: List[Dict[str, Any]],
        evidences: List[str],
        final_status: str,
    ) -> RegenReport:
        return RegenReport(
            execution_id=execution_id,
            objective=objective,
            scopes=scopes,
            routes_analyzed=[f"{r['method']} {r['path']}" for r in routes],
            questions_by_scope=questions_by_scope,
            generated_inputs=generated_inputs,
            cycles_executed=len(rounds),
            failures_detected=failures_detected,
            input_validation_gaps=input_validation_gaps,
            corrections_applied=corrections,
            final_status=final_status,
            evidences=evidences,
            rounds=rounds,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def persist_reports(self, report: RegenReport) -> Tuple[str, str]:
        reports_root = Path(__file__).resolve().parent.parent / "reports"
        execution_dir = reports_root / report.execution_id
        execution_dir.mkdir(parents=True, exist_ok=True)

        json_path = execution_dir / "report.json"
        md_path = execution_dir / "report.md"

        report_dict = report.model_dump()
        report_dict["report_json_path"] = str(json_path)
        report_dict["report_md_path"] = str(md_path)

        json_path.write_text(
            json.dumps(report_dict, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        md_path.write_text(self._build_markdown(report_dict), encoding="utf-8")
        return str(json_path), str(md_path)

    def _build_markdown(self, report: Dict[str, Any]) -> str:
        lines: List[str] = []
        lines.append(f"# RegenAI Report - {report['execution_id']}")
        lines.append("")
        lines.append("## Objetivo recebido")
        lines.append(report["objective"])
        lines.append("")
        lines.append("## Escopos executados")
        for scope in report.get("scopes", []):
            lines.append(f"- {scope}")
        lines.append("")
        lines.append("## Rotas analisadas")
        for item in report.get("routes_analyzed", []):
            lines.append(f"- {item}")
        lines.append("")
        lines.append("## Perguntas por escopo")
        questions_by_scope = report.get("questions_by_scope", {})
        if questions_by_scope:
            for scope, questions in questions_by_scope.items():
                lines.append(f"### {scope}")
                if questions:
                    for item in questions[:20]:
                        category = item.get("category", "unknown")
                        question = item.get("question", "")
                        source_file = item.get("source_file", "")
                        lines.append(f"- [{category}] {question} ({source_file})")
                else:
                    lines.append("- Sem perguntas carregadas para este escopo.")
        else:
            lines.append("- Nenhuma pergunta carregada.")
        lines.append("")
        lines.append("## Entradas geradas")
        for item in report.get("generated_inputs", [])[:50]:
            method = item.get("method")
            path = item.get("path")
            scope = item.get("scope", "unknown")
            source_file = item.get("question_source_file", "sem_arquivo")
            question = item.get("question", "")
            lines.append(f"- {method} {path} | scope={scope} | source={source_file} | question={question}")
        lines.append("")
        lines.append("## Ciclos executados")
        lines.append(f"- Total: {report.get('cycles_executed', 0)}")
        lines.append("")
        lines.append("## Falhas detectadas")
        failures = report.get("failures_detected", [])
        if failures:
            for failure in failures:
                lines.append(f"- {failure}")
        else:
            lines.append("- Nenhuma falha detectada.")
        lines.append("")
        lines.append("## Gaps de validacao de entrada (422)")
        gaps = report.get("input_validation_gaps", [])
        if gaps:
            for gap in gaps[:50]:
                method = gap.get("method")
                path = gap.get("path")
                missing = ", ".join(gap.get("missing_fields") or []) or "nao identificado"
                lines.append(f"- {method} {path} | campos faltantes: {missing}")
        else:
            lines.append("- Nenhum gap de validacao de entrada registrado.")
        lines.append("")
        lines.append("## Correcoes aplicadas")
        corrections = report.get("corrections_applied", [])
        if corrections:
            for correction in corrections:
                lines.append(
                    f"- Rodada {correction.get('round')}: "
                    f"{correction.get('correction_status', correction.get('reason', 'sem detalhes'))}"
                )
        else:
            lines.append("- Nenhuma correcao executada.")
        lines.append("")
        lines.append("## Status final")
        lines.append(f"- {report.get('final_status')}")
        lines.append("")
        lines.append("## Evidencias principais")
        evidences = report.get("evidences", [])
        if evidences:
            for evidence in evidences[:30]:
                lines.append(f"- {evidence}")
        else:
            lines.append("- Sem evidencias registradas.")
        lines.append("")
        return "\n".join(lines)

