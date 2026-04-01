from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class QueryGetDBConfig(BaseModel):
    """
    Database connection configuration (SQL apenas).
    SQL: db_type (mysql|postgresql|sqlserver|sqlite|oracle), host, port, user, password, database.
    SQLite: database/path (arquivo), host/user/password opcionais.
    """
    db_type: Optional[str] = Field(default="mysql", description="mysql|postgresql|sqlserver|sqlite|oracle")
    host: Optional[str] = None
    port: int = Field(default=3306, ge=1, le=65535)
    user: Optional[str] = None
    password: Optional[str] = None
    database: str = Field(..., description="Database name ou path (SQLite)")

    @model_validator(mode="after")
    def check_sqlite_vs_network(self) -> "QueryGetDBConfig":
        db_type = (self.db_type or "mysql").strip().lower()
        if db_type != "sqlite" and (not self.host or not self.user or not self.password):
            raise ValueError("host, user e password são obrigatórios para bancos SQL em rede")
        return self


class QueryGetInput(BaseModel):
    """
    Input model for the data intelligence agent.
    db_config aceita Dict flexível para compatibilidade com MongoDB (retorna erro claro).
    """
    prompt: str = Field(..., min_length=3)
    db_config: Dict[str, Any] = Field(..., description="Conexão: SQL (host, user, password, database) ou NoSQL (uri, database)")


class QueryGetRawResult(BaseModel):
    """
    Raw result returned directly from database execution.
    """
    rows: List[Dict[str, Any]]
    row_count: int


class QueryGetOutput(BaseModel):
    """
    Final output returned to the user.
    """
    answer: str
    generated_sql: Optional[str] = None
    raw_result: Optional[QueryGetRawResult] = None