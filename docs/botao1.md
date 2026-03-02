# Elemento 07 - Botão Sparkle

## O que é
Botão com efeito de brilho e partículas ao passar o mouse. Exibe texto "Generate Site" com ícone de estrelas. Possui animação de spark (brilho rotativo) e partículas que flutuam no hover.

## HTML

```html
<div class="sp">
  <button class="sparkle-button">
    <span class="spark"></span>
    <span class="backdrop"></span>
    <svg class="sparkle" viewBox="0 0 24 24">...</svg>
    <span class="text">Generate Site</span>
  </button>
  <div class="bodydrop"></div>
  <span class="particle-pen">
    <svg class="particle" viewBox="0 0 15 15">...</svg>
    <!-- múltiplos .particle -->
  </span>
</div>
```

## CSS
Arquivo: `css/components/buttons.css` (classes: `.sparkle-button`, `.spark`, `.backdrop`, `.particle-pen`, `.text`)

```css
.sparkle-button {
  --active: 0;
  background: var(--bg);
  border-radius: 100px;
  padding: 1em 1em;
  transition: box-shadow, scale, background;
}

.sparkle-button:is(:hover, :focus-visible) {
  --active: 1;
}

.particle-pen .particle {
  animation: float-out calc(var(--duration) * 1s) infinite linear;
  animation-play-state: var(--play-state, paused);
}
```
