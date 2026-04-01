import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from RegenAI.models.regen_request import RegenRequest

DOCS_MAP = {
    "PulsoCSA/Python": "pulsocsa_python_tests.md",
    "PulsoCSA/JavaScript": "pulsocsa_javascript_tests.md",
    "InteligenciaDados": "inteligencia_dados_tests.md",
    "FinOps": "finops_tests.md",
    "CloudIAC": "cloudiac_tests.md",
}

EXTERNAL_SCOPE_DOCS = {
    "InteligenciaDados": "docs/PERGUNTAS_TESTE_ID.md",
    "FinOps": "docs/PERGUNTAS_TESTE_FINOPS.md",
    "CloudIAC": "docs/PERGUNTAS_TESTE_CLOUDIAC.md",
    "PulsoCSA/Python": "docs/PERGUNTAS_TESTE_PULSOCSA.md",
    "PulsoCSA/JavaScript": "docs/PERGUNTAS_TESTE_PULSOCSA.md",
}

QUESTION_SECTIONS = {
    "## valid_questions": "valid_questions",
    "## invalid_questions": "invalid_questions",
    "## edge_cases": "edge_cases",
    "## ambiguous_inputs": "ambiguous_inputs",
}


class InputGenerationService:
    def generate(
        self,
        routes: List[Dict[str, str]],
        req: RegenRequest,
        round_number: int,
        questions_by_scope: Dict[str, List[Dict[str, str]]],
        openapi_schema: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        inputs: List[Dict[str, Any]] = []
        question_cursor: Dict[str, int] = {scope: 0 for scope in questions_by_scope.keys()}
        for route in routes:
            path = route["path"]
            raw_path = route.get("raw_path") or route["path"]
            method = route["method"].upper()
            resolved_path = self._resolve_path_params(path)
            scope = route.get("scope", "")
            scoped_questions = questions_by_scope.get(scope, [])
            chosen_question: Dict[str, str] = {}
            if scoped_questions:
                idx = question_cursor.get(scope, 0) % len(scoped_questions)
                chosen_question = scoped_questions[idx]
                question_cursor[scope] = idx + 1
            question_text = chosen_question.get("question", req.objective)

            payload: Dict[str, Any] = {
                "objective": req.objective,
                "question": question_text,
                "round": round_number,
                "origin": "regenai",
                "scope": scope,
                "question_source_file": chosen_question.get("source_file"),
                "question_category": chosen_question.get("category"),
                "question_expected_output": chosen_question.get("expected_output"),
            }
            query = {"regen_round": str(round_number), "regen_mode": "minimal"}
            if question_text:
                query["regen_question"] = question_text[:120]
            operation = self._get_operation_schema(openapi_schema, raw_path, method)
            query = self._inject_required_query_params(
                query=query,
                operation=operation,
                openapi_schema=openapi_schema,
                question_text=question_text,
                round_number=round_number,
            )

            item: Dict[str, Any] = {
                "path": resolved_path,
                "raw_path": raw_path,
                "method": method,
                "scope": scope,
                "query": query,
                "json": None,
                "timeout_s": 90 if "/inteligencia-dados/captura-dados" in raw_path else 25,
                "question": question_text,
                "question_source_file": chosen_question.get("source_file"),
                "question_category": chosen_question.get("category"),
                "question_expected_output": chosen_question.get("expected_output"),
            }

            if method in {"POST", "PUT", "PATCH"}:
                schema_payload = self._build_body_from_openapi(
                    operation=operation,
                    openapi_schema=openapi_schema,
                    question_text=question_text,
                    round_number=round_number,
                    req=req,
                    raw_path=raw_path,
                )
                item["json"] = schema_payload or payload
            inputs.append(item)
        inputs.extend(
            self._build_user_journey_inputs(
                routes=routes,
                req=req,
                round_number=round_number,
                questions_by_scope=questions_by_scope,
            )
        )
        return inputs

    @staticmethod
    def _route_or_synthetic(
        by_path: Dict[str, Dict[str, str]],
        path: str,
        method: str,
        scope: str,
    ) -> Dict[str, str]:
        found = by_path.get(path)
        if found:
            return found
        return {"path": path, "raw_path": path, "method": method, "scope": scope}

    def load_questions_for_scopes(self, scopes: List[str]) -> Dict[str, List[Dict[str, str]]]:
        docs_root = Path(__file__).resolve().parent.parent / "Docs"
        repo_root = Path(__file__).resolve().parents[4]
        questions_by_scope: Dict[str, List[Dict[str, str]]] = {}
        for scope in scopes:
            external_doc = EXTERNAL_SCOPE_DOCS.get(scope)
            if external_doc:
                external_path = repo_root / external_doc
                external_questions = self._parse_external_questions_file(external_path)
                if external_questions:
                    questions_by_scope[scope] = external_questions
                    continue
            filename = DOCS_MAP.get(scope)
            if not filename:
                questions_by_scope[scope] = []
                continue
            path = docs_root / filename
            questions_by_scope[scope] = self._parse_questions_file(path)
        return questions_by_scope

    def _parse_questions_file(self, file_path: Path) -> List[Dict[str, str]]:
        if not file_path.exists():
            return []

        lines = file_path.read_text(encoding="utf-8").splitlines()
        current_category = ""
        output: List[Dict[str, str]] = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            lower_line = line.lower()
            if lower_line in QUESTION_SECTIONS:
                current_category = QUESTION_SECTIONS[lower_line]
                continue

            if line.startswith("- ") and current_category:
                question = line[2:].strip()
                if question:
                    output.append(
                        {
                            "question": question,
                            "category": current_category,
                            "source_file": file_path.name,
                        }
                    )
        return output

    def _parse_external_questions_file(self, file_path: Path) -> List[Dict[str, str]]:
        """
        Parse de arquivo markdown em formato de tabela:
        | # | Pergunta | Saida esperada |
        """
        if not file_path.exists():
            return []
        output: List[Dict[str, str]] = []
        section_category = "general"
        lines = file_path.read_text(encoding="utf-8").splitlines()
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("## "):
                title = line[3:].lower()
                if "baixa" in title:
                    section_category = "baixa_complexidade"
                elif "média" in title or "media" in title:
                    section_category = "media_complexidade"
                elif "alta" in title:
                    section_category = "alta_complexidade"
                elif "profissional" in title:
                    section_category = "profissional"
                elif "treino" in title:
                    section_category = "treino_modelo"
                elif "previsão" in title or "previsao" in title:
                    section_category = "previsao"
                else:
                    section_category = "general"
                continue

            if not line.startswith("|"):
                continue
            if "|---" in line or "| # |" in line.lower():
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 2:
                continue
            idx_text = cols[0]
            question = cols[1]
            expected_output = cols[2] if len(cols) > 2 else ""
            if not question or not idx_text.isdigit():
                continue
            output.append(
                {
                    "question": question,
                    "category": section_category,
                    "source_file": file_path.as_posix(),
                    "expected_output": expected_output,
                }
            )
        return output

    def _build_user_journey_inputs(
        self,
        routes: List[Dict[str, str]],
        req: RegenRequest,
        round_number: int,
        questions_by_scope: Dict[str, List[Dict[str, str]]],
    ) -> List[Dict[str, Any]]:
        """
        Testes como usuario: perguntas externas por escopo -> endpoints de linguagem natural / chat / analise.
        """
        by_path = {r.get("raw_path") or r["path"]: r for r in routes}
        extra: List[Dict[str, Any]] = []
        for scope in req.scopes:
            questions = questions_by_scope.get(scope) or []
            if not questions:
                continue
            if scope == "InteligenciaDados":
                extra.extend(
                    self._user_journey_inteligencia_dados(
                        by_path, req, round_number, questions
                    )
                )
            elif scope == "FinOps":
                extra.extend(self._user_journey_finops(by_path, req, round_number, questions))
            elif scope == "CloudIAC":
                extra.extend(self._user_journey_cloudiac(by_path, req, round_number, questions))
            elif scope == "PulsoCSA/Python":
                extra.extend(self._user_journey_pulsocsa_python(by_path, req, round_number, questions))
            elif scope == "PulsoCSA/JavaScript":
                extra.extend(self._user_journey_pulsocsa_js(by_path, req, round_number, questions))
        return extra

    def _user_journey_inteligencia_dados(
        self,
        by_path: Dict[str, Dict[str, str]],
        req: RegenRequest,
        round_number: int,
        questions: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        chat_route = self._route_or_synthetic(by_path, "/inteligencia-dados/chat", "POST", "InteligenciaDados")
        insights_route = self._route_or_synthetic(
            by_path, "/inteligencia-dados/insights/generate", "POST", "InteligenciaDados"
        )
        query_route = self._route_or_synthetic(by_path, "/inteligencia-dados/query", "POST", "InteligenciaDados")
        extra_inputs: List[Dict[str, Any]] = []
        for idx, q in enumerate(questions):
            question_text = q.get("question", req.objective)
            route = self._select_user_route_for_question(
                question_text=question_text,
                chat_route=chat_route,
                insights_route=insights_route,
                query_route=query_route,
            )
            if not route:
                continue
            method = route["method"].upper()
            raw_path = route.get("raw_path") or route["path"]
            resolved_path = self._resolve_path_params(route["path"])
            payload = self._build_user_payload(raw_path=raw_path, question_text=question_text, round_number=round_number)
            extra_inputs.append(
                {
                    "path": resolved_path,
                    "raw_path": raw_path,
                    "method": method,
                    "scope": "InteligenciaDados",
                    "query": {
                        "regen_round": str(round_number),
                        "regen_mode": "user_journey",
                        "regen_case_index": str(idx + 1),
                        "regen_question": question_text[:120],
                    },
                    "json": payload,
                    "timeout_s": 90 if "/inteligencia-dados/chat" in raw_path.lower() else 45,
                    "question": question_text,
                    "question_source_file": q.get("source_file"),
                    "question_category": q.get("category", "general"),
                    "question_expected_output": q.get("expected_output"),
                }
            )
        return extra_inputs

    def _user_journey_finops(
        self,
        by_path: Dict[str, Dict[str, str]],
        req: RegenRequest,
        round_number: int,
        questions: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        route = self._route_or_synthetic(by_path, "/finops/chat", "POST", "FinOps")
        out: List[Dict[str, Any]] = []
        raw_path = route.get("raw_path") or route["path"]
        resolved_path = self._resolve_path_params(route["path"])
        for idx, q in enumerate(questions):
            question_text = q.get("question", req.objective)
            out.append(
                {
                    "path": resolved_path,
                    "raw_path": raw_path,
                    "method": "POST",
                    "scope": "FinOps",
                    "query": {
                        "regen_round": str(round_number),
                        "regen_mode": "user_journey",
                        "regen_case_index": str(idx + 1),
                        "regen_question": question_text[:120],
                    },
                    "json": {
                        "mensagem": question_text,
                        "id_requisicao": f"regen-finops-r{round_number}-{idx + 1}",
                        "usuario": req.usuario,
                    },
                    "timeout_s": 60,
                    "question": question_text,
                    "question_source_file": q.get("source_file"),
                    "question_category": q.get("category", "general"),
                    "question_expected_output": q.get("expected_output"),
                }
            )
        return out

    def _user_journey_cloudiac(
        self,
        by_path: Dict[str, Dict[str, str]],
        req: RegenRequest,
        round_number: int,
        questions: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        route = self._route_or_synthetic(by_path, "/infra/analyze", "POST", "CloudIAC")
        out: List[Dict[str, Any]] = []
        raw_path = route.get("raw_path") or route["path"]
        resolved_path = self._resolve_path_params(route["path"])
        for idx, q in enumerate(questions):
            question_text = q.get("question", req.objective)
            out.append(
                {
                    "path": resolved_path,
                    "raw_path": raw_path,
                    "method": "POST",
                    "scope": "CloudIAC",
                    "query": {
                        "regen_round": str(round_number),
                        "regen_mode": "user_journey",
                        "regen_case_index": str(idx + 1),
                        "regen_question": question_text[:120],
                    },
                    "json": {
                        "root_path": ".",
                        "tenant_id": "regenai",
                        "id_requisicao": f"regen-infra-r{round_number}-{idx + 1}",
                        "user_request": question_text,
                    },
                    "timeout_s": 120,
                    "question": question_text,
                    "question_source_file": q.get("source_file"),
                    "question_category": q.get("category", "general"),
                    "question_expected_output": q.get("expected_output"),
                }
            )
        return out

    def _user_journey_pulsocsa_python(
        self,
        by_path: Dict[str, Dict[str, str]],
        req: RegenRequest,
        round_number: int,
        questions: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        route = self._route_or_synthetic(by_path, "/comprehension/run", "POST", "PulsoCSA/Python")
        return self._user_journey_comprehension(route, req, round_number, questions, "PulsoCSA/Python", 45)

    def _user_journey_pulsocsa_js(
        self,
        by_path: Dict[str, Dict[str, str]],
        req: RegenRequest,
        round_number: int,
        questions: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        route = self._route_or_synthetic(by_path, "/comprehension-js/run", "POST", "PulsoCSA/JavaScript")
        return self._user_journey_comprehension(route, req, round_number, questions, "PulsoCSA/JavaScript", 45)

    def _user_journey_comprehension(
        self,
        route: Dict[str, str],
        req: RegenRequest,
        round_number: int,
        questions: List[Dict[str, str]],
        scope: str,
        timeout_s: int,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        raw_path = route.get("raw_path") or route["path"]
        resolved_path = self._resolve_path_params(route["path"])
        for idx, q in enumerate(questions):
            question_text = q.get("question", req.objective)
            out.append(
                {
                    "path": resolved_path,
                    "raw_path": raw_path,
                    "method": "POST",
                    "scope": scope,
                    "query": {
                        "regen_round": str(round_number),
                        "regen_mode": "user_journey",
                        "regen_case_index": str(idx + 1),
                        "regen_question": question_text[:120],
                    },
                    "json": {
                        "usuario": req.usuario,
                        "prompt": question_text,
                        "id_requisicao": f"regen-csa-r{round_number}-{idx + 1}",
                    },
                    "timeout_s": timeout_s,
                    "question": question_text,
                    "question_source_file": q.get("source_file"),
                    "question_category": q.get("category", "general"),
                    "question_expected_output": q.get("expected_output"),
                }
            )
        return out

    @staticmethod
    def _select_user_route_for_question(
        question_text: str,
        chat_route: Optional[Dict[str, str]],
        insights_route: Optional[Dict[str, str]],
        query_route: Optional[Dict[str, str]],
    ) -> Optional[Dict[str, str]]:
        text = (question_text or "").lower()
        if any(t in text for t in ["sql", "tabela", "coluna", "dataset", "registros", "nulos", "schema"]):
            return query_route or chat_route or insights_route
        if any(t in text for t in ["gráfico", "grafico", "distribuição", "distribuicao", "correlação", "correlacao"]):
            return insights_route or chat_route or query_route
        return chat_route or insights_route or query_route

    @staticmethod
    def _build_user_payload(raw_path: str, question_text: str, round_number: int) -> Dict[str, Any]:
        path = (raw_path or "").lower()
        if "/inteligencia-dados/query" in path:
            return {
                "prompt": question_text,
                "db_config": {
                    "db_type": "mongodb",
                    "uri": "mongodb://localhost:27017",
                    "database": "pulso_database",
                },
            }
        if "/inteligencia-dados/insights/generate" in path:
            return {
                "prompt": question_text,
                "id_requisicao": f"regen-r{round_number}",
            }
        return {
            "mensagem": question_text,
            "id_requisicao": f"regen-r{round_number}",
        }

    def _get_operation_schema(
        self,
        openapi_schema: Optional[Dict[str, Any]],
        raw_path: str,
        method: str,
    ) -> Dict[str, Any]:
        if not openapi_schema:
            return {}
        paths = openapi_schema.get("paths") or {}
        path_item = paths.get(raw_path) or {}
        return path_item.get(method.lower()) or {}

    def _inject_required_query_params(
        self,
        query: Dict[str, str],
        operation: Dict[str, Any],
        openapi_schema: Optional[Dict[str, Any]],
        question_text: str,
        round_number: int,
    ) -> Dict[str, str]:
        output = dict(query)
        for param in operation.get("parameters", []):
            resolved_param = self._resolve_schema_ref(param, operation_root=openapi_schema)
            if resolved_param.get("in") != "query":
                continue
            if not resolved_param.get("required"):
                continue
            name = resolved_param.get("name")
            if not name or name in output:
                continue
            schema = resolved_param.get("schema") or {}
            output[name] = str(
                self._coerce_special_values(
                    key=name,
                    value=self._sample_from_schema(schema, {}, depth=0),
                    question_text=question_text,
                    round_number=round_number,
                )
            )
        return output

    def _build_body_from_openapi(
        self,
        operation: Dict[str, Any],
        openapi_schema: Optional[Dict[str, Any]],
        question_text: str,
        round_number: int,
        req: RegenRequest,
        raw_path: str,
    ) -> Dict[str, Any]:
        if not operation:
            return {}
        request_body = operation.get("requestBody") or {}
        if "$ref" in request_body:
            request_body = self._resolve_schema_ref(request_body, openapi_schema)

        content = request_body.get("content") or {}
        media = content.get("application/json")
        if media is None and content:
            media = next(iter(content.values()))
        if not media:
            return {}

        schema = media.get("schema") or {}
        components = (openapi_schema or {}).get("components") or {}
        base = self._sample_from_schema(schema, components, depth=0)
        if not isinstance(base, dict):
            return {}

        context_defaults: Dict[str, Any] = {
            "objective": req.objective,
            "question": question_text,
            "mensagem": question_text,
            "prompt": question_text,
            "id_requisicao": f"regen-r{round_number}",
            "agendamento_id": "1",
            "usuario": req.usuario,
            "origem": "regenai",
        }
        for key, value in list(base.items()):
            base[key] = self._coerce_special_values(
                key=key,
                value=value,
                question_text=question_text,
                round_number=round_number,
            )
        self._enrich_known_nested_defaults(base)
        self._apply_route_specific_defaults(raw_path=raw_path, payload=base)
        for key, value in context_defaults.items():
            if key in base and (base[key] in ("", None, "sample", 0)):
                base[key] = value
        return base

    def _sample_from_schema(self, schema: Dict[str, Any], components: Dict[str, Any], depth: int) -> Any:
        if depth > 4:
            return "sample"

        resolved = self._resolve_schema_ref(schema, {"components": components})
        if not isinstance(resolved, dict):
            return "sample"

        if "enum" in resolved and resolved["enum"]:
            return resolved["enum"][0]

        for composite in ("oneOf", "anyOf", "allOf"):
            options = resolved.get(composite) or []
            if options:
                if composite == "allOf":
                    merged: Dict[str, Any] = {}
                    for option in options:
                        part = self._sample_from_schema(option, components, depth + 1)
                        if isinstance(part, dict):
                            merged.update(part)
                    if merged:
                        return merged
                return self._sample_from_schema(options[0], components, depth + 1)

        schema_type = resolved.get("type")
        if schema_type == "object" or "properties" in resolved:
            properties = resolved.get("properties") or {}
            required = resolved.get("required") or []
            if not required:
                required = list(properties.keys())[:2]
            output: Dict[str, Any] = {}
            for key in required:
                prop_schema = properties.get(key) or {}
                output[key] = self._sample_from_schema(prop_schema, components, depth + 1)
            return output
        if schema_type == "array":
            item_schema = resolved.get("items") or {}
            return [self._sample_from_schema(item_schema, components, depth + 1)]
        if schema_type == "integer":
            return 1
        if schema_type == "number":
            return 1.0
        if schema_type == "boolean":
            return True
        if resolved.get("format") == "date-time":
            return "2026-03-16T00:00:00Z"
        if resolved.get("format") == "date":
            return "2026-03-16"
        return "sample"

    def _resolve_schema_ref(self, node: Any, operation_root: Optional[Dict[str, Any]]) -> Any:
        if not isinstance(node, dict):
            return node
        ref = node.get("$ref")
        if not ref:
            return node
        if not operation_root:
            return node
        if not ref.startswith("#/"):
            return node
        target: Any = operation_root
        for token in ref[2:].split("/"):
            target = target.get(token) if isinstance(target, dict) else None
            if target is None:
                return node
        return target

    @staticmethod
    def _coerce_special_values(key: str, value: Any, question_text: str, round_number: int) -> Any:
        lower_key = key.lower()
        if "id_requisicao" in lower_key:
            return f"regen-r{round_number}"
        if "agendamento_id" in lower_key:
            return "1"
        if lower_key in {"prompt", "mensagem", "pergunta", "question"}:
            return question_text
        if lower_key in {"usuario", "user"}:
            return "regenai"
        return value

    @staticmethod
    def _enrich_known_nested_defaults(payload: Dict[str, Any]) -> None:
        db_config = payload.get("db_config")
        if isinstance(db_config, dict):
            # Mantem comportamento mínimo: não força conexão SQL de rede por padrão.
            db_config.setdefault("db_type", "sqlite")
            db_config.setdefault("database", "regenai.db")
        if "dataset_ref" in payload and payload.get("dataset_ref") in ("", None):
            payload["dataset_ref"] = "dataset_ref_regen"
        if "model_ref" in payload and payload.get("model_ref") in ("", None):
            payload["model_ref"] = "model_ref_regen"

    @staticmethod
    def _apply_route_specific_defaults(raw_path: str, payload: Dict[str, Any]) -> None:
        path = (raw_path or "").lower()
        if "/inteligencia-dados/query" in path or "/inteligencia-dados/captura-dados" in path:
            # Evita 500 por conexão SQL externa inexistente durante ciclo automático.
            payload["db_config"] = {
                "db_type": "mongodb",
                "uri": "mongodb://localhost:27017",
                "database": "pulso_database",
            }
        if "/inteligencia-dados/captura-dados" in path:
            payload.setdefault("incluir_amostra", True)
            payload.setdefault("max_rows_amostra", 200)

    @staticmethod
    def _resolve_path_params(path: str) -> str:
        def _replace(match: re.Match[str]) -> str:
            key = match.group(1).lower()
            if "id" in key:
                return "1"
            return "sample"

        return re.sub(r"\{([^}]+)\}", _replace, path)

