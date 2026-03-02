# Tela HTTPS para download da ferramenta Pulso

Especificação **extremamente detalhada** da landing page pública em HTTPS cujo único objetivo é permitir o download seguro do instalador do Pulso (desktop). A página reutiliza os elementos predominantes da pasta `docs` e a identidade visual do app.

---

## 1. Objetivo e contexto

| Item | Especificação |
|------|----------------|
| **Objetivo** | Página pública, servida via **HTTPS**, para o usuário baixar o instalador do Pulso (Windows). |
| **URL sugerida** | `https://pulso.tech/download` ou `https://app.pulso.tech/download` (ou equivalente no deploy). No app React com HashRouter: `/#/download`. |
| **Público** | Visitante que chegou por link (email, anúncio, site) e quer apenas baixar o app. |
| **Ação principal** | Um único CTA dominante: **Baixar Pulso para Windows** → inicia download do `.exe` (ou redireciona para URL do instalador). |
| **Segurança** | Toda a página e o link de download devem ser servidos exclusivamente por HTTPS. |

---

## 2. Estrutura geral da página

A página é **single-page**, com scroll vertical, em ordem:

1. **Header** (sticky)
2. **Hero** (logo + título + subtítulo + CTA principal de download)
3. **Seção “Por que baixar?”** (3 cards em grid)
4. **Seção “Recursos”** (card tipo Performance Analytics + lista)
5. **Seção “Comece agora”** (CTA secundário + botão padrão gradient)
6. **Footer** (links mínimos: Documentação, Suporte, Termos)

Não há sidebar. Conteúdo centralizado em container `max-w-[1400px]` ou equivalente.

---

## 3. Identidade visual obrigatória

- **Tema:** Usar tema Pulso escuro (ex.: `theme-pulso-dark` ou `:root` default). Fundo com profundidade: `bg-space` ou gradiente conforme `index.css` (`.theme-pulso-dark body`).
- **Cores:** Primary cyan/teal (`hsl(var(--primary))`), secondary roxo, accent. Texto em `foreground`, secundário em `muted-foreground`.
- **Superfícies:** Cards e header com efeito **Elemento 23 — Glass padrão**: `.glass` no header, `.glass` ou `.glass-strong` nos cards (ver `docs/glass-padrao.md`).
- **CTA principal:** Estilo **Elemento 24 — Botão Download** (Docs + Download) e/ou **Elemento 12 — Get Started** (gradiente + glow) e/ou classe `.btn-aurora` (gradiente aurora magenta→roxo→ciano) do `index.css`.
- **CTA secundário:** **Elemento 22 — Botão Padrão (Gradient Border)** (`.btn-padrao-gradient`), ver `docs/botao7.md`.
- **Tipografia:** `font-sans` (Inter), tamanhos `text-body`, títulos em `text-2xl`/`text-3xl`/`text-4xl`, `font-bold` ou `font-semibold`.
- **Radius:** `var(--radius)` (0.75rem) ou `rounded-xl` / `rounded-2xl` para cards.
- **Efeitos:** Opcionalmente `.pulso-orb` ou `.pulso-orb-sm` no hero; `.neon-glow` ou `.pulso-glow` no botão principal; `.card-bottom-glow` em um card de destaque.

---

## 4. Header (sticky)

- **Comportamento:** `sticky top-0 z-40`, com `sticky-below-electron` se estiver dentro do Electron (ver `index.css`).
- **Estilo:** `glass-strong border-b border-border` — igual ao da `Index.tsx` (Elemento 23).
- **Conteúdo (esquerda → direita):**
  - **Logo:** `<img src="{BASE_URL}App.png" alt="Pulso" />` — altura ~40px (ex.: `h-10 w-10`).
  - **Nome:** texto “Pulso Tech” ao lado do logo, `text-lg font-semibold text-foreground`.
  - **Direita:** 
    - Link “Entrar” (navega para `/#/auth`) usando **Elemento 22** ou `Button` com classe `btn-aurora` (como em `Index.tsx`).
- **Acessibilidade:** Incluir `aria-label` no logo e no botão Entrar. Skip link já existe no App (pular para conteúdo).

**Referência de código:** `src/pages/Index.tsx` linhas 16–38 (header com glass-strong e btn-aurora).

---

## 5. Hero

- **Container:** `max-w-4xl mx-auto px-6 py-16 sm:py-24 text-center`.
- **Fundo (opcional):** Uma orbe decorativa com `.pulso-orb` ou `.pulso-orb-sm` atrás do conteúdo (z-index baixo), ou loader decorativo em fundo (Elemento 01 — Loader Anel) com `showcase-loader1-bg` em modo sutil (apenas visual, sem texto “loading”).
- **Conteúdo em ordem:**
  1. **Logo:** mesma `App.png`, altura maior (ex.: `h-20 w-20` ou `h-24 w-24`), `object-contain`.
  2. **Título H1:** “Baixe o Pulso” ou “Pulso para Windows” — `text-4xl sm:text-5xl font-bold text-foreground` (pode usar gradiente com `primary`/`secondary` e `bg-clip-text text-transparent` como na página Error).
  3. **Subtítulo:** Uma linha, ex.: “Assistente de código e dados na sua máquina. Rápido, seguro e offline quando precisar.” — `text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mt-4`.
  4. **CTA principal:** 
     - **Componente:** Botão que ao clicar inicia o download (ou abre a URL do instalador em nova aba). 
     - **Visual:** Usar o **Elemento 24 — Botão Download** (`DownloadReportButton` ou equivalente) com texto “Baixar Pulso” (em vez de “Baixar Relatório”). Classes: `showcase-download-report-btn`; no hover, área “Docs” sobe e revela ícone de download com animação (ver `docs/download-button.md`). 
     - **Alternativa ou complemento:** Um botão **Elemento 12 — Get Started** (“Baixar para Windows”) com wrapper de glow (gradiente indigo/pink/amarelo adaptado para Pulso: primary/secondary) e seta, como na seção “Botões e Cards” da `Index.tsx`.
  5. **Texto de segurança:** Abaixo do botão, em `text-sm text-muted-foreground`: “Download via HTTPS. Windows 10/11. Verifique a origem antes de instalar.”

**Referências:** `docs/download-button.md`, `docs/loader1.md`, `src/pages/Auth.tsx` (logo + título “Pulso”), `src/pages/Error.tsx` (gradiente no título).

---

## 6. Seção “Por que baixar?” (3 cards)

- **Título da seção:** “Por que baixar?” — `text-2xl font-bold text-foreground mb-8`.
- **Layout:** Grid 3 colunas em desktop (`grid-cols-1 md:grid-cols-3 gap-6`), cards com **Elemento 23 (Glass)** e borda: `glass rounded-xl border border-border p-6`.
- **Conteúdo de cada card (sugestão):**
  - **Card 1:** Ícone (ex.: Shield ou Lock), título “Seguro”, texto curto: “Conexão HTTPS e controle dos seus dados.”
  - **Card 2:** Ícone (ex.: Zap), título “Rápido”, texto: “Roda local. Menos latência, mais produtividade.”
  - **Card 3:** Ícone (ex.: Code ou Workflow), título “Feito para devs”, texto: “Pulso CSA, FinOps e Data & AI no mesmo lugar.”
- **Estilo dos cards:** Título `text-lg font-semibold text-foreground`, corpo `text-sm text-muted-foreground`. Ícone em `text-primary` ou em uma caixa com `bg-primary/10 rounded-lg p-2`.

Opcional: um dos cards pode usar **Elemento 14 — Card Performance Analytics** (estilo compacto com badge “Recomendado” e métrica simbólica) em vez de apenas ícone + texto; ver `docs/card2.md`.

---

## 7. Seção “Recursos” (card Analytics + lista)

- **Título:** “O que você tem no Pulso” — `text-2xl font-bold text-foreground mb-8`.
- **Layout:** Um card grande à esquerda (ou em cima no mobile), lista à direita (ou abaixo).
- **Card grande:** Estilo **Elemento 14 — Card Performance Analytics** (`docs/card2.md`): fundo escuro, borda, ícone em gradiente (usar cores Pulso: primary/secondary), título “Recursos incluídos”, badge “Incluído”, 2 “métricas” (ex.: “Chats assistidos” e “Integrações”), área de “gráfico” mínima ou texto “Pulso CSA, FinOps, Data & AI”, e botão “Ver detalhes” (link para documentação ou `/#/auth`). Usar classes existentes do showcase (Performance Analytics) ou `.glass` + estrutura interna semelhante.
- **Lista:** Lista com ícones (check ou ícone primary) com itens: “Pulso CSA (estrutura de projeto)”, “FinOps (custos cloud)”, “Data & AI (métricas e ML)”, “Temas claro/escuro”, “Atualizações automáticas”. Estilo: `flex items-center gap-3 text-foreground` com ícone `text-primary`.

---

## 8. Seção “Comece agora” (CTA secundário)

- **Container:** `text-center py-12 px-6`.
- **Texto:** “Já tem conta? Entre e acesse o dashboard.” ou “Use na web ou baixe para desktop.”
- **Botões (lado a lado ou empilhados no mobile):**
  - **Primário:** Link “Entrar” → `/#/auth`, usando **Elemento 12 — Get Started** (gradiente + glow) ou `btn-aurora`. Texto: “Entrar”.
  - **Secundário:** **Elemento 22 — Botão Padrão (Gradient Border)** (ver `docs/botao7.md`), texto “Documentação”, link para docs ou site. Classe: `btn-padrao-gradient` (gradiente azul→rosa; no app pode ser adaptado para primary→secondary com variáveis CSS).

---

## 9. Barra de busca (opcional — Elemento 21)

- Se a página tiver conteúdo longo ou links múltiplos, incluir **Elemento 21 — Barra de Busca Padrão (Cosmic)** (`docs/searchbar-padrao.md`) em uma posição discreta (ex.: abaixo do hero ou no header colapsado em mobile).
- Placeholder sugerido: “Buscar na página...” ou “Explore o Pulso...”.
- Implementação: usar `CosmicSearchInput` com `variant="pulso"` se existir, ou a estrutura HTML/CSS do searchbar cósmico (galaxy, nebula, starfield, cosmic-ring, input, ícones lupa e wormhole). Cores adaptadas para `primary`/`secondary` (ciano/roxo).

---

## 10. Cards adicionais (Elementos 13 e 17)

- **Elemento 13 — Card Menu** (`docs/card1.md`): Pode ser usado no footer ou em uma coluna “Ações rápidas”: itens “Documentação”, “Suporte”, “Termos de uso”, “Entrar”, com ícones e hover em primary (e delete em vermelho apenas para “Excluir conta” se aplicável; na landing não é necessário). Classe: `showcase-menu-card` com lista e separadores.
- **Elemento 17 — Card Pricing** (`docs/card5.md`): Opcional — um card “Starter” ou “Grátis para começar” com preço “R$ 0” e botão “Baixar”, para reforçar que o download é gratuito. Estilo do card conforme showcase (título, descrição, preço, botão).

---

## 11. Loaders (Elementos 01–06)

- **Durante o download:** Ao clicar em “Baixar Pulso”, opcionalmente mostrar overlay com **Elemento 01 — Loader Anel** (`.showcase-loader1-bg` + `.showcase-loader1`) ou **Elemento 03 — Loader Liquid** com texto “Preparando download...” até o navegador iniciar o download. Depois o overlay some.
- **Decoração no hero:** Loader 01 em modo background (sem texto, apenas anel rotativo em gradiente) atrás do título, como em `docs/loader1.md`, para reforçar identidade.

---

## 12. Footer

- **Estilo:** Borda superior `border-t border-border`, fundo `bg-card/50` ou `glass`, padding `py-6 px-6`.
- **Conteúdo:** Logo pequeno + “Pulso Tech”, links: “Documentação”, “Suporte”, “Termos de uso”, “Privacidade”. Separadores entre links. Ano e “© Pulso Tech”. Tudo em `text-sm text-muted-foreground`; links com `hover:text-primary`.

---

## 13. Comportamento do botão de download

- **Fonte da URL:** A URL do instalador deve vir de variável de ambiente (ex.: `VITE_DOWNLOAD_URL`) ou de API/backend (ex.: `VersionGate` ou config) para não hardcodar em código. Exemplo: `const downloadUrl = import.meta.env.VITE_DOWNLOAD_URL || 'https://releases.pulso.tech/Pulso-Setup-1.0.0.exe';`
- **Ação no clic:** 
  - Opção A: `<a href={downloadUrl} download target="_blank" rel="noopener noreferrer">` com texto “Baixar Pulso”.
  - Opção B: `window.open(downloadUrl, '_blank')` ou `window.location.href = downloadUrl` a partir de um `<button>` que estiliza como Elemento 24.
- **Rastreamento (opcional):** Evento de analytics “download_started” ao clicar, com propriedades (versão, SO, timestamp).
- **Acessibilidade:** Botão/link com `aria-label="Baixar instalador do Pulso para Windows"` e texto visível “Baixar Pulso” ou “Baixar para Windows”.

---

## 14. Responsividade

- **Mobile first:** Header com logo + “Pulso Tech” + ícone de menu (hamburger) que abre drawer com “Entrar” e “Documentação”; hero com título em `text-3xl` e botão full-width; grid de 3 cards em 1 coluna; seção Recursos em coluna única.
- **Tablet:** 2 colunas nos cards “Por que baixar?” se desejado.
- **Desktop:** 3 colunas, container `max-w-[1400px]`, padding lateral consistente.

---

## 15. SEO e meta

- **Título da página:** “Baixar Pulso | Pulso Tech”.
- **Meta description:** “Baixe o Pulso para Windows. Assistente de código, FinOps e Data & AI na sua máquina. Download seguro via HTTPS.”
- **Open Graph:** `og:title`, `og:description`, `og:image` (logo ou banner), `og:url` = URL canônica HTTPS.
- **Canonical:** Definir URL canônica HTTPS para evitar duplicação.

---

## 16. Resumo dos elementos da pasta `docs` utilizados

| Elemento | Doc | Uso na tela |
|---------|-----|-------------|
| 23 Glass | glass-padrao.md | Header sticky, cards “Por que baixar?”, card Recursos |
| 24 Botão Download | download-button.md | CTA principal “Baixar Pulso” |
| 22 Botão Padrão | botao7.md | CTA “Documentação” ou secundário |
| 12 Get Started | botao6.md | CTA “Entrar” ou “Baixar para Windows” (glow) |
| 14 Card Analytics | card2.md | Card “Recursos incluídos” |
| 13 Card Menu | card1.md | Footer ou “Ações rápidas” |
| 17 Card Pricing | card5.md | Opcional: card “Grátis” |
| 21 Barra Cosmic | searchbar-padrao.md | Opcional: busca na página |
| 01 Loader Anel | loader1.md | Overlay “Preparando download” e/ou decoração hero |

Identidade visual: `docs/identidade-visual.md` e `src/index.css` (temas, glass, aurora, space, primary/secondary).

---

## 17. Arquivos criados/alterados

- **Implementado:** `src/pages/DownloadPage.tsx` — página conforme esta especificação (Elementos 23, 24, 22, 12, 14, 01; hero, 3 cards, recursos, CTA, footer).
- **Rota:** `src/App.tsx` — rota `path="/download"` com `<DownloadPage />` (lazy). URL no app: `/#/download`.
- **Variável:** `VITE_DOWNLOAD_URL` em `.env.example` — URL do instalador; fallback no código se não definida.
- **Acesso:** Botão "Baixar" no header da `Index.tsx` navega para `/#/download`.

Com isso, a tela HTTPS de download fica **extremamente específica e detalhada**, alinhada à identidade visual e aos elementos predominantes da pasta `docs`.
