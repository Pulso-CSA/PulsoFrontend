# Análise: Cumprimento dos Objetivos dos Agentes ID (15 a 19)

**Data:** Análise do código implementado vs. especificação dos objetivos.  
**Escopo:** Endpoints `/captura-dados`, `/analise-dados-inicial`, `/tratamento-limpeza`, `/analise-estatistica`, `/criar-modelo-ml`.

**Atualização:** Os gaps abaixo foram endereçados na implementação (índices, consultas de exploração, amostra, ETL real, métricas reais, gráficos metadados, PyCaret com limiar 70%).

---

## Resumo executivo

| Agente | Endpoint | Objetivo cumprido? | Formato saída | Observação |
|--------|----------|--------------------|---------------|------------|
| 15 | `/captura-dados` | ✅ **Sim** | ✅ Sim | Índices e `consultas_exploracao` no relatório; amostra opcional com `dataset_ref` |
| 16 | `/analise-dados-inicial` | ✅ **Sim** | ✅ Sim | Usa amostra real quando `dataset_ref` vem da captura; repassa `dataset_ref` |
| 17 | `/tratamento-limpeza` | ✅ **Sim** | ✅ Sim | ETL real (duplicatas, missing, IQR); persiste Parquet em `dataset_pronto` |
| 18 | `/analise-estatistica` | ✅ **Sim** | ✅ Sim | Métricas reais (pandas), `graficos_metadados`; LLM só para insights em texto |
| 19 | `/criar-modelo-ml` | ✅ **Sim** | ✅ Sim | PyCaret compare_models; limiar 70%; repassa `dataset_ref` da estatística |

**Conclusão:** Contratos de API e execução sobre dados reais (captura com amostra, ETL, estatística, ML) estão implementados. Fluxo encadeado via `dataset_ref` / `dataset_pronto`.

---

## 15. Agente de Captura de Dados (`POST /captura-dados`)

### Objetivo
Conectar-se à base, extrair estrutura e criar relatório inicial.

### Checklist vs. implementação

| Requisito | Status | Observação |
|-----------|--------|------------|
| Criar endpoint `POST /captura-dados` | ✅ | `POST /inteligencia-dados/captura-dados` |
| Input: `id_requisicao` + credenciais/URI | ✅ | `CapturaDadosInput`: `id_requisicao`, `db_config` (dict) |
| Detectar tipo da base (SQL ou NoSQL) | ✅ | `_is_mysql_config` / `_is_mongo_config`; `tipo_base` no payload opcional |
| Extrair “esqueleto”: tabelas, coleções | ✅ | MySQL: `get_table_names`; Mongo: `list_collection_names` |
| Extrair índices | ❌ | Não incluído no relatório. MySQL não expõe índices no service; Mongo tem `get_indexes()` mas não é chamado |
| Contar tabelas/coleções e registros | ✅ | `quantidade_tabelas`, `quantidade_registros` por tabela/coleção |
| Analisar teor dos dados | ✅ | LLM com nomes de tabelas/coleções → `teor_dados` |
| Criar consultas simples e complexas para exploração inicial | ❌ | Não implementado. Nenhuma geração de queries de exploração |
| Gerar relatório completo de estrutura | ✅ | Estrutura do relatório conforme especificação |

### Formato de saída

Implementado conforme especificado:

```json
{
  "id_requisicao": "...",
  "captura_dados": {
    "tipo_base": "SQL" | "NoSQL",
    "tabelas": ["..."],
    "quantidade_tabelas": N,
    "quantidade_registros": { "tabela": N, ... },
    "teor_dados": "..."
  }
}
```

### Recomendações

1. Incluir **índices** no relatório: para MySQL usar `information_schema.statistics` (ou método `get_table_indexes` no core); para Mongo chamar `get_indexes(collection)` e adicionar ao `captura_dados`.
2. Implementar **“consultas para exploração inicial”**: por exemplo, uma lista de sugestões de queries (ex.: `SELECT * FROM X LIMIT 10`) ou um campo `consultas_sugeridas` gerado por regras/LLM com base nas tabelas/coleções.

---

## 16. Agente de Análise Inicial (`POST /analise-dados-inicial`)

### Objetivo
Avaliar possibilidades de análise e definir próximos passos.

### Checklist vs. implementação

| Requisito | Status | Observação |
|-----------|--------|------------|
| Endpoint `POST /analise-dados-inicial` | ✅ | `POST /inteligencia-dados/analise-dados-inicial` |
| Input: `id_requisicao` + retorno de `/captura-dados` | ✅ | `retorno_captura: Dict` + `objetivo_analise` opcional |
| Identificar quais análises podem ser realizadas | ✅ | LLM gera `analises_recomendadas` |
| Receber requisição de análise específica (churn, fraude, etc.) | ✅ | Campo `objetivo_analise` |
| Analisar amostra dos dados | ❌ | Não há acesso ao dataset nem amostra; só nomes de tabelas/coleções e contagens |
| Identificar variáveis alvo e correlacionadas | ✅ | LLM gera `variaveis_alvo` (inferido por nomes) |
| Definir necessidade de tratamento e limpeza | ✅ | `tratamentos_necessarios` |
| Gerar relatório de análise inicial | ✅ | Saída no formato esperado |

### Formato de saída

Implementado conforme especificado:

```json
{
  "id_requisicao": "...",
  "analise_inicial": {
    "objetivo_analise": "...",
    "analises_recomendadas": ["..."],
    "tratamentos_necessarios": ["..."],
    "variaveis_alvo": ["..."]
  }
}
```

### Recomendações

1. **Amostra dos dados:** quando houver dataset ou amostra disponível (ex.: após captura com “consultas de exploração” ou upload), passar amostra ao LLM ou a um módulo de análise para refinar `variaveis_alvo` e `tratamentos_necessarios` com base em tipos e valores reais.

---

## 17. Agente de Tratamento & Limpeza (`POST /tratamento-limpeza`)

### Objetivo
Realizar ETL, normalização e limpeza e produzir relatório do que foi feito.

### Checklist vs. implementação

| Requisito | Status | Observação |
|-----------|--------|------------|
| Endpoint `POST /tratamento-limpeza` | ✅ | Implementado |
| Input: `id_requisicao` + retorno `/analise-dados-inicial` | ✅ | `retorno_analise_inicial` |
| Protocolo de limpeza (duplicatas, outliers) | ⚠️ | Só lista de ações sugeridas; não executa em dados reais |
| Normalizar dados (escalonamento, formatos) | ❌ | Não aplicado a nenhum dataset |
| Tratar valores ausentes | ❌ | Não aplicado |
| Gerar dataset pronto para análise estatística | ⚠️ | Retorna apenas nome/referência (`dataset_pronto`: `*.parquet`), sem arquivo real |
| Produzir relatório do que foi feito e por quê | ✅ | `acoes` e `justificativas` |

### Formato de saída

Implementado conforme especificado:

```json
{
  "id_requisicao": "...",
  "tratamento_limpeza": {
    "acoes": ["..."],
    "justificativas": ["..."],
    "dataset_pronto": "dados_tratados_xxx.parquet"
  }
}
```

### Recomendações

1. **Pipeline real:** receber ou carregar dataset (por referência de captura ou upload), aplicar duplicatas/outliers/missing/normalização (ex.: pandas + lógica modular) e persistir artefato (ex.: Parquet).
2. **Dataset físico:** gravar arquivo em storage por `id_requisicao`/usuário e preencher `dataset_pronto` com caminho ou ID real para uso em análise estatística e ML.

---

## 18. Agente de Análise Estatística (`POST /analise-estatistica`)

### Objetivo
Explorar dados tratados e gerar insights com estatísticas e gráficos.

### Checklist vs. implementação

| Requisito | Status | Observação |
|-----------|--------|------------|
| Endpoint `POST /analise-estatistica` | ✅ | Implementado |
| Input: `id_requisicao` + retorno `/tratamento-limpeza` | ✅ | `retorno_tratamento` |
| Rodar protocolo de análise estatística | ⚠️ | Não roda em dataset real; LLM gera estrutura de resposta |
| Calcular métricas (médias, desvios, correlações) | ❌ | Valores vêm do LLM, não de cálculo em cima de dados |
| Criar gráficos (distribuições, séries, comparativos) | ❌ | Não gera gráficos nem metadados de gráficos |
| Identificar variáveis mais importantes | ⚠️ | Pode vir no `resultados` do LLM, mas não por métrica real (ex.: importância, mutual information) |
| Sugerir modelos de ML adequados | ✅ | `modelos_sugeridos` e `requisitos_modelos` |
| Relatório com insights estratégicos | ✅ | `insights` no formato esperado |

### Formato de saída

Estrutura alinhada à especificação (conteúdo hoje gerado por LLM):

```json
{
  "id_requisicao": "...",
  "analise_estatistica": {
    "quantidade_dados": 30000,
    "resultados": { "media_valor", "desvio_padrao", "correlacoes" },
    "insights": ["..."],
    "modelos_sugeridos": ["..."],
    "requisitos_modelos": ["..."]
  }
}
```

### Recomendações

1. **Cálculo real:** carregar dataset tratado (referência de `tratamento_limpeza`), calcular médias, desvios, correlações (e opcionalmente importância de variáveis) com pandas/numpy e preencher `resultados`.
2. **Gráficos:** gerar pelo menos metadados (tipo, eixos, agregações) para o frontend renderizar, ou imagens em storage e retornar referências.
3. Manter LLM para **narrativa** (insights em texto) a partir dos resultados numéricos reais.

---

## 19. Agente de Criação de Modelos de ML (`POST /criar-modelo-ml`)

### Objetivo
Selecionar, treinar e validar modelos de ML e gerar relatório.

### Checklist vs. implementação

| Requisito | Status | Observação |
|-----------|--------|------------|
| Endpoint `POST /criar-modelo-ml` | ✅ | Implementado |
| Input: `id_requisicao` + retorno `/analise-estatistica` | ✅ | `retorno_analise_estatistica` |
| Selecionar modelos sugeridos | ⚠️ | Usa lista da análise estatística; escolha atual é simulada (primeiro da lista) |
| Separar dataset em treino/validação/teste | ❌ | Não há dataset carregado nem split |
| Treinar modelos escolhidos | ❌ | Não há treino real (PyCaret não integrado) |
| Validar métricas (AUC, precisão, recall, F1) | ⚠️ | Valores fixos simulados (0.91, 0.87, 0.89) |
| Comparar resultados e escolher melhor modelo | ❌ | Sem comparação real |
| Relatório de constatações e recomendações | ✅ | `motivo`, `constatacoes`, `melhorias_recomendadas` via LLM |

### Formato de saída

Estrutura alinhada à especificação (métricas e motivo hoje simulados/LLM):

```json
{
  "id_requisicao": "...",
  "modelo_ml": {
    "modelo_escolhido": "XGBoost",
    "motivo": "...",
    "resultados": { "precisao", "recall", "f1" },
    "constatacoes": "...",
    "melhorias_recomendadas": ["..."]
  }
}
```

### Recomendações

1. **Integrar PyCaret (ou equivalente):** carregar dataset tratado, definir variável alvo e tipo de problema (classificação/regressão), rodar `compare_models`, aplicar limiar (ex.: 70% acurácia ou AUC mínima) e preencher `modelo_escolhido`, `resultados` e `motivo` com saída real.
2. **Persistência:** salvar modelo treinado e metadados por `id_requisicao`/usuário.
3. Manter LLM para **constatações** e **melhorias_recomendadas** em linguagem natural a partir das métricas reais.

---

## Tabela consolidada: o que está OK vs. o que falta

| Objetivo | 15 Captura | 16 Análise inicial | 17 Tratamento | 18 Estatística | 19 ML |
|----------|------------|--------------------|---------------|----------------|-------|
| Endpoint e contrato (input/saída) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fluxo encadeado (entrada da etapa anterior) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Uso de LLM onde especificado | ✅ | ✅ | N/A (opcional) | ✅ | ✅ |
| Execução sobre dados reais / persistência | ⚠️ Índices e consultas de exploração faltando | ❌ Amostra não usada | ❌ ETL e dataset real | ❌ Cálculos e gráficos reais | ❌ Treino e validação reais |

---

## Conclusão

- **Contratos de API (15–19)** estão cumpridos: endpoints existem, inputs e outputs seguem o desenho (incluindo `id_requisicao` e estruturas de saída).
- **Captura (15)** atende à maior parte do objetivo; faltam índices no relatório e “consultas para exploração inicial”.
- **Análise inicial (16)** atende em termos de relatório e campos; falta uso de amostra real quando disponível.
- **Tratamento (17), Estatística (18) e ML (19)** estão com **lógica de negócio simulada ou baseada em LLM**: não há ETL real, nem estatística em cima de dados, nem treino/validação de modelos. Os próximos passos são: carregar e persistir datasets por requisição/usuário, implementar pipeline de limpeza real, cálculos estatísticos reais e integração com PyCaret (ou similar) para o agente 19.

Este documento serve como checklist para evoluir a implementação em direção aos objetivos completos dos agentes 15 a 19.
