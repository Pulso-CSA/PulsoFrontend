# Análise Geral – PulsoAPI

**Data:** 12 de fevereiro de 2025  
**Escopo:** Inventário completo das capacidades da PulsoAPI – API modular de IA para governança, desenvolvimento, infraestrutura e inteligência de dados.

---

## 1. Visão Geral

A **PulsoAPI** (PulsoCSA API) é uma API modular de Inteligência Artificial que integra:

- **Governança de requisitos** com RAG e compliance (LGPD, ISO 27001, COBIT, ITIL)
- **Análise e geração de código** (estrutura, backend, infraestrutura)
- **Workflows de criação** (projetos novos) e **correção** (projetos existentes)
- **Inteligência de Dados (ID)**: consultas em linguagem natural, ML, previsões, chat
- **Infraestrutura como código** (Terraform – AWS, Azure, GCP)
- **Deploy**, testes automatizados e pipeline de qualidade

**Versão:** 1.0.0  
**Stack:** FastAPI, OpenAI, MongoDB, LangChain, FAISS, PyCaret, Terraform

---

## 2. Arquitetura

```
app/
├── core/           # Conexões (OpenAI, Mongo, MySQL, ID, storage)
├── models/         # DTOs Pydantic por domínio
├── services/       # Regras de negócio
├── routers/       # Endpoints FastAPI
├── agents/        # Agentes LLM (governance, architecture, execution, ID, infra)
├── workflow/      # Orquestração (creator, correct)
├── storage/       # MongoDB, vectorstore, id_artifacts
├── prompts/       # Prompts por domínio
└── utils/         # rate_limit, path_validation, log_manager, etc.
```

---

## 3. Sistema de Compreensão (Entrada Principal)

**Rota:** `POST /comprehension/run`

- **Classificação de intenção** (LLM): `ANALISAR` vs `EXECUTAR`
- **Estado do projeto:** `ROOT_VAZIA` (novo) ou `ROOT_COM_CONTEUDO` (existente)
- **Roteamento dinâmico:**
  - Projeto vazio + EXECUTAR → workflow de **criação** (`governance/run`)
  - Projeto com conteúdo + EXECUTAR → workflow de **correção** (`workflow/correct/run`)
  - ANALISAR → análise sem executar (recomendações, diagnóstico)
- **Cache de intent** por usuário (TTL configurável)
- **Resposta humanizada:** `message`, `intent_confidence`, `intent_warning`, `processing_time_ms`, `file_tree`, `frontend_suggestion`

**Contrato:** `GET /comprehension/contract` – JSON de request/response para o frontend

---

## 4. Camada 1 – Governança

**Objetivo:** Refinar, validar e documentar requisitos com RAG e compliance.

| Rota | Descrição |
|------|-----------|
| `POST /governance/input` | Recebe prompt, gera `id_requisicao`, persiste no MongoDB |
| `POST /governance/refine` | Refina prompt com RAG (LangChain + FAISS + documentos normativos) |
| `POST /governance/validate` | Valida prompt, gera documento técnico de requisitos |
| `POST /governance/run` | Workflow completo: input → refine → validate |

**RAG:** PDFs de ISO 27001, LGPD, COBIT, ITIL em `app/datasets/`; índice FAISS em `faiss_governance`.

---

## 5. Camada 2 – Análise (Backend e Infra)

### 5.1 Backend

| Rota | Descrição |
|------|-----------|
| `POST /backend/analise-estrutura` | Analisa estrutura do projeto (árvore, componentes) |
| `POST /backend/analise-backend` | Analisa APIs, padrões, código |
| `POST /backend/seguranca-codigo` | Analisa vulnerabilidades e boas práticas |

### 5.2 Infraestrutura

| Rota | Descrição |
|------|-----------|
| `POST /infra/analise-infra` | Analisa infraestrutura (deploy, serviços, redes) |
| `POST /infra/seguranca-infra` | Analisa segurança da infraestrutura |

---

## 6. Camada 3 – Execução (Criação)

| Rota | Descrição |
|------|-----------|
| `POST /execution/execution/create-structure` | Cria estrutura de pastas/arquivos a partir do manifesto |
| `POST /execution/execution/create-code` | Gera código a partir dos relatórios de análise |

**Workflow de criação completo** (`run_workflow_pipeline`): Camada 1 → Camada 2 → create-structure → create-code

---

## 7. Stack de Correção (C2b → C3 → C4)

| Componente | Rota | Descrição |
|------------|------|-----------|
| **Code Plan (C2b)** | `POST /code-plan/run` | Gera plano de correção (o que mudar, em que ordem) |
| **Code Writer (C3)** | `POST /code-writer/run` | Gera código/trechos a partir do plano |
| **Code Implementer (C4)** | `POST /code-implementer/run` | Aplica implementação final no projeto |

---

## 8. Workflow de Correção Completo

**Rota:** `POST /workflow/correct/run`

**Fluxo:**
1. **C1 – Governança** (input, refine, validate)
2. **C2 – Análise estrutural** (scan do projeto, change plan)
3. **C2b – Code Plan** (plano de mudanças)
4. **C2 – Aplicação estrutural** (criar pastas/arquivos)
5. **C3 – Code Writer** (stubs e integração)
6. **C4 – Code Implementer** (implementação real)
7. **C5 – Teste automatizado** (venv ou Docker)
8. **Pipeline 11–13.2** (se habilitado): análise de retorno → correção de erros → segurança código → segurança infra

**Modo `only_c4_c5`:** Pula C1–C3 e executa só C4 + C5 (retry barato a partir do code plan existente).

---

## 9. Full Auto Workflow

**Rota:** `POST /workflow/correct/full-run`

Executa em uma chamada: **Code Plan** → **Code Writer** (sem Code Implementer). Útil para geração rápida de código assistido.

---

## 10. Pipeline de Qualidade (11 → 13.2)

| Etapa | Rota | Descrição |
|-------|------|-----------|
| **11** | `POST /pipeline/teste-automatizado` | Roda testes (venv ou Docker); retorna relatório |
| **12** | `POST /pipeline/analise-retorno` | Analisa resultado dos testes (LLM); extrai objetivo_final, falhas, vulnerabilidades |
| **13** | `POST /pipeline/correcao-erros` | Aplica correções com base na análise; chama workflow de correção |
| **13.1** | `POST /pipeline/seguranca-codigo-pos` | Revalida segurança do código após correções |
| **13.2** | `POST /pipeline/seguranca-infra-pos` | Revalida segurança da infra após correções |

**Idempotência:** Suporte a `idempotency_key` em `teste-automatizado`.

---

## 11. Aliases da Spec (Rotas na Raiz)

Permitem chamar pelo nome da documentação sem prefixo:

| Rota | Equivalente |
|------|-------------|
| `POST /input` | `/governance/input` |
| `POST /refinar` | `/governance/refine` |
| `POST /validar` | `/governance/validate` |
| `POST /analise-estrutura` | backend |
| `POST /analise-backend` | backend |
| `POST /analise-infra` | infra |
| `POST /seguranca-infra` | infra |
| `POST /seguranca-codigo` | backend |
| `POST /criar-estrutura` | execution |
| `POST /criar-codigo` | execution |

---

## 12. Inteligência de Dados (ID)

**Prefixo:** `/inteligencia-dados`

### 12.1 Captura e Estrutura

| Rota | Descrição |
|------|-----------|
| `POST /query` | Pergunta em linguagem natural + `db_config` → gera SQL e executa (read-only) |
| `POST /captura-dados` | Conecta MySQL/MongoDB; extrai tabelas/coleções; amostra em Parquet; retorna `dataset_ref` |
| `POST /analise-dados-inicial` | Interpreta objetivo; sugere variáveis alvo e tratamentos (LLM) |

### 12.2 Tratamento e Estatística

| Rota | Descrição |
|------|-----------|
| `POST /tratamento-limpeza` | ETL: duplicatas, missing, outliers (IQR); persiste em Parquet; retorna `dataset_pronto` |
| `POST /analise-estatistica` | Métricas, correlações, resposta à pergunta, insights (LLM) |

### 12.3 ML e Previsão

| Rota | Descrição |
|------|-----------|
| `POST /criar-modelo-ml` | Treina com PyCaret (compare_models); limiar 70%; salva modelo; retorna `model_ref` |
| `GET /listar-modelos` | Lista `model_ref` por `id_requisicao` (múltiplas versões). |
| `POST /prever` | Aplica modelo a `dataset_ref` ou dados em tempo real; valida schema |

### 12.4 Chat e Agendamento

| Rota | Descrição |
|------|-----------|
| `POST /chat` | Orquestrador: mensagem em linguagem natural → captura, tratamento, estatística, treino e/ou previsão conforme intenção |
| `POST /agendar-retreino` | Registra agendamento de retreino (dataset_ref, variável_alvo, cron) |
| `POST /executar-retreino-agendado` | Executa retreino agendado |
| `GET /agendamentos-pendentes` | Lista agendamentos de retreino pendentes |

**Artefatos:** Isolados por `usuario` + `id_requisicao`; Parquet para datasets; cache de interpretação por usuário.

---

## 13. Infraestrutura (Terraform)

**Prefixo:** `/infra`

| Rota | Descrição |
|------|-----------|
| `POST /infra/analyze` | Escaneia repo; gera `infra_spec_draft`; custo estimado; provider_diff; next_actions |
| `POST /infra/generate` | Gera artefatos Terraform a partir de InfraSpec ou user_request |
| `POST /infra/validate` | Valida (fmt, validate, plan + policy); retorna `deploy_token` e `confirm_phrase` |
| `POST /infra/deploy` | `terraform apply`; exige `confirm=true`, `deploy_token`, `confirm_phrase` |

**Módulos Terraform:** AWS, Azure, GCP – compute, container, networking, storage, IAM, observability.

---

## 14. Tela de Teste (FrontendEX)

| Rota | Descrição |
|------|-----------|
| `POST /analise-tela-teste` | Analisa requisitos para tela de teste QA; retorna layout, funcionalidades, testes_cruciais, dados_ficticios |
| `POST /criar-tela-teste` | Cria pasta FrontendEX com app Streamlit modularizado; consume endpoints do backend; localhost:3000 |

---

## 15. Análise Estrutural

| Rota | Descrição |
|------|-----------|
| `POST /struc-anal/plan` | Gera plano de análise estrutural (pastas, módulos, dependências) |

---

## 16. Deploy e Docker

**Prefixo:** `/deploy/docker`

| Rota | Descrição |
|------|-----------|
| `POST /start` | Inicia containers Docker |
| `POST /rebuild` | Rebuild e sobe containers |
| `POST /stop` | Para containers |
| `GET /logs` | Retorna logs da aplicação (filtro: todos, info, warning, error) |
| `DELETE /logs/clear` | Limpa logs |

---

## 17. Venv e Testes

| Área | Rota | Descrição |
|------|------|-----------|
| **Venv** | `GET /venv/logs` | Logs do venv |
| | `DELETE /venv/logs/clear` | Limpa logs |
| | `POST /venv/create` | Cria ambiente virtual |
| | `POST /venv/recreate` | Recria venv |
| | `POST /venv/execute` | Executa comando no venv |
| | `POST /venv/deactivate` | Desativa venv |
| **Test** | `POST /test/run` | Executa testes (venv ou Docker) |

---

## 18. Autenticação e Segurança

### 18.1 Login

| Rota | Descrição |
|------|-----------|
| `GET /auth/login/google` | Redireciona para OAuth Google |
| `GET /auth/login/google/callback` | Callback OAuth; troca código por token |
| `POST /auth/signup` | Registro de usuário |
| `POST /auth/login` | Login por email/senha |
| `POST /auth/logout` | Invalida token |
| `POST /auth/refresh` | Renova access token |
| `POST /auth/request-password-reset` | Envia email de recuperação |
| `POST /auth/reset-password` | Redefine senha |
| `GET /auth/me` | Retorna usuário autenticado |

### 18.2 Perfis e Assinatura

| Área | Rotas |
|------|-------|
| **Profiles** | CRUD de perfis; convites; membros |
| **Subscription** | Estado da assinatura; faturas; cancelar; reativar; mudar plano; portal Stripe |

### 18.3 Proteção das Rotas

- **Rotas sensíveis:** `auth_and_rate_limit` (autenticação + rate limit por usuário)
- **Rate limit por IP:** 120 req/min (default); `RATE_LIMIT_REQUESTS_PER_MINUTE`
- **Rate limit por usuário:** 100 req/min (default); `RATE_LIMIT_PER_USER_PER_MINUTE`
- **Body size:** `MAX_BODY_SIZE_MB` (default 1 MB)
- **Path traversal:** `sanitize_root_path` rejeita `..` e paths fora de `ALLOWED_ROOT_BASE`

---

## 19. Webhook Stripe

`POST /` – Recebe webhooks do Stripe; valida assinatura com `STRIPE_WEBHOOK_SECRET`; delega ao handler de subscription.

---

## 20. Resumo de Capacidades

| Domínio | Capacidades |
|---------|-------------|
| **Governança** | Input, refine (RAG), validate, run; compliance LGPD/ISO/COBIT/ITIL |
| **Análise** | Estrutura, backend, infra, segurança código/infra |
| **Criação** | Estrutura de pastas; geração de código a partir de relatórios |
| **Correção** | Code Plan → Code Writer → Code Implementer; workflow completo C1–C5 |
| **Pipeline** | Teste → Análise retorno → Correção → Segurança código/infra |
| **ID** | Query NL, captura, tratamento, estatística, ML, previsão, chat, retreino |
| **Infra** | Analyze → Generate → Validate → Deploy (Terraform) |
| **Tela teste** | Análise e criação de tela Streamlit (FrontendEX) |
| **Deploy** | Docker start/stop/rebuild; logs |
| **Auth** | Login Google, local; JWT; perfis; assinatura Stripe |

---

## 21. Mapa de Rotas por Prefixo

| Prefixo | Área |
|---------|------|
| `/` | Root, webhook Stripe |
| `/auth` | Login, perfis, password reset |
| `/profiles` | CRUD perfis |
| `/subscription` | Assinatura Stripe |
| `/comprehension` | Entrada do workflow |
| `/governance` | Camada 1 |
| `/backend` | Análise backend |
| `/infra` | Análise infra + Terraform |
| `/execution` | Criação estrutura/código |
| `/code-plan`, `/code-writer`, `/code-implementer` | Stack de correção |
| `/workflow/correct` | Workflow correção |
| `/pipeline` | Pipeline 11–13.2 |
| `/inteligencia-dados` | ID |
| `/deploy/docker` | Deploy Docker |
| `/venv` | Gerenciamento venv |
| `/test` | Execução de testes |
| `/struc-anal` | Análise estrutural |
| `/analise-tela-teste`, `/criar-tela-teste` | Tela teste |
| `/input`, `/refinar`, `/validar`, etc. | Aliases da spec |

---

*Documento gerado com base na análise do código-fonte da PulsoAPI em 12/02/2025.*
