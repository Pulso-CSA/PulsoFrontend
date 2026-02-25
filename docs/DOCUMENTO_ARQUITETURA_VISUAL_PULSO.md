# Arquitetura Visual PULSO — Direção Criativa Oficial

Documento de referência para UI/UX do ecossistema PULSO. Baseado nas imagens de inspiração autorizadas e nos princípios de Controle, Profundidade, Sofisticação e Inteligência Silenciosa.

---

## 0. Fonte Prioritária de Cores — App.png

**REGRA ABSOLUTA:** O arquivo `App.png` (logo oficial, ícone do atalho e barra de tarefas) é a **fonte prioritária** para a paleta de cores do ecossistema PULSO.

### Paleta extraída de App.png

| Token | Valor | Origem no logo |
|-------|-------|----------------|
| **Ciano/Turquesa** | `#00BEC8` | Metade esquerda da nuvem, arcos superiores, grade global |
| **Roxo institucional** | `#502878` / `#522A6F` | Metade direita da nuvem, transição dos arcos |
| **Azul-roxo** | `#6B4C9A` (variação) | Centro luminoso, nós da rede |
| **Grafite** | `#1A1A1A` / `#222023` | Contornos, elementos escuros, fundo |
| **Micro-luz** | Brilho sutil nas bordas | Nós da rede, bordas da nuvem |

### Gradiente principal (App.png)

- **Transição:** Ciano/verde-água (esquerda) → azul → roxo profundo (direita)
- **Aplicação:** Backgrounds inteligentes, cards, arcos luminosos
- **Regra:** Baixo contraste agressivo; transições longas e suaves

### Hierarquia de cores

1. **Primary:** Roxo institucional `#522A6F` — base de autoridade e sofisticação
2. **Accent:** Ciano/turquesa `#00BEC8` — destaques, CTAs, micro-luz
3. **Fundo:** Grafite/preto — espaço negativo, profundidade

---

## 1. Problemas Identificados

### 1.1 Dashboard
| Problema | Severidade | Descrição |
|----------|------------|-----------|
| Orbes genéricos | Alta | Blobs `blur-3xl animate-pulse` sem hierarquia; parecem decorativos, não estruturais |
| Cores inconsistentes | Alta | Primary cyan (180°), FinOps verde, DataAI roxo — não segue roxo institucional como base |
| Layouts sem identidade | Média | Grid/Compact/Bento não comunicam "sistema analítico" |
| Falta de espaço negativo | Média | Elementos competem por atenção; pouca respiração visual |

### 1.2 Chats (DataChat, FinOpsChat)
| Problema | Severidade | Descrição |
|----------|------------|-----------|
| Sensação de mensageiro | **Crítica** | Bolhas de chat, cores pastel, layout conversacional |
| Chat-user cyan/verde | Alta | Não transmite "operando sistema"; parece app popular |
| Falta de gradientes profundos | Alta | Fundos chapados; sem roxo → azul → grafite |
| Sem núcleos/arcos | Alta | Ausência de elementos estruturais luminosos |

### 1.3 Auth / ProfileSelection
| Problema | Severidade | Descrição |
|----------|------------|-----------|
| Orbes genéricos | Média | Mesmos blobs do Dashboard; sem identidade |
| Gradiente cyan/verde | Alta | Não alinhado à paleta roxo institucional |
| Card sem glass sutil | Média | Bordas sólidas; falta elevação discreta |

### 1.4 PromptPanel
| Problema | Severidade | Descrição |
|----------|------------|-----------|
| Neon-glow excessivo | Média | `neon-glow` em todos os cards; micro-luz direcional ausente |
| Chat interno genérico | Média | Mesmos problemas dos chats principais |
| Layout denso | Baixa | Muitos elementos visíveis; pouco espaço negativo |

### 1.5 LayerSelection
| Problema | Severidade | Descrição |
|----------|------------|-----------|
| Cores por camada | Média | Primary/Secondary/FinOps/DataAI — fragmenta identidade |
| Ícones grandes demais | Baixa | 40x40; poderia ser mais sutil |
| Sem arco/núcleo central | Média | Falta elemento estrutural de fundo |

### 1.6 Sistema de Temas
| Problema | Severidade | Descrição |
|----------|------------|-----------|
| Variantes não PULSO | **Crítica** | neon, classic, emerald, slate, fuchsia — não há Claro/Médio/Escuro |
| Sem roxo institucional | Alta | Nenhum tema usa roxo escuro como base |
| Paleta fragmentada | Alta | Cada variante tem cores diferentes; não há coesão |

---

## 2. Impacto Cognitivo

| Área | Impacto | Causa |
|------|---------|-------|
| **Carga cognitiva** | Alta | Muitas cores e estilos competindo; usuário não sabe onde focar |
| **Confiança** | Média | Interface "app popular" reduz percepção de autoridade técnica |
| **Foco** | Baixo | Falta de hierarquia e micro-luz direcional |
| **Memória de marca** | Baixa | Sem identidade visual coesa |

---

## 3. Layouts Propostos

### Layout A — Analítico / Denso
- **Dashboard:** Grid central com cards de métricas em destaque; sidebar de chats colapsável; dados em primeiro plano |
- **Chats:** Área de mensagens 70%; sidebar 30%; métricas em cards compactos acima do input |
- **Uso:** Usuários power users, análise intensiva |

### Layout B — Equilibrado / Modular
- **Dashboard:** Layout atual (Grid/Compact/Bento) com cards flutuantes e glass sutil |
- **Chats:** 50/50 ou 60/40; cards com bordas suaves e elevação discreta |
- **Uso:** Usuário padrão, equilíbrio entre informação e ação |

### Layout C — Minimalista / Decisório
- **Dashboard:** Um único foco por vez; espaço negativo amplo; CTAs com micro-luz |
- **Chats:** Área de mensagens ampla; input mínimo; sem sidebar lateral |
- **Uso:** Decisões rápidas, fluxos simples |

---

## 4. Temas PULSO

### Tema Claro
- **Background:** `#FAFAFA` → `#F5F5F5` (gradiente sutil)
- **Card:** `#FFFFFF` com borda `rgba(82, 42, 111, 0.12)`
- **Primary:** Roxo institucional `#522A6F` (App.png — metade direita da nuvem)
- **Accent:** Ciano/turquesa `#00BEC8` (App.png — metade esquerda da nuvem) para CTAs
- **Texto:** `#1A1A1A` (Noir Void)

### Tema Médio
- **Background:** `#1A1A1A` (Noir Void)
- **Card:** `#222023` (Wet Charcoal) com glass
- **Primary:** `#522A6F` (roxo institucional — App.png)
- **Accent:** `#00BEC8` (ciano — App.png)
- **Gradientes:** Ciano → azul → roxo → grafite (transição do App.png)

### Tema Escuro
- **Background:** `#0A0A0B` (preto profundo)
- **Card:** `#1A1A1A` com glass e borda sutil
- **Primary:** `#522A6F` (roxo institucional — App.png)
- **Accent:** `#00BEC8` (ciano — App.png)
- **Micro-luz:** Glow ciano/roxo em CTAs e estados ativos apenas

---

## 5. Paleta Fixa (Chats)

| Token | Valor | Uso |
|-------|-------|-----|
| `--chat-bg` | `#1A1A1A` | Fundo do container de chat |
| `--chat-user` | `#522A6F` (roxo institucional) | Bolhas do usuário |
| `--chat-system` | `#2D1B4E` (roxo mais escuro) | Respostas do sistema |
| `--chat-user-foreground` | `#FFFFFF` | Texto usuário |
| `--chat-system-foreground` | `#E8E0F0` | Texto sistema |

**Regra:** O chat deve parecer "Estou operando um sistema inteligente", não "Estou conversando num mensageiro".

---

## 6. Elementos Visuais Obrigatórios

### 6.1 Núcleos / Esferas / Semiesferas
- Orbes roxas luminosas com gradiente interno
- Arcos luminosos como background inteligente
- Uso: estruturais, não decorativos

### 6.2 Gradientes Profundos
- Transições longas: ciano → azul → roxo → grafite (conforme App.png)
- Baixo contraste agressivo
- Função: hierarquia, guia de foco

### 6.3 Espaço Negativo
- Grandes áreas escuras
- Poucos elementos ativos
- Regra: quanto mais importante, mais espaço

### 6.4 Micro-Luz Direcional
- Glow sutil apenas em: estados ativos, CTAs, foco atual
- Nunca difuso em todo o layout

### 6.5 Cards Flutuantes
- Bordas suaves (radius 0.75rem–1rem)
- Elevação discreta (shadow sutil)
- Glass sutil (backdrop-blur)

---

## 7. Justificativa UX + Psicologia

| Princípio | Aplicação |
|-----------|-----------|
| **Controle** | Hierarquia clara; micro-luz direcional guia o foco |
| **Profundidade** | Gradientes e camadas criam sensação de sistema em camadas |
| **Sofisticação** | Roxo institucional; sem roxo pastel ou lilás |
| **Autoridade técnica** | Interface minimalista; sem elementos decorativos |
| **Inteligência silenciosa** | Interface que não grita; informação respira |
| **Escalabilidade enterprise** | Modular; cards reutilizáveis |

---

## 8. Implementação Técnica

### 8.1 ThemeContext
- Trocar `ThemeVariant` de `neon|classic|emerald|slate|fuchsia` para `light|medium|dark`
- Manter `ThemeMode` apenas para compatibilidade (legado)
- Novas classes: `theme-pulso-light`, `theme-pulso-medium`, `theme-pulso-dark`

### 8.2 index.css
- Nova paleta `theme-pulso-*` com roxo institucional
- Variáveis `--chat-*` fixas para todos os chats
- Utilitários: `.pulso-card`, `.pulso-glow`, `.pulso-orb`

### 8.3 Componentes
- **DataChat / FinOpsChat:** `bg-chat-bg`, `chat-user` roxo institucional, cards com glass
- **Dashboard:** Orbes com gradiente roxo; remover cyan
- **Auth / ProfileSelection:** Card com glass; gradiente roxo sutil
- **LayerSelection:** Núcleo central opcional; cores unificadas em roxo
- **PromptPanel:** Reduzir neon-glow; micro-luz em inputs focados

---

## 9. Checklist de Validação

- [ ] Tema Claro aplicável em Auth, ProfileSelection, Dashboard
- [ ] Tema Médio (padrão) com roxo institucional em todos os chats
- [ ] Tema Escuro com fundo preto profundo
- [ ] Chats sem sensação de mensageiro
- [ ] Orbes/núcleos como elementos estruturais
- [ ] Micro-luz apenas em CTAs e estados ativos
- [ ] Cards com bordas suaves e glass sutil
- [ ] Espaço negativo em áreas críticas
