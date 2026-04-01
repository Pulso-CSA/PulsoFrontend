from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RegenStatus(BaseModel):
    execution_id: str
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    objective: str
    scopes: List[str] = Field(default_factory=list)
    current_round: int = 0
    max_rounds: int = 5
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_routes: int = 0
    total_inputs: int = 0
    total_failures: int = 0
    rounds: List[Dict[str, Any]] = Field(default_factory=list)
    report_json_path: Optional[str] = None
    report_md_path: Optional[str] = None
    error: Optional[str] = None

