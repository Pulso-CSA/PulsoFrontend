# Análise: Melhorias do Frontend – Inteligência de Dados

Documento de análise baseado nas perguntas de teste, fluxos de uso e capturas de tela do chat ID. Foco em **experiência do usuário**, **apresentação visual** e **interatividade**.

---

## 1. Contexto das perguntas analisadas

| Tipo | Exemplos | O que o frontend deve exibir |
|------|----------|------------------------------|
| Análise estatística | "Faça uma análise gráfica e estatística... variáveis correlacionadas para churn" | Resumo estatístico, correlações, histogramas, dispersões |
| Treino de modelo | "Treine um modelo para prever churn" | Métricas, matriz de confusão, modelos comparados |
| Previsão | "Gere previsões de churn", "Quais clientes devem churnar?" | Previsões, amostras, distribuição Yes/No |
| Exploração | "Mostre distribuição de variável categórica" | Gráficos de contagem, metadados |

---

## 2. Problemas identificados

### 2.1 Estilo “markdown” e texto cru

**Situação atual:**
- Respostas em blocos de texto com listas e negrito (`**texto**`)
- "Gráficos disponíveis: distribuições, contagens e dispersões."
- "Previsões: 500 geradas. Amostra: Yes, No, Yes, No, Yes..."
- Vantagens e desvantagens em bullet points genéricos em todos os cards

**Impacto:** Interface parece documento, não dashboard interativo.

**Recomendação:** Substituir por componentes estruturados (cards, badges, tabelas) em vez de renderizar markdown cru.

---

### 2.2 Apresentação das métricas de ML

**Situação atual (treino):**
- Métricas em caixas simples (Precisão 86.7%, Recall 87.0%, F1 86.8%, Acurácia 87.0%)
- AUC em caixa separada (ex.: 19.7% – possível bug de exibição)
- Matriz de confusão em grade 2x2 numérica (345, 27, 38, 90)
- Legenda "TN | FP - FN | TP" (possível erro de formatação: `-` em vez de `|`)

**O que falta:**
- Hierarquia visual clara (modelo escolhido vs. demais)
- Barra de progresso ou indicador visual de “bom/ruim” para métricas
- Matriz de confusão como mapa de calor (cores por intensidade)
- Tooltips explicando TN, FP, FN, TP

---

### 2.3 Tabela de modelos comparados

**Situação atual:**
- Seção "Modelos comparados" às vezes vazia ou com tabela funcional
- Quando preenchida: colunas Modelo, Acurácia, AUC, Recall, Prec., F1, Kappa, MCC
- Modelo escolhido (Logistic Regression) destacado em azul

**Oportunidades:**
- Gráfico de barras horizontais comparando Acurácia ou F1
- Ordenação por coluna clicável
- Filtro por tipo de modelo
- Espaço à direita da tabela para gráficos complementares (ex.: importância de variáveis)

---

### 2.4 Gráficos exploratórios

**Situação atual:**
- Cards com histogramas (SeniorCitizen, tenure) e gráficos de contagem (Dependents, PhoneService)
- Dispersão SeniorCitizen vs tenure
- Carrossel "Gráfico 1 de 9" com setas e pontos
- Vantagens/desvantagens idênticas em todos os cards (genéricas)

**Problemas:**
- Gráficos estáticos, sem tooltip ao passar o mouse
- Listas de vantagens/desvantagens ocupam muito espaço e são repetitivas
- Transição entre gráficos sem animação
- Correlações (ex.: "Churn ↔ tenure: -0.381") em texto, não integradas ao gráfico

---

### 2.5 Respostas de previsão

**Situação atual:**
- "Geração de previsões de churn para o dataset disponível."
- Listas de dados disponíveis (médias, desvio padrão, etc.) em texto
- "Previsões: 500 geradas. Amostra: Yes, No, Yes, No, Yes..."
- Gráficos de distribuição de features, não de previsões

**O que falta:**
- Distribuição das previsões (quantos Yes vs No)
- Tabela ou lista paginada de exemplos (ID + previsão)
- Destaque para clientes com maior risco de churn
- Métricas do modelo usado (Accuracy, AUC) quando disponíveis

---

### 2.6 Análise estatística e correlações

**Situação atual:**
- Resumo em texto: "SeniorCitizen: média 0.1680, dp 0.37, Q3 0.00, assimetria 1.78"
- Correlações: "Churn ↔ tenure: -0.381 (moderada)"
- Gráficos de contagem e dispersão

**Oportunidades:**
- Cards por variável com métricas (média, dp, quartis) em layout visual
- Matriz de correlação como heatmap
- Correlações com Churn em ranking visual (barras ordenadas)

---

## 3. Recomendações priorizadas

### Alta prioridade

| Item | Ação |
|------|------|
| Remover dependência de markdown | Usar componentes estruturados para métricas, previsões e resumos |
| Exibir métricas em cards/grid | `modelo_ml.resultados` em cards com ícones e valores em destaque |
| Matriz de confusão visual | Heatmap ou grade colorida (TN, FP, FN, TP) com legenda clara |
| Garantir modelos comparados | Sempre exibir tabela quando `modelos_comparados` existir no payload |

### Média prioridade

| Item | Ação |
|------|------|
| Efeitos hover e transições | `hover:shadow-lg`, `transition`, leve `translateY` em cards |
| Skeleton/loading | Indicador durante treino (~90s) e previsão |
| Tooltips em gráficos | Valor exato ao passar o mouse em barras/pontos |
| Reduzir vantagens/desvantagens | Colapsar ou mostrar só em ícone "?" para evitar repetição |

### Baixa prioridade

| Item | Ação |
|------|------|
| Gráfico de importância de variáveis | Barras horizontais com `importancia_variaveis` |
| Distribuição de previsões | Pizza ou barras Yes vs No |
| Matriz de correlação | Heatmap quando houver dados de correlação |
| Navegação entre gráficos | Transição suave no carrossel |

---

## 4. Estrutura sugerida da bolha de resposta

```
┌─────────────────────────────────────────────────────────────┐
│ [Texto explicativo – sem markdown cru, parágrafos curtos]   │
├─────────────────────────────────────────────────────────────┤
│ ## Modelo treinado (quando aplicável)                       │
│ [Card: nome do modelo | badge de acurácia]                  │
│ [Grid 2x2 ou 4 colunas: Precisão | Recall | F1 | Acurácia]  │
│ [Matriz de confusão – heatmap 2x2 com TN, FP, FN, TP]       │
├─────────────────────────────────────────────────────────────┤
│ ## Modelos comparados                                       │
│ [Tabela com ordenação + destaque no modelo escolhido]       │
│ [Opcional: gráfico de barras comparando métricas]           │
├─────────────────────────────────────────────────────────────┤
│ ## Previsões (quando aplicável)                             │
│ [Badge: X previsões | Y Yes, Z No]                         │
│ [Tabela amostra ou lista com badges Yes/No]                 │
├─────────────────────────────────────────────────────────────┤
│ ## Gráficos                                                 │
│ [Carrossel com transição suave]                             │
│ [Cada card: gráfico + explicacao breve, vantagens colapsadas]│
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Checklist de validação (Frontend)

- [ ] Gráficos aparecem na mesma resposta (sem mensagem extra)
- [ ] Métricas de ML em cards, não em texto markdown
- [ ] Matriz de confusão com legenda TN | FP | FN | TP correta
- [ ] Tabela de modelos comparados sempre visível quando existir
- [ ] Carrossel/scroll para múltiplos gráficos
- [ ] Sem vazamento de prompt na resposta
- [ ] Labels legíveis ou truncadas com tooltip
- [ ] Loading/skeleton durante treino e previsão
- [ ] Efeitos hover e transições em cards
- [ ] Mensagem amigável quando banco indisponível
