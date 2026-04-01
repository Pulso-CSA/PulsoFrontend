import json
from typing import Any, Dict, List

from RegenAI.utils.response_semantics import evaluate_expected_output


class LogAnalysisService:
    def analyze_round(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        failures: List[Dict[str, Any]] = []
        correction_candidates: List[Dict[str, Any]] = []
        evidences: List[str] = []
        input_validation_gaps: List[Dict[str, Any]] = []

        for result in results:
            expected_output = (result.get("question_expected_output") or "").strip()
            has_expected_output = bool(expected_output)
            expected_matched = True
            if has_expected_output and result.get("success"):
                semantic = str(
                    result.get("semantic_response_text")
                    or result.get("response_text")
                    or result.get("body_preview")
                    or ""
                )
                expected_matched, match_reason = evaluate_expected_output(
                    semantic_text=semantic,
                    expected_output=expected_output,
                    parsed_body=result.get("parsed_response"),
                )
                if not expected_matched:
                    result["success"] = False
                    result["error"] = "Resposta divergente do esperado para a pergunta de teste"
                    result["status_code"] = result.get("status_code") or 200
                elif match_reason:
                    result["expected_match_detail"] = match_reason

            if result.get("success"):
                continue
            failures.append(result)
            method = result.get("method", "UNKNOWN")
            path = result.get("path", "/")
            status_code = result.get("status_code")
            error = result.get("error")
            if error:
                evidences.append(f"{method} {path} erro: {error}")
            else:
                evidences.append(f"{method} {path} status {status_code}")

            # 422 representa payload/contrato invalido, nao erro de implementacao da rota.
            if status_code == 422:
                parsed = self._extract_validation_gaps(result)
                if parsed:
                    input_validation_gaps.append(parsed)
                continue

            # Baseline de infraestrutura nao deve disparar autocorrecao de codigo.
            if method == "BASELINE":
                continue

            correction_candidates.append(result)

        return {
            "has_failures": len(failures) > 0,
            "failure_count": len(failures),
            "failures": failures,
            "has_correction_candidates": len(correction_candidates) > 0,
            "correction_candidates": correction_candidates,
            "input_validation_gaps": input_validation_gaps,
            "evidences": evidences[:20],
        }

    @staticmethod
    def _extract_validation_gaps(result: Dict[str, Any]) -> Dict[str, Any]:
        body_preview = result.get("body_preview") or ""
        missing_fields: List[str] = []
        try:
            payload = json.loads(body_preview)
            for item in payload.get("detail", []):
                loc = item.get("loc") or []
                if isinstance(loc, list) and len(loc) >= 2:
                    missing_fields.append(".".join(str(p) for p in loc[1:]))
        except Exception:
            pass

        return {
            "method": result.get("method"),
            "path": result.get("path"),
            "scope": result.get("scope"),
            "status_code": result.get("status_code"),
            "missing_fields": missing_fields,
            "raw_preview": body_preview[:300],
        }

