#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮SQLite – Conexão ID❯━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Any, Dict, List

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .sql_connection_base import SQLConnectionBase, validate_identifier

__all__ = ["SQLiteConnection"]


class SQLiteConnection(SQLConnectionBase):
    """Conexão SQLite para Inteligência de Dados. Read-only."""

    def __init__(self, db_config: Dict[str, Any]) -> None:
        if not isinstance(db_config, dict):
            raise ValueError("db_config must be a dictionary")
        self._db_config = db_config
        self._engine: Engine = self._create_engine()

    def _create_engine(self) -> Engine:
        database = self._db_config.get("database") or self._db_config.get("path", ":memory:")
        if database.startswith("/") or ":\\" in database or database.endswith(".db"):
            connection_url = f"sqlite:///{database}"
        else:
            connection_url = f"sqlite:///{database}"
        return create_engine(
            connection_url,
            future=True,
            connect_args={"check_same_thread": False},
        )

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

    def get_exploration_query(self, database: str, table: str, limit: int = 10) -> str:
        validate_identifier(table)
        tbl_esc = table.replace('"', '""')
        return f'SELECT * FROM "{tbl_esc}" LIMIT {limit}'

    def get_table_names(self, database: str) -> List[str]:
        validate_identifier(database)
        sql = text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [r[0] for r in rows]

    def get_column_info(self, database: str, table: str) -> List[Dict[str, Any]]:
        validate_identifier(table)
        tbl_esc = table.replace('"', '""')
        with self._engine.connect() as conn:
            rows = conn.execute(text(f'PRAGMA table_info("{tbl_esc}")')).fetchall()
        return [
            {"column_name": r[1], "data_type": r[2], "is_nullable": "YES" if r[3] == 0 else "NO"}
            for r in rows
        ]

    def get_table_row_count(self, database: str, table: str) -> int:
        validate_identifier(table)
        tbl_esc = table.replace('"', '""')
        with self._engine.connect() as conn:
            row = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl_esc}"')).fetchone()
        return row[0] if row else 0

    def get_table_indexes(self, database: str, table: str) -> List[Dict[str, Any]]:
        validate_identifier(table)
        tbl_esc = table.replace('"', '""')
        result: List[Dict[str, Any]] = []
        with self._engine.connect() as conn:
            idx_list = conn.execute(text(f'PRAGMA index_list("{tbl_esc}")')).fetchall()
            for idx in idx_list:
                idx_name = idx[1]
                is_unique = bool(idx[2])
                idx_esc = idx_name.replace('"', '""')
                info = conn.execute(text(f'PRAGMA index_info("{idx_esc}")')).fetchall()
                cols = [r[2] for r in info]
                result.append({"name": idx_name, "columns": cols, "unique": is_unique})
        return result

    def close(self) -> None:
        self._engine.dispose()
