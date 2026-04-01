#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Modelos: Camada 3 – Execução❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from pydantic import BaseModel
from typing import Optional, Dict, List

#━━━━━━━━━❮Entrada❯━━━━━━━━━

class ExecutionRequest(BaseModel):
    id_requisicao: str
    root_path: str

#━━━━━━━━━❮Saída❯━━━━━━━━━

class ManifestResponse(BaseModel):
    root_path: str
    created: Dict[str, List[str]]
    skipped: List[str]
    timestamp: str
    status: str
