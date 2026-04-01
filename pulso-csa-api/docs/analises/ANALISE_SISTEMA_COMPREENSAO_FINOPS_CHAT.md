# Análise: Sistema de Compreensão para Chat FinOps Melhorado

**Data:** 12 de fevereiro de 2025  
**Objetivo:** Analisar os sistemas de compreensão existentes (código, infraestrutura, inteligência de dados) e propor como aplicar ao FinOps para um chat melhorado.

**Premissa:** O sistema de compreensão do FinOps deve ser **exclusivo** do módulo FinOps, assim como cada módulo tem seu próprio sistema de compreensão (código, infraestrutura, inteligência de dados). Não integra no comprehension global.

---

## 1. Arquitetura Atual dos Sistemas de Compreensão

### 1.1 Fluxo Unificado (POST /comprehension/run) — exclusivo dos módulos Código, Infra, ID

```
POST /comprehension/run { prompt, usuario, root_path, force_execute, force_module, history }
    │
    ▼
comprehension_orchestrator.route_to_module()
    │
    ├── detect_module(prompt) → codigo | infraestrutura | inteligencia-dados
    │   └── Heurística: INFRA_KEYWORDS, ID_KEYWORDS, CODIGO_KEYWORDS (regex)
    │   └── Fallback: LLM classifica módulo
    │   └── Cache: TTL 600s, isolado por usuário
    │
    └── Delegar ao handler do módulo:
        ├── route_decision_codigo()   → ANALISAR | EXECUTAR
        ├── route_decision_infra()    → ANALISAR_INFRA | GERAR_TERRAFORM | VALIDAR_INFRA | DEPLOY_INFRA
        └── route_decision_id()       → CHAT_ID | QUERY | CAPTURA | ESTATISTICA | CRIAR_MODELO | PREVER
```

**Nota:** FinOps NÃO faz parte deste fluxo. O FinOps tem seu próprio sistema de compreensão, rodando exclusivamente dentro do módulo FinOps.

### 1.2 Padrões por Módulo

| Módulo | Orquestrador | Classificação | Comportamento no Router |
|--------|--------------|---------------|-------------------------|
| **Código** | `comprehension_codigo` | ANALISAR vs EXECUTAR (regex + LLM) | **Executa direto**: ANALISAR → `generate_analysis_text()`; EXECUTAR → dispara governance ou correct workflow |
| **Infraestrutura** | `comprehension_infra` | 4 intents (ANALISAR, GERAR, VALIDAR, DEPLOY) | **Decisão apenas**: retorna `target_endpoint`, cliente chama o endpoint |
| **Inteligência de Dados** | `comprehension_id` | 6 sub-intents | **Decisão apenas**: retorna target, cliente chama `/inteligencia-dados/chat` |

### 1.3 Chat ID como Orquestrador Local

O módulo ID tem um **chat orquestrador** (`IDChatService`) que:

1. **Interpreta** a mensagem com LLM → extrai intents: `fazer_captura`, `fazer_tratamento`, `fazer_estatistica`, `fazer_treino`, `fazer_previsao`
2. **Executa** pipeline condicional: captura → tratamento → estatística → treino → previsão
3. **Monta** resposta em linguagem natural
4. **Retorna** `IDChatOutput` com `resposta_texto`, `etapas_executadas`, `previsoes`, etc.

O comprehension apenas **roteia** para `/inteligencia-dados/chat`; o chat faz o trabalho pesado.

### 1.4 Base Compartilhada (`comprehension_base`)

- **Cache**: `intent_cache_get/set` com namespace por módulo, TTL 300s, isolado por usuário
- **Confirmação**: `detect_execute_signal()` — verbos imperativos ou "sim", "ok", emojis
- **Decisão padronizada**: `build_module_decision()` — retorna dict com module, intent, target_endpoint, should_execute, explanation, next_action

---

## 2. Situação Atual do FinOps

### 2.1 O que existe hoje

- **Endpoint direto**: `POST /finops/analyze` — recebe `cloud`, credenciais, parâmetros, retorna `message` (texto)
- **Sem comprehension próprio**: o módulo FinOps não tem sistema de compreensão interno
- **Sem chat orquestrador**: o usuário precisa chamar o endpoint com payload estruturado; não há interpretação de linguagem natural

### 2.2 Lacunas para um "Chat Melhorado"

1. **Sem interpretação de mensagem**: não há LLM que extraia `cloud`, `quick_win_mode`, etc. a partir de texto livre
2. **Credenciais**: o chat ID recebe `db_config` no payload; FinOps precisaria de credenciais cloud — possivelmente pré-configuradas por usuário/tenant
3. **Comprehension exclusivo**: o FinOps deve ter seu próprio sistema de compreensão, no mesmo padrão que os outros módulos, mas **contido dentro do módulo FinOps** — não no comprehension global

---

## 3. Proposta: Sistema de Compreensão Exclusivo do FinOps

O sistema de compreensão do FinOps deve ser **exclusivo** do módulo FinOps. A área FinOps (chat ou UI dedicada) usa apenas seus próprios endpoints e lógica de compreensão — sem passar pelo `/comprehension/run` global.

### 3.1 Entrada: POST /finops/chat (único ponto de entrada do chat FinOps)

O frontend da área FinOps chama **diretamente** `POST /finops/chat`. Não há detecção de módulo — o usuário já está na área FinOps.

### 3.2 Comprehension Interno (dentro do módulo FinOps)

**Criar `comprehension_finops.py`** — exclusivo do pacote `app.services.finops` (ou `app.agents.finops`):

1. **Classificar intent** da mensagem (regex + LLM fallback):
   - `ANALISAR_FINOPS` — análise completa
   - `QUICK_WINS` — "mostre quick wins", "oportunidades imediatas"
   - `COMPARAR_REGIOES` — "compare custos por região"
   - `POLITICAS_DESLIGAMENTO` — "sugira políticas de desligamento"
   - `GUARDRAILS` — "recomende guardrails", "budgets e alertas"

2. **Extrair parâmetros** com LLM:
   - `cloud`: aws | azure | gcp | multi (inferir de "minha AWS", "Azure", etc.)
   - `quick_win_mode`, `guardrails_mode`, janela de datas

3. **Cache** isolado por usuário (mesmo padrão do comprehension_base)

### 3.3 FinOpsChatService (orquestrador)

**Criar `FinOpsChatService`** que:

1. Recebe `mensagem`, `usuario`, `credenciais` (ou ref)
2. Chama `comprehension_finops.classify_intent_finops()` → intent + parâmetros
3. Monta `FinOpsAnalyzeRequest`
4. Chama `run_finops_analyze(req)`
5. Retorna `FinOpsChatOutput` com `resposta_texto`, `id_requisicao`, `cloud`, `etapas_executadas`

### 3.4 Contrato do Endpoint

```json
// POST /finops/chat — Request
{
  "mensagem": "analise custos da minha AWS e me mostre quick wins",
  "usuario": "user@email.com",
  "id_requisicao": "REQ-xxx",
  "aws_credentials": { ... },
  "azure_credentials": null,
  "gcp_credentials": null
}

// Response
{
  "resposta_texto": "<texto narrativo completo>",
  "id_requisicao": "FINOP-xxx",
  "cloud": "aws",
  "etapas_executadas": ["comprehension", "preflight", "billing", "inventory", "heuristics", "llm_narrative"]
}
```

---

## 4. Arquitetura: Comprehension Exclusivo por Módulo

| Módulo | Ponto de entrada | Comprehension | Orquestrador |
|--------|------------------|---------------|--------------|
| **Código** | `/comprehension/run` | comprehension_codigo | governance, correct workflow |
| **Infraestrutura** | `/comprehension/run` | comprehension_infra | cliente chama /infra/* |
| **Inteligência de Dados** | `/comprehension/run` → `/inteligencia-dados/chat` | comprehension_id | IDChatService |
| **FinOps** | `/finops/chat` (direto) | comprehension_finops (interno) | FinOpsChatService |

O FinOps **não** passa pelo `/comprehension/run`. O usuário acessa a área FinOps e usa `/finops/chat` como entrada única.

---

## 5. Padrões a Replicar (dentro do módulo FinOps)

| Componente | Onde fica | Descrição |
|------------|-----------|-----------|
| comprehension_finops | `services/finops/` ou `agents/finops/` | classify_intent_finops, extrair parâmetros (cloud, quick_win_mode) |
| FinOpsChatService | `services/finops/` | Orquestrador: comprehension → monta request → run_finops_analyze |
| POST /finops/chat | `routers/finops/` | Entrada única do chat FinOps |

**Não modificar:** `comprehension_orchestrator`, `comprehension_router` — permanecem exclusivos de codigo, infra, ID.

---

## 6. Arquivos a Criar/Modificar (todos dentro do módulo FinOps)

| Ação | Caminho |
|------|---------|
| Criar | `services/finops/comprehension_finops.py` — classify_intent_finops, extrair_params |
| Criar | `services/finops/finops_chat_service.py` — FinOpsChatService |
| Criar | `models/finops/finops_chat_models.py` — FinOpsChatInput, FinOpsChatOutput |
| Modificar | `routers/finops/finops_routers.py` — adicionar POST /finops/chat |

---

*Documento gerado em 12/02/2025.*
