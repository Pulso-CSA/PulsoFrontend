from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RegenReport(BaseModel):
    execution_id: str
    objective: str
    scopes: List[str] = Field(default_factory=list)
    routes_analyzed: List[str] = Field(default_factory=list)
    questions_by_scope: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    generated_inputs: List[Dict[str, Any]] = Field(default_factory=list)
    cycles_executed: int = 0
    failures_detected: List[str] = Field(default_factory=list)
    input_validation_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    corrections_applied: List[Dict[str, Any]] = Field(default_factory=list)
    final_status: str
    evidences: List[str] = Field(default_factory=list)
    rounds: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: str
    report_json_path: Optional[str] = None
    report_md_path: Optional[str] = None

