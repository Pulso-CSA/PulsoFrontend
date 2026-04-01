# RegenAI

## Objetivo e arquitetura

O modulo `RegenAI` executa o ciclo:

`teste dinamico -> analise -> correcao minima -> reexecucao -> relatorio`.

Ele atua como orquestrador e **reutiliza** os servicos existentes de autocorrecao do PulsoCSA, sem copiar a logica core.

Componentes internos:

- `routers/regen_router.py`
- `workflow/regen_workflow.py`
- `services/regen_orchestrator_service.py`
- `services/route_discovery_service.py`
- `services/input_generation_service.py`
- `services/test_execution_service.py`
- `services/log_analysis_service.py`
- `services/correction_bridge_service.py`
- `services/report_service.py`
- `storage/execution_cache.py`
- `utils/concurrency_manager.py`

## Escopo por modulo (requisito critico)

O `POST /regenai/run` exige escopo explicito via `scopes` (tambem aceita aliases `scope` e `target_modules`).

Escopos suportados:

- `PulsoCSA/Python`
- `PulsoCSA/JavaScript`
- `InteligenciaDados`
- `FinOps`
- `CloudIAC`

Mapeamento:

- `PulsoCSA/Python` -> `api/app/PulsoCSA/Python`
- `PulsoCSA/JavaScript` -> `api/app/PulsoCSA/JavaScript`
- `InteligenciaDados` -> `api/app/InteligenciaDados`
- `FinOps` -> `api/app/FinOps`
- `CloudIAC` -> `api/app/CloudIAC`

O fluxo restringe descoberta de rotas, geracao de inputs/perguntas, baseline de testes e ponte de correcao aos escopos selecionados.

## Origem das perguntas (externa e versionavel)

As perguntas de teste ficam em `app/RegenAI/Docs`:

- `pulsocsa_python_tests.md`
- `pulsocsa_javascript_tests.md`
- `inteligencia_dados_tests.md`
- `finops_tests.md`
- `cloudiac_tests.md`

Cada arquivo segue secoes:

- `## valid_questions`
- `## invalid_questions`
- `## edge_cases`
- `## ambiguous_inputs`

Cada pergunta usada em rodada registra `scope`, `source_file` e `category`.

## Fluxo RegenAI

1. Recebe requisicao (`/regenai/run`).
2. Valida escopos e cria execucao.
3. Carrega perguntas externas por escopo.
4. Descobre rotas apenas dos modulos selecionados.
5. Gera entradas com perguntas e metadados de origem.
6. Executa testes concorrentes (padrao: 6).
7. Executa baseline por escopo selecionado.
8. Analisa falhas.
9. Dispara autocorrecao existente por escopo.
10. Repete ate 5 rodadas.
11. Persiste relatorio JSON e Markdown.

## Endpoints

- `POST /regenai/run`
- `GET /regenai/status/{execution_id}`
- `GET /regenai/report/{execution_id}`
- `GET /regenai/logs/{execution_id}`

### Visibilidade em tempo real para frontend

`GET /regenai/logs/{execution_id}` retorna, alem dos logs textuais, o campo `live_results` com os resultados parciais de cada teste concluido.

Cada item de `live_results` inclui:

- `question` (pergunta aplicada)
- `request_query` e `request_json` (entrada enviada)
- `status_code`, `success`, `elapsed_ms`
- `body_preview` (trecho da resposta da rota)

Tambem retorna `exception_questions`, que registra todas as perguntas efetivamente disparadas durante a execucao. Essa lista pode ser usada pelo frontend para evitar repeticao de perguntas em novas rodadas.

### Autocorrecao por resposta incorreta

Quando a pergunta tiver `expected_output` (vinda dos arquivos externos de perguntas), uma resposta HTTP `200` ainda pode ser marcada como falha caso o texto esperado nao esteja contido na resposta. Nesses casos, a entrada e enviada para o pipeline de autocorrecao da mesma forma que erros HTTP.

## Reuso da stack existente

- `run_analise_retorno`
- `run_correcao_erros`
- `run_automated_test`
- `log_manager.add_log`
- `idempotency` (run id + idempotencia de request)

## Relatorios

Arquivos gerados:

- `app/RegenAI/reports/{execution_id}/report.json`
- `app/RegenAI/reports/{execution_id}/report.md`

Campos principais:

- objetivo
- escopos executados
- rotas analisadas
- perguntas por escopo (com origem)
- entradas usadas
- rodadas
- falhas
- correcoes
- status final

