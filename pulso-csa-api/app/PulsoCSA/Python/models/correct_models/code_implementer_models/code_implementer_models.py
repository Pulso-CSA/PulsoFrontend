#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Models – Code Implementer (C4)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CodeImplementerRequest(BaseModel):
    """
    Request payload for Code Implementer execution.
    It is tightly coupled to a previously generated Code Plan (same id_requisicao).
    """

    id_requisicao: str
    root_path: str
    usuario: str = "anonymous"
    dry_run: bool = False


class CodeImplementerFileResult(BaseModel):
    """
    Represents the result of a single implementation operation on a file.
    """

    path: str
    action: str  # "implemented" | "skipped" | "error"
    success: bool = True
    message: str = ""
    backup_path: Optional[str] = None


class CodeImplementerExecutionResult(BaseModel):
    """
    High-level result for a Code Implementer execution.
    """

    id_requisicao: str
    root_path: str
    usuario: str
    dry_run: bool
    executed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "success"  # "success" | "partial" | "error"
    files: List[CodeImplementerFileResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
