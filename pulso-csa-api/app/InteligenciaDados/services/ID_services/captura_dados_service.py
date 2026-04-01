# Serviço de Captura de Dados – estrutura de bases externas (MySQL, PostgreSQL, SQL Server, SQLite, Oracle, MongoDB)
import logging
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from bson import ObjectId

from app.InteligenciaDados.core.ID_core.mongo_connection import MongoConnection
from app.InteligenciaDados.core.ID_core.sql_connection_factory import create_sql_connection, SQL_DB_TYPES
from app.core.openai.openai_client import get_openai_client
from app.prompts.loader import load_prompt
from app.InteligenciaDados.models.ID_models.captura_dados_models import CapturaDadosInput, CapturaDadosOutput
from app.InteligenciaDados.storage.id_artifacts.id_artifacts_io import ensure_artifact_dir, save_dataframe
from app.utils.db_config_validation import validar_db_config

logger = logging.getLogger(__name__)


def _is_sql_config(c: Dict[str, Any]) -> bool:
    db_type = (c.get("db_type") or "").strip().lower()
    if db_type in SQL_DB_TYPES:
        if db_type == "sqlite":
            return "database" in c or "path" in c
        return "database" in c and "host" in c and "user" in c and "password" in c
    if "database" in c and "host" in c and "user" in c and "password" in c:
        return True
    return (c.get("database") or c.get("path")) and "host" not in c and "uri" not in c


def _is_mongo_config(c: Dict[str, Any]) -> bool:
    return "uri" in c or ("database" in c and ("host" in c or "uri" in c))


def _sanitize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Converte ObjectId, datetime e outros tipos BSON para tipos serializáveis em Parquet."""
    result = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, dict):
            result[k] = _sanitize_mongo_doc(v)
        elif isinstance(v, list):
            result[k] = [
                _sanitize_mongo_doc(x) if isinstance(x, dict) else str(x) if isinstance(x, ObjectId) else x
                for x in v
            ]
        else:
            result[k] = v
    return result


class CapturaDadosService:
    """
    Conecta à base externa, detecta tipo (SQL/NoSQL), extrai esqueleto
    (tabelas, índices, contagens), gera consultas de exploração e opcionalmente
    amostra em Parquet. Usa LLM para descrever o teor dos dados.
    """

    def __init__(self) -> None:
        self._llm = get_openai_client()

    def run(self, payload: CapturaDadosInput) -> CapturaDadosOutput:
        id_requisicao = payload.id_requisicao
        usuario = payload.usuario or "default"
        db_config = payload.db_config if isinstance(payload.db_config, dict) else payload.db_config.model_dump()
        # Validação de db_config contra allowlist
        is_valid, error_msg = validar_db_config(db_config)
        if not is_valid:
            raise ValueError(error_msg)
        tipo_base = payload.tipo_base

        if tipo_base is None:
            tipo_base = "SQL" if _is_sql_config(db_config) else "NoSQL"

        if tipo_base == "SQL" or _is_sql_config(db_config):
            captura = self._captura_sql(db_config)
        else:
            captura = self._captura_mongo(db_config)

        teor = self._descrever_teor_com_llm(captura)
        captura["teor_dados"] = teor

        if payload.incluir_amostra and captura.get("tabelas"):
            dataset_ref = self._extrair_e_salvar_amostra(
                db_config, tipo_base, captura["tabelas"], usuario, id_requisicao, payload.max_rows_amostra
            )
            if dataset_ref:
                captura["dataset_ref"] = dataset_ref

        return CapturaDadosOutput(
            id_requisicao=id_requisicao,
            captura_dados=captura,
        )

    def _get_schema_name(self, db_config: Dict[str, Any]) -> str:
        db_type = (db_config.get("db_type") or "mysql").strip().lower()
        if db_type == "sqlite":
            return "main"
        if db_type in ("sqlserver", "mssql"):
            return db_config.get("schema") or "dbo"
        return db_config.get("database") or db_config.get("path", "")

    def _captura_sql(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        conn = create_sql_connection(db_config)
        schema_name = self._get_schema_name(db_config)
        try:
            tables = conn.get_table_names(schema_name)
            quantidade_registros: Dict[str, int] = {}
            indices: Dict[str, List[Dict[str, Any]]] = {}
            for t in tables:
                quantidade_registros[t] = conn.get_table_row_count(schema_name, t)
                idx = conn.get_table_indexes(schema_name, t)
                indices[t] = [{"name": x["name"], "columns": x["columns"], "unique": x["unique"]} for x in idx]
            consultas_exploracao = [
                conn.get_exploration_query(schema_name, t, 10) for t in tables[:20]
            ]
            return {
                "tipo_base": "SQL",
                "tabelas": tables,
                "quantidade_tabelas": len(tables),
                "quantidade_registros": quantidade_registros,
                "indices": indices,
                "consultas_exploracao": consultas_exploracao,
                "teor_dados": "",
            }
        finally:
            conn.close()

    def _captura_mongo(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        conn = MongoConnection(db_config)
        try:
            collections = conn.list_collection_names()
            quantidade_registros: Dict[str, int] = {}
            indices: Dict[str, List[Dict[str, Any]]] = {}
            for c in collections:
                quantidade_registros[c] = conn.count_documents(c)
                raw_idx = conn.get_indexes(c)
                indices[c] = [
                    {"name": idx.get("name", ""), "key": list(idx.get("key", {}).keys())}
                    for idx in raw_idx
                ]
            consultas_exploracao = [
                f"db.{c}.find().limit(10)" for c in collections[:20]
            ]
            return {
                "tipo_base": "NoSQL",
                "tabelas": collections,
                "quantidade_tabelas": len(collections),
                "quantidade_registros": quantidade_registros,
                "indices": indices,
                "consultas_exploracao": consultas_exploracao,
                "teor_dados": "",
            }
        finally:
            conn.close()

    def _extrair_e_salvar_amostra(
        self,
        db_config: Dict[str, Any],
        tipo_base: str,
        tabelas: List[str],
        usuario: str,
        id_requisicao: str,
        max_rows: int,
    ) -> str:
        """Extrai amostra da primeira tabela/coleção e salva em Parquet. Retorna path ou vazio."""
        try:
            if tipo_base == "SQL":
                conn = create_sql_connection(db_config)
                schema_name = self._get_schema_name(db_config)
                if not tabelas:
                    return ""
                t = tabelas[0]
                q = conn.get_exploration_query(schema_name, t, limit=max_rows)
                rows = conn.execute_select(q)
                conn.close()
                if not rows:
                    return ""
                df = pd.DataFrame(rows)
            else:
                conn = MongoConnection(db_config)
                if not tabelas:
                    return ""
                docs = conn.find_sample(tabelas[0], limit=max_rows)
                conn.close()
                if not docs:
                    return ""
                # Converte ObjectId e outros tipos BSON para serializáveis (Parquet não suporta ObjectId)
                docs_sanitized = [_sanitize_mongo_doc(d) for d in docs]
                df = pd.json_normalize(docs_sanitized)
            path = save_dataframe(
                df, usuario, id_requisicao, f"amostra_captura_{id_requisicao[:8]}.parquet", subdir="datasets"
            )
            return path
        except Exception as e:
            logger.warning("Falha ao extrair/salvar amostra: %s", e)
            return ""

    def _descrever_teor_com_llm(self, captura: Dict[str, Any]) -> str:
        tabelas = captura.get("tabelas", [])[:20]
        if not tabelas:
            return "Nenhuma tabela ou coleção encontrada."
        prompt = load_prompt("ID_prompts/captura_dados_teor").format(tabelas=", ".join(tabelas))
        try:
            return self._llm.generate_text(prompt, use_fast_model=True).strip() or "Dados diversos."
        except Exception as e:
            logger.warning("LLM teor_dados falhou: %s", e)
            return "Dados diversos (descrição não disponível)."
