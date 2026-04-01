#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Preview Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from pydantic import BaseModel, Field
from typing import Optional


class PreviewStartRequest(BaseModel):
    """Request para iniciar o servidor de preview."""
    root_path: str = Field(..., description="Caminho absoluto da raiz do projeto.")
    project_type: Optional[str] = Field(
        default="auto",
        description="Tipo do projeto: 'javascript', 'python' ou 'auto' (detecta automaticamente).",
    )


class PreviewStartResponse(BaseModel):
    """Resposta ao iniciar o preview."""
    success: bool = Field(..., description="Se o servidor foi iniciado com sucesso.")
    preview_url: Optional[str] = Field(None, description="URL do preview (ex.: http://localhost:3000).")
    message: str = Field(..., description="Mensagem descritiva do resultado.")
    project_type: Optional[str] = Field(None, description="Tipo detectado ou informado: javascript ou python.")
    details: Optional[str] = Field(None, description="Detalhes adicionais (erros, logs).")
    preview_auto_open: bool = Field(
        default=False,
        description="Se False, o frontend NÃO deve abrir nova aba, terminal ou navegador automaticamente.",
    )
