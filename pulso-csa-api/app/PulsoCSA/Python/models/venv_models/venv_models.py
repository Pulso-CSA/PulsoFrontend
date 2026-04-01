#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Venv Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from pydantic import BaseModel

class VenvRequest(BaseModel):
    """Request model to manage virtual environments."""
    project_path: str

class VenvResponse(BaseModel):
    """Response model for venv operations."""
    status: str
    message: str
    details: str | None = None
