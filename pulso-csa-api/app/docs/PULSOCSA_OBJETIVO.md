# PulsoCSA – Objetivo e Comportamento

A área **PulsoCSA** (entrada via `POST /comprehension/run` e fluxos de criação/correção) funciona como um **Cursor sem IDE**: múltiplos agentes em pipeline para criar e corrigir código com qualidade.

## Objetivos

### Criação de código (do zero)
- **Melhores práticas**: PEP 8, tipagem (PEP 484), estrutura modular (routes/, services/, models/).
- **Documentação**: docstrings (PEP 257) em módulos e funções públicas.
- **Otimização**: código performático (estruturas de dados adequadas, sem loops redundantes).
- **Segurança**: segredos em variáveis de ambiente, queries parametrizadas, validação de entrada (Pydantic quando aplicável).

### Correção e análise de código existente
- **Alteração mínima**: modificar apenas o estritamente necessário; preservar ao máximo o código original (estilo, nomes, estrutura).
- **Velocidade**: mudanças localizadas, preferência por trechos pequenos em vez de reescrever arquivos inteiros.
- **Segurança**: sem eval/exec em input de usuário, inputs validados.
- **Qualidade**: legibilidade, tipagem, código testável.

## Checklist – Onde cada objetivo está implementado

| Objetivo | Onde está |
|----------|------------|
| Criação: melhores práticas, documentação, otimização, segurança | `api/app/prompts/creation/code_creation.txt` (regras gerais) |
| Correção: alteração mínima, velocidade, qualidade | `api/app/prompts/correct/code_plan_system.txt`, `implementation_system.txt`, `implementation_user.txt` |
| Pipeline correção: alteração mínima | `api/app/services/pipeline_services/correcao_erros_service.py` (`_build_prompt_from_analise`) |
| Contrato Cursor-like e agentes | `api/app/services/comprehension_services/comprehension_service.py` (`get_system_behavior_spec`) |
| Roteamento e sugestão frontend | `get_frontend_suggestion` no mesmo módulo; `api/app/routers/comprehension_router/README.md` |

## Agentes (Pipeline)

| Etapa | Nome            | Função |
|-------|-----------------|--------|
| C1    | Governança      | Refino e validação do prompt |
| C2    | Análise estrutural | Scanner do projeto, plano de mudanças (novos/alterar) |
| C2b   | Code Plan       | Plano de código (JSON: changes, new_files, artifacts) |
| C3    | Code Writer     | Stubs e integração (arquivos criados/alterados) |
| C4    | Code Implementer| Implementação real do código em cada arquivo |
| C5    | Teste           | Testes automatizados (venv/docker) |
| 11–13.2 | Pipeline     | Análise de retorno → correção de erros → segurança código/infra |

## Aceleração (software)

- **Code Plan (C2b)**: modelo rápido (`use_fast_model=True`), `num_predict=1536`, timeout 6 min (`CODE_PLAN_LLM_TIMEOUT_SEC=360`).
- **Code Implementer (C4)**: modelo de código (`use_fast_model=False`), timeout 6 min (`CODE_IMPLEMENTER_LLM_TIMEOUT_SEC=360`).
- **Comprehension**: cache de intent e de análise, retentativas e timeout 6 min para reduzir “Análise indisponível”.
- **Change Plan (C2)**: cache TTL, paralelismo (ThreadPoolExecutor), timeout 6 min (`CHANGE_PLAN_LLM_TIMEOUT_SEC=360`).
- **Correção (pipeline)**: prompt de correção enfatiza “alteração mínima” para menos retrabalho.
- **Rotas bloqueantes**: uso de `run_in_executor` para não bloquear o event loop (comprehension, workflow, ID, governance, etc.).
- **Paralelismo**: C2 (infra + sec_code em paralelo em workflow_steps); C4 e code_creator (arquivos em paralelo); change_plan (chunks em paralelo).

## Timeouts (6 minutos = 360 s)

Todos os timeouts de LLM/workflow estão configurados por padrão para **6 minutos** (360 s). Podem ser sobrescritos por variáveis de ambiente.

| Variável | Default | Uso |
|----------|---------|-----|
| `OPENAI_REQUEST_TIMEOUT` | 360 | Cliente OpenAI (todas as chamadas) |
| `OLLAMA_TIMEOUT_SEC` | 360 | Cliente Ollama |
| `COMPREHENSION_ANALYSIS_TIMEOUT_SEC` | 360 | Análise (ANALISAR) no comprehension |
| `CODE_PLAN_LLM_TIMEOUT_SEC` | 360 | Code Plan (C2b) |
| `CODE_IMPLEMENTER_LLM_TIMEOUT_SEC` | 360 | Code Implementer (C4) |
| `CHANGE_PLAN_LLM_TIMEOUT_SEC` | 360 | Plano de mudanças (C2) |
| `INFRA_TERRAFORM_TIMEOUT_SEC` | 360 | Terraform (infra) |
| FinOps | 360 (fixo) | Análise FinOps |
| ID Chat | 360 (override nas chamadas) | Interpretação de mensagem e resumos |

## Variáveis de ambiente opcionais (cache e retries)

- `COMPREHENSION_INTENT_CACHE_TTL_SEC` (300)
- `COMPREHENSION_ANALYSIS_CACHE_TTL_SEC` (120)
- `COMPREHENSION_ANALYSIS_MAX_RETRIES` (2)
- `CODE_PLAN_CACHE_TTL_SEC` (60)
- `CHANGE_PLAN_CACHE_TTL_SEC` (45)

## Contrato do sistema

O campo `system_behavior` na resposta de `POST /comprehension/run` descreve esse comportamento (PulsoCSA, Cursor-like, agentes e regras de criação/correção).
