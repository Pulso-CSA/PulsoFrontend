#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Workflow Steps JavaScript❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Executa Camadas 1 e 2 do pipeline com stack=javascript.
Define set_request_stack("javascript") para que load_prompt carregue
os prompts de PulsoCSA/JavaScript/prompts/analyse/.
"""
from app.prompts.loader import set_request_stack

# Importa do pipeline Python (PulsoCSA/Python está no sys.path)
try:
    from workflow.creator_workflow.workflow_steps import execute_layer1, execute_layer2
except ImportError:
    from app.PulsoCSA.Python.workflow.creator_workflow.workflow_steps import (
        execute_layer1,
        execute_layer2,
    )


def execute_layer1_js(prompt: str, usuario: str, root_path: str = None):
    """Camada 1 – Governança (Input → Refine → Validate) com prompts JS."""
    set_request_stack("javascript")
    return execute_layer1(prompt, usuario, root_path)


def execute_layer2_js(id_requisicao: str, refined_prompt: str, root_path: str = None):
    """Camada 2 – Arquitetura (Structure → Backend → Infra → Sec) com prompts JS."""
    set_request_stack("javascript")
    return execute_layer2(id_requisicao, refined_prompt, root_path)
