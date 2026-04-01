#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━❮Comprehension Código JavaScript❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
from typing import Any, Dict, List, Optional

# Reutiliza serviços Python quando possível
from app.PulsoCSA.Python.services.comprehension_services.comprehension_service import (
    INTENT_ANALISAR,
    INTENT_EXECUTAR,
    PROJECT_STATE_VAZIA,
    PROJECT_STATE_COM_CONTEUDO,
    TARGET_GOVERNANCE,
    TARGET_CORRECT,
)
from app.PulsoCSA.Python.services.comprehension_services.comprehension_codigo import (
    route_decision_codigo,
)

try:
    from core.openai.openai_client import get_openai_client
except ImportError:
    from app.core.openai.openai_client import get_openai_client


def route_decision_codigo_js(
    prompt: str,
    root_path: str | None,
    usuario: str | None,
    language: str,
    framework: str | None,
    force_execute: bool = False,
    history: List[Dict[str, str]] | None = None,
    root_path_validated: bool = False,
) -> Dict[str, Any]:
    """
    Roteia decisão para módulo código JavaScript/TypeScript/React.
    Retorna decisão completa com informações de linguagem e framework.
    """
    # Reutiliza a lógica do Python, mas adiciona informações de linguagem
    decision = route_decision_codigo(prompt, root_path, usuario, force_execute, history)
    
    intent = decision["intent"]
    project_state = decision["mode"]
    should_exec = decision["should_execute"]
    
    # Determina target endpoint baseado no estado do projeto.
    # Se language=python, roteia para os endpoints Python (backend).
    if intent == INTENT_EXECUTAR and should_exec:
        if language == "python":
            target_endpoint = TARGET_GOVERNANCE if project_state == PROJECT_STATE_VAZIA else TARGET_CORRECT
        else:
            target_endpoint = "/comprehension-js/governance/run" if project_state == PROJECT_STATE_VAZIA else "/comprehension-js/workflow/correct/run"
    else:
        target_endpoint = None

    # Monta explicação considerando linguagem e framework
    lang_desc = language
    if framework and framework != "vanilla" and language != "python":
        lang_desc = f"{language} com {framework}"
    
    explanation = f"Intenção: {intent}. Estado do projeto: {project_state}. Linguagem: {lang_desc}."
    
    if intent == INTENT_ANALISAR:
        next_action = "Análise do projeto será realizada."
    elif intent == INTENT_EXECUTAR and should_exec:
        if project_state == PROJECT_STATE_VAZIA:
            next_action = f"Criação de projeto {lang_desc} será executada."
        else:
            next_action = f"Correção de projeto {lang_desc} será executada."
    else:
        next_action = "Aguardando confirmação para executar."

    return {
        "module": "codigo",
        "intent": intent,
        "mode": project_state,
        "should_execute": should_exec,
        "target_endpoint": target_endpoint,
        "explanation": explanation,
        "next_action": next_action,
        "language": language,
        "framework": framework,
        "intent_confidence": 0.85,
        "intent_warning": None,
    }
