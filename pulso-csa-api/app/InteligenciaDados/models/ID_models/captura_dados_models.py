# Models para o agente de Captura de Dados (ID)
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MySQLDBConfig(BaseModel):
    host: str
    port: int = Field(default=3306, ge=1, le=65535)
    user: str
    password: str
    database: str


class MongoDBConfig(BaseModel):
    uri: Optional[str] = None
    host: Optional[str] = None
    port: int = Field(default=27017, ge=1, le=65535)
    database: str
    user: Optional[str] = None
    password: Optional[str] = None


class CapturaDadosInput(BaseModel):
    id_requisicao: str = Field(..., min_length=1)
    usuario: Optional[str] = None
    tipo_base: Optional[str] = Field(None, description="SQL | NoSQL ou auto")
    db_config: Dict[str, Any] = Field(
        ...,
        description="SQL: db_type (mysql|postgresql|sqlserver|sqlite|oracle), host, port, user, password, database. "
        "SQLite: database/path (arquivo). MongoDB: uri ou host, port, database.",
    )
    incluir_amostra: bool = Field(False, description="Se True, extrai amostra e grava dataset_ref")
    max_rows_amostra: int = Field(100, ge=10, le=10_000, description="Máximo de linhas na amostra por tabela")


class CapturaDadosOutput(BaseModel):
    id_requisicao: str
    captura_dados: Dict[str, Any] = Field(
        ...,
        description="tipo_base, tabelas/coleções, quantidade_registros, teor_dados",
    )


def relatorio_captura_schema() -> Dict[str, Any]:
    return {
        "tipo_base": "SQL | NoSQL",
        "tabelas": ["lista de nomes"],
        "quantidade_tabelas": 0,
        "quantidade_registros": {"tabela": 0},
        "teor_dados": "descrição em texto",
    }
