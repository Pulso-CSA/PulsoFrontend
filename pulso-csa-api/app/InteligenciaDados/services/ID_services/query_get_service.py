import json
import logging
import re
from typing import Any, Dict, List

from app.InteligenciaDados.core.ID_core.sql_connection_factory import create_sql_connection
from app.core.openai.openai_client import get_openai_client
from app.core.openai.rag_trainer import load_rag_index
from app.prompts.loader import load_prompt
from app.InteligenciaDados.models.ID_models.query_get_models import (
    QueryGetInput,
    QueryGetOutput,
    QueryGetRawResult,
)
from app.utils.query_get_prompt import QueryGetPromptBuilder
from app.storage.database.ID_database.query_get_database import QueryGetDatabase
from app.utils.db_config_validation import validar_db_config

logger = logging.getLogger(__name__)


class QueryGetService:
    """
    Serviço de Inteligência de Dados:
    NL -> SQL -> DB -> NL
    """

    def __init__(self) -> None:
        self._llm_client = get_openai_client()
        self._rag_index = load_rag_index()

        self._forbidden_sql_patterns = [
            r"\bINSERT\b",
            r"\bUPDATE\b",
            r"\bDELETE\b",
            r"\bDROP\b",
            r"\bTRUNCATE\b",
            r"\bALTER\b",
            r"\bCREATE\b",
            r"\bGRANT\b",
            r"\bREVOKE\b",
        ]

    # ==========================
    # Public API
    # ==========================

    def _is_mongo_config(self, c: Dict[str, Any]) -> bool:
        """Detecta se db_config é MongoDB (NoSQL)."""
        uri = c.get("uri") or ""
        db_type = (c.get("db_type") or "").strip().lower()
        return (
            (isinstance(uri, str) and uri.startswith("mongodb://"))
            or db_type in ("nosql", "mongodb")
        )

    def run(self, payload: QueryGetInput) -> QueryGetOutput:
        logger.info("QueryGetService.run | start")

        db_config = payload.db_config if isinstance(payload.db_config, dict) else payload.db_config.model_dump()

        # MongoDB: /query é SQL-only; orientar uso do /chat
        if self._is_mongo_config(db_config):
            return QueryGetOutput(
                answer="O endpoint de consulta atual suporta apenas bancos SQL. Para MongoDB, use o chat de Inteligência de Dados e envie sua pergunta em linguagem natural (ex.: 'mostre as 5 primeiras linhas'). O chat fará a captura e responderá com os dados.",
                generated_sql="",
                raw_result=None,
            )

        # Validação de db_config contra allowlist
        is_valid, error_msg = validar_db_config(db_config)
        if not is_valid:
            return QueryGetOutput(
                answer=f"Erro de validação: {error_msg}",
                generated_sql=None,
                raw_result=None,
            )
        user_prompt = payload.prompt.strip()

        # 1️⃣ Schema do banco (real)
        schema_text = self._build_database_schema_text(db_config)

        # 2️⃣ Few-shot via RAG
        few_shots = self._retrieve_few_shots(user_prompt)

        # 3️⃣ Prompt NL -> SQL
        prompt_builder = QueryGetPromptBuilder(
            database_schema=schema_text,
            few_shot_examples=few_shots,
        )
        sql_prompt = prompt_builder.build(user_prompt=user_prompt)

        # 4️⃣ Geração SQL
        generated_sql = self._normalize_sql(
            self._llm_client.generate_text(sql_prompt, use_fast_model=True)
        )

        # 5️⃣ Validação de segurança
        if not self._is_sql_safe(generated_sql):
            return QueryGetOutput(
                answer="Não foi possível gerar uma consulta SQL segura para essa solicitação.",
                generated_sql=generated_sql,
                raw_result=None,
            )

        if self._is_invalid_request_sql(generated_sql):
            return QueryGetOutput(
                answer="A pergunta não pôde ser respondida com base no schema disponível.",
                generated_sql=generated_sql,
                raw_result=None,
            )

        # 6️⃣ Execução (conexão fechada automaticamente em fetch)
        database = QueryGetDatabase(db_config=db_config)
        raw_result = database.fetch(generated_sql)

        # 7️⃣ Humanização
        answer = self._humanize_answer(
            user_prompt=user_prompt,
            generated_sql=generated_sql,
            raw_result=raw_result,
        )

        logger.info("QueryGetService.run | done")

        return QueryGetOutput(
            answer=answer,
            generated_sql=generated_sql,
            raw_result=raw_result,
        )

    # ==========================
    # Schema
    # ==========================

    def _build_database_schema_text(self, db_config: Dict[str, Any]) -> str:
        conn = create_sql_connection(db_config)
        db_type = (db_config.get("db_type") or "mysql").strip().lower()
        db_name = "main" if db_type == "sqlite" else (db_config.get("database") or db_config.get("path", ""))
        try:
            table_names = conn.get_table_names(db_name)
            table_map: Dict[str, List[str]] = {}
            for t in table_names:
                cols_info = conn.get_column_info(db_name, t)
                table_map[t] = [f"{c['column_name']}:{c['data_type']}" for c in cols_info]
            lines = [f"- {name}({', '.join(table_map.get(name, []))})" for name in table_names]
            return "TABLES AND COLUMNS:\n" + "\n".join(lines)
        finally:
            conn.close()

    # ==========================
    # RAG
    # ==========================

    def _retrieve_few_shots(self, user_prompt: str) -> List[Dict[str, str]]:
        """
        Busca exemplos SQL semanticamente similares no índice RAG.
        """
        docs = self._rag_index.similarity_search(user_prompt, k=3)

        examples = []
        for doc in docs:
            content = doc.page_content
            if "SQL:" in content and "QUESTION:" in content:
                try:
                    q = content.split("QUESTION:")[1].split("SQL:")[0].strip()
                    s = content.split("SQL:")[1].strip()
                    examples.append({"question": q, "sql": s})
                except Exception:
                    continue

        return examples

    # ==========================
    # Humanização
    # ==========================

    def _humanize_answer(
        self,
        user_prompt: str,
        generated_sql: str,
        raw_result: QueryGetRawResult,
    ) -> str:
        payload = {
            "question": user_prompt,
            "sql": generated_sql,
            "row_count": raw_result.row_count,
            "rows": raw_result.rows[:5],
        }

        dados_str = json.dumps(payload, ensure_ascii=False)
        prompt = load_prompt("ID_prompts/query_get_resposta_usuario").format(dados=dados_str)

        return self._llm_client.generate_text(prompt, use_fast_model=True)

    # ==========================
    # SQL safety
    # ==========================

    def _normalize_sql(self, sql: str) -> str:
        sql = sql.strip()
        sql = re.sub(r"^```.*?\n", "", sql)
        sql = re.sub(r"\n```$", "", sql)
        parts = [p.strip() for p in sql.split(";") if p.strip()]
        return parts[0] + ";" if parts else ""

    def _is_invalid_request_sql(self, sql: str) -> bool:
        return "invalid_request" in sql.lower()

    def _is_sql_safe(self, sql: str) -> bool:
        if not sql.upper().startswith(("SELECT", "WITH")):
            return False

        for pattern in self._forbidden_sql_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                return False

        return True