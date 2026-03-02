# Identidade visual — Pulso

Referência única da marca, cores, tipografia e temas do app **Pulso** / **Pulso Tech**.  
Definições vivem em `src/index.css` e `tailwind.config.ts`.

---

## 1. Marca

| Item | Valor |
|------|--------|
| **Nome** | Pulso / Pulso Tech |
| **Logo** | `App.png` (usado em header, auth, installer; roxo→ciano conforme arte) |
| **Favicon** | `public/favicon.ico` |

---

## 2. Paletas de cor

### 2.1 Paleta base Pulso (degradê / design tokens)

| Token | Hex | Uso |
|-------|-----|-----|
| `--pulso-bg-dark` | `#222023` | Fundo escuro base |
| `--pulso-purple-deep` | `#420d95` | Roxo profundo |
| `--pulso-purple` | `#a54bce` | Roxo principal |
| `--pulso-cyan` | `#60bcd5` | Ciano |
| `--pulso-teal` | `#1897a0` | Teal |
| `--pulso-gray` | `#4d4d4d` | Cinza neutro |

### 2.2 Space-Neon / Aurora (extraídos do logo App.png)

| Token | Hex | Uso |
|-------|-----|-----|
| `--pulso-near-black` | `#08051D` | Quase preto |
| `--pulso-near-black-2` | `#090521` | |
| `--pulso-near-black-3` | `#0B0526` | |
| `--pulso-indigo-deep` | `#160E5B` / `#1C1259` / `#281651` | Índigo |
| `--pulso-purple-neon` | `#905DED` / `#925DF1` | Roxo neon |
| `--pulso-cyan-neon` | `#4F9FF3` / `#60AACE` / `#2599A5` | Ciano neon |
| `--pulso-magenta-aurora` | `#A74FD8` | Magenta aurora |
| `--pulso-gray-frost` | `#4C4C4C` / `#5D5D5E` / `#545468` | Cinza frost |

---

## 3. Cores semânticas (HSL, por tema)

Todas as cores do design system são **HSL** via variáveis CSS. Cada tema define:

- **background / foreground** — fundo e texto principal  
- **card / popover** — superfícies elevadas  
- **primary** (DEFAULT, deep, light) — cor principal (cyan/teal no default)  
- **secondary** — complementar  
- **accent** — destaque interativo  
- **muted** — fundos e textos secundários  
- **success / warning / destructive / info** — feedback  
- **finops** — FinOps  
- **data-ai** — Data & AI  
- **border / input / ring** — bordas e foco  
- **chat-user / chat-system** — mensagens do chat  

**Default (tema escuro luxo):**

- Primary: `178 92% 52%` (ciano)
- Secondary: `178 55% 48%`
- Ring: `178 95% 48%`

---

## 4. Temas disponíveis

| Classe / Nome | Descrição |
|----------------|-----------|
| `:root` | Default — escuro luxo/corporativo, cyan principal |
| `theme-neon` | Neon — cyan perguntas, roxo respostas, WCAG AA |
| `theme-classic` | Clássico — editorial, preto/branco refinado |
| `theme-emerald` | Emerald — verde corporativo, sustentável |
| `theme-slate` | Slate Pro — azul slate, corporativo premium |
| `theme-pulso-light` | Pulso claro — contraste suave, paleta harmoniosa |
| `theme-pulso-medium` | Pulso médio — escuro intermediário |
| `theme-pulso-dark` | Pulso escuro — fundos profundos, space-neon |
| `theme-fuchsia` | Fuchsia — luxo jewel, magenta + azul |

Temas Pulso oficiais no app: **light**, **medium**, **dark** (controlados por `ThemeContext` → `theme-pulso-*`).

---

## 5. Tipografia

| Uso | Família | Fallbacks |
|-----|---------|------------|
| **Sans** | Inter | Segoe UI, system-ui, sans-serif |
| **Mono** | JetBrains Mono | Fira Code, Consolas, monospace |

**Tamanhos (CSS):**

- `--text-body`: 15px  
- `--text-sm`: 13px  
- `--text-xs`: 12px  
- `--text-chart`: 13px  
- `--leading-relaxed`: 1.625  

**Body:** `font-size: var(--text-body)`, `line-height: 1.6`, `letter-spacing: 0.01em`, antialiased.

---

## 6. Espaçamento e forma

| Token | Valor | Uso |
|-------|--------|-----|
| `--radius` | `0.75rem` (default) | Bordas gerais (varia por tema: 0.5rem–0.75rem) |
| `--pulso-radius-sm` | 16px | Space-neon |
| `--pulso-radius-md` | 20px | |
| `--pulso-radius-lg` | 24px | |
| `--pulso-blur-sm/md/lg` | 12px / 16px / 24px | Blur glass |

---

## 7. Efeitos e utilitários

- **Glass (padrão Pulso):** `--glass-bg`, inset shadows (escuro + luz cyan), `backdrop-filter: blur(24px)`. Classes: `.glass`, `.glass-strong`, `.glass-hover`.
- **Glass card (space-neon):** `.glass-card` — borda branca 12%, blur 18px, sombra roxa.
- **Neon:** `.neon-glow`, `.neon-glow-strong`, `.neon-text`, `.neon-glow-finops` (sombras com `--glow-primary` / `--glow-finops`).
- **Fundos:** `.bg-space` (radial + vinheta); `.bg-space-if-dark` para temas escuros Pulso.
- **Orbes:** `.pulso-orb`, `.pulso-orb-sm` (radial gradient + blur).
- **CTA aurora:** `.btn-aurora` — gradiente magenta → roxo → ciano, borda sutil, sombra roxa.
- **Card glow:** `.card-bottom-glow` — faixa luminosa inferior (roxo→ciano).
- **Carousel:** `.carousel-glow-card` — sombras roxo/índigo.

---

## 8. Animações (Tailwind + CSS)

- `slide-up`, `slide-down`, `fade-in`, `scale-in`  
- `float`, `glow-pulse`, `typing-bounce`  
- `fluid-fade`, `service-transition`, `shimmer`, `soft-glow`  
- Duração fluida: `duration-fluid` (400ms), `ease-fluid` (cubic-bezier 0.4, 0, 0.2, 1)

---

## 9. Scrollbars

- Largura 8px, thumb em `primary` (50% / 70% / 100% em hover/active), track em `muted`.

---

## 10. Onde está no código

| O quê | Onde |
|-------|------|
| Variáveis de tema (HSL, tokens Pulso) | `src/index.css` — `@layer base`, `:root` e `.theme-*` |
| Cores Tailwind (primary, accent, etc.) | `tailwind.config.ts` — `theme.extend.colors` |
| Fontes | `tailwind.config.ts` — `fontFamily`; `index.css` — `--font-sans`, `--font-mono` |
| Glass, neon, space, aurora | `src/index.css` — `@layer utilities` e keyframes |
| Logo | `public/App.png`; uso: `import.meta.env.BASE_URL + "App.png"` |

---

*Documento gerado a partir do design system do repositório PulsoFrontend.*
