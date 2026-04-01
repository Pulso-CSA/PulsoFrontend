# Análise: Impacto em percentual de tempo – Resumo prático

**Data da análise:** Com base nos logs de execução do correct workflow e no resumo prático de melhorias (velocidade + custo).

**Objetivo:** Estimar o impacto em **percentual de tempo total** do fluxo ao aplicar cada item do resumo prático. Os números são **orientativos** e assumem um run típico (projeto existente, ~10–18 arquivos, 4 arquivos no code plan).

---

## 1. Referência de tempo por etapa (um run típico)

Com base em logs reais (ex.: 08:30:02 a 08:36:01, com C4 ~2 min 30 s):

| Etapa | Tempo aprox. | % do total (ref.) |
|-------|----------------|-------------------|
| C1 – Governança | ~7 s | ~2% |
| C2 – Scanner | <1 s | ~0% |
| C2 – Plano de mudanças | ~20 s | ~6% |
| C2 – Estrutura aplicada | <1 s | ~0% |
| C2b – Code Plan | ~33 s | ~10% |
| C3 – Code Writer | ~5 s | ~1% |
| C4 – Code Implementer | ~150 s (2 min 30 s) | **~45%** |
| C5 – Venv + pip + teste | ~90 s (até falha) | **~27%** |
| Pipeline 12–13 (se executado) | variável | +50–100% se re-run completo |

**Total de referência (sem segunda rodada):** ~330 s (~5,5 min).  
**Total com segunda rodada completa (objetivo não atingido):** ~660 s (~11 min).

As percentagens abaixo usam esse total de referência (~330 s) como base.

---

## 2. Itens do resumo prático – impacto em % de tempo

Cada item é avaliado em **redução percentual do tempo total** do fluxo (ex.: “−10%” = o fluxo fica ~10% mais rápido na média).

| Prioridade | O que fazer | Impacto em tempo (% do total) | Observação |
|------------|-------------|-------------------------------|------------|
| **Alta** | Reduzir chamadas e tamanho de prompt no **Code Implementer** (agrupar, enxugar contexto). | **−15% a −25%** | C4 é ~45% do tempo. Menos chamadas (ex.: agrupar 2 arquivos) ou prompts menores reduzem tempo de C4 em ~1/3 a ~1/2 → ganho de 15–25% no total. |
| **Alta** | Evitar **segunda rodada completa** no pipeline 12–13 (limitar a 1 retry ou só C4 + testes). | **−30% a −50%** *quando há retry* | Se “objetivo não atingido” dispara re-run completo, o tempo praticamente dobra nesses casos. Restringir a uma re-execução só de C4 + testes reduz o tempo **dessa segunda rodada** em ~60–80%, logo no cenário “1 retry” o ganho sobre o total (primeira + segunda) é da ordem de 30–50%. Em runs que não entram em retry, impacto 0%. |
| **Alta** | Usar **modelo mais barato** em comprehension + governança (classificação, refino). | **~0%** | Mesmo número de chamadas; modelo mais barato não reduz tempo de resposta de forma relevante (pode até ser marginalmente mais rápido). **Impacto é em custo, não em tempo.** |
| **Média** | **Enxugar** system prompt do Code Plan e contexto do Plano de mudanças. | **−2% a −5%** | Menos tokens → respostas um pouco mais rápidas em C2 (~6%) e C2b (~10%). Proporção no total: 6%×0,3 + 10%×0,2 ≈ 2–5%. |
| **Média** | **Cache** de refino (e talvez de planos para o mesmo projeto/prompt). | **−1% a −3%** (quando cache acerta) | C1 refino é ~2% do total; quando o cache evita a chamada, ganha-se quase todo esse tempo. Em fluxos repetidos (mesmo prompt/projeto), impacto médio 1–3%. |
| **Baixa** | **Paralelizar** etapas independentes (ex.: chunks C2, arquivos C4). | **−10% a −20%** | C2: vários chunks em paralelo pode reduzir ~50% do tempo de C2 → −3% no total. C4: N arquivos em paralelo (ex.: 4) pode reduzir ~40–60% do tempo de C4 → −18% a −27% no total. Soma conservadora: −10% a −20%. |
| **Baixa** | Ajustar **venv/pip** (reusar venv ou imagem Docker) para C5. | **−20% a −27%** | C5 (venv + pip) é ~27% do tempo no run de referência. Reusar venv existente ou usar imagem Docker com deps prontas elimina a maior parte desse tempo → ganho de 20–27% no total. |

---

## 3. Síntese: impacto acumulado (ordem de grandeza)

Se **todas** as mudanças forem aplicadas:

- **Tempo:** reduções são parcialmente acumuláveis, mas com efeitos sobrepostos (ex.: menos chamadas em C4 já reduz tempo; paralelizar C4 reduz ainda mais). Estimativa **conservadora** de redução total: **−40% a −55%** no tempo do fluxo (ex.: de ~5,5 min para ~2,5–3,5 min no run típico).
- **Cenário com retry:** evitar segunda rodada completa traz o maior ganho nesses casos (**−30% a −50%** só nessa situação).
- **Custo:** modelo mais barato em comprehension + C1 refino (e opcionalmente em C2 chunks/consolidação) reduz custo por request; impacto em tempo é desprezível.

---

## 4. Tabela resumo (uma linha por item)

| # | Item (resumo prático) | Impacto em tempo (% total) | Impacto em custo |
|---|------------------------|-----------------------------|-------------------|
| 1 | Reduzir chamadas/prompt Code Implementer | −15% a −25% | Redução (menos tokens e menos chamadas) |
| 2 | Evitar segunda rodada completa (12–13) | −30% a −50% quando há retry | Grande redução quando há retry |
| 3 | Modelo mais barato (comprehension + governança) | ~0% | Redução relevante |
| 4 | Enxugar prompt Code Plan e contexto C2 | −2% a −5% | Redução (menos tokens) |
| 5 | Cache de refino (e planos) | −1% a −3% quando hit | Redução (menos chamadas) |
| 6 | Paralelizar (C2 chunks, C4 arquivos) | −10% a −20% | Neutro |
| 7 | Reusar venv / Docker para C5 | −20% a −27% | Neutro |

Nenhum código foi alterado nesta análise; o documento serve como referência para priorização e medição futura (métricas reais de tempo por etapa).
