## Plano de Implementação – Subsistema de Inteligência de Dados (ID)

**Objetivo:** definir tudo o que falta criar na área de Inteligência de Dados, bem como as diretrizes de **redução de custo**, **otimização de velocidade** e **segurança**, considerando que o sistema irá consumir **bancos de dados externos** (SQL e NoSQL), com necessidade de **compressão** e **paginação** para grandes volumes.

Este plano serve como **backlog técnico** para implementação iterativa.

---

## 0. Modelo de uso: sob demanda (não em sequência)

Os endpoints de ID **não são executados em pipeline sequencial automático**. Cada etapa é **disparada pelo usuário** quando ele precisar daquela resposta.

**Exemplos:**

- **"Qual a correlação entre x e y?"**  
  O usuário chama **só** `POST /analise-estatistica` com `dataset_ref` (ou `retorno_tratamento`) e `pergunta: "qual a correlação entre x e y"`. A resposta traz métricas reais e um campo `resposta_pergunta` (ex.: valor da correlação).

- **"Quantos clientes vão dar churn no mês que vem?"**  
  O usuário chama **só** `POST /criar-modelo-ml` com `dataset_ref` (dataset já tratado), `variavel_alvo` (ex.: churn) e `tipo_problema: classificacao`. Não é obrigatório ter chamado antes analise-dados-inicial ou analise-estatistica.

- **"Quero só limpar os dados"**  
  O usuário chama **só** `POST /tratamento-limpeza` com `dataset_ref` e `id_requisicao`; não precisa enviar `retorno_analise_inicial`.

**Regras de contrato:**

- **`retorno_*` (retorno da etapa anterior)** são **opcionais**. Quando o usuário já tem o output de uma etapa anterior, pode enviar para enriquecer contexto; quando não tem, envia só o mínimo (ex.: `dataset_ref`, `pergunta`, `variavel_alvo`).
- **`dataset_ref`** (path do dataset) é o elo comum: quem tiver um path pode pular direto para tratamento, estatística ou ML.
- **`pergunta`** em análise-estatística permite respostas diretas (ex.: correlação entre duas colunas) sem precisar da cadeia completa.

Assim, o fluxo é **orientado pela pergunta do usuário**, e não por uma sequência fixa captura → análise inicial → tratamento → estatística → ML.

### 0.1. Cientista de dados de alto nível: Chat e previsão em tempo real

- **`POST /inteligencia-dados/chat`**  
  Orquestrador: o usuário envia uma **mensagem em linguagem natural** (e opcionalmente `dataset_ref`, `model_ref`, `dados_para_prever`). O sistema interpreta a intenção (estatística, treino, previsão), executa as etapas necessárias e devolve uma **resposta unificada**, incluindo **previsões no próprio retorno** quando a mensagem pedir (ex.: “treina modelo de churn e me diz quem vai churnar”).

- **`POST /inteligencia-dados/prever`**  
  Aplica um modelo já treinado (`model_ref`) a um dataset (`dataset_ref`) ou a registros em tempo real (`dados`). O `model_ref` é retornado por `POST /inteligencia-dados/criar-modelo-ml` após o treino, permitindo **aplicação de previsões no próprio chat** (enviando `dados_para_prever` no chat ou chamando `/prever` com `dados`).

- **Persistência do modelo**  
  O modelo treinado é salvo em artefatos (subdir `models/`); o path retornado (`model_ref`) pode ser reutilizado para previsões sem retreinar.

- **Uso do próprio modelo criado**  
  No mesmo turno do chat, se o usuário pedir treino e previsão (ex.: “treina modelo de churn e me diz quem vai churnar”), o sistema **treina, salva o modelo, obtém o `model_ref` e usa esse mesmo modelo** na etapa de previsão. Ou seja, a previsão em tempo real no chat usa sempre o modelo que o próprio sistema acabou de criar (ou um `model_ref` enviado pelo usuário de um treino anterior).

---

### 0.2. O que pode deixar a área ID mais poderosa (implementado)

- **Interpretação de variável alvo**  
  Quando a mensagem não trouxer `variavel_alvo` explícita, usar LLM com a lista de colunas do dataset para inferir o alvo (ex.: “modelo de churn” → coluna `churn` ou `churn_flag`).

- **Tratamento no fluxo do chat**  
  Incluir etapa “tratamento” no orquestrador quando a mensagem pedir limpeza/normalização ou quando a análise inicial sugerir; assim o chat pode fazer captura → tratamento → estatística → treino → previsão em uma única mensagem.

- **Captura no chat**  
  Permitir no chat envio de `db_config` (ou referência a conexão salva) e mensagem tipo “conecta no banco X e treina modelo de churn na tabela clientes”; orquestrador chama captura com amostra, depois treino com o `dataset_ref` retornado.

- **Explicabilidade (SHAP / feature importance)**  
  Após treino ou previsão, expor importância das variáveis ou explicação por registro (SHAP values) para “por que esse cliente foi previsto como churn?”.

- **Múltiplos modelos e A/B**  
  Manter mais de um modelo por `id_requisicao` (ex.: `model_ref_v1`, `model_ref_v2`) e endpoint para comparar previsões ou escolher qual usar.

- **Previsão com intervalo de confiança**  
  Para regressão, retornar intervalo (ex.: predição ± erro) quando o modelo/pipeline expuser incerteza.

- **Validação de dados na previsão**  
  Ao receber `dados` ou `dados_para_prever`, validar schema (colunas e tipos) contra o que o modelo espera e devolver erro claro se faltar coluna ou tipo incorreto.

- **Cache de interpretação**  
  Cachear o resultado do LLM de interpretação da mensagem por (hash da mensagem + contexto) para reduzir custo e latência em mensagens repetidas.

- **Métricas de negócio no retorno**  
  Além de acurácia/F1, calcular e devolver métricas acionáveis (ex.: “quantos clientes previstos como churn”, “valor em risco”) quando fizer sentido.

- **Agendamento e retreino**  
  Permitir agendar retreino periódico (ex.: semanal) com novo dataset e substituição do `model_ref` em uso.

**Status:** Todas as melhorias acima foram implementadas: captura e tratamento no chat (`db_config`, intent `fazer_captura`/`fazer_tratamento`), cache de interpretação LLM, validação de schema na previsão, métricas de negócio (treino e previsão), importância de variáveis no treino, intervalos de confiança na regressão, múltiplas versões de modelo (`lista_model_refs`, `GET /listar-modelos`), agendamento (`POST /agendar-retreino`, `POST /executar-retreino-agendado`).

---

## 1. Estrutura de Pastas e Serviços a Criar

### 1.1. Diretório raiz de ID (seguindo padrão atual do PulsoAPI)

Em vez de criar uma nova raiz fora do padrão, a área de ID **deve seguir a mesma organização já usada no projeto** (`core/`, `models/`, `services/`, `routers/`, `agents/`):

- **Core (baixo nível / conexões):**
  - `app/core/ID_core/`
    - Conexões externas (MySQL, MongoDB externo, etc.).
- **Models (DTOs, schemas de API):**
  - `app/models/ID_models/`
    - Ex.: `captura_dados_models.py`, `analise_dados_models.py`, `tratamento_limpeza_models.py`, `analise_estatistica_models.py`, `modelos_ml_models.py`.
- **Services (regras de negócio):**
  - `app/services/ID_services/`
    - Ex.: `captura_dados_service.py`, `analise_dados_service.py`, `tratamento_limpeza_service.py`, `analise_estatistica_service.py`, `modelos_ml_service.py`.
- **Routers (endpoints FastAPI):**
  - `app/routers/ID_routers/`
    - Ex.: `captura_dados_router.py`, `analise_dados_router.py`, `tratamento_limpeza_router.py`, `analise_estatistica_router.py`, `modelos_ml_router.py`.
- **Agents (quando houver agentes LLM específicos):**
  - `app/agents/ID_agents/` (opcional, se seguir o padrão de `app/agents/architecture/`)
    - Ex.: `captura_dados_agent.py`, `analise_dados_agent.py`, etc., encapsulando chamadas de LLM.

Ou seja, os “serviços” de ID (captura, análise, tratamento, etc.) são **features** implementadas como **conjunto consistente de `models/`, `services/`, `routers/` (e opcionalmente `agents/`)**, mantendo o mesmo padrão estrutural já usado no PulsoAPI.

### 1.2. Movimentação e Refatoração do que já existe

**Arquivos identificados que precisam ser movidos/refatorados:**

#### 1.2.1. Arquivos a mover/refatorar mantendo o padrão atual

- **`app/core/ID_core/mysql_connection.py`** (permanece em `app/core/ID_core/`)
  - Classe `MySQLConnection` já existe e funciona.
  - **Mudanças necessárias:**
    - Adicionar suporte a **paginação** em `execute_select()` (parâmetros `limit` e `offset`).
    - Adicionar método `execute_count()` para contar registros sem carregar dados.
    - Adicionar método `get_table_metadata()` para extrair metadados (índices, chaves, tipos).
    - Adicionar método `get_table_names()` e `get_column_info()` (extrair da lógica atual de `_build_database_schema_text`).
    - Adicionar **timeout configurável** nas conexões.
    - Adicionar **pool de conexões** com limite máximo para evitar esgotamento de recursos.

- **`app/routers/ID_routers/query_get_router.py`**
  - Router atual com endpoint `/inteligencia-dados/query`.
  - **Mudanças necessárias / novos arquivos:**
    - Manter endpoint `/query` temporariamente para compatibilidade (deprecar depois).
    - Criar novo arquivo `app/routers/ID_routers/captura_dados_router.py` com endpoint `POST /captura-dados` seguindo especificação do plano.
    - Adicionar validação de `id_requisicao` e `usuario` em todas as rotas de ID.
    - Adicionar tratamento de erros específicos (timeout, conexão recusada, credenciais inválidas).

- **`app/services/ID_services/query_get_service.py`**
  - Serviço atual que faz NL→SQL→DB→NL.
  - **Mudanças necessárias / novos arquivos:**
    - Extrair a parte de captura de schema e criar `app/services/ID_services/captura_dados_service.py` para o fluxo de captura de estrutura.
    - Manter um serviço específico `query_get_service.py` (ou `query_dados_service.py`) para o fluxo NL→SQL→DB→NL, reutilizando a mesma camada de conexão e schema.
    - Quando houver necessidade de lógica LLM mais rica (ex.: interpretação de objetivos de análise), criar agentes em `app/agents/ID_agents/` que orquestram chamadas LLM e usam os services como backend.

- **`app/models/ID_models/query_get_models.py`**
  - Modelos atuais: `QueryGetDBConfig`, `QueryGetInput`, `QueryGetOutput`, `QueryGetRawResult`.
  - **Mudanças necessárias / novos arquivos:**
    - Criar novo arquivo `app/models/ID_models/captura_dados_models.py` com modelos: `CapturaDadosInput`, `CapturaDadosOutput`, `RelatorioEstrutura`.
    - Manter modelos antigos temporariamente (deprecar depois).
    - Adicionar modelo `DBConfig` genérico que suporte MySQL e MongoDB (com validação por tipo).

- **`app/storage/database/ID_database/query_get_database.py`**
  - Classe `QueryGetDatabase` atual.
  - **Mudanças necessárias / novos arquivos:**
    - Refatorar para usar interface comum de banco (abstração).
    - Adicionar suporte a MongoDB.
    - Se necessário, criar `app/storage/database/ID_database/captura_dados_database.py` para separar responsabilidades (captura vs query NL→SQL).
    - Adicionar paginação em `fetch()`.

#### 1.2.2. Mudanças específicas necessárias no código existente

**Em `mysql_connection.py` (atual):**

**Mudanças de funcionalidade:**
- [ ] Adicionar método `execute_select_paginated(sql: str, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]`:
  ```python
  # Exemplo de implementação:
  def execute_select_paginated(self, sql: str, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
      # Validar que SQL é SELECT
      if not sql.strip().upper().startswith("SELECT"):
          raise ValueError("Only SELECT queries are allowed")
      # Adicionar LIMIT e OFFSET de forma segura
      paginated_sql = f"{sql.rstrip(';')} LIMIT {limit} OFFSET {offset}"
      return self.execute_select(paginated_sql)
  ```

- [ ] Adicionar método `execute_count(sql: str) -> int`:
  ```python
  # Exemplo: converter SELECT * FROM tabela em SELECT COUNT(*) FROM tabela
  # Retornar número inteiro
  ```

- [ ] Adicionar método `get_table_names(database: str) -> List[str]`:
  ```python
  # Usar information_schema.tables (já usado em _build_database_schema_text)
  # Retornar lista de nomes de tabelas
  ```

- [ ] Adicionar método `get_column_info(database: str, table: str) -> List[Dict]`:
  ```python
  # Retornar: [{"column_name": "...", "data_type": "...", "is_nullable": "...", ...}]
  # Usar information_schema.columns
  ```

- [ ] Adicionar método `get_table_indexes(database: str, table: str) -> List[Dict]`:
  ```python
  # Retornar índices da tabela usando information_schema.statistics
  ```

- [ ] Adicionar método `get_table_row_count(database: str, table: str) -> int`:
  ```python
  # Executar SELECT COUNT(*) FROM {database}.{table} de forma segura
  # Validar nomes de database e table para evitar SQL injection
  ```

**Mudanças de segurança e performance:**
- [ ] Adicionar timeout configurável no `create_engine()`:
  ```python
  # Adicionar parâmetros: connect_args={"connect_timeout": 10}
  # E pool_pre_ping com timeout
  ```

- [ ] Adicionar pool_size e max_overflow no engine:
  ```python
  # pool_size=5, max_overflow=10 (evitar esgotamento de conexões)
  ```

- [ ] Adicionar validação de SQL injection em métodos que recebem nomes de tabela/coluna:
  ```python
  # Validar que database e table contêm apenas caracteres alfanuméricos e underscore
  # Rejeitar caracteres especiais que possam ser usados em SQL injection
  ```

- [ ] Adicionar método `close()` para fechar conexões explicitamente:
  ```python
  # Útil para cleanup em context managers ou quando não precisar mais da conexão
  ```

- [ ] Adicionar suporte a context manager (`__enter__`, `__exit__`):
  ```python
  # Permitir uso com: with MySQLConnection(config) as conn: ...
  ```

**Em `query_get_service.py` (atual):**
- [ ] Extrair `_build_database_schema_text()` para classe `SchemaExtractor` reutilizável.
- [ ] A lógica de validação SQL (`_is_sql_safe`, `_forbidden_sql_patterns`) deve ser mantida e reutilizada no novo agente de captura.
- [ ] A lógica de RAG (`_retrieve_few_shots`) pode ser mantida para o endpoint `/query` antigo, mas não é necessária para `/captura-dados`.

**Em `query_get_router.py` (atual):**
- [ ] Adicionar validação de `id_requisicao` obrigatório.
- [ ] Adicionar validação de `usuario` (extrair do token ou payload).
- [ ] Adicionar tratamento de erros específicos (conexão, timeout, SQL injection).
- [ ] Adicionar logging seguro (sem credenciais).

**Em `query_get_models.py` (atual):**
- [ ] Criar `DBConfigBase` (classe base) e `MySQLConfig`, `MongoDBConfig` (herdeiras).
- [ ] Adicionar validação de URI/host (bloquear hosts internos não autorizados).
- [ ] Adicionar máscara de senha em `__repr__` e `model_dump()`.

#### 1.2.3. O que NÃO existe ainda e precisa ser criado

- **Conexão MongoDB externa**: não existe ainda (só existe MongoDB interno para persistência do PulsoAPI).
- **Abstração de banco de dados**: interface comum para MySQL e MongoDB não existe.
- **Paginação**: não implementada em nenhuma consulta atual.
- **Compressão**: não há uso de Parquet ou compressão em datasets intermediários.
- **Cache de relatórios**: não há cache de captura/análise por `id_requisicao`.
- **Isolamento por usuário**: não há isolamento de artefatos (datasets, modelos) por usuário/`id_requisicao`.
- **Agentes de análise/tratamento/ML**: não existem ainda (só existe o endpoint `/query` que faz NL→SQL).

---

## 2. Agentes / Endpoints a Implementar

Cada agente será exposto por um endpoint específico no `router` de seu service, com entrada e saída em JSON, sempre incluindo `id_requisicao` e contexto do usuário.

### 2.1. Agente de Captura de Dados – `/captura-dados`

- **Router:** `app/routers/ID_routers/captura_dados_router.py`
- **Service:** `app/services/ID_services/captura_dados_service.py`
- **Models:** `app/models/ID_models/captura_dados_models.py`
- **(Opcional) Agent LLM:** `app/agents/ID_agents/captura_dados_agent.py`
- **Responsabilidade:** conectar à base de dados externa, detectar tipo (SQL/NoSQL), extrair “esqueleto” e gerar relatório de estrutura, usando LLM para descrever o teor dos dados e gerar explicações em linguagem natural quando necessário.

**Tarefas a implementar:**

- Criar endpoint `POST /captura-dados` em `router`.
- Definir modelos de entrada (em `model`):
  - `id_requisicao`
  - dados de conexão (URI/credenciais, tipo de base ou auto-detecção).
- Implementar camada de **abstração de banco de dados**:
  - **Drivers suportados inicialmente:**
    - MySQL (já existente – refatorar para essa camada).
    - MongoDB (criar conexão análoga à do MySQL).
  - Interface/contrato comum para:
    - listar tabelas/coleções,
    - contar registros por tabela/coleção,
    - recuperar amostras de dados,
    - obter metadados (índices, tipos de coluna, chaves).
- Implementar lógica de detecção de tipo de base (SQL vs NoSQL) a partir da URI ou config.
- Implementar lógica de **teor dos dados** (ex.: “cadastro”, “logs”, “métricas”) com base em:
  - nome de tabelas/coleções,
  - campos principais,
  - possíveis dicionários de termos.
- Gerar **relatório de estrutura** com o formato geral:
  - `tipo_base`, lista de tabelas/coleções,
  - contagens de registros,
  - descrição de teor, observações.
- Persistir (opcional) o relatório e metadados associados ao `id_requisicao` e usuário para reuso posterior.

### 2.2. Agente de Análise Inicial dos Dados – `/analise-dados-inicial`

- **Router:** `app/routers/ID_routers/analise_dados_router.py`
- **Service:** `app/services/ID_services/analise_dados_service.py`
- **Models:** `app/models/ID_models/analise_dados_models.py`
- **Agent LLM:** `app/agents/ID_agents/analise_dados_agent.py` (fortemente recomendado)
- **Responsabilidade:** interpretar o retorno de `/captura-dados`, propor objetivos de análise, identificar variáveis relevantes e tratamentos necessários, usando LLM para:
  - interpretar objetivos em linguagem natural;
  - sugerir análises possíveis;
  - descrever variáveis alvo/correlacionadas de forma explicável.

**Tarefas a implementar:**

- Criar endpoint `POST /analise-dados-inicial`.
- Definir modelos de entrada (em `model`):
  - `id_requisicao`
  - retorno do `/captura-dados` (ou referência ao relatório salvo).
  - objetivo de análise solicitado (ex.: churn, fraude, desempenho) – opcional ou obrigatório conforme decisão de design.
- Implementar regras para:
  - identificar **objetivo_analise** (explícito ou inferido),
  - listar **análises recomendadas** (ex.: distribuição, correlações, sequência temporal),
  - listar **tratamentos necessários** (remoção de duplicatas, normalização, tratamento de missing, balanceamento),
  - sugerir **variáveis alvo** e **variáveis correlacionadas** com base na estrutura (tipos de coluna, nomes, presença de campos como `status`, `data`, `valor`, etc.).
- Gerar relatório de **análise inicial** com saída no formato acordado (JSON).

### 2.3. Agente de Tratamento & Limpeza de Dados – `/tratamento-limpeza`

- **Router:** `app/routers/ID_routers/tratamento_limpeza_router.py`
- **Service:** `app/services/ID_services/tratamento_limpeza_service.py`
- **Models:** `app/models/ID_models/tratamento_limpeza_models.py`
- **(Opcional) Agent LLM:** `app/agents/ID_agents/tratamento_limpeza_agent.py`
- **Responsabilidade:** executar ETL, limpeza e normalização, produzindo dataset pronto para análise e ML. O LLM pode ser usado para:
  - sugerir pipelines de tratamento com base na estrutura e no objetivo;
  - gerar explicações em linguagem natural sobre o que foi feito e por quê;
  - ajudar a escolher estratégias de imputação/outlier quando houver múltiplas opções válidas.

**Tarefas a implementar:**

- Criar endpoint `POST /tratamento-limpeza`.
- Definir modelos de entrada:
  - `id_requisicao`
  - retorno de `/analise-dados-inicial` (ou referência).
- Implementar pipeline de tratamento:
  - remoção de **duplicatas**;
  - tratamento de **valores ausentes**:
    - para colunas categóricas: imputação por proporção de categorias (como no exemplo de `valores_vazios`) ou moda;
    - para colunas numéricas: mediana, média ou métodos mais sofisticados;
  - tratamento de **outliers** (ex.: winsorization, clipping por quantil, remoção, ou flag de outlier);
  - **normalização/escalonamento** de variáveis numéricas (min-max, padronização z-score, etc.);
  - padronização de **formatos** (datas, moedas, códigos).
- Garantir que o pipeline seja:
  - **modular** (cada transformação como bloco plugável),
  - **configurável por usuário/requisição** (possibilidade de estratégias diferentes).
- Gerar um dataset de saída (ex.: DataFrame em memória + artefato persistido em armazenamento interno):
  - formato sugerido: **Parquet com compressão** (ex.: `snappy` ou `gzip`) para boa relação custo/velocidade.
- Produzir relatório de tratamento:
  - lista de ações feitas,
  - justificativas (por que cada tratamento foi aplicado),
  - estatísticas antes/depois (opcional).

### 2.4. Agente de Análise Estatística – `/analise-estatistica`

- **Router:** `app/routers/ID_routers/analise_estatistica_router.py`
- **Service:** `app/services/ID_services/analise_estatistica_service.py`
- **Models:** `app/models/ID_models/analise_estatistica_models.py`
- **Agent LLM:** `app/agents/ID_agents/analise_estatistica_agent.py` (recomendado)
- **Responsabilidade:** executar análise estatística sobre o dataset tratado, gerar métricas, gráficos e insights, além de sugerir modelos de ML. O LLM deve ser usado para:
  - transformar resultados numéricos em insights textuais compreensíveis;
  - sugerir hipóteses e interpretações de correlações;
  - descrever gráficos e destacar padrões relevantes.

**Tarefas a implementar:**

- Criar endpoint `POST /analise-estatistica`.
- Definir modelos de entrada:
  - `id_requisicao`
  - referência ao dataset tratado (arquivo Parquet/CSV comprimido, ID interno, etc.).
- Implementar protocolo de análise estatística:
  - cálculo de **médias, medianas, desvios padrões** e percentis;
  - análise de **correlações** (Pearson, Spearman, etc.);
  - identificação de **variáveis mais importantes** (ex.: via importância de features em modelos simples ou mutual information);
  - geração de **descrições para gráficos**:
    - distribuições (histogramas),
    - séries temporais (quando houver data/hora),
    - comparativos por categoria (boxplots, barplots, etc.).
- Definir formato para saída de gráficos:
  - idealmente, devolver **metadados de gráficos** (ex.: tipo, eixos, agregações) em vez de imagens binárias, para o frontend gerar visualizações.
- Sugerir **modelos de ML** adequados:
  - com base no tipo de problema:
    - classificação binária/multiclasse,
    - regressão,
    - séries temporais,
    - agrupamento (clustering), se fizer sentido.
  - listar **requisitos** (balanceamento, encoding, tamanho mínimo de amostra, etc.).

### 2.5. Agente de Criação de Modelos de ML – `/criar-modelo-ml`

- **Router:** `app/routers/ID_routers/modelos_ml_router.py`
- **Service:** `app/services/ID_services/modelos_ml_service.py`
- **Models:** `app/models/ID_models/modelos_ml_models.py`
- **Agent LLM:** `app/agents/ID_agents/modelos_ml_agent.py` (recomendado)
- **Responsabilidade:** treinar, comparar e validar modelos de Machine Learning de forma automatizada, garantindo um limiar mínimo de qualidade (ex.: 70% de acurácia real). O LLM deve ser usado para:
  - explicar em linguagem natural os resultados de métricas (precisão, recall, F1, AUC);
  - justificar a escolha do modelo vencedor;
  - sugerir melhorias (features adicionais, balanceamento, mais dados) a partir dos resultados numéricos.

### 2.6. Padrão de Uso de LLM nos Agentes de ID

- Todos os agentes de ID devem **reutilizar a infraestrutura de LLM já existente** no projeto, via `app.core.openai.openai_client.get_openai_client()` e, quando fizer sentido, via agentes em `app/agents/` (seguindo o padrão de `app/agents/architecture/`).
- **Captura de dados (`/captura-dados`):**
  - LLM usado para descrever o “teor dos dados” (ex.: classificar se são cadastros, logs, métricas) e gerar resumos do esqueleto da base.
- **Análise inicial (`/analise-dados-inicial`):**
  - LLM é central para interpretar o objetivo de negócio, propor análises e identificar variáveis alvo/correlacionadas.
- **Tratamento & limpeza (`/tratamento-limpeza`):**
  - LLM auxilia na escolha de estratégias (imputação, outliers, normalização) e na explicação do pipeline aplicado; a execução é feita com bibliotecas de dados (pandas, numpy, etc.).
- **Análise estatística (`/analise-estatistica`):**
  - Bibliotecas estatísticas calculam métricas; LLM transforma esses números em insights, narrativas e recomendações compreensíveis.
- **Modelos de ML (`/criar-modelo-ml`):**
  - Bibliotecas de ML (ex.: PyCaret) cuidam do treino/validação; LLM explica resultados, compara modelos em termos de negócio e sugere próximos passos.

Assim, o subsistema de ID continua **100% alinhado ao padrão de agentes + services + routers** já existente no PulsoAPI e **usa LLM em todas as etapas onde interpretação e explicação em linguagem natural são necessárias**.

**Tarefas a implementar:**

- Criar endpoint `POST /criar-modelo-ml`.
- Definir modelos de entrada:
  - `id_requisicao`
  - retorno de `/analise-estatistica` (incluindo `modelos_sugeridos` e requisitos).
  - referência ao dataset tratado.
- Implementar pipeline de ML automatizado (ex.: com **PyCaret** ou equivalente):
  - identificar tipo de problema (classificação/regressão/etc.);
  - dividir dataset em **treino/validação/teste**;
  - executar `compare_models` (ou rotina análoga) para comparar algoritmos;
  - aplicar **limiar de qualidade**:
    - nenhum modelo deve ser aceito com menos de **70% de acurácia real** (ou métrica equivalente para o problema: AUC, F1, etc.);
  - selecionar melhor modelo com base em métrica prioritária (ex.: AUC para fraude, F1 para classes desbalanceadas).
- Persistir:
  - artefato do modelo treinado (arquivo serializado, exemplo: pickle ou formato seguro compatível),
  - metadados de treinamento (data, hiperparâmetros, métricas, versão do código).
- Gerar relatório final:
  - `modelo_escolhido`,
  - motivo da escolha (melhor métrica, robustez, interpretabilidade),
  - principais métricas (precisão, recall, F1, AUC, etc.),
  - constatações sobre o desempenho,
  - melhorias recomendadas (mais dados, balanceamento, feature engineering).

---

## 3. Técnicas de Redução de Custos

Nesta seção, o foco é reduzir **custo computacional e financeiro** sem perder qualidade.

### 3.1. Uso eficiente de I/O e consultas a bancos externos

- **Paginação e limites de amostra**:
  - Evitar `SELECT *` ou leitura integral de grandes coleções.
  - Definir **tamanho máximo de página** e **limite de linhas** para:
    - análise inicial,
    - amostras para estatística,
    - fase de prototipação de modelos.
  - Só carregar dataset completo quando explicitamente necessário.
- **Projeções específicas**:
  - selecionar apenas colunas necessárias para a análise/modelagem inicial.
  - no MongoDB, usar projeções para reduzir campos retornados.

### 3.2. Compressão e formatos de armazenamento

- Utilizar **Parquet com compressão** (Snappy/Gzip) como formato padrão para datasets intermediários (pós-tratamento).
  - reduz tamanho em disco e custo de transferência,
  - mantém leitura eficiente para análises e ML.
- Quando armazenar CSV, considerar **compressão Gzip** com suporte a leitura streaming.

### 3.3. Reuso de artefatos (cache)

- Cachear:
  - relatórios de captura e análise inicial por (`id_requisicao`, versão dos dados),
  - datasets tratados (versões identificadas com hash ou timestamp),
  - resultados de algumas análises estatísticas repetitivas.
- Vantagem:
  - reduzir reprocessamento em cenários de iteração sobre a mesma base/requisição.

### 3.4. Uso racional de pipeline de ML

- Limitar quantidade de modelos comparados em `compare_models` conforme:
  - tamanho do dataset,
  - SLA de tempo,
  - perfil de uso (desenvolvimento vs produção).
- Permitir configuração de:
  - tempo máximo por experimento,
  - número máximo de modelos,
  - número de folds de cross-validation.

---

## 4. Técnicas de Otimização de Velocidade

### 4.1. Arquitetura assíncrona e paralelismo

- Sempre que possível:
  - usar **acesso assíncrono** a bancos externos, para não bloquear o servidor.
  - paralelizar:
    - consultas independentes (várias tabelas/coleções),
    - etapas internas de análise estatística e geração de gráficos.
- Usar filas/tarefas assíncronas (job queue) para:
  - treinos de modelos de ML mais pesados,
  - análises estatísticas complexas em grandes volumes.

### 4.2. Paginação de respostas da API

- Para endpoints que retornam listas (ex.: prévias de registros, amostras):
  - implementar **paginação** explícita:
    - parâmetros: `page`, `page_size`, `cursor` ou similar.
  - proteger contra `page_size` exagerado com limite máximo.
- Para relatórios extensos:
  - retornar apenas **resumo** e, opcionalmente, um identificador para baixar detalhes em outra rota (ou por streaming).

### 4.3. Minimização de cópias de dados em memória

- Processar dados de forma **streaming** sempre que possível (principalmente na captura):
  - ler em chunks,
  - resumir/contar sem carregar tudo na memória.
- Evitar múltiplas cópias do mesmo DataFrame em memória:
  - aplicar transformações in-place quando seguro,
  - liberar referências antigas após gerar artefatos persistidos.

---

## 5. Segurança do Sistema (com Bases Externas)

### 5.1. Gestão de credenciais e URIs

- **Nunca** armazenar credenciais em texto puro nos logs ou respostas da API.
- Utilizar:
  - storage seguro de segredos (variáveis de ambiente, vault, ou equivalente).
  - mascaramento de URIs (exibir apenas host/porta ou hash em relatórios).
- Validar entradas de conexão:
  - bloquear URIs que apontem para hosts internos não autorizados,
  - restringir portas e protocolos aceitos.

### 5.2. Princípio de menor privilégio

- Recomendar (e suportar) que o cliente forneça:
  - usuários de banco com **permissão apenas de leitura** para as etapas de captura/análise.
  - se for estritamente necessário escrita (ex.: staging temporário), usar schemas/coleções dedicados e credenciais distintas.

### 5.3. Isolamento entre usuários e requisições

- Cada `id_requisicao` deve ser:
  - associado a um **usuário** ou tenant,
  - isolado logicamente (e, quando possível, fisicamente) em termos de:
    - arquivos (datasets, modelos),
    - registros de log e relatórios.
- Evitar exposição de dados de um usuário em respostas de outro:
  - validação rigorosa de autorização em todas as rotas ID.

### 5.4. Proteção contra ataques via entrada de dados

- Sanitizar parâmetros das conexões:
  - evitar injeção em strings de conexão (SQL injection em queries internas).
- Implementar **validações de schema** nos JSONs:
  - uso de schemas fortes (ex.: Pydantic) para garantir tipos e formatos.
- Limitar o tamanho do payload de entrada:
  - proteger contra requisições com objetos gigantes ou aninhamentos excessivos.

### 5.5. Logs e auditoria

- Registrar:
  - início/fim de cada etapa por `id_requisicao`,
  - erros de conexão, falhas de análise, problemas de modelo.
- Mas **sem** logar:
  - dados sensíveis de registros (ex.: CPF, cartões, senhas),
  - credenciais de banco,
  - amostras completas de linhas (usar amostras anonimizadas quando necessário).

---

## 6. Considerações Específicas para Compressão e Paginação

### 6.1. Compressão

- **Entrada:** quando o cliente enviar arquivos (CSV, Parquet), permitir compressão (`.gz`, `.zip`) com descompressão controlada.
- **Intermediários:** usar Parquet + compressão como padrão para:
  - dataset pós-tratamento,
  - datasets reduzidos para treino de modelo.
- **Saída:** quando for necessário disponibilizar dataset, permitir opção de:
  - saída compactada (zip/gzip),
  - ou somente amostras/estatísticas (sem o dataset completo).

### 6.2. Paginação e streaming de dados

- Para respostas com muitos registros:
  - retornar **páginas** em vez de tudo de uma vez.
  - se necessário, usar **cursor-based pagination** para grandes coleções.
- Para relatórios muito grandes:
  - opção de dividir em seções (ex.: estrutura, estatísticas, insights),
  - ou retornar um ID que permita o frontend buscar partes sob demanda.

---

## 7. Backlog Resumido (Checklist)

### 7.1. Infraestrutura de ID

- [ ] Manter o padrão atual de estrutura do PulsoAPI para ID:
  - `app/core/ID_core/` (conexões externas – MySQL, MongoDB externo, etc.).
  - `app/models/ID_models/` (DTOs por agente: captura, análise, tratamento, estatística, modelos ML).
  - `app/services/ID_services/` (regras de negócio de cada agente de ID).
  - `app/routers/ID_routers/` (endpoints FastAPI para cada agente de ID).
  - `app/agents/ID_agents/` (quando houver agentes LLM específicos).
- [ ] Mapear e refatorar código atual de captura/estrutura (`query_get_*`) para os novos services/routers/models mantendo esse padrão.
- [ ] Definir contratos (schemas/DTOs) de entrada/saída para todos os endpoints.

### 7.2. Conectividade com bancos externos

- [ ] Implementar camada de abstração de banco com suporte a:
  - [ ] MySQL (reuso do que já existe).
  - [ ] MongoDB (nova conexão, leitura de coleções e índices).
- [ ] Adicionar suporte a paginação em todas as leituras grandes.
- [ ] Configurar projeções para reduzir colunas/campos retornados.

### 7.3. Pipelines de análise

- [ ] Implementar agente `/captura-dados` (estrutura e relatório).
- [ ] Implementar agente `/analise-dados-inicial`.
- [ ] Implementar agente `/tratamento-limpeza` (pipeline modular de ETL).
- [ ] Implementar agente `/analise-estatistica`.
- [ ] Implementar agente `/criar-modelo-ml` (PyCaret ou similar) com:
  - [ ] Comparação de modelos.
  - [ ] Limiar mínimo de 70% de acurácia (ou métrica equivalente).

### 7.4. Custo e velocidade

- [ ] Introduzir formatos comprimidos (Parquet + compressão) para datasets intermediários.
- [ ] Adicionar paginação em endpoints que retornam dados ou amostras.
- [ ] Permitir configuração de limites de linhas/amostras por requisição.
- [ ] Implementar execuções assíncronas/filas para tarefas pesadas (treino de ML, análises grandes).

### 7.5. Segurança

- [ ] Definir e aplicar padrão de gestão de credenciais (sem exposição em logs/respostas).
- [ ] Implementar máscaras de URIs e logs mínimos.
- [ ] Garantir isolamento por usuário e `id_requisicao` em todos os artefatos.
- [ ] Adicionar validação de schema forte em todas as rotas de ID.
- [ ] Definir política de logging e auditoria (incluindo anonimização quando necessário).

---

## 8. Itens que Passaram Batido (Análise Completa do Sistema)

Após análise completa do código existente, foram identificados os seguintes itens que não estavam explícitos no plano original:

### 8.1. Integração com Sistema de Autenticação e Autorização

- [ ] **Validar token de autenticação** em todos os endpoints de ID (usar middleware existente ou criar específico).
- [ ] **Extrair `usuario` do token** e associar a `id_requisicao` em todos os artefatos (datasets, modelos, relatórios).
- [ ] **Validar permissões** do usuário para acessar `id_requisicao` específico (evitar acesso cruzado entre usuários).
- [ ] **Integrar com sistema de rate limiting** existente (`check_rate_limit_user`, `check_rate_limit_ip`) para limitar uso de recursos pesados (ML, análises grandes).

### 8.2. Integração com Sistema de Logging Existente

- [ ] **Usar `add_log()` existente** (`app/utils/log_manager.py`) em todas as etapas de ID.
- [ ] **Logar início/fim de cada agente** com `id_requisicao` e `usuario`.
- [ ] **Não logar credenciais** ou dados sensíveis (já há padrão no sistema, seguir).
- [ ] **Logar métricas de performance** (tempo de execução, tamanho de datasets, uso de memória) para monitoramento.

### 8.3. Integração com Armazenamento Interno (MongoDB do PulsoAPI)

- [ ] **Persistir relatórios de captura** na coleção MongoDB interna (ex.: `id_captura_relatorios`).
- [ ] **Persistir metadados de datasets tratados** (localização do arquivo Parquet, hash, tamanho, `id_requisicao`, `usuario`).
- [ ] **Persistir metadados de modelos ML** (localização do arquivo serializado, métricas, data de treinamento, `id_requisicao`, `usuario`).
- [ ] **Criar índices MongoDB** para consultas rápidas por `id_requisicao`, `usuario`, `data_criacao`.
- [ ] **Implementar TTL (Time To Live)** para datasets e modelos antigos (ex.: deletar após 30 dias de inatividade).

### 8.4. Gestão de Arquivos e Armazenamento Local

- [ ] **Definir estrutura de diretórios** para artefatos de ID:
  - `app/storage/id_artifacts/{usuario}/{id_requisicao}/datasets/`
  - `app/storage/id_artifacts/{usuario}/{id_requisicao}/modelos/`
  - `app/storage/id_artifacts/{usuario}/{id_requisicao}/relatorios/`
- [ ] **Implementar limpeza automática** de arquivos antigos (cron job ou task agendada).
- [ ] **Validar espaço em disco** antes de criar novos artefatos (evitar esgotamento).
- [ ] **Usar nomes de arquivo únicos** com hash ou timestamp para evitar colisões.

### 8.5. Tratamento de Erros e Resiliência

- [ ] **Tratamento específico para erros de conexão** (banco externo indisponível, timeout, credenciais inválidas).
- [ ] **Retry com backoff exponencial** para operações de rede (conexão, consultas).
- [ ] **Validação de tamanho de dataset** antes de processar (evitar OOM - Out of Memory).
- [ ] **Graceful degradation**: se análise estatística falhar, retornar pelo menos estatísticas básicas.
- [ ] **Validação de formato de dados** antes de aplicar tratamentos (evitar erros em tipos inesperados).

### 8.6. Validações de Entrada Adicionais

- [ ] **Validar tamanho máximo de `db_config`** (evitar payloads gigantes).
- [ ] **Validar formato de URI** (MySQL, MongoDB) antes de tentar conectar.
- [ ] **Validar `id_requisicao`** (formato, unicidade, não vazio).
- [ ] **Validar limites de paginação** (`page_size` máximo, `offset` não negativo).
- [ ] **Sanitizar nomes de tabelas/coleções** em queries SQL para evitar SQL injection (mesmo em queries internas).

### 8.7. Compatibilidade com Workflow Existente

- [ ] **Manter endpoint `/inteligencia-dados/query` funcionando** durante transição (deprecar depois).
- [ ] **Criar aliases/redirecionamentos** se necessário para não quebrar integrações existentes.
- [ ] **Documentar breaking changes** quando houver (ex.: mudança de formato de resposta).

### 8.8. Monitoramento e Métricas

- [ ] **Expor métricas** de uso de ID (número de capturas, análises, modelos criados por dia).
- [ ] **Expor métricas de performance** (tempo médio de cada agente, taxa de erro).
- [ ] **Alertas** para falhas recorrentes (ex.: muitos timeouts em conexões externas).
- [ ] **Dashboard interno** (opcional) para visualizar uso e saúde do subsistema ID.

### 8.9. Testes e Qualidade

- [ ] **Testes unitários** para cada classe/modelo (MySQLConnection, SchemaExtractor, etc.).
- [ ] **Testes de integração** para cada endpoint (captura, análise inicial, tratamento, etc.).
- [ ] **Testes de segurança** (SQL injection, validação de credenciais, isolamento de usuários).
- [ ] **Testes de performance** (tempo de resposta, uso de memória, escalabilidade).

### 8.10. Documentação Técnica

- [ ] **Documentar contratos de API** (OpenAPI/Swagger) para todos os endpoints de ID.
- [ ] **Documentar exemplos de uso** de cada agente (request/response).
- [ ] **Documentar limitações** (tamanho máximo de dataset, número máximo de modelos comparados, etc.).
- [ ] **Documentar troubleshooting** (erros comuns e soluções).

---

## 9. Resumo: Técnicas a Aplicar no Código MySQL Existente

### 9.1. Redução de Custos (aplicar em `mysql_connection.py`)

- [ ] **Limitar tamanho de resultados por padrão**: adicionar `LIMIT` automático em `execute_select()` se não especificado (ex.: máximo 10.000 linhas por padrão).
- [ ] **Usar `COUNT(*)` em vez de `SELECT *`** quando só precisar de contagem (método `execute_count()`).
- [ ] **Reusar conexões**: manter pool de conexões (já parcialmente implementado com SQLAlchemy, otimizar parâmetros).
- [ ] **Fechar conexões não utilizadas**: implementar `close()` e usar context managers.
- [ ] **Cache de metadados**: cachear resultados de `get_table_names()`, `get_column_info()` por database (TTL de 5 minutos).

### 9.2. Otimização de Velocidade (aplicar em `mysql_connection.py`)

- [ ] **Paginação obrigatória**: sempre usar `LIMIT` e `OFFSET` em consultas grandes.
- [ ] **Queries assíncronas**: considerar usar `asyncio` e driver assíncrono (ex.: `aiomysql`) para não bloquear event loop.
- [ ] **Timeout configurável**: evitar esperas infinitas (timeout de 30s por padrão, configurável).
- [ ] **Pool de conexões otimizado**: `pool_size=5`, `max_overflow=10`, `pool_recycle=3600` (reciclar conexões a cada hora).
- [ ] **Prepared statements**: usar `text()` com parâmetros nomeados quando possível (já usado parcialmente, expandir).

### 9.3. Segurança (aplicar em `mysql_connection.py` e `query_get_service.py`)

- [ ] **Validação rigorosa de nomes**: validar `database` e `table` em métodos que os recebem (apenas alfanuméricos e underscore).
- [ ] **Sanitização de SQL**: nunca concatenar strings diretamente em SQL, sempre usar parâmetros ou validação prévia.
- [ ] **Mascaramento de credenciais**: nunca logar `password` ou URI completa (já parcialmente implementado, reforçar).
- [ ] **Validação de hosts permitidos**: bloquear conexões para hosts internos não autorizados (ex.: `127.0.0.1`, `localhost`, IPs privados).
- [ ] **Rate limiting por conexão**: limitar número de queries por conexão/minuto (evitar abuso).
- [ ] **Validação de tamanho de resultado**: rejeitar resultados maiores que X MB (ex.: 100 MB) para evitar OOM.

### 9.4. Compressão e Paginação (aplicar em `query_get_database.py` e novos serviços)

- [ ] **Paginação em `fetch()`**: adicionar parâmetros `page` e `page_size` (padrão: `page_size=1000`).
- [ ] **Retornar metadados de paginação**: incluir `total_rows`, `page`, `page_size`, `total_pages` na resposta.
- [ ] **Compressão de resultados grandes**: se resultado > 1 MB, considerar comprimir antes de retornar (opcional, para frontend que suporte).

### 9.5. Isolamento e Rastreabilidade (aplicar em todos os serviços ID)

- [ ] **Associar `id_requisicao` a todas as operações**: passar `id_requisicao` para `MySQLConnection` e logar em todas as queries.
- [ ] **Associar `usuario` a todas as operações**: validar e associar `usuario` em todas as conexões e queries.
- [ ] **Isolar artefatos por usuário**: datasets, modelos e relatórios armazenados em diretórios separados por `usuario` e `id_requisicao`.

---

## 10. Próximos Passos Sugeridos (Atualizado)

1. **Fase 1 - Refatoração e Movimentação:**
   - [ ] Criar estrutura de pastas `ID/` com todos os serviços.
   - [ ] Mover e refatorar código existente (`mysql_connection.py`, `query_get_service.py`, etc.).
   - [ ] Adicionar paginação e melhorias de segurança no código movido.
   - [ ] Criar abstração de banco de dados (interface comum para MySQL e MongoDB).

2. **Fase 2 - Novo Agente de Captura:**
   - [ ] Implementar endpoint `/captura-dados` com suporte a MySQL e MongoDB.
   - [ ] Implementar detecção de tipo de base e extração de estrutura completa.
   - [ ] Implementar persistência de relatórios no MongoDB interno.
   - [ ] Testar com bases reais (pequenas e grandes).

3. **Fase 3 - Pipeline de Análise:**
   - [ ] Implementar agente `/analise-dados-inicial`.
   - [ ] Implementar agente `/tratamento-limpeza` com pipeline modular.
   - [ ] Implementar agente `/analise-estatistica` com geração de insights.
   - [ ] Testar pipeline completo end-to-end.

4. **Fase 4 - Machine Learning:**
   - [ ] Implementar agente `/criar-modelo-ml` com PyCaret.
   - [ ] Implementar limiar de qualidade (70% acurácia mínima).
   - [ ] Implementar persistência de modelos e metadados.
   - [ ] Testar com datasets reais de diferentes tipos (classificação, regressão).

5. **Fase 5 - Otimizações e Produção:**
   - [ ] Implementar cache de relatórios e datasets.
   - [ ] Implementar compressão (Parquet) e paginação em todos os endpoints.
   - [ ] Implementar execuções assíncronas para tarefas pesadas.
   - [ ] Implementar monitoramento e alertas.
   - [ ] Documentar completamente e fazer code review de segurança.

