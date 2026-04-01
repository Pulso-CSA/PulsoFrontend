#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Models – Code Writer❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CodeWriterRequest(BaseModel):
    """Request payload for Code Writer execution."""
    id_requisicao: str
    root_path: str
    usuario: str = "anonymous"
    dry_run: bool = False


class CodeWriterFileResult(BaseModel):
    """Represents the result of a single file operation."""
    path: str
    action: str  # "modified" | "created" | "skipped" | "error"
    success: bool = True
    message: str = ""
    backup_path: Optional[str] = None


class CodeWriterExecutionResult(BaseModel):
    """High-level result of a Code Writer execution."""
    id_requisicao: str
    root_path: str
    usuario: str
    dry_run: bool
    executed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "success"  # "success" | "partial" | "error"
    files: List[CodeWriterFileResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
