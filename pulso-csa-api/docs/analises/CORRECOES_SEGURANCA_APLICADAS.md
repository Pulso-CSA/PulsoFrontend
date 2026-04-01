# Correções de Segurança e Gaps Aplicadas

## ✅ Correções Implementadas

### 1. Autenticação Obrigatória em Rotas Sensíveis
- **Criado**: `app/core/auth/auth_deps.py` com `verificar_token()` dependency
- **Aplicado em**:
  - `/inteligencia-dados/chat`
  - `/inteligencia-dados/criar-modelo-ml`
  - `/inteligencia-dados/listar-modelos`
  - `/inteligencia-dados/prever`
  - `/inteligencia-dados/captura-dados`
  - `/inteligencia-dados/tratamento-limpeza`
  - `/inteligencia-dados/analise-estatistica`
  - `/inteligencia-dados/query`
  - `/inteligencia-dados/agendar-retreino`
  - `/inteligencia-dados/executar-retreino-agendado`
  - `/inteligencia-dados/agendamentos-pendentes`

### 2. Cache Isolado por Usuário
- **Arquivo**: `app/services/ID_services/id_chat_service.py`
- **Mudança**: Cache de interpretação LLM agora inclui `usuario` na chave (`cache_key_user = f"{usuario or 'default'}:{cache_key}"`)
- **Benefício**: Evita vazamento comportamental entre usuários

### 3. Usuário Obrigatório (Não Default)
- **Aplicado em rotas ID que escrevem dados**:
  - `/chat`: `payload.usuario = user.get("email") or user.get("_id")`
  - `/criar-modelo-ml`: `payload.usuario = user.get("email") or user.get("_id")`
  - `/captura-dados`: `payload.usuario = user.get("email") or user.get("_id")`
  - `/tratamento-limpeza`: `payload.usuario = user.get("email") or user.get("_id")`
  - `/agendar-retreino`: `payload.usuario = user.get("email") or user.get("_id")`

### 4. Validação de db_config (Allowlist)
- **Criado**: `app/utils/db_config_validation.py`
- **Funcionalidade**: Valida hosts e databases contra allowlist via env vars:
  - `ALLOWED_DB_HOSTS` (comma-separated)
  - `ALLOWED_DB_DATABASES` (comma-separated)
- **Aplicado em**:
  - `captura_dados_service.py`
  - `query_get_service.py`
  - `id_chat_service.py`

### 5. Lock para Retreino (Evitar Duplicação)
- **Criado**: `app/utils/retreino_lock.py`
- **Funcionalidade**: Lock por `agendamento_id` para evitar execução concorrente/duplicada
- **Aplicado em**: `agendamento_retreino_service.py` no método `executar_um()`

### 6. Limiar ML Configurável
- **Arquivo**: `app/services/ID_services/modelos_ml_service.py`
- **Mudanças**:
  - Limiar via env: `ML_ACURACIA_MINIMA` (padrão: 0.70)
  - Limiar por request: `payload.acuracia_minima` (opcional)
  - Atualizado modelo: `ModelosMLInput.acuracia_minima: Optional[float]`

### 7. NL→SQL Read-Only
- **Já implementado**: `query_get_service.py` já possui `_forbidden_sql_patterns` que bloqueia INSERT, UPDATE, DELETE, DROP, etc.
- **Status**: ✅ Funcional (validação de segurança já existente)

### 8. Utilitários Criados
- **Idempotência**: `app/utils/idempotency.py`
  - `gerar_run_id()`: Gera run_id único
  - `gerar_correlation_id()`: Gera correlation_id para rastreabilidade
  - `verificar_idempotency_key()`: Valida idempotency keys
  - `registrar_idempotency_key()`: Registra resposta para idempotência
- **Sanitização de Logs**: `app/utils/log_sanitizer.py`
  - `sanitizar_log()`: Remove secrets de strings
  - `sanitizar_dict()`: Remove campos sensíveis de dicts

## ✅ Correções Adicionais Implementadas

### 9. Rate Limit por Usuário Ativado
- **Arquivo**: `app/utils/rate_limit.py`
- **Mudança**: Padrão alterado de `0` (desativado) para `100` req/min por usuário
- **Status**: ✅ Ativo por padrão (configurável via `RATE_LIMIT_PER_USER_PER_MINUTE`)

### 10. Agendamentos em BD (Estrutura Mínima)
- **Criado**: `app/storage/database/ID_database/database_agendamentos.py`
- **Funcionalidade**: Migração para MongoDB com fallback para arquivo JSON
- **Aplicado em**: `agendamento_retreino_service.py` (tenta BD primeiro, fallback arquivo)

### 11. Allowlist de Comandos Venv
- **Criado**: `app/utils/venv_allowlist.py`
- **Funcionalidade**: Whitelist de comandos permitidos + blacklist de padrões perigosos
- **Aplicado em**: `venv_utils.py` no método `run_cmd()` com validação automática

### 12. Sanitização de Logs Aplicada
- **Arquivo**: `app/utils/log_manager.py`
- **Mudança**: `add_log()` agora sanitiza mensagens automaticamente usando `sanitizar_log()`
- **Benefício**: Secrets removidos de todos os logs automaticamente

### 13. Idempotência e Correlation ID em Pipelines
- **Arquivo**: `app/models/pipeline_models/pipeline_models.py`
- **Mudanças**:
  - Adicionado `idempotency_key` e `correlation_id` nos Requests
  - Adicionado `run_id` e `correlation_id` nos Responses
- **Aplicado em**: `pipeline_router.py` no endpoint `/teste-automatizado` (exemplo)

### 14. Paginação Consistente
- **Criado**: `app/utils/pagination.py`
- **Funcionalidade**: Constantes globais para limites (DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MAX_QUERY_ROWS, MAX_SAMPLE_ROWS)
- **Configurável via env**: `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`, `MAX_QUERY_ROWS`, `MAX_SAMPLE_ROWS`

### 15. Webhook Stripe Idempotência
- **Arquivo**: `app/services/subscription/subscription_service.py`
- **Mudança**: `handle_stripe_webhook()` agora aceita `event_id` e verifica se já foi processado
- **Aplicado em**: `router_subscription.py` e `main.py` (passa `event.id` do Stripe)

### 16. Autenticação em Todas as Rotas Sensíveis
- **Aplicado em**:
  - `/comprehension/run` ✅
  - `/pipeline/*` ✅ (exemplo: `/teste-automatizado`)
  - `/deploy/docker/*` ✅ (start, rebuild, stop, logs, clear)
  - `/venv/*` ✅ (create, recreate, execute, deactivate, logs, clear)
  - `/test/run` ✅
  - `/workflow/correct/run` ✅

## ✅ Correções Adicionais (Rodada 12/02/2025 – Produção)

### 17. Headers de Segurança (Middleware)
- **Arquivo**: `app/main.py`
- **Headers**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
- **Status**: ✅ Implementado

### 18. Sanitização de Exceções em Produção
- **Arquivos**: `main.py` (health/ready), `agendamento_retreino_service`, `code_creator_service`, `structure_creator_service`, `finops_services`, `router_subscription` (webhook Stripe)
- **Mudança**: Em produção, não expor `str(e)`; usar mensagens genéricas
- **Status**: ✅ Implementado

### 19. Lock em Agendamentos JSON (FileLock)
- **Arquivo**: `app/storage/id_artifacts/id_artifacts_io.py`
- **Mudança**: `load_agendamentos`, `save_agendamento`, `pop_agendamento_por_id` usam `FileLock` para evitar race conditions
- **Status**: ✅ Implementado

### 20. Cache get_user_by_email (60s)
- **Arquivo**: `app/storage/database/login/database_login.py`
- **Mudança**: Cache em memória com TTL configurável via `USER_CACHE_TTL_SEC`
- **Status**: ✅ Implementado

### 21. Allowlist em Produção
- **Arquivo**: `app/utils/db_config_validation.py`, `path_validation.py`
- **Mudança**: `ALLOWED_DB_HOSTS`, `ALLOWED_DB_DATABASES`, `ALLOWED_ROOT_BASE` exigidos em prod
- **Status**: ✅ Implementado

---

## ⚠️ Pendências (Requerem Implementação Adicional)

### 1. Rate Limit Aplicado em Todas as Rotas Sensíveis
- **Status**: Rate limit ativado por padrão (100 req/min), mas precisa ser aplicado explicitamente em todas as rotas
- **Ação**: Adicionar `check_rate_limit_user()` em rotas ID que ainda não têm (algumas já têm)

### 2. Idempotência Completa em Pipelines
- **Status**: Modelos atualizados e exemplo aplicado em `/teste-automatizado`
- **Ação**: Aplicar idempotência nos demais endpoints de pipeline (`/analise-retorno`, `/correcao-erros`, etc.)

### 3. Correlation ID em Todos os Responses
- **Status**: Utilitário criado e exemplo aplicado
- **Ação**: Adicionar `correlation_id` em todos os responses de workflows e pipelines

### 4. Paginação Aplicada
- **Status**: Utilitário criado com constantes globais
- **Ação**: Aplicar `validar_pagina()` e `validar_limite_query()` nos endpoints que retornam listas grandes

## 📝 Notas de Implementação

- **Cache em memória**: Utilitários de idempotência e lock usam cache em memória. Para produção com múltiplas instâncias, migrar para Redis.
- **Allowlist em prod**: `ALLOWED_DB_HOSTS`, `ALLOWED_DB_DATABASES` e `ALLOWED_ROOT_BASE` são obrigatórios em ambiente de produção.
- **Lock timeout**: Lock de retreino tem timeout de 60 segundos por padrão; FileLock em agendamentos tem timeout de 10s.
