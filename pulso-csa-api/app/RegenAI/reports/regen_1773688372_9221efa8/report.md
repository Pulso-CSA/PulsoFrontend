# RegenAI Report - regen_1773688372_9221efa8

## Objetivo recebido
Validar respostas de InteligenciaDados, incluindo formato de saida para usuario final e analise de graficos.

## Escopos executados
- InteligenciaDados

## Rotas analisadas
- POST /inteligencia-dados/analise-estatistica
- POST /inteligencia-dados/analise-dados-inicial
- GET /inteligencia-dados/insights/widgets
- POST /inteligencia-dados/insights/generate
- POST /inteligencia-dados/query
- POST /inteligencia-dados/captura-dados
- POST /inteligencia-dados/tratamento-limpeza
- POST /inteligencia-dados/criar-modelo-ml
- GET /inteligencia-dados/listar-modelos
- POST /inteligencia-dados/prever
- POST /inteligencia-dados/chat
- POST /inteligencia-dados/agendar-retreino
- POST /inteligencia-dados/executar-retreino-agendado
- GET /inteligencia-dados/agendamentos-pendentes

## Perguntas por escopo
### InteligenciaDados
- [valid_questions] Validar consulta basica de InteligenciaDados com retorno estruturado e status 2xx. (inteligencia_dados_tests.md)
- [valid_questions] Confirmar endpoint de analise estatistica com parametros minimos validos. (inteligencia_dados_tests.md)
- [valid_questions] Verificar endpoint de previsao com input simples e resposta sem erro. (inteligencia_dados_tests.md)
- [invalid_questions] Enviar dataset invalido para rota de analise e confirmar erro de validacao. (inteligencia_dados_tests.md)
- [invalid_questions] Omitir metadados obrigatorios na rota de modelos ML e validar retorno 4xx. (inteligencia_dados_tests.md)
- [invalid_questions] Enviar formato de data inconsistente e verificar resposta de erro clara. (inteligencia_dados_tests.md)
- [edge_cases] Testar volume maior de registros em consulta para observar tempo e estabilidade. (inteligencia_dados_tests.md)
- [edge_cases] Enviar dados com campos faltantes opcionais e validar fallback seguro. (inteligencia_dados_tests.md)
- [edge_cases] Usar valores extremos (muito altos/baixos) em campos numericos e observar comportamento. (inteligencia_dados_tests.md)
- [ambiguous_inputs] Fazer pergunta analitica ampla sem metrica definida e avaliar orientacao do endpoint. (inteligencia_dados_tests.md)
- [ambiguous_inputs] Enviar instrucao que mistura previsao e limpeza no mesmo payload e verificar tratamento. (inteligencia_dados_tests.md)
- [ambiguous_inputs] Informar objetivo de negocio sem dataset explicito e validar mensagem de apoio. (inteligencia_dados_tests.md)

## Entradas geradas
- POST /inteligencia-dados/analise-estatistica | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Validar consulta basica de InteligenciaDados com retorno estruturado e status 2xx.
- POST /inteligencia-dados/analise-dados-inicial | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Confirmar endpoint de analise estatistica com parametros minimos validos.
- GET /inteligencia-dados/insights/widgets | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Verificar endpoint de previsao com input simples e resposta sem erro.
- POST /inteligencia-dados/insights/generate | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Enviar dataset invalido para rota de analise e confirmar erro de validacao.
- POST /inteligencia-dados/query | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Omitir metadados obrigatorios na rota de modelos ML e validar retorno 4xx.
- POST /inteligencia-dados/captura-dados | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Enviar formato de data inconsistente e verificar resposta de erro clara.
- POST /inteligencia-dados/tratamento-limpeza | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Testar volume maior de registros em consulta para observar tempo e estabilidade.
- POST /inteligencia-dados/criar-modelo-ml | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Enviar dados com campos faltantes opcionais e validar fallback seguro.
- GET /inteligencia-dados/listar-modelos | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Usar valores extremos (muito altos/baixos) em campos numericos e observar comportamento.
- POST /inteligencia-dados/prever | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Fazer pergunta analitica ampla sem metrica definida e avaliar orientacao do endpoint.
- POST /inteligencia-dados/chat | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Enviar instrucao que mistura previsao e limpeza no mesmo payload e verificar tratamento.
- POST /inteligencia-dados/agendar-retreino | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Informar objetivo de negocio sem dataset explicito e validar mensagem de apoio.
- POST /inteligencia-dados/executar-retreino-agendado | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Validar consulta basica de InteligenciaDados com retorno estruturado e status 2xx.
- GET /inteligencia-dados/agendamentos-pendentes | scope=InteligenciaDados | source=inteligencia_dados_tests.md | question=Confirmar endpoint de analise estatistica com parametros minimos validos.

## Ciclos executados
- Total: 3

## Falhas detectadas
- POST /inteligencia-dados/analise-estatistica status 422
- POST /inteligencia-dados/analise-dados-inicial status 422
- POST /inteligencia-dados/insights/generate status 422
- POST /inteligencia-dados/query status 422
- POST /inteligencia-dados/captura-dados status 422
- POST /inteligencia-dados/tratamento-limpeza status 422
- POST /inteligencia-dados/criar-modelo-ml status 422
- GET /inteligencia-dados/listar-modelos status 422
- POST /inteligencia-dados/prever status 422
- POST /inteligencia-dados/chat status 422
- POST /inteligencia-dados/agendar-retreino status 422
- POST /inteligencia-dados/executar-retreino-agendado status 422
- BASELINE api/app/InteligenciaDados erro: Nenhum método de teste disponível (sem docker-compose.yml e sem requirements.txt/venv).
- POST /inteligencia-dados/analise-estatistica status 422
- POST /inteligencia-dados/analise-dados-inicial status 422
- POST /inteligencia-dados/insights/generate status 422
- POST /inteligencia-dados/query status 422
- POST /inteligencia-dados/captura-dados status 422
- POST /inteligencia-dados/tratamento-limpeza status 422
- POST /inteligencia-dados/criar-modelo-ml status 422
- GET /inteligencia-dados/listar-modelos status 422
- POST /inteligencia-dados/prever status 422
- POST /inteligencia-dados/chat status 422
- POST /inteligencia-dados/agendar-retreino status 422
- POST /inteligencia-dados/executar-retreino-agendado status 422
- BASELINE api/app/InteligenciaDados erro: Nenhum método de teste disponível (sem docker-compose.yml e sem requirements.txt/venv).
- POST /inteligencia-dados/analise-estatistica status 422
- POST /inteligencia-dados/analise-dados-inicial status 422
- POST /inteligencia-dados/insights/generate status 422
- POST /inteligencia-dados/query status 422
- POST /inteligencia-dados/captura-dados status 422
- POST /inteligencia-dados/tratamento-limpeza status 422
- POST /inteligencia-dados/criar-modelo-ml status 422
- GET /inteligencia-dados/listar-modelos status 422
- POST /inteligencia-dados/prever status 422
- POST /inteligencia-dados/chat status 422
- POST /inteligencia-dados/agendar-retreino status 422
- POST /inteligencia-dados/executar-retreino-agendado status 422
- BASELINE api/app/InteligenciaDados erro: Nenhum método de teste disponível (sem docker-compose.yml e sem requirements.txt/venv).

## Correcoes aplicadas
- Rodada 1: sem detalhes
- Rodada 2: sem detalhes
- Rodada 3: sem detalhes

## Status final
- failed

## Evidencias principais
- POST /inteligencia-dados/analise-estatistica status 422
- POST /inteligencia-dados/analise-dados-inicial status 422
- POST /inteligencia-dados/insights/generate status 422
- POST /inteligencia-dados/query status 422
- POST /inteligencia-dados/captura-dados status 422
- POST /inteligencia-dados/tratamento-limpeza status 422
- POST /inteligencia-dados/criar-modelo-ml status 422
- GET /inteligencia-dados/listar-modelos status 422
- POST /inteligencia-dados/prever status 422
- POST /inteligencia-dados/chat status 422
- POST /inteligencia-dados/agendar-retreino status 422
- POST /inteligencia-dados/executar-retreino-agendado status 422
- BASELINE api/app/InteligenciaDados erro: Nenhum método de teste disponível (sem docker-compose.yml e sem requirements.txt/venv).
- POST /inteligencia-dados/analise-estatistica status 422
- POST /inteligencia-dados/analise-dados-inicial status 422
- POST /inteligencia-dados/insights/generate status 422
- POST /inteligencia-dados/query status 422
- POST /inteligencia-dados/captura-dados status 422
- POST /inteligencia-dados/tratamento-limpeza status 422
- POST /inteligencia-dados/criar-modelo-ml status 422
- GET /inteligencia-dados/listar-modelos status 422
- POST /inteligencia-dados/prever status 422
- POST /inteligencia-dados/chat status 422
- POST /inteligencia-dados/agendar-retreino status 422
- POST /inteligencia-dados/executar-retreino-agendado status 422
- BASELINE api/app/InteligenciaDados erro: Nenhum método de teste disponível (sem docker-compose.yml e sem requirements.txt/venv).
- POST /inteligencia-dados/analise-estatistica status 422
- POST /inteligencia-dados/analise-dados-inicial status 422
- POST /inteligencia-dados/insights/generate status 422
- POST /inteligencia-dados/query status 422
