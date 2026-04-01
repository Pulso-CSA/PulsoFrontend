#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from pydantic import BaseModel, Field
from typing import Optional

class ProfileCreate(BaseModel):
    """Payload para criar perfil."""
    name: str = Field(..., min_length=1, max_length=50, description="Nome do perfil")
    description: Optional[str] = Field(None, max_length=200, description="Descrição opcional")

class ProfileUpdate(BaseModel):
    """Payload para atualizar perfil."""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class ProfileResponse(BaseModel):
    """Resposta com dados do perfil."""
    id: str
    name: str
    description: Optional[str]
    created_at: str  # ISO format
    updated_at: str   # ISO format

class ProfileListResponse(BaseModel):
    """Resposta com lista de perfis."""
    profiles: list[ProfileResponse]
    total: int

