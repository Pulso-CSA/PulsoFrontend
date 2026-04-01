from typing import Any, Dict

from app.InteligenciaDados.core.ID_core.sql_connection_factory import create_sql_connection
from app.InteligenciaDados.models.ID_models.query_get_models import QueryGetRawResult


class QueryGetDatabase:
    """
    Database access layer for query execution.
    Fecha a conexão após uso para evitar esgotamento do pool.
    """

    def __init__(self, db_config: Dict[str, Any]) -> None:
        self._connection = create_sql_connection(db_config)

    def fetch(self, sql: str) -> QueryGetRawResult:
        """
        Execute SQL and return structured raw result.
        """
        try:
            rows = self._connection.execute_select(sql)
            return QueryGetRawResult(rows=rows, row_count=len(rows))
        finally:
            self._connection.close()

    def close(self) -> None:
        """Fecha a conexão com o banco."""
        self._connection.close()