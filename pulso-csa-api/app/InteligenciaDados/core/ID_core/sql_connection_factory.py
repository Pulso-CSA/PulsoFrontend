#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Factory – Conexões SQL ID❯━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import re
from typing import Any, Dict

from .mysql_connection import MySQLConnection
from .oracle_connection import OracleConnection
from .postgres_connection import PostgresConnection
from .sql_connection_base import SQLConnectionBase
from .sqlite_connection import SQLiteConnection
from .sqlserver_connection import SQLServerConnection

__all__ = ["create_sql_connection", "detect_sql_db_type", "SQL_DB_TYPES"]

SQL_DB_TYPES = frozenset({"mysql", "postgresql", "postgres", "sqlserver", "mssql", "sqlite", "oracle"})

# Portas padrão por banco
_PORT_MYSQL = 3306
_PORT_POSTGRES = 5432
_PORT_SQLSERVER = 1433
_PORT_ORACLE = 1521

# Extensões típicas de SQLite
_SQLITE_EXTENSIONS = (".db", ".sqlite", ".sqlite3")
_PATH_LIKE = re.compile(r"^[./\\]|[/\\]|:[\\/]|^[A-Za-z]:\\")


def detect_sql_db_type(db_config: Dict[str, Any]) -> str:
    """
    Detecta o tipo de banco SQL a partir dos dados do frontend, sem db_type explícito.

    Heurísticas (nesta ordem):
    1. SQLite: sem host, ou database/path com extensão .db/.sqlite, ou path-like
    2. driver com ODBC/SQL Server → SQL Server
    3. service_name presente → Oracle
    4. porta 5432 → PostgreSQL
    5. porta 1433 → SQL Server
    6. porta 1521 → Oracle
    7. porta 3306 ou ausente → MySQL (padrão)
    """
    if not isinstance(db_config, dict):
        return "mysql"

    db_type = (db_config.get("db_type") or "").strip().lower()
    if db_type in SQL_DB_TYPES:
        return "postgresql" if db_type == "postgres" else db_type

    host = db_config.get("host") or db_config.get("hostname")
    port = db_config.get("port")
    database = db_config.get("database") or db_config.get("path") or db_config.get("db")
    driver = str(db_config.get("driver") or "")
    service_name = db_config.get("service_name")

    # 1) SQLite: sem host ou config minimalista
    if not host:
        if database and (
            str(database).lower().endswith(_SQLITE_EXTENSIONS)
            or _PATH_LIKE.search(str(database))
            or database == ":memory:"
        ):
            return "sqlite"
        if database or db_config.get("path"):
            return "sqlite"

    # 2) Driver ODBC/SQL Server
    if driver and ("odbc" in driver.lower() or "sql server" in driver.lower()):
        return "sqlserver"

    # 3) service_name → Oracle
    if service_name:
        return "oracle"

    # 4) Porta como indicador
    try:
        p = int(port) if port is not None else None
    except (TypeError, ValueError):
        p = None

    if p == _PORT_POSTGRES:
        return "postgresql"
    if p == _PORT_SQLSERVER:
        return "sqlserver"
    if p == _PORT_ORACLE:
        return "oracle"
    if p == _PORT_MYSQL:
        return "mysql"

    # 5) Padrão MySQL para compatibilidade
    return "mysql"


def create_sql_connection(db_config: Dict[str, Any]) -> SQLConnectionBase:
    """
    Cria conexão SQL adequada ao db_type em db_config.

    db_type pode ser explícito ou inferido automaticamente via detect_sql_db_type.
    """
    if not isinstance(db_config, dict):
        raise ValueError("db_config must be a dictionary")

    db_type = detect_sql_db_type(db_config)

    if db_type in ("postgresql", "postgres"):
        return PostgresConnection(db_config)
    if db_type in ("sqlserver", "mssql"):
        return SQLServerConnection(db_config)
    if db_type == "sqlite":
        return SQLiteConnection(db_config)
    if db_type == "oracle":
        return OracleConnection(db_config)
    if db_type == "mysql":
        return MySQLConnection(db_config)

    raise ValueError(f"db_type não suportado: {db_type!r}. Use: {', '.join(sorted(SQL_DB_TYPES))}")
