# Análise Geral Atualizada – PulsoAPI (app/)

**Data:** 12 de fevereiro de 2025  
**Escopo:** pasta `api/app/` — inventário completo, funcionalidades, aplicação empresarial e individual, lacunas para uso empresarial avançado.

---

## 1. Visão Executiva

A **PulsoAPI** (PulsoCSA API) é uma plataforma de **IA aplicada** que integra múltiplos módulos em uma única API FastAPI:

- **Governança e Refino de Requisitos** (Camada 1)
- **Análise e Arquitetura** (Camada 2: Backend, Infraestrutura, Segurança)
- **Execução e Geração de Código** (Camada 3)
- **Inteligência de Dados** (ID): consultas NL, ETL, estatística, ML, previsão
- **FinOps**: análise multi-cloud (AWS, Azure, GCP) com custos, performance e segurança
- **Infraestrutura as Code**: Terraform para AWS, Azure, GCP
- **Pipeline de Qualidade**: testes automatizados, análise de retorno, correção de erros, segurança pós-correção

**Versão:** 1.0.0  
**Stack:** FastAPI, Python, MongoDB, LangChain, OpenAI, FAISS, PyCaret, Stripe, boto3, azure-mgmt-*, google-cloud-*.

---

## 2. Arquitetura Modular

### 2.1 Estrutura de Diretórios (app/)

| Camada | Diretório | Responsabilidade |
|--------|-----------|------------------|
| **Core** | `core/` | Conexões (MySQL, PostgreSQL, Oracle, SQL Server, SQLite, MongoDB, OpenAI), auth, config Pulso |
| **Models** | `models/` | DTOs Pydantic por domínio (ID, login, profile, subscription, finops, pipeline, etc.) |
| **Services** | `services/` | Lógica de negócio: agents, comprehension, finops, ID, pipeline, login, profile, subscription, deploy, infra |
| **Routers** | `routers/` | Endpoints FastAPI por área funcional |
| **Agents** | `agents/` | Agentes LLM: governance, architecture, execution, ID, finops |
| **Storage** | `storage/` | Persistência: MongoDB (login, profiles, subscriptions), id_artifacts (Parquet, modelos), vectorstore (FAISS) |
| **Utils** | `utils/` | rate_limit, path_validation, log_manager, db_config_validation, venv, pagination |
| **Prompts** | `prompts/` | Templates por domínio (analyse, correct, creation, ID_prompts, finops, infra) |
| **Workflow** | `workflow/` | Orquestradores: correct_workflow, creator_workflow |
| **Datasets** | `datasets/` | PDFs e CSVs para RAG (governança, segurança, arquitetura, compliance) |

### 2.2 Fluxo de Entrada Principal

```
POST /comprehension/run
    │
    ▼
detect_module(prompt) → codigo | infraestrutura | inteligencia-dados
    │
    ├── codigo       → governance/run ou workflow/correct/run
    ├── infraestrutura → /infra/* (análise, geração, validação, deploy)
    └── inteligencia-dados → /inteligencia-dados/chat

POST /finops/chat (entrada direta, sem passar pelo comprehension global)
```

---

## 3. Funcionalidades Detalhadas

### 3.1 Autenticação e Usuários

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Login Google OAuth | `GET /auth/login/google` | Início do fluxo OAuth |
| Callback OAuth | `GET /auth/login/google/callback` | Troca código por token |
| Signup | `POST /auth/signup` | Registro de novo usuário |
| Login email/senha | `POST /auth/login` | Autenticação por credenciais |
| Logout | `POST /auth/logout` | Invalida sessão |
| Refresh token | `POST /auth/refresh` | Renova access token |
| Recuperação de senha | `POST /auth/request-password-reset`, `POST /auth/reset-password` | Fluxo de recuperação |
| Me | `GET /auth/me` | Dados do usuário autenticado |
| Profiles (auth) | `POST/GET /auth/profiles`, `GET/PUT/DELETE /auth/profiles/{id}` | CRUD de perfis na área auth |

**Tecnologias:** JWT, bcrypt, OAuth 2.0 (Google).

### 3.2 Perfis e Colaboração

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Listar perfis | `GET /profiles` | Perfis do usuário |
| Criar perfil | `POST /profiles` | Novo perfil/workspace |
| Editar/Excluir | `PUT /DELETE /profiles/{id}` | Gestão de perfil |
| Convidar membro | `POST /profiles/{id}/invite` | Enviar convite |
| Aceitar convite | `POST /profiles/{id}/accept-invite` | Aceitar e associar |
| Listar membros | `GET /profiles/{id}/members` | Membros do perfil |

**Modelo:** Um usuário pode ter múltiplos perfis; perfis podem ter membros (colaboração).

### 3.3 Assinaturas e Monetização

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Estado da assinatura | `GET /subscription` | Plano e status |
| Faturas | `GET /subscription/invoices` | Histórico de pagamentos |
| Cancelar | `POST /subscription/cancel` | Cancela plano |
| Reativar | `POST /subscription/resume` | Reativa assinatura cancelada |
| Alterar plano | `POST /subscription/change-plan` | Upgrade/downgrade |
| Portal Stripe | `GET /subscription/portal` | URL do portal do cliente |
| Webhook Stripe | `POST /`, `POST /subscription/webhook` | Eventos Stripe (checkout, cancelamento) |

**Integração:** Stripe para pagamentos, webhooks com idempotência por event_id.

### 3.4 Camada 1 – Governança

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Input | `POST /governance/input`, `POST /input` | Recebe prompt, gera id_requisicao |
| Refinar | `POST /governance/refine`, `POST /refinar` | Refino com RAG (FAISS + LangChain) |
| Validar | `POST /governance/validate`, `POST /validar` | Valida e gera documento de requisitos |
| Run completo | `POST /governance/run` | input → refine → validate + blueprint |

**Compliance:** RAG treinado com ISO 27001, LGPD, COBIT, ITIL, DevSecOps. Base de conhecimento em `datasets/pdf/` e `datasets/csv/`.

### 3.5 Camada 2 – Análise (Backend e Infra)

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Análise estrutura | `POST /backend/analise-estrutura`, `POST /analise-estrutura` | Árvore e componentes do projeto |
| Análise backend | `POST /backend/analise-backend`, `POST /analise-backend` | APIs, padrões de código |
| Segurança código | `POST /backend/seguranca-codigo`, `POST /seguranca-codigo` | Vulnerabilidades e boas práticas |
| Análise infra | `POST /infra/analise-infra`, `POST /analise-infra` | Deploy, serviços, redes |
| Segurança infra | `POST /infra/seguranca-infra`, `POST /seguranca-infra` | Checklist de segurança |

### 3.6 Camada 3 – Execução

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Criar estrutura | `POST /execution/execution/create-structure`, `POST /criar-estrutura` | Estrutura de pastas/arquivos |
| Criar código | `POST /execution/execution/create-code`, `POST /criar-codigo` | Geração de código |

### 3.7 Code Generation Stack (C2b, C3, C4)

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Code Plan | `POST /code-plan/run` | Plano de correção (o que mudar, em que ordem) |
| Code Writer | `POST /code-writer/run` | Gera trechos de código |
| Code Implementer | `POST /code-implementer/run` | Aplica implementação final no projeto |

### 3.8 Workflows de Correção

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Correct workflow | `POST /workflow/correct/run` | Análise + correção guiada |
| Full auto | `POST /workflow/correct/full-run` | Fluxo completo automatizado |

### 3.9 Inteligência de Dados (ID)

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Query NL | `POST /inteligencia-dados/query` | Pergunta em linguagem natural → SQL → execução |
| Captura | `POST /inteligencia-dados/captura-dados` | Conecta MySQL/Mongo/Postgres/Oracle/SQLite/SQL Server; extrai schema, amostra Parquet |
| Análise inicial | `POST /inteligencia-dados/analise-dados-inicial` | Sugere variável alvo e tratamentos (LLM) |
| Tratamento/limpeza | `POST /inteligencia-dados/tratamento-limpeza` | ETL: duplicatas, missing, outliers (IQR) |
| Análise estatística | `POST /inteligencia-dados/analise-estatistica` | Média, mediana, correlações, insights (LLM) |
| Criar modelo ML | `POST /inteligencia-dados/criar-modelo-ml` | PyCaret compare_models; limiar 70%; salva modelo |
| Listar modelos | `GET /inteligencia-dados/listar-modelos` | model_ref por id_requisicao |
| Prever | `POST /inteligencia-dados/prever` | Previsão em lote ou tempo real |
| Chat ID | `POST /inteligencia-dados/chat` | Orquestrador: interpreta mensagem, executa pipeline (captura→tratamento→estatística→treino→previsão) |
| Agendar retreino | `POST /inteligencia-dados/agendar-retreino` | Cron ou próxima execução |
| Executar retreino | `POST /inteligencia-dados/executar-retreino-agendado` | Roda retreino |
| Agendamentos pendentes | `GET /inteligencia-dados/agendamentos-pendentes` | Lista fila |

**Bancos suportados:** MySQL, PostgreSQL, Oracle, SQL Server, SQLite, MongoDB.

### 3.10 FinOps – Análise Multi-Cloud

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Chat FinOps | `POST /finops/chat` | Mensagem em linguagem natural; comprehension interno; extrai cloud, quick_win_mode etc. |
| Analyze | `POST /finops/analyze` | Payload estruturado; análise custos, performance, segurança |

**Providers:** AWS (boto3), Azure (azure-mgmt-*, azure-identity), GCP (google-cloud-billing, compute, storage).

**Pipeline FinOps:** conectores → billing + inventory + metrics → heurísticas (rightsizing, storage, commitments, políticas desligamento) → LLM → narrativa em texto natural.

**Heurísticas:** custo total, instâncias paradas, t2/t3 → graviton, S3 lifecycle, CPU baixo para downsizing, guardrails (budgets, alertas).

### 3.11 Infraestrutura as Code (Terraform)

| Funcionalidade | Área | Descrição |
|----------------|------|-----------|
| Módulos Terraform | `terraform/modules/` | AWS, Azure, GCP: compute, container, IAM, networking, observability, storage |
| Infra router | `POST /infra/*` | Análise, geração, validação, deploy |
| Serviços | `services/infra/` | cost_guardrails, deploy_token, golden_module_selector, infra_spec_builder, policy_runner, provider_diff, repo_scanner, terraform_runner, terraform_stack_generator |

### 3.12 Pipeline de Qualidade (11–13.2)

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Teste automatizado | `POST /pipeline/teste-automatizado` | Roda testes (venv ou Docker) |
| Análise retorno | `POST /pipeline/analise-retorno` | Interpreta falhas, vulnerabilidades (LLM) |
| Correção erros | `POST /pipeline/correcao-erros` | Aplica correções via workflow |
| Segurança código pós | `POST /pipeline/seguranca-codigo-pos` | Revalida segurança após correção |
| Segurança infra pós | `POST /pipeline/seguranca-infra-pos` | Revalida infra após correção |

### 3.13 Deploy e Ambiente

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Docker start | `POST /deploy/docker/start` | Inicia container |
| Docker rebuild | `POST /deploy/docker/rebuild` | Rebuild e sobe |
| Docker stop | `POST /deploy/docker/stop` | Para container |
| Logs | `GET /deploy/docker/logs` | Logs do deploy |
| Limpar logs | `DELETE /deploy/docker/logs/clear` | Limpa buffer |

### 3.14 Venv e Testes

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Venv create | `POST /venv/create` | Cria ambiente virtual |
| Venv recreate | `POST /venv/recreate` | Recria venv |
| Venv execute | `POST /venv/execute` | Executa comando no venv |
| Venv deactivate | `POST /venv/deactivate` | Desativa |
| Test run | `POST /test/run` | Executa suite de testes (Venv + Docker) |

### 3.15 Tela de Teste

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Análise tela | `POST /analise-tela-teste` | Analisa requisitos para tela de teste (LLM) |
| Criar tela | `POST /criar-tela-teste` | Gera artefato de tela de teste |

### 3.16 Análise Estrutural

| Funcionalidade | Endpoint | Descrição |
|----------------|----------|-----------|
| Struc-anal plan | `POST /struc-anal/plan` | Plano de análise estrutural do projeto |

---

## 4. Aplicação Empresarial

### 4.1 O que a Pulso oferece hoje para empresas

| Área | Oferta | Benefício |
|-----|--------|-----------|
| **Governança** | Refino de requisitos com compliance (ISO, LGPD, COBIT) | Documentos técnicos alinhados a normas |
| **Desenvolvimento** | Criação e correção de código assistida por IA | Aceleração de desenvolvimento |
| **Infraestrutura** | Terraform multi-cloud (AWS, Azure, GCP) | Provisionamento padronizado |
| **FinOps** | Análise de custos, performance e segurança cloud | Redução de custos e otimização |
| **Dados** | Pipeline completo: captura → ETL → estatística → ML → previsão | Democratização de dados e IA |
| **Qualidade** | Pipeline teste → análise → correção → segurança | Redução de bugs e vulnerabilidades |
| **Monetização** | Assinaturas Stripe, perfis, convites | Modelo SaaS pronto |

### 4.2 Multi-tenancy e Perfis

- **Perfis:** workspace por usuário; convites para membros.
- **Artefatos ID:** isolados por `usuario` + `id_requisicao` (paths em `id_artifacts`).
- **Assinaturas:** por usuário (userId → planId, status, billing).

### 4.3 Segurança Implementada

| Aspecto | Status |
|---------|--------|
| Rate limit por IP | Implementado (default 120/min) |
| Tamanho do body | Limitado (default 1 MB) |
| Exceções em produção | Ocultas (não expõe stack) |
| Request ID | Rastreio para logs |
| Path traversal | Validado (`path_validation`) |
| CORS | Configurável por env (nunca `*` em produção) |
| Chaves de API | Nunca logadas |
| Webhook Stripe | Assinatura verificada |
| ID artefatos | Sanitização de paths |
| Auth em FinOps | `Depends(auth_and_rate_limit)` obrigatório |

---

## 5. Aplicação Individual (Usuário Final)

| Funcionalidade | Caso de uso |
|----------------|-------------|
| **Comprehension** | Usuário descreve em linguagem natural o que quer; sistema roteia para código, infra ou dados |
| **Chat ID** | "Analise meu banco X e treine modelo de churn" → pipeline automático |
| **Chat FinOps** | "Analise custos da minha AWS e mostre quick wins" → análise + narrativa |
| **Query NL** | "Quantos clientes inativos no último mês?" → SQL gerado e executado |
| **Governança** | "Criar API Flask com JWT" → documento refinado e validado |
| **Correção** | "Corrija o projeto em /path" → workflow de correção |
| **Perfis** | Organizar projetos em workspaces |
| **Assinatura** | Escolher plano e pagar via Stripe |

---

## 6. Lacunas para Uso Empresarial Avançado

### 6.1 Autenticação e Autorização

| Gap | Situação | Recomendação |
|-----|----------|---------------|
| Auth obrigatória | Rotas ID, comprehension, pipeline, deploy, venv não exigem token por padrão | Aplicar `Depends(verificar_token)` ou `auth_and_rate_limit` em todas as rotas sensíveis |
| RBAC | Não há papéis (admin, editor, viewer) por perfil | Definir roles e checar permissão por recurso |
| Feature gating | Assinatura existe, mas bloqueio por plano não está claro | Mapear features por plano; validar entitlement antes de executar |
| SSO empresarial | Apenas Google OAuth | SAML/OIDC para Okta, Azure AD, etc. |

### 6.2 Multi-tenancy e Escalabilidade

| Gap | Situação | Recomendação |
|-----|----------|---------------|
| Agendamentos | Arquivo único (`agendamentos_retreino.json`); sem isolamento por tenant | Persistir em BD com tenant_id; ou fila (Redis/Celery) por tenant |
| Cache de intent | Global, sem isolamento por usuário | Incluir usuario na chave; ou migrar para Redis com TTL |
| Rate limit por usuário | `RATE_LIMIT_PER_USER_PER_MINUTE=0` por padrão | Ativar e aplicar em rotas sensíveis |
| Quotas por plano | Não há limites por tier (requests, tokens, jobs) | Definir quotas; rejeitar ou enfileirar quando exceder |

### 6.3 Observabilidade e Operação

| Gap | Situação | Recomendação |
|-----|----------|---------------|
| Métricas | Sem Prometheus/StatsD (latência, erros, tokens) | Expor métricas por rota; alertas e dashboards |
| Tracing | Apenas request_id por request | Correlation_id por execução de pipeline/workflow |
| Idempotência | Fraca em pipelines/workflows | run_id por execução; idempotency key no header |
| Auditoria | Logs operacionais podem vazar segredos | Sanitizar logs (remover env, tokens) |

### 6.4 Dados e Conectores

| Gap | Situação | Recomendação |
|-----|----------|---------------|
| NL→SQL | Query livre; risco de DELETE/DDL | Read-only na conexão; allowlist de comandos; validar SQL gerado |
| db_config | Aceito livremente pelo cliente | Allowlist de hosts; conexões pré-configuradas por tenant |
| Credenciais cloud (FinOps) | Enviadas no payload | Vault ou secrets manager; credenciais por tenant |

### 6.5 Produto e UX

| Gap | Situação | Recomendação |
|-----|----------|---------------|
| Limiar 70% ML | Fixo; pode bloquear casos válidos | Configurável por request ou plano |
| Duplicidade /auth/profiles e /profiles | Duas superfícies de perfis | Unificar ou documentar papel de cada um |
| Contratos entre etapas | Sem schemas rígidos entre etapas do pipeline | OpenAPI/JSON Schema por payload; versionar |

### 6.6 Endpoints de Alto Poder

| Gap | Situação | Recomendação |
|-----|----------|---------------|
| Deploy/Docker, Venv execute, Test run | Podem virar "terminal remoto" | Auth + autorização (só admin); allowlist de comandos no venv |
| Logs | Podem expor tokens, paths | Sanitizar antes de retornar |

---

## 7. Base de Conhecimento (RAG)

### 7.1 Datasets

| Categoria | Conteúdo |
|-----------|----------|
| **Governança** | COBIT5, ISO27001, prompt engineering |
| **Arquitetura** | 12FactorApp, OWASP, NIST, DevOps Handbook, Well-Architected |
| **Desenvolvimento** | Clean Architecture, Clean Code, Design Patterns, Pragmatic Programmer |
| **Segurança** | Ethical Hacking, Bug Bounty, Digital Forensics, Web Application Security |
| **Compliance** | compliance_risks.csv, governance_metrics.csv, strategic_alignment.csv |
| **Treinamento** | prompt_refino_examples.csv, refinement_pairs.jsonl |

### 7.2 Vectorstore

- **FAISS** em `storage/vectorstore/faiss_governance`
- Treinamento automático a partir de `datasets/pdf/` e `datasets/csv/`
- Uso em refino de prompts (governança)

---

## 8. Dependências Principais

| Categoria | Pacotes |
|-----------|---------|
| **Framework** | FastAPI, uvicorn, Starlette |
| **IA/LLM** | openai, langchain, langchain-openai, langchain-community |
| **Bancos** | pymongo, SQLAlchemy, PyPika |
| **ML** | pycaret, scikit-learn, pandas, numpy, pyarrow |
| **Cloud** | boto3, azure-identity, azure-mgmt-*, google-cloud-* |
| **Pagamentos** | stripe (implícito) |
| **Vectorstore** | faiss-cpu, chromadb |
| **Infra** | GitPython, PyYAML, httpx |

---

## 9. Resumo Executivo

| Aspecto | Status |
|---------|--------|
| **Módulos funcionais** | Governança, Backend, Infra, ID, FinOps, Pipeline, Deploy, Venv, Test |
| **Integrações** | OpenAI, Stripe, MongoDB, MySQL/Postgres/Oracle/SQLite/SQL Server, AWS/Azure/GCP |
| **Multi-usuário** | Perfis, convites, assinaturas; artefatos ID por usuario+id_requisicao |
| **Segurança** | Rate limit, body limit, CORS, path validation, webhook Stripe; auth parcial |
| **Uso empresarial** | Pronto para MVP/SaaS; falta RBAC, SSO, quotas, observabilidade, isolamento de agendamentos |
| **Uso individual** | Chat único (comprehension), ID, FinOps; fluxos completos end-to-end |

---

*Documento gerado em 12/02/2025.*
