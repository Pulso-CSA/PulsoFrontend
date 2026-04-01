#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮PostgreSQL – Conexão ID❯━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Any, Dict, List

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .sql_connection_base import SQLConnectionBase, validate_identifier

__all__ = ["PostgresConnection"]

DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_CONNECT_TIMEOUT = 30


class PostgresConnection(SQLConnectionBase):
    """Conexão PostgreSQL para Inteligência de Dados. Read-only."""

    def __init__(self, db_config: Dict[str, Any]) -> None:
        if not isinstance(db_config, dict):
            raise ValueError("db_config must be a dictionary")
        self._db_config = db_config
        self._engine: Engine = self._create_engine()

    def _create_engine(self) -> Engine:
        try:
            user = self._db_config["user"]
            password = self._db_config["password"]
            host = self._db_config["host"]
            port = self._db_config.get("port", 5432)
            database = self._db_config["database"]
            connection_url = (
                f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
            )
            connect_timeout = self._db_config.get("connect_timeout", DEFAULT_CONNECT_TIMEOUT)
            return create_engine(
                connection_url,
                pool_pre_ping=True,
                pool_size=self._db_config.get("pool_size", DEFAULT_POOL_SIZE),
                max_overflow=self._db_config.get("max_overflow", DEFAULT_MAX_OVERFLOW),
                pool_recycle=3600,
                connect_args={"connect_timeout": connect_timeout},
                future=True,
            )
        except KeyError as exc:
            raise ValueError(f"Missing database configuration field: {exc}") from exc

    def execute_select(self, sql: str) -> List[Dict[str, Any]]:
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("SQL query must be a non-empty string")
        try:
            with self._engine.connect() as connection:
                result = connection.execute(text(sql))
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as exc:
            raise RuntimeError(f"Database execution error: {exc}") from exc

    def execute_select_paginated(
        self, sql: str, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        s = sql.strip().upper()
        if not s.startswith(("SELECT", "WITH")):
            raise ValueError("Only SELECT queries are allowed")
        limit = max(1, min(limit, 50_000))
        offset = max(0, offset)
        paginated = f"{sql.rstrip(';').rstrip()} LIMIT {limit} OFFSET {offset}"
        return self.execute_select(paginated)

    def get_table_names(self, database: str) -> List[str]:
        validate_identifier(database)
        sql = text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = :db AND table_type = 'BASE TABLE' ORDER BY table_name"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"db": database}).fetchall()
        return [r[0] for r in rows]

    def get_column_info(self, database: str, table: str) -> List[Dict[str, Any]]:
        validate_identifier(database)
        validate_identifier(table)
        sql = text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema = :db AND table_name = :tbl ORDER BY ordinal_position"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"db": database, "tbl": table}).fetchall()
        return [
            {"column_name": r[0], "data_type": r[1], "is_nullable": r[2]}
            for r in rows
        ]

    def get_table_row_count(self, database: str, table: str) -> int:
        validate_identifier(database)
        validate_identifier(table)
        sql = text(f'SELECT COUNT(*) FROM "{database}"."{table}"')
        with self._engine.connect() as conn:
            row = conn.execute(sql).fetchone()
        return row[0] if row else 0

    def get_exploration_query(self, database: str, table: str, limit: int = 10) -> str:
        validate_identifier(database)
        validate_identifier(table)
        return f'SELECT * FROM "{database}"."{table}" LIMIT {limit}'

    def get_table_indexes(self, database: str, table: str) -> List[Dict[str, Any]]:
        validate_identifier(database)
        validate_identifier(table)
        sql = text("""
            SELECT i.relname, a.attname, ix.indisunique
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey) AND a.attnum > 0 AND NOT a.attisdropped
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = :db AND t.relname = :tbl
            ORDER BY i.relname, a.attnum
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"db": database, "tbl": table}).fetchall()
        by_name: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            iname, cname, is_unique = r[0], r[1], r[2]
            if iname not in by_name:
                by_name[iname] = {"name": iname, "columns": [], "unique": bool(is_unique)}
            if cname not in by_name[iname]["columns"]:
                by_name[iname]["columns"].append(cname)
        return list(by_name.values())

    def close(self) -> None:
        self._engine.dispose()
