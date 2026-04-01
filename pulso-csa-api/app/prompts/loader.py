#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Loader central de prompts (.txt)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
"""
Todos os prompts devem ser consumidos de arquivos .txt na pasta prompts.
Path relativo à pasta prompts, com ou sem .txt:
  load_prompt("analyse/base_refine")
  load_prompt("creation/code_creation_env.txt")
  load_prompt("ID_prompts/query_get_system_rules")

Prompts CSA (criação e correção) por stack:
  load_prompt("creation/code_creation", stack="python")   → PulsoCSA/Python/prompts/
  load_prompt("creation/code_creation", stack="javascript") → PulsoCSA/JavaScript/prompts/
"""
from contextvars import ContextVar
from pathlib import Path
from typing import Literal, Optional

PROMPTS_DIR = Path(__file__).resolve().parent

# Contexto de stack para pipeline JS (evita propagar stack em todas as chamadas)
_request_stack: ContextVar[Optional[str]] = ContextVar("request_stack", default=None)


def set_request_stack(stack: Literal["python", "javascript"]) -> None:
    """Define a stack do request atual. Usado pelo workflow JS no início da execução."""
    _request_stack.set(stack)


def get_request_stack() -> Optional[str]:
    """Retorna a stack do request atual, ou None se não definida."""
    return _request_stack.get()


# Prompts de Inteligência de Dados (em InteligenciaDados/prompts/)
ID_PROMPTS_DIR = PROMPTS_DIR.parent / "InteligenciaDados" / "prompts"
# Prompts CSA por stack: Python e JavaScript/TypeScript/React
PYTHON_CSA_PROMPTS_DIR = PROMPTS_DIR.parent / "PulsoCSA" / "Python" / "prompts"
JAVASCRIPT_CSA_PROMPTS_DIR = PROMPTS_DIR.parent / "PulsoCSA" / "JavaScript" / "prompts"

# Prefixos de path que indicam prompts CSA (criação/correção/análise)
_CSA_PREFIXES = ("analyse/", "creation/", "correct/", "tela_teste/")


def _is_csa_path(relative_path: str) -> bool:
    """Verifica se o path é de prompts CSA (criação, correção, análise)."""
    return any(relative_path.startswith(p) for p in _CSA_PREFIXES)


def load_prompt(
    relative_path: str,
    stack: Optional[Literal["python", "javascript"]] = "python",
) -> str:
    """
    Carrega o conteúdo de um arquivo de prompt .txt.

    relative_path: path relativo (ex: "analyse/base_refine" ou "creation/code_creation.txt").
    stack: "python" para prompts de criação/correção Python; "javascript" para JS/TS/React.
           Default "python". Ignorado para ID_prompts/*.

    Resolução:
    - ID_prompts/* → InteligenciaDados/prompts/
    - analyse/*, creation/*, correct/*, tela_teste/* → PulsoCSA/{stack}/prompts/
    - demais → api/app/prompts/ (fallback)
    """
    path = Path(relative_path)
    if path.suffix != ".txt":
        path = Path(str(path) + ".txt")

    if relative_path.startswith("ID_prompts"):
        base_dir = ID_PROMPTS_DIR
    elif _is_csa_path(relative_path):
        effective_stack = get_request_stack() or stack
        base_dir = JAVASCRIPT_CSA_PROMPTS_DIR if effective_stack == "javascript" else PYTHON_CSA_PROMPTS_DIR
    else:
        base_dir = PROMPTS_DIR

    full_path = base_dir / path
    if not full_path.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {full_path}")
    return full_path.read_text(encoding="utf-8").strip()
