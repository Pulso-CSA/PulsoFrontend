#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮SQL Server – Conexão ID❯━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from typing import Any, Dict, List

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .sql_connection_base import SQLConnectionBase, validate_identifier

__all__ = ["SQLServerConnection"]

DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_CONNECT_TIMEOUT = 30

# Drivers comuns; usar o primeiro disponível
ODBC_DRIVERS = [
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 11 for SQL Server",
    "SQL Server Native Client 11.0",
]


def _build_paginated_sql(sql: str, limit: int, offset: int) -> str:
    """Envolve SELECT em subquery com OFFSET/FETCH (SQL Server)."""
    base = sql.rstrip(";").rstrip()
    return f"SELECT * FROM ({base}) AS _page OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"


class SQLServerConnection(SQLConnectionBase):
    """Conexão SQL Server para Inteligência de Dados. Read-only."""

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
            port = self._db_config.get("port", 1433)
            database = self._db_config["database"]
            driver = self._db_config.get("driver") or ODBC_DRIVERS[0]
            driver_encoded = driver.replace(" ", "+")
            connection_url = (
                f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}"
                f"?driver={driver_encoded}"
            )
            connect_timeout = self._db_config.get("connect_timeout", DEFAULT_CONNECT_TIMEOUT)
            return create_engine(
                connection_url,
                pool_pre_ping=True,
                pool_size=self._db_config.get("pool_size", DEFAULT_POOL_SIZE),
                max_overflow=self._db_config.get("max_overflow", DEFAULT_MAX_OVERFLOW),
                pool_recycle=3600,
                connect_args={"timeout": connect_timeout},
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
        return f"SELECT TOP {limit} * FROM [{database}].[{table}]"

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
        # SQL Server usa [schema].[table]
        sql = text(f"SELECT COUNT(*) FROM [{database}].[{table}]")
        with self._engine.connect() as conn:
            row = conn.execute(sql).fetchone()
        return row[0] if row else 0

    def get_table_indexes(self, database: str, table: str) -> List[Dict[str, Any]]:
        validate_identifier(database)
        validate_identifier(table)
        sql = text("""
            SELECT i.name, c.name AS col_name, i.is_unique
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            JOIN sys.tables t ON i.object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = :db AND t.name = :tbl AND i.type > 0
            ORDER BY i.name, ic.key_ordinal
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
