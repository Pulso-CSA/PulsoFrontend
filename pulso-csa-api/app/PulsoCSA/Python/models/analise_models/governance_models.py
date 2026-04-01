#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Bibliotecas❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from pydantic import BaseModel
from typing import Optional, List

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos de Requisição❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class PromptRequest(BaseModel):
    prompt: str
    usuario: str
    root_path: Optional[str] = None  # ✅ novo campo


class RefineRequest(BaseModel):
    id_requisicao: str
    prompt: str


class ValidateRequest(BaseModel):
    id_requisicao: str
    refined_prompt: str
    feedback_usuario: str  # ← campo que estava faltando


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos de Resposta❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class GovernanceResponse(BaseModel):
    workflow: str
    steps_executed: List[str]
    final_prompt: str
    status: str
