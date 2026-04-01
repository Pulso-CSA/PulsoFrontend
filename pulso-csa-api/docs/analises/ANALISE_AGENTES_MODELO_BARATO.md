# Análise: Agentes que podem usar modelos mais baratos (economia de custo)

**Data da análise:** Com base no mapeamento de chamadas LLM no `app` e no fluxo do correct workflow.

**Objetivo:** Identificar quais agentes/serviços podem usar um modelo OpenAI mais barato (ex.: gpt-4o-mini) em vez do modelo padrão (ex.: o3), com impacto aceitável em qualidade.

---

## 1. Mapeamento de uso de LLM por componente

| Componente | Arquivo(s) | Chamadas LLM por request | Contexto típico |
|------------|------------|---------------------------|-----------------|
| **Comprehension – classificação** | `comprehension_service.py` | 1 (ou 0 se cache) | `classify_intent`: ANALISAR vs EXECUTAR. Saída curta, JSON. |
| **Comprehension – análise (ANALISAR)** | `comprehension_service.py` | 1 (ou 0 se cache) | `generate_analysis_text`: diagnóstico + 3–5 ações. Texto ~400 palavras. |
| **C1 – Refino** | `refine_service.py` | 1 (RAG ou fallback) | Refinar prompt do usuário; RAG usa `client.llm` + retriever. |
| **C1 – Validação** | `validate_service.py` | 0 | Apenas regra (ex.: >12 palavras). Não usa LLM. |
| **C2 – Plano de mudanças** | `change_plan_service.py` | N + 2 | N = chunks do projeto; +1 consolidação; +1 plano JSON. |
| **C2b – Code Plan** | `code_plan_service.py` | 1 (até 3 com retry) | JSON do plano de código (summary, new_files, changes). |
| **C3 – Code Writer** | `code_writer_service.py` | 0 | Gera stubs por template; não chama LLM. |
| **C4 – Code Implementer** | `code_implementer_service.py` | 1 por arquivo | Gera implementação por arquivo a partir do code plan. |
| **Pipeline 12–13** | `correcao_erros_service.py` | 0 direto | Reinvoca `run_correct_workflow` → repete C1→C4 (+ análise de retorno). |
| **Creator (workflow criação)** | `backend_service`, `infra_service`, `sec_*`, `code_creator_service` | Vários | RAG/LLM por relatório; geração de código. |
| **Outros** | `query_get_service`, `analise_tela_teste_service`, `generative_trainer` | 1 cada | Fluxos específicos (ID, tela teste, treino). |

Hoje todos usam o mesmo cliente: `get_openai_client()`, configurado por `OPENAI_MODEL` (ex.: o3).

---

## 2. Recomendações: quem pode usar modelo mais barato

Critérios usados: tarefa é **classificação/saída curta/estruturada**, **não gera código final** e **erro tolerável** (fallback ou retry).

| Agente / Serviço | Usar modelo barato? | Justificativa | Risco de qualidade |
|------------------|---------------------|---------------|---------------------|
| **Comprehension – classificação de intenção** | **Sim** | Saída binária (ANALISAR/EXECUTAR) + JSON pequeno. Já existe fallback regex; cache reduz chamadas. | Baixo. Erro ocasional → fallback ou EXECUTAR indevido; usuário pode refazer. |
| **Comprehension – análise (ANALISAR)** | **Sim** | Texto analítico curto (~400 palavras). Não altera código nem executa nada. | Baixo. Análise um pouco menos refinada; aceitável para “diagnóstico + ações”. |
| **C1 – Refino (refine_service)** | **Sim** | Reescreve prompt para clareza; não decide execução. Fallback já existe se RAG falhar. | Baixo. Refino menos “rico”; prompt final ainda utilizável. |
| **C2 – Plano de mudanças (chunks + consolidação)** | **Parcial** | Chunks: descrição de papel por trecho (respostas curtas). Consolidação: um resumo. Plano JSON: impacto estrutural. | Chunks/consolidação: **sim** (modelo barato). Plano JSON: **manter modelo forte** (erro aqui = arquivos errados). |
| **C2b – Code Plan** | **Não (ou modelo médio)** | Saída é o contrato para C3/C4. Erro gera stubs/implementação errados. | Alto se usar só modelo barato. Opção: modelo “médio” (ex.: gpt-4o) em vez de o3. |
| **C4 – Code Implementer** | **Não** | Gera código Python por arquivo. Sintaxe e lógica precisam ser corretas. | Alto. Modelo barato aumenta falhas de sintaxe e retries. |
| **Creator – backend/infra/sec_*** | **Parcial** | Relatórios de análise (backend, infra, sec): **sim**. Geração de código (`code_creator_service`): **não**. | Relatórios: baixo. Código: alto. |
| **ID / query_get, tela_teste, generative_trainer** | **Sim (ID/tela)** | Query_get e analise_tela_teste: tarefas limitadas, saída controlada. Trainer: depende do uso (geração de texto). | Baixo para ID/tela; médio para trainer. |

---

## 3. Resumo por prioridade de implementação

| Prioridade | Onde | Ação sugerida | Economia estimada (custo por request) |
|------------|------|----------------|---------------------------------------|
| **Alta** | Comprehension (classificação + análise) | Usar um único modelo barato (ex.: gpt-4o-mini) para `classify_intent` e `generate_analysis_text`. | Redução relevante (2 chamadas por request de ANALISAR; 1 por EXECUTAR com cache). |
| **Alta** | C1 – Refino | Usar modelo barato no `refine_service` (RAG + fallback). | 1 chamada cara → 1 barata por request de correção. |
| **Média** | C2 – Change plan | Modelo barato para **chunks** e **consolidação**; manter modelo forte só para a chamada que gera o **JSON do plano** (novos_arquivos / arquivos_a_alterar). | N+1 chamadas mais baratas; 1 continua cara. N proporcional ao tamanho do projeto. |
| **Média** | C2b – Code Plan | Avaliar modelo “médio” (gpt-4o) em vez de o3; ou manter o3 e reduzir tokens (prompt mais enxuto). | Se trocar para gpt-4o: economia; se só enxugar prompt: menos custo sem trocar modelo. |
| **Baixa** | Creator (relatórios) | Modelo barato para backend/infra/sec_* (relatórios); manter modelo forte para `code_creator_service`. | Economia no fluxo de criação; impacto menor que no correct. |

**Não recomendar (sem mudança de modelo):** C4 – Code Implementer (qualidade de código); validação já é heurística (sem LLM).

---

## 4. Implementação técnica sugerida (referência)

- **Variáveis de ambiente:** por exemplo `OPENAI_MODEL_FAST` (gpt-4o-mini) e `OPENAI_MODEL` (o3 ou gpt-4o).
- **OpenAIClient:** permitir `generate_text(..., model_override="fast")` ou novo método que instancia `ChatOpenAI` com `OPENAI_MODEL_FAST`.
- **Pontos de uso:**
  - `comprehension_service.classify_intent` e `generate_analysis_text` → modelo fast.
  - `refine_service.execute_refine_prompt` → modelo fast (tanto no RAG quanto no fallback).
  - `change_plan_service`: nas chamadas por chunk e em `consolidate_chunks` → modelo fast; na chamada que gera o plano JSON (`plan_prompt` / `system_prompt_plan`) → modelo padrão.

Nenhum código foi alterado nesta análise; o documento serve apenas como base para decisão e implementação futura.
