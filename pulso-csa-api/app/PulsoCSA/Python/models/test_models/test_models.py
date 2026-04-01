#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos de Teste Automatizado❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from pydantic import BaseModel, Field
from typing import Optional, List


class TestRunRequest(BaseModel):
    """Modelo de entrada para execução de teste automatizado (venv ou docker)."""
    project_path: str = Field(..., description="Caminho absoluto do projeto a testar.")
    prefer_docker: bool = Field(
        True,
        description="Se True, tenta Docker primeiro quando docker-compose existir."
    )


class TestRunResponse(BaseModel):
    """Modelo de resposta do teste automatizado (usado por rota e workflow)."""
    success: bool = Field(..., description="Se o teste passou (app subiu / execução ok).")
    message: str = Field(..., description="Mensagem resumida do resultado.")
    method_used: Optional[str] = Field(
        None,
        description="Método usado: 'docker' ou 'venv'."
    )
    logs: Optional[List[str]] = Field(None, description="Logs da execução.")
    details: Optional[str] = Field(None, description="Detalhes adicionais (ex.: stderr).")
