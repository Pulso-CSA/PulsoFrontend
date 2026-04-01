from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List

import httpx
from fastapi import FastAPI

from RegenAI.utils.concurrency_manager import run_with_limit
from RegenAI.utils.response_semantics import (
    build_semantic_test_string,
    has_chart_signals,
    parse_json_safe,
)


class TestExecutionService:
    async def execute(
        self,
        app: FastAPI,
        test_inputs: List[Dict[str, Any]],
        max_concurrency: int,
        request_headers: Dict[str, str],
        on_log: Callable[[str, str], None],
        on_result: Callable[[Dict[str, Any]], None] | None = None,
    ) -> List[Dict[str, Any]]:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://regenai.local",
            timeout=20.0,
        ) as client:
            tasks = [self._build_task(client, item, request_headers, on_log, on_result) for item in test_inputs]
            return await run_with_limit(tasks, max_concurrency)

    def _build_task(
        self,
        client: httpx.AsyncClient,
        item: Dict[str, Any],
        request_headers: Dict[str, str],
        on_log: Callable[[str, str], None],
        on_result: Callable[[Dict[str, Any]], None] | None,
    ):
        async def _task() -> Dict[str, Any]:
            started = time.perf_counter()
            method = item["method"]
            path = item["path"]
            timeout_s = float(item.get("timeout_s", 25))
            on_log("info", f"Teste iniciado: {method} {path}")
            try:
                response = await asyncio.wait_for(
                    client.request(
                        method=method,
                        url=path,
                        params=item.get("query") or None,
                        json=item.get("json"),
                        headers=request_headers or None,
                    ),
                    timeout=timeout_s,
                )
                elapsed_ms = (time.perf_counter() - started) * 1000
                body_preview = response.text[:1200] if response.text else ""
                ok = response.status_code < 400
                level = "info" if ok else "warning"
                on_log(level, f"Teste finalizado: {method} {path} -> {response.status_code} ({elapsed_ms:.0f}ms)")
                parsed = parse_json_safe(response.text) if response.text else None
                narrative = ""
                if isinstance(parsed, dict):
                    narrative = (
                        str(parsed.get("resposta_texto") or "")
                        or str(parsed.get("answer") or "")
                        or str(parsed.get("message") or "")
                        or str(parsed.get("explanation") or "")
                        or ""
                    )
                semantic_response_text = build_semantic_test_string(
                    body_preview if not narrative else f"{body_preview} {narrative}",
                    parsed,
                )
                result = {
                    "method": method,
                    "path": path,
                    "scope": item.get("scope"),
                    "status_code": response.status_code,
                    "success": ok,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "body_preview": body_preview,
                    "semantic_response_text": semantic_response_text,
                    "response_has_chart": bool(parsed is not None and has_chart_signals(parsed)),
                    "question": item.get("question"),
                    "question_source_file": item.get("question_source_file"),
                    "question_category": item.get("question_category"),
                    "question_expected_output": item.get("question_expected_output"),
                    "request_query": item.get("query"),
                    "request_json": item.get("json"),
                    "parsed_response": parsed,
                }
                result["response_text"] = narrative if isinstance(parsed, dict) else ""
                if on_result:
                    on_result(result)
                return result
            except asyncio.TimeoutError:
                elapsed_ms = (time.perf_counter() - started) * 1000
                on_log("warning", f"Timeout no teste: {method} {path} ({timeout_s:.0f}s)")
                result = {
                    "method": method,
                    "path": path,
                    "scope": item.get("scope"),
                    "status_code": 504,
                    "success": False,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "error": f"Timeout apos {timeout_s:.0f}s",
                    "body_preview": "",
                    "semantic_response_text": "",
                    "response_has_chart": False,
                    "parsed_response": None,
                    "response_text": "",
                    "question": item.get("question"),
                    "question_source_file": item.get("question_source_file"),
                    "question_category": item.get("question_category"),
                    "question_expected_output": item.get("question_expected_output"),
                    "request_query": item.get("query"),
                    "request_json": item.get("json"),
                }
                if on_result:
                    on_result(result)
                return result
            except Exception as exc:  # pragma: no cover
                elapsed_ms = (time.perf_counter() - started) * 1000
                on_log("error", f"Erro no teste: {method} {path} -> {type(exc).__name__}")
                result = {
                    "method": method,
                    "path": path,
                    "scope": item.get("scope"),
                    "status_code": None,
                    "success": False,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "error": str(exc),
                    "body_preview": "",
                    "semantic_response_text": "",
                    "response_has_chart": False,
                    "parsed_response": None,
                    "response_text": "",
                    "question": item.get("question"),
                    "question_source_file": item.get("question_source_file"),
                    "question_category": item.get("question_category"),
                    "question_expected_output": item.get("question_expected_output"),
                    "request_query": item.get("query"),
                    "request_json": item.get("json"),
                }
                if on_result:
                    on_result(result)
                return result

        return _task

