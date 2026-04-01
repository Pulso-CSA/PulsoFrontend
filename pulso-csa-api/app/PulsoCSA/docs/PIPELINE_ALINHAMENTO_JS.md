# Alinhamento do Pipeline JavaScript ao Python

## Princípio

O pipeline JavaScript deve ser **idêntico** ao pipeline Python. A única diferença prática é a **linguagem de programação** usada para atender ao pedido do usuário (JavaScript/TypeScript/React em vez de Python).

---

## Pipeline Python (Referência)

### Creator (Criação de Projeto)

| Etapa | Descrição |
|-------|-----------|
| **C1 – Governança** | Input → Refine → Validate |
| **C2 – Arquitetura** | Structure → Backend → Infra (paralelo com Sec_code) → Sec_infra |
| **C3 – Estrutura** | Criação de diretórios e arquivos base |
| **C3.2 – Código** | Code Plan → Code Writer → Code Implementer → Teste automatizado |
| *(Ollama)* | Code Creator (1 LLM por arquivo) em vez de Plan+Writer+Implementer |

### Correct (Correção de Projeto)

| Etapa | Descrição |
|-------|-----------|
| **C1 – Governança** | Input → Refine → Validate |
| **C2 – Análise estrutural** | Scan projeto → Change Plan → Aplicar mudanças estruturais |
| **C2b – Code Plan** | Plano de alterações em JSON |
| **C3 – Code Writer** | Escreve código conforme plano |
| **C4 – Code Implementer** | Implementa alterações no projeto |
| **C5 – Teste** | Teste automatizado (venv/docker) |
| **Pipeline autocorreção** | Análise retorno → Correção erros → Segurança código → Segurança infra |

---

## O que o Pipeline JS deve ter (igual ao Python)

### Creator

1. **Camada 1 – Governança**: Input, Refine, Validate (reutilizar ou adaptar)
2. **Camada 2 – Arquitetura**: Structure, Backend, Infra, Sec_code, Sec_infra (prompts JS)
3. **Camada 3 – Estrutura**: Criação de pastas/arquivos base (JS/TS/React)
4. **Camada 3.2 – Código**: Code Plan → Code Writer → Code Implementer → Teste (npm test/vitest/jest)

### Correct

1. **C1 – Governança**
2. **C2 – Scan** (projeto JS) → Change Plan → Aplicar estrutura
3. **C2b – Code Plan** (para JS/TS/React)
4. **C3 – Code Writer** (JS)
5. **C4 – Code Implementer** (JS)
6. **C5 – Teste** (npm test)
7. **Pipeline autocorreção** (análise retorno, correção, segurança)

---

## Plano de Implementação

### Fase 1 – Infraestrutura ✅

- [x] Criar `PulsoCSA/JavaScript/prompts/analyse/` com prompts JS:
  - `structure_blueprint.txt` (estrutura para React/Vue/Angular)
  - `backend.txt`, `infra.txt`, `sec_code.txt`, `sec_infra.txt`
  - `base_refine.txt`, `refine_*.txt` (refino compartilhado)
- [x] Contextvar `set_request_stack` / `get_request_stack` em `loader.py`
- [x] `load_prompt` usa contextvar quando definido

### Fase 2 – Creator ✅

- [x] `workflow_steps_js.py`: `execute_layer1_js`, `execute_layer2_js`
- [x] Reutiliza `execute_layer1`/`execute_layer2` com `set_request_stack("javascript")`
- [x] `workflow_core_js.py`: Camadas 1, 2, 3, 3.2 (LLM App), C5 (teste)
- [x] Test runner JS: `run_automated_test_js` (npm test)

### Fase 3 – Correct ✅

- [x] C1 – Governança integrada
- [x] C2 – Scanner de projeto JS (`scan_full_project_js`)
- [x] C2 – Change Plan para JS (`generate_change_plan_js`)
- [x] C2 – Apply Change Plan para JS (`apply_change_plan_to_filesystem_js`)
- [x] C4 – Code Implementer (correct_file_js)
- [x] C5 – Test runner JS
- [x] Pipeline de autocorreção (análise retorno → correção → segurança código/infra)

### Fase 4 – Testes e Ajustes

- [ ] Testes de integração do pipeline JS
- [ ] Ajustes de prompts e mensagens

---

## Arquivos Principais

| Python | JavaScript (alvo) |
|--------|------------------|
| `workflow_steps.py` | `workflow_steps_js.py` |
| `workflow_core.py` | `workflow_core_js.py` (já existe, integrar) |
| `workflow_core_cor.py` | `workflow_core_cor_js.py` (já existe, integrar) |
| `structure_scanner_service` | `structure_scanner_service_js` |
| `change_plan_service` | `change_plan_service_js` |
| `code_plan_agent` | `code_plan_agent_js` ou `code_plan_agent(..., stack="javascript")` |
| `code_writer_service` | `code_writer_service_js` ou versão com stack |
| `code_implementer_service` | `code_implementer_service_js` (já existe) |
| `run_automated_test` | `run_automated_test_js` (npm test) |

---

## Contexto de Stack

Para evitar alterar assinaturas em dezenas de funções, usar `contextvars`:

```python
# app/prompts/loader.py ou novo módulo
from contextvars import ContextVar
_request_stack: ContextVar[str] = ContextVar("request_stack", default="python")

def set_request_stack(stack: str):
    _request_stack.set(stack)

def get_request_stack() -> str:
    return _request_stack.get()
```

No início do `run_workflow_pipeline_js`, chamar `set_request_stack("javascript")`. O `load_prompt` pode verificar `get_request_stack()` quando `stack` não for passado explicitamente.
