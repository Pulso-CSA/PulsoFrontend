#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Version Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from pydantic import BaseModel, Field
from typing import Optional

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Response DTOs❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


class VersionResponse(BaseModel):
    """Resposta com informações de versão do cliente (app Electron)."""

    minClientVersion: str = Field(
        default="0.0.0",
        description="Versão mínima aceita do app. Versões abaixo devem ser atualizadas.",
    )
    latestVersion: str = Field(
        default="1.0.0",
        description="Última versão disponível.",
    )
    releaseNotes: Optional[str] = Field(
        default=None,
        description="Notas da última release.",
    )
    forceUpgrade: bool = Field(
        default=False,
        description="Se true, força upgrade obrigatório (ex.: vulnerabilidade crítica).",
    )
    downloadUrl: Optional[str] = Field(
        default=None,
        description="URL do instalador (opcional, se não usar GitHub Releases).",
    )
    platform: str = Field(
        default="win",
        description="Plataforma: win, mac, linux.",
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Request DTOs (Admin)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━


class VersionUpdateRequest(BaseModel):
    """Payload para atualizar configuração de versão (admin)."""

    platform: str = Field(default="win", description="Plataforma: win, mac, linux")
    minClientVersion: str = Field(default="0.0.0", description="Versão mínima aceita")
    latestVersion: str = Field(..., description="Última versão disponível")
    releaseNotes: Optional[str] = Field(default=None, description="Notas da release")
    forceUpgrade: bool = Field(default=False, description="Forçar upgrade obrigatório")
    downloadUrl: Optional[str] = Field(default=None, description="URL do instalador")
