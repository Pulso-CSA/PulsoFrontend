# Análise total – PulsoAPI (app/)

**Escopo:** pasta `app/`. Objetivo: segurança, multi-usuário, velocidade, custo, organização e inventário de funcionalidades.

---

## 1. Segurança

| Aspecto | Situação | Observação |
|--------|----------|------------|
| **Rate limit** | Implementado | `utils/rate_limit.py`: limite por IP (RATE_LIMIT_REQUESTS_PER_MINUTE, default 120/min). Middleware em `main.py` retorna 429 se excedido. |
| **Tamanho do body** | Limitado | `MAX_BODY_SIZE_BYTES` (env `MAX_BODY_SIZE_MB`, default 1 MB). POST/PUT/PATCH rejeitados com 413 se ultrapassar. |
| **Exceções em produção** | Ocultas | `global_exception_handler`: em produção não expõe stack nem detalhe da exceção; retorna "Erro interno." + request_id. |
| **Request ID** | Rastreio | `X-Request-Id` no middleware; resposta 4xx/5xx inclui request_id para log. |
| **Path traversal** | Validado | `utils/path_validation.py`: `sanitize_root_path` rejeita `..` e paths fora de `ALLOWED_ROOT_BASE`. |
| **CORS** | Configurável | Produção: `ALLOWED_ORIGINS` por env (nunca `*`); fallback Railway. `config.py` lista chaves sensíveis que nunca são exibidas. |
| **Chaves de API** | Não logadas | `.env` carregado em `main.py`; status "carregada/não encontrada" apenas. OpenAI/Stripe nunca expostos em print. |
| **Webhook Stripe** | Assinatura verificada | `root_webhook` usa `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)`. |
| **ID artefatos** | Sanitização | `id_artifacts_io`: usuario e id_requisicao sanitizados (alnum + ._-); paths sob diretório controlado. |
| **Autenticação** | Parcial | Login/profile/subscription existem; rotas de ID e compreensão não exigem token por padrão. Depende de uso de `Depends` em cada rota. |

**Gaps:** Rotas ID e compreensão não têm auth obrigatória; qualquer um com a URL pode chamar. Recomendação: proteger com Depends(verificar_token) ou API key por ambiente.

---

## 2. Múltiplos usuários

| Aspecto | Situação | Observação |
|--------|----------|------------|
| **Artefatos ID** | Isolados por usuário | `get_artifact_dir(usuario, id_requisicao, subdir)`: paths `base/usuario/id_requisicao/datasets|models`. Usuario default se não informado. |
| **Modelos e datasets** | Por usuario + id_requisicao | Salvos em diretórios distintos; listagem de modelos por id_requisicao. |
| **Agendamentos** | Globais no arquivo | `agendamentos_retreino.json` único; agendamento guarda `usuario` e `id_requisicao` para execução. Não há isolamento por tenant no arquivo. |
| **Rate limit por usuário** | Opcional | `RATE_LIMIT_PER_USER_PER_MINUTE` (0 = desativado). Se > 0, `check_rate_limit_user(usuario)` pode ser usado nas rotas. |
| **Login/Profile/Subscription** | Por usuário | Rotas de perfil e assinatura atreladas a usuário/contas. |
| **Cache de intent (chat ID)** | Por hash mensagem+contexto | Cache em memória global; não separado por usuario (reuso entre usuários com mesma mensagem). |

**Conclusão:** Pronto para múltiplos usuários na camada ID (usuario + id_requisicao). Falta: auth obrigatória nas rotas e, se necessário, rate limit por usuário ativo; agendamentos poderiam ser por usuario (subdir ou chave no JSON).

---

## 3. Otimização de velocidade

| Aspecto | Situação | Observação |
|--------|----------|------------|
| **Singleton OpenAI** | Uma instância por processo | `get_openai_client()` com lock; evita recriar cliente a cada request. |
| **Modelo rápido (LLM)** | Uso em tarefas leves | `use_fast_model=True` em ID (análise, chat, modelos_ml), comprehension, refino, etc. Usa `OPENAI_MODEL_FAST` (ex.: gpt-4o-mini) — menor latência e custo. |
| **Cache de interpretação (chat ID)** | Até 100 entradas | Hash(mensagem + dataset_ref + model_ref + db_config); evita nova chamada LLM para mesma pergunta/contexto. |
| **Paginação MySQL** | Suportada | `mysql_connection`: limit/offset em consultas; evita carregar tabelas inteiras. |
| **Amostra opcional (captura)** | Limitada | `max_rows_amostra` (default 100, máx 10k); reduz volume trafegado. |
| **Parquet** | Datasets | Leitura/escrita em Parquet (compactado); mais rápido que CSV para grandes volumes. |

**Gaps:** Cache de intent é em memória (perdido no restart). Para alta escala: Redis ou TTL; conexões MySQL/Mongo com pool já previstas no plano ID.

---

## 4. Redução de custos

| Aspecto | Situação | Observação |
|--------|----------|------------|
| **OPENAI_MODEL_FAST** | gpt-4o-mini (default) | Tarefas de classificação, refino, análise e chat usam modelo barato. |
| **use_fast_model=True** | Padrão em ID e comprehension | Geração de texto para intent, justificativas, insights e análise inicial. |
| **Cache de intent** | Menos chamadas LLM | Mesma pergunta + contexto = resposta em cache. |
| **Chamadas LLM apenas quando necessário** | Motivo precisão baixa | Só gera `motivo_precisao_baixa` quando acurácia < 70%. |
| **PyCaret** | Compare e escolha um modelo | Evita treinar muitos modelos manualmente; limiar 70% evita deploy de modelo ruim. |

**Recomendações:** Manter uso de fast model em fluxos leves; considerar cache distribuído (Redis) para múltiplas instâncias; monitorar tokens por endpoint.

---

## 5. Organização

| Camada | Local | Papel |
|--------|--------|--------|
| **Core** | `app/core/` | Conexões e config: ID_core (MySQL, Mongo), openai (cliente LLM), pulso (config), storage (vectorstore). |
| **Models** | `app/models/` | DTOs/Pydantic: por domínio (ID_models, login, etc.). |
| **Services** | `app/services/` | Regras de negócio: ID_services, comprehension_services, pipeline_services, agents, login, profile, subscription, etc. |
| **Routers** | `app/routers/` | Endpoints FastAPI: um router por área (ID_routers, analise_router, correct_router, workflow, etc.). |
| **Agents** | `app/agents/` | Agentes LLM: architecture, execution, governance, ID (encapsulam serviços ID). |
| **Storage** | `app/storage/` | Persistência: database (login, etc.), id_artifacts (Parquet, modelos, agendamentos), vectorstore. |
| **Utils** | `app/utils/` | rate_limit, path_validation, log_manager, file_loader, etc. |
| **Prompts** | `app/prompts/` | Textos de prompt por domínio (analyse, correct, creation, ID_prompts, tela_teste). |

Padrão consistente: core → models → services → routers (e agents quando há LLM). ID segue o mesmo: ID_core, ID_models, ID_services, ID_routers, agents/ID.

---

## 6. Todas as rotas do sistema

Cada linha: **Método** **Rota** — **O que faz** | **Para que serve**.

### 6.1 Raiz
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| GET | `/` | Retorna status, nome, versão e descrição da API | Health check e informação básica para o cliente |
| POST | `/` | Recebe webhook do Stripe, valida assinatura e delega ao handler de subscription | Receber eventos de pagamento/assinatura (checkout, cancelamento, etc.) |

### 6.2 Autenticação (`/auth`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| GET | `/auth/login/google` | Redireciona para login OAuth Google | Início do fluxo de login com Google |
| GET | `/auth/login/google/callback` | Callback OAuth; troca código por token e cria sessão | Finalizar login Google e obter usuário |
| POST | `/auth/signup` | Registra novo usuário (email/senha ou similar) | Cadastro |
| POST | `/auth/login` | Autentica credenciais e retorna tokens | Login por email/senha |
| POST | `/auth/logout` | Invalida sessão/token | Logout |
| POST | `/auth/refresh` | Renova access token usando refresh token | Manter sessão ativa |
| POST | `/auth/request-password-reset` | Envia email de recuperação de senha | Recuperação de senha (passo 1) |
| POST | `/auth/reset-password` | Redefine senha com token enviado por email | Recuperação de senha (passo 2) |
| GET | `/auth/me` | Retorna dados do usuário autenticado | Verificar quem está logado |
| POST | `/auth/profiles` | Cria perfil (201) | Criar perfil associado ao usuário |
| GET | `/auth/profiles` | Lista perfis do usuário | Listar perfis |
| GET | `/auth/profiles/{profile_id}` | Retorna um perfil por ID | Detalhe do perfil |
| PUT | `/auth/profiles/{profile_id}` | Atualiza perfil | Editar perfil |
| DELETE | `/auth/profiles/{profile_id}` | Remove perfil (204) | Excluir perfil |

### 6.3 Perfis (`/profiles`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| GET | `/profiles` | Lista perfis (com filtros/contexto do usuário) | Listagem de perfis na área de perfis |
| POST | `/profiles` | Cria perfil (201) | Criar perfil |
| PUT | `/profiles/{profile_id}` | Atualiza perfil | Editar perfil |
| DELETE | `/profiles/{profile_id}` | Remove perfil | Excluir perfil |
| POST | `/profiles/{profile_id}/invite` | Envia convite para o perfil | Convidar membro |
| POST | `/profiles/{profile_id}/accept-invite` | Aceita convite e associa ao usuário | Aceitar convite |
| GET | `/profiles/{profile_id}/members` | Lista membros do perfil | Ver membros do perfil |

### 6.4 Assinatura (`/subscription`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| GET | `/subscription` | Retorna estado da assinatura do usuário | Exibir plano e status |
| GET | `/subscription/invoices` | Lista faturas | Histórico de pagamentos |
| POST | `/subscription/cancel` | Cancela assinatura | Cancelar plano |
| POST | `/subscription/resume` | Reativa assinatura cancelada | Reativar plano |
| POST | `/subscription/change-plan` | Altera plano (upgrade/downgrade) | Mudar plano |
| GET | `/subscription/portal` | Retorna URL do portal do cliente Stripe | Usuário gerir assinatura no Stripe |
| POST | `/subscription/webhook` | Recebe eventos Stripe (assinatura) | Webhook alternativo de subscription |

### 6.5 Inteligência de Dados (`/inteligencia-dados`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/inteligencia-dados/query` | Recebe pergunta em linguagem natural + db_config; gera SQL/consulta (LLM) e executa se aplicável | Consultar base em linguagem natural |
| POST | `/inteligencia-dados/captura-dados` | Conecta MySQL ou MongoDB; extrai tabelas/coleções, contagens, índices; opcionalmente amostra em Parquet e retorna dataset_ref | Conhecer estrutura da base e obter amostra para análise |
| POST | `/inteligencia-dados/analise-dados-inicial` | Interpreta objetivo e retorno da captura (ou dataset_ref); sugere variáveis alvo e tratamentos (LLM) | Definir o que analisar e como tratar os dados |
| POST | `/inteligencia-dados/tratamento-limpeza` | ETL: duplicatas, missing, outliers (IQR); persiste dataset em Parquet; retorna dataset_pronto | Limpar e normalizar dados antes de modelo/estatística |
| POST | `/inteligencia-dados/analise-estatistica` | Calcula métricas (média, mediana, quartis, assimetria, curtose), correlações, responde pergunta (correlação, regressão, normalidade); insights (LLM) | Análise exploratória e respostas diretas a perguntas estatísticas |
| POST | `/inteligencia-dados/criar-modelo-ml` | Treina com PyCaret (compare_models); limiar 70%; salva modelo; retorna model_ref, importância de variáveis, métricas; se acurácia < 70% retorna motivo_precisao_baixa (LLM) | Treinar modelo de classificação/regressão e obter modelo pronto para previsão |
| GET | `/inteligencia-dados/listar-modelos` | Lista todos os model_ref do id_requisicao (e usuario) | Ver versões de modelos (A/B ou histórico) |
| POST | `/inteligencia-dados/prever` | Carrega modelo por model_ref; aplica a dataset_ref ou dados; valida schema; retorna previsões, métricas de negócio, intervalos (regressão) | Previsão em lote ou em tempo real (ex.: no chat) |
| POST | `/inteligencia-dados/chat` | Interpreta mensagem em linguagem natural; executa captura, tratamento, estatística, treino e/ou previsão conforme intenção; retorna resposta unificada com previsões | Um único ponto de entrada “estilo cientista de dados” no chat |
| POST | `/inteligencia-dados/agendar-retreino` | Registra agendamento de retreino (dataset_ref, variavel_alvo, cron ou proxima_execucao) | Agendar retreino periódico do modelo |
| POST | `/inteligencia-dados/executar-retreino-agendado` | Executa um retreino agendado (body: agendamento_id); treina e atualiza modelo | Rodar retreino quando due (cron ou manual) |
| GET | `/inteligencia-dados/agendamentos-pendentes` | Lista agendamentos de retreino ainda não executados | Consultar fila de retreinos |

### 6.6 Compreensão (entrada do workflow)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| GET | `/comprehension/contract` | Retorna contrato (request/response) da rota de compreensão para o frontend | Documentação dinâmica e integração frontend |
| POST | `/comprehension/run` | Classifica intenção (analisar vs executar), estado do projeto; opcionalmente chama governance/run ou workflow/correct/run; retorna mensagem humanizada, intent, tempo | Entrada principal do produto: usuário descreve o que quer e o sistema decide qual fluxo (governança ou correção) executar |

### 6.7 Aliases da spec (rotas na raiz, como na documentação)
Todas reencaminham para a lógica das camadas (governance, backend, infra, execution); permitem chamar pelo nome da spec sem prefixo de camada.

| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/input` | Recebe prompt inicial; armazena e retorna id_requisicao (alias de governance/input) | Primeiro passo do fluxo: enviar pedido do usuário |
| POST | `/refinar` | Refina prompt com base em id_requisicao (alias de governance/refine) | Refinar o pedido antes de validar |
| POST | `/validar` | Valida prompt e prepara para as camadas seguintes (alias de governance/validate) | Validar pedido antes de análise |
| POST | `/analise-estrutura` | Analisa estrutura do projeto (alias de backend) | Análise de estrutura (Camada 2) |
| POST | `/analise-backend` | Analisa backend/código (alias de backend) | Análise de backend (Camada 2) |
| POST | `/analise-infra` | Analisa infraestrutura (alias de infra) | Análise de infra (Camada 2) |
| POST | `/seguranca-infra` | Analisa segurança da infra (alias de infra) | Segurança infra (Camada 2) |
| POST | `/seguranca-codigo` | Analisa segurança do código (alias de backend) | Segurança código (Camada 2) |
| POST | `/criar-estrutura` | Cria estrutura a partir de relatório (alias de execution) | Criar estrutura do projeto (Camada 3) |
| POST | `/criar-codigo` | Gera código a partir de relatórios (alias de execution) | Criar código (Camada 3) |

### 6.8 Governança (Camada 1 – sem prefixo no router)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/governance/run` | Executa workflow completo: input → refino → validação → blueprint → análises backend/infra e segurança | Automatizar todo o fluxo Camada 1 + Camada 2 em uma chamada |
| POST | `/governance/input` | Recebe prompt, gera id_requisicao, persiste na camada 1 | Registrar pedido inicial (usado por /input) |
| POST | `/governance/refine` | Refina prompt do id_requisicao (LLM) | Refinar pedido (usado por /refinar) |
| POST | `/governance/validate` | Valida prompt e marca como validado | Validar pedido (usado por /validar) |

### 6.9 Backend (Camada 2 – prefixo `/backend`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/backend/analise-estrutura` | Analisa estrutura do projeto (árvore, componentes) | Entender estrutura atual |
| POST | `/backend/analise-backend` | Analisa backend/código (APIs, padrões) | Entender backend atual |
| POST | `/backend/seguranca-codigo` | Analisa segurança do código (vulnerabilidades, boas práticas) | Checagem de segurança no código |

### 6.10 Infra (Camada 2 – prefixo `/infra`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/infra/analise-infra` | Analisa infraestrutura (deploy, serviços, redes) | Entender infra atual |
| POST | `/infra/seguranca-infra` | Analisa segurança da infraestrutura | Checagem de segurança na infra |

### 6.11 Execução (Camada 3 – prefixo `/execution`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/execution/execution/create-structure` | Cria estrutura de pastas/arquivos a partir de manifesto/relatório | Gerar esqueleto do projeto |
| POST | `/execution/execution/create-code` | Gera código a partir de relatórios de análise | Gerar código inicial |

### 6.12 Deploy (`/deploy/docker`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/deploy/docker/start` | Inicia container/serviço Docker | Subir ambiente |
| POST | `/deploy/docker/rebuild` | Rebuild e sobe container | Atualizar e subir |
| POST | `/deploy/docker/stop` | Para container | Parar ambiente |
| GET | `/deploy/docker/logs` | Retorna logs do deploy | Debug e monitoramento |
| DELETE | `/deploy/docker/logs/clear` | Limpa logs | Limpar buffer de logs |

### 6.13 Code Plan / Code Writer / Code Implementer (C2b, C3, C4)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/code-plan/run` | Gera plano de correção de código (o que mudar, em que ordem) | Planejar correções antes de implementar |
| POST | `/code-writer/run` | Gera código/trechos a partir de contexto e especificação | Gerar código assistido por IA |
| POST | `/code-implementer/run` | Aplica implementação final (correções no projeto) | Implementar mudanças no código base |

### 6.14 Workflows
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/workflow/correct/run` | Executa workflow de correção estrutural (análise + correção guiada) | Corrigir projeto conforme especificação |
| POST | `/workflow/correct/full-run` | Executa fluxo full auto de correção em uma chamada | Automatizar todo o fluxo de correção |

### 6.15 Pipeline (11–13.2) — rotas de pipeline
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/pipeline/teste-automatizado` | Roda testes no backend (venv ou Docker); retorna relatório de testes | Etapa 11 do pipeline: validar estado atual com testes |
| POST | `/pipeline/analise-retorno` | Analisa resultado dos testes; extrai objetivo_final, falhas, vulnerabilidades, faltantes (LLM) | Etapa 12: interpretar resultado dos testes para decidir correções |
| POST | `/pipeline/correcao-erros` | Aplica correções com base na análise de retorno; chama workflow de correção; retorna relatório de correção | Etapa 13: corrigir erros identificados |
| POST | `/pipeline/seguranca-codigo-pos` | Revalida segurança do código após correções; retorna corrigidas, pendentes, recomendações | Etapa 13.1: garantir que código pós-correção está seguro |
| POST | `/pipeline/seguranca-infra-pos` | Revalida segurança da infra após correções | Etapa 13.2: garantir que infra pós-correção está segura |

### 6.16 Tela de teste
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/analise-tela-teste` | Analisa requisitos/contexto para tela de teste (LLM) | Definir o que testar na tela |
| POST | `/criar-tela-teste` | Gera tela de teste com base na análise | Gerar artefato de tela de teste |

### 6.17 Venv (`/venv`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| GET | `/venv/logs` | Retorna logs do gerenciamento de venv | Debug do venv |
| DELETE | `/venv/logs/clear` | Limpa logs do venv | Limpar logs |
| POST | `/venv/create` | Cria ambiente virtual | Criar venv |
| POST | `/venv/recreate` | Recria venv (remove e cria de novo) | Resetar ambiente |
| POST | `/venv/execute` | Executa comando no venv | Rodar comandos no venv |
| POST | `/venv/deactivate` | Desativa venv | Desativar ambiente |

### 6.18 Test (`/test`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/test/run` | Executa testes (Venv + Docker); retorna resultado da execução | Rodar suite de testes do projeto |

### 6.19 Análise estrutural (`/struc-anal`)
| Método | Rota | O que faz | Para que serve |
|--------|------|-----------|----------------|
| POST | `/struc-anal/plan` | Gera plano de análise estrutural do projeto | Planejar análise da estrutura (pastas, módulos, dependências) |

---

## 7. Rotas de pipeline: o que são e por que existem

**O que é um pipeline aqui:** sequência de etapas automatizadas em que a saída de uma alimenta a próxima, para um objetivo único (ex.: “testar → analisar falhas → corrigir → revalidar segurança”).

**Quais rotas são de pipeline:** todas sob o prefixo **`/pipeline`** (router `pipeline_router`, tag "Pipeline (11–13.2)").

**Por que são pipeline:**

1. **Ordem fixa e encadeada:** 11 → 12 → 13 → 13.1 → 13.2. Cada etapa consome o resultado da anterior (ex.: `analise-retorno` recebe o `relatorio_testes` de `teste-automatizado`; `correcao-erros` recebe `analise_retorno`; as rotas de segurança pós recebem `relatorio_correcao`).

2. **Objetivo único:** garantir qualidade e segurança do projeto após mudanças: rodar testes, interpretar falhas, corrigir, revalidar segurança de código e de infra.

3. **Automatização:** pensadas para serem chamadas por orquestrador (CI/CD ou frontend em sequência), não apenas por usuário clicando uma vez; cada POST é um passo do pipeline.

4. **Rastreio:** todas usam `id_requisicao` e `root_path` (quando aplicável) para manter contexto da mesma “execução” do pipeline.

5. **Numeração 11–13.2:** reflete a especificação do produto (passos 11, 12, 13, 13.1, 13.2 do fluxo de qualidade). Não são pipelines: governance/run, comprehension/run, workflow/correct/run — são **workflows** (um único endpoint orquestra vários passos internos). No pipeline, o cliente (ou cron) chama cada etapa explicitamente e passa o payload da etapa anterior.

**Resumo:** As rotas `/pipeline/*` são as únicas que, no desenho atual, formam um **pipeline explícito** de etapas (teste → análise → correção → segurança código → segurança infra). As demais são endpoints de serviço ou workflows que orquestram passos internamente.

---

## 8. Riscos, gaps e pontos de atenção

Pontos a considerar para segurança, multi-tenancy, custo e operação em produção. Não substituem auditoria de segurança formal.

### 8.1 Autenticação e autorização

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Autenticação não obrigatória por padrão** | Rotas sensíveis (ID, comprehension, workflows, pipeline, deploy, venv, test) podem estar expostas a quem tiver a URL. | Aplicar `Depends(verificar_token)` (ou equivalente) em todas as rotas sensíveis; manter opcional apenas em health/contract se desejado. |
| **Autorização vs autenticação** | Mesmo logado, não há evidência de RBAC/escopo por usuário ou perfil (quem pode fazer o quê em cada workspace/perfil). | Definir papéis e escopos; checar permissão por recurso (ex.: este usuário pode usar este profile_id, este id_requisicao). |
| **Entitlements / feature gating incerto** | Existir assinatura não garante bloqueio real de features caras ou sensíveis (ex.: LLM pesado, retreino, deploy). | Mapear features por plano; validar entitlement antes de executar ação; retornar 403 com mensagem clara quando plano não cobre. |

### 8.2 Cache e isolamento

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Cache de intent global sem isolamento** | Cache de interpretação (chat ID) é global; reuso de decisões entre usuários com mesmas entradas → “vazamento comportamental” e possível vazamento de contexto. | Incluir `usuario` (ou tenant_id) na chave do cache; ou desativar cache até haver isolamento. |
| **Cache em memória volátil** | Perde no restart; não escala horizontalmente; comportamento inconsistente entre instâncias. | Migrar para Redis (ou similar) com TTL; mesma chave em todas as instâncias para consistência. |

### 8.3 Rate limit e billing

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Rate limit por usuário desativado por default** | Existe `check_rate_limit_user`, mas RATE_LIMIT_PER_USER_PER_MINUTE=0; na prática só rate limit por IP. | Ativar por usuário onde fizer sentido; aplicar em comprehension e rotas ID sensíveis. |
| **Rate limit não diferenciado por plano** | Billing/Stripe existe, mas não há sinal de quotas/limites por tier (requests, tokens, jobs). | Definir quotas por plano (requests/min, tokens/mês, jobs em fila); rejeitar ou enfileirar quando exceder. |
| **Custos de LLM sem orçamento por endpoint** | Fast model e cache ajudam, mas faltam quotas, observabilidade de tokens e bloqueio por abuso. | Medir tokens por rota/usuário; alertas e hard limit por conta/plano; opcionalmente orçamento por endpoint em ambiente crítico. |

### 8.4 Superfícies duplicadas e contratos

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Duplicidade /auth/profiles e /profiles** | Duas superfícies de perfis; risco de contratos divergentes, lógica duplicada e confusão no frontend. | Unificar em um único conjunto de rotas (ex.: só `/profiles` com auth) ou documentar claramente o papel de cada um e manter sincronizados. |
| **Validação de schema/contratos entre etapas** | Múltiplas etapas (captura→tratamento→treino→previsão) sem contratos rígidos → drift e erros silenciosos. | Definir schemas (ex.: OpenAPI/JSON Schema) por payload entre etapas; validar em cada entrada; versionar contrato quando mudar. |

### 8.5 Dados e conexões (ID)

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **NL→SQL/consulta sem governança explícita** | Query em linguagem natural pode virar consulta livre; risco operacional (DELETE, DDL, sobrecarga). | Garantir read-only na conexão ou allowlist de comandos; validar/sanitizar SQL gerado pelo LLM; timeout e limite de linhas. |
| **db_config como vetor de abuso** | Se aceito livremente pelo cliente, pode direcionar conexões/consultas para alvos indevidos. | Allowlist de hosts/databases permitidos; não aceitar credenciais arbitrárias do cliente; preferir conexões pré-configuradas por tenant. |

### 8.6 Agendamentos e retreino

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Agendamentos em arquivo único global** | Pouca escalabilidade; risco de concorrência/corrupção; difícil isolamento por tenant; ruim para múltiplas instâncias. | Persistir em BD com tenant_id; ou fila (Redis/RQ/Celery) com fila por tenant/plano. |
| **Execução de retreino sem fila/lock** | Risco de rodar duplicado, em paralelo, consumindo recursos inesperadamente. | Fila com um worker por agendamento_id; lock (BD ou Redis) antes de executar; marcar “em execução” e “concluído” de forma atômica. |

### 8.7 Endpoints de alto poder e logs

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Endpoints operacionais de alto poder** | `/deploy/docker/*`, `/venv/execute`, `/test/run` podem virar “terminal remoto via HTTP” se não protegidos. | Autenticação obrigatória + autorização (ex.: só admin ou serviço interno); preferir rede interna ou VPN; auditoria de quem chamou. |
| **Allowlist de comandos no venv** | Se `/venv/execute` aceitar comandos arbitrários → risco de RCE e custo descontrolado. | Allowlist estrita de comandos (ex.: pip install X, pytest); nunca passar comando livre do cliente; timeout e limite de recursos. |
| **Logs operacionais podem vazar segredos** | Endpoints de logs (docker/venv) podem expor tokens, variáveis de ambiente, stack traces. | Sanitizar logs antes de retornar (remover env, tokens, paths internos); restringir acesso a logs por perfil. |

### 8.8 Pipelines, workflows e rastreabilidade

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Idempotência fraca em pipelines/workflows** | Sem run_id forte e persistência de artefatos, fica difícil auditar, reproduzir e evitar reexecução acidental. | Gerar run_id por execução; persistir inputs e outputs por run_id; suportar idempotency key no header para POST. |
| **Rastreabilidade parcial** | request_id ajuda por request, mas falta trilha consolidada por “execução de pipeline/workflow” (inputs→artefatos→outputs). | Um correlation_id por “execução” (ex.: pipeline 11→13.2); log e storage de artefatos indexados por esse id. |

### 8.9 ML e produto

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Limiar fixo de 70% no ML** | Pode bloquear casos válidos (ex.: baseline pior que 70%, ou plano que permite modelo “experimental”). | Tornar configurável por request ou por plano; ou derivar de baseline/regra de negócio. |

### 8.10 Usuário, storage e configuração

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Usuario default quando não informado** | “usuario default se não informado” pode agrupar dados de usuários não autenticados ou mal identificados. | Em rotas sensíveis, exigir usuario (ou token que resolva para usuario); não usar default em produção para ações que escrevem dados. |
| **Isolamento de storage depende de input sanitizado** | Qualquer falha no “contexto do usuário” (ex.: header falsificado) pode levar a leitura/gravação em pasta errada. | Usuario/tenant sempre derivado de token/sessão no servidor; nunca confiar em header/body para isolamento sem validar assinatura/sessão. |
| **CORS por env com risco de má configuração** | Erro de config pode abrir para origens indevidas ou quebrar clientes legítimos. | Lista mínima em produção; testes de smoke com origens esperadas; documentar variável FRONTEND_ORIGINS. |

### 8.11 Webhooks e paginação

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Webhooks Stripe duplicados/alternativos** | Duas rotas (POST / e POST /subscription/webhook) podem gerar processamento duplicado se não houver idempotência por event_id. | Processar cada event_id do Stripe no máximo uma vez (BD ou cache); rota única de webhook ou roteamento explícito sem duplicar lógica. |
| **Paginação/limites inconsistentes** | Se alguns endpoints não aplicarem limites uniformes, viram ponto de explosão (memória, custo, tempo). | Política global: max page size, timeout, max rows em consultas e amostras; aplicar em ID (captura, query) e em listagens. |

### 8.12 Observabilidade

| Ponto | Risco | Recomendação |
|------|--------|----------------|
| **Observabilidade incompleta** | Sem métricas (latência por rota, taxa de erro, custo/tokens, jobs em fila) fica difícil operar em produção com previsibilidade. | Expor métricas (Prometheus/StatsD): latência por rota, 4xx/5xx, tokens por chamada LLM, tamanho de filas; alertas e dashboards por ambiente. |

---

## 9. Resumo

- **Segurança:** rate limit (por IP), body limit, exceções ocultas em produção, path validation, CORS e secrets não logados. Falta: auth obrigatória em rotas sensíveis e RBAC (seção 8.1).
- **Multi-usuário:** artefatos ID por usuario + id_requisicao; login/profile/subscription por usuário. Agendamentos em arquivo único; riscos em 8.6.
- **Velocidade:** singleton OpenAI, use_fast_model, cache de intent, paginação e Parquet. Cache volátil e sem isolamento por usuário (8.2).
- **Custo:** modelo rápido e cache reduzem custo; faltam quotas por plano e observabilidade de tokens (8.3, 8.12).
- **Organização:** core / models / services / routers / agents / storage / utils / prompts; ID alinhado ao mesmo padrão.
- **Rotas:** Seção 6 lista todas as rotas; Seção 7 explica rotas de pipeline (`/pipeline/*`).
- **Riscos e gaps:** Seção 8 consolida autenticação/autorização, cache, rate limit/billing, duplicidade de APIs, NL→SQL e db_config, agendamentos e retreino, endpoints de alto poder, logs, idempotência/rastreabilidade, ML, usuario default/storage, CORS, webhooks, paginação e observabilidade, com recomendações.
