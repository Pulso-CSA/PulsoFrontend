#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agent – Code Plan Orchestrator❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from datetime import datetime
from typing import Dict, Any

from services.agents.correct_services.code_plan_services.code_plan_service import (
    run_code_plan,
)
from utils.log_manager import add_log


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Agent Principal❯
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def run_code_plan_agent(
    log_type: str,
    usuario: str,
    prompt_usuario: str,
    root_path: str,
    analise_sistema: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Orchestrates code plan generation (hybrid AB model).

    Responsibilities:
      - reuse the structural analysis id_requisicao when available,
      - log the start and end of the operation,
      - delegate to the Code Plan service,
      - return a simple, workflow-friendly payload.
    """

    # Try to reuse id_requisicao from previous stage
    if analise_sistema and "id_requisicao" in analise_sistema:
        id_req = analise_sistema["id_requisicao"]
    else:
        # Fallback if structural analysis did not generate an ID
        id_req = f"CODEPLAN-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    add_log(
        log_type,
        f"[code_plan_agent] Executing code plan for request={id_req} user={usuario}",
        "code_plan_agent",
    )

    # Delegate to Code Plan Service (already AB-aware)
    result = run_code_plan(
        prompt=prompt_usuario,
        root_path=root_path,
        usuario=usuario,
        id_requisicao=id_req,
        analise_sistema=analise_sistema,
    )

    add_log(
        log_type,
        f"[code_plan_agent] Code plan generated successfully for {id_req}",
        "code_plan_agent",
    )

    return {
        "id_requisicao": id_req,
        "usuario": usuario,
        "code_plan": result,
    }
