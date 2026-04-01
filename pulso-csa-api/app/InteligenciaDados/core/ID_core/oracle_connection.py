#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Oracle – Conexão ID❯━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Any, Dict, List

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .sql_connection_base import SQLConnectionBase, validate_identifier

__all__ = ["OracleConnection"]

DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_CONNECT_TIMEOUT = 30


def _build_paginated_sql(sql: str, limit: int, offset: int) -> str:
    """Envolve SELECT em subquery com OFFSET/FETCH (Oracle 12c+)."""
    base = sql.rstrip(";").rstrip()
    return f"SELECT * FROM ({base}) OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"


class OracleConnection(SQLConnectionBase):
    """Conexão Oracle para Inteligência de Dados. Read-only."""

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
            port = self._db_config.get("port", 1521)
            database = self._db_config["database"]  # service_name ou SID
            service_name = self._db_config.get("service_name") or database
            connection_url = (
                f"oracle+oracledb://{user}:{password}@{host}:{port}/"
                f"?service_name={service_name}"
            )
            connect_args: Dict[str, Any] = {}
            if self._db_config.get("connect_timeout", DEFAULT_CONNECT_TIMEOUT):
                connect_args["timeout"] = self._db_config.get(
                    "connect_timeout", DEFAULT_CONNECT_TIMEOUT
                )
            return create_engine(
                connection_url,
                pool_pre_ping=True,
                pool_size=self._db_config.get("pool_size", DEFAULT_POOL_SIZE),
                max_overflow=self._db_config.get("max_overflow", DEFAULT_MAX_OVERFLOW),
                pool_recycle=3600,
                connect_args=connect_args or None,
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
        paginated = _build_paginated_sql(sql, limit, offset)
        return self.execute_select(paginated)

    def get_exploration_query(self, database: str, table: str, limit: int = 10) -> str:
        validate_identifier(database)
        validate_identifier(table)
        return f'SELECT * FROM "{database.upper()}"."{table.upper()}" WHERE ROWNUM <= {limit}'

    def get_table_names(self, database: str) -> List[str]:
        validate_identifier(database)
        sql = text(
            "SELECT table_name FROM all_tables WHERE owner = :db ORDER BY table_name"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(sql, {"db": database.upper()}).fetchall()
        return [r[0] for r in rows]

    def get_column_info(self, database: str, table: str) -> List[Dict[str, Any]]:
        validate_identifier(database)
        validate_identifier(table)
        sql = text("""
            SELECT column_name, data_type, nullable
            FROM all_tab_columns
            WHERE owner = :db AND table_name = :tbl
            ORDER BY column_id
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(
                sql, {"db": database.upper(), "tbl": table.upper()}
            ).fetchall()
        return [
            {
                "column_name": r[0],
                "data_type": r[1],
                "is_nullable": "YES" if r[2] == "Y" else "NO",
            }
            for r in rows
        ]

    def get_table_row_count(self, database: str, table: str) -> int:
        validate_identifier(database)
        validate_identifier(table)
        sql = text(
            f'SELECT COUNT(*) FROM "{database.upper()}"."{table.upper()}"'
        )
        with self._engine.connect() as conn:
            row = conn.execute(sql).fetchone()
        return row[0] if row else 0

    def get_table_indexes(self, database: str, table: str) -> List[Dict[str, Any]]:
        validate_identifier(database)
        validate_identifier(table)
        sql = text("""
            SELECT i.index_name, c.column_name, i.uniqueness
            FROM all_indexes i
            JOIN all_ind_columns c ON i.owner = c.index_owner AND i.index_name = c.index_name
            WHERE i.table_owner = :db AND i.table_name = :tbl
            ORDER BY i.index_name, c.column_position
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(
                sql, {"db": database.upper(), "tbl": table.upper()}
            ).fetchall()
        by_name: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            iname, cname, uniqueness = r[0], r[1], r[2]
            if iname not in by_name:
                by_name[iname] = {
                    "name": iname,
                    "columns": [],
                    "unique": uniqueness == "UNIQUE",
                }
            if cname not in by_name[iname]["columns"]:
                by_name[iname]["columns"].append(cname)
        return list(by_name.values())

    def close(self) -> None:
        self._engine.dispose()
