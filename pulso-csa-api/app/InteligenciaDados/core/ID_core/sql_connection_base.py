#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Base – Interface comum para conexões SQL❯━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List

_SCHEMA_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


def validate_identifier(name: str) -> None:
    if not name or not _SCHEMA_NAME_PATTERN.match(str(name)):
        raise ValueError(f"Identificador inválido: {name!r}")


class SQLConnectionBase(ABC):
    """Interface comum para MySQL, PostgreSQL, SQL Server, SQLite, Oracle."""

    @abstractmethod
    def execute_select(self, sql: str) -> List[Dict[str, Any]]:
        """Executa SELECT e retorna linhas como dicts."""
        pass

    @abstractmethod
    def execute_select_paginated(
        self, sql: str, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Executa SELECT com paginação."""
        pass

    @abstractmethod
    def get_table_names(self, database: str) -> List[str]:
        """Lista tabelas do schema/database."""
        pass

    @abstractmethod
    def get_column_info(self, database: str, table: str) -> List[Dict[str, Any]]:
        """Retorna colunas: column_name, data_type, is_nullable."""
        pass

    @abstractmethod
    def get_table_row_count(self, database: str, table: str) -> int:
        """Conta registros da tabela."""
        pass

    @abstractmethod
    def get_table_indexes(self, database: str, table: str) -> List[Dict[str, Any]]:
        """Retorna índices: name, columns, unique."""
        pass

    def get_exploration_query(self, database: str, table: str, limit: int = 10) -> str:
        """Retorna query SELECT * FROM schema.table para exploração (dialect-specific)."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        pass
