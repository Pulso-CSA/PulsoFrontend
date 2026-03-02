# Elemento 25 - Navbar de Serviços

## O que é
Barra de navegação para alternar entre os quatro serviços: **Pulso CSA**, **Cloud IaC**, **FinOps** e **Dados & IA**. Estilo inspirado em container de ícones (Uiverse.io), com **efeito glass**, **bordas bem arredondadas** (formato pill) e **cores da plataforma**. Não utiliza barra grossa — o container é discreto, com fundo em glass e bordas arredondadas que se integram ao fundo.

## Referência de inspiração
Uiverse.io by eslam-hany: container de botões com bordas arredondadas e ícones. Adaptado para Pulso com glass, pills e paleta existente.

## HTML

```html
<nav class="pulso-navbar-servicos" aria-label="Serviços">
  <div class="pulso-navbar-servicos-inner">
    <button type="button" class="pulso-navbar-btn" aria-pressed="true">
      <svg class="pulso-navbar-icon">...</svg>
      <span>Pulso CSA</span>
    </button>
    <button type="button" class="pulso-navbar-btn">
      <svg class="pulso-navbar-icon">...</svg>
      <span>Cloud IaC</span>
    </button>
    <button type="button" class="pulso-navbar-btn">
      <svg class="pulso-navbar-icon">...</svg>
      <span>FinOps</span>
    </button>
    <button type="button" class="pulso-navbar-btn">
      <svg class="pulso-navbar-icon">...</svg>
      <span>Dados & IA</span>
    </button>
  </div>
</nav>
```

## CSS
Arquivo: `src/styles/pulso-layouts.css`. Implementação atual usa as classes do Layout A: `.pulso-layout-a-services-bar` (container pill + glass), `.pulso-layout-a-services-inner`, `.pulso-layout-a-btn` e `.pulso-layout-a-btn.pulso-active` (botões pill com hover e estado ativo).

Cores da plataforma: `--glass-bg`, `--glass-shadow-dark`, `--glass-shadow-light`, `--primary`, `--border`, `--foreground`.

```css
/* Container: efeito glass, sem barra grossa — bordas muito arredondadas (pill) */
.pulso-navbar-servicos {
  position: sticky;
  top: 0;
  z-index: 30;
  flex-shrink: 0;
  padding: 0.5rem 1rem;
  /* Sem fundo sólido: apenas glass e bordas arredondadas */
  background: var(--glass-bg);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: inset 16px -16px 32px var(--glass-shadow-dark),
              inset -16px 16px 32px var(--glass-shadow-light);
  border-radius: 62px; /* pill */
  border: 1px solid hsl(var(--border) / 0.4);
  max-width: fit-content;
  margin: 0 auto;
}

.pulso-navbar-servicos-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: nowrap;
}

.pulso-navbar-btn {
  outline: 0;
  border: 0;
  min-width: 44px;
  height: 44px;
  padding: 0 1rem;
  border-radius: 9999px; /* pill */
  background: transparent;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.28s ease;
  font-size: 0.75rem;
  font-weight: 500;
}

.pulso-navbar-btn:hover {
  background: hsl(var(--primary) / 0.12);
  transform: translateY(-2px);
}

.pulso-navbar-btn.pulso-active {
  background: hsl(var(--primary) / 0.18);
  border: 1px solid hsl(var(--primary) / 0.5);
  box-shadow: 0 0 20px hsl(var(--primary) / 0.2);
}

.pulso-navbar-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}
```

## Uso
- Navegação principal do Dashboard entre os quatro serviços (Layout A).
- Implementação: `src/layouts/LayoutA.tsx` — container com `.pulso-layout-a-services-bar`, botões com `.pulso-layout-a-btn` e `.pulso-layout-a-btn-horizontal`.

## Diferenças em relação à “barra grossa”
- **Antes:** faixa horizontal com fundo mais opaco e borda inferior marcada, lendo-se como uma barra sólida.
- **Depois:** container em formato **pill** (border-radius grande), apenas **glass** (backdrop-filter + inset shadow), sem faixa pesada; visual mais leve e integrado ao fundo.
