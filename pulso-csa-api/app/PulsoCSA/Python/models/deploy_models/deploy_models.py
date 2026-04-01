#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos de Deploy (Pydantic)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from pydantic import BaseModel, Field
from typing import Optional, List


class DeployRequest(BaseModel):
    """Modelo de entrada para operações de Docker Compose."""
    project_path: str = Field(..., description="Caminho absoluto do diretório com docker-compose.yml.")
    root_path: Optional[str] = Field(
        None,
        description="Caminho raiz do projeto onde o pipeline de deploy será iniciado."
    )


class DeployResponse(BaseModel):
    """Modelo padrão de resposta das operações de deploy."""
    message: str
    logs: Optional[List[str]] = None
    success: bool = True


class LogEntry(BaseModel):
    """Modelo de log armazenado na aplicação."""
    timestamp: str
    level: str
    message: str
    source: str
