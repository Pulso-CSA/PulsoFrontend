# Elemento 06 - Loader Browser/Chat

## O que é
Tela de carregamento que simula uma janela de navegador com skeleton (placeholders pulsantes) e linhas de fluxo de dados animadas. Ideal para indicar carregamento de chat ou conteúdo.

## HTML

```html
<div class="browser-loader">
  <svg viewBox="0 0 900 500">
    <defs>
      <linearGradient id="traceGradient1">...</linearGradient>
      <!-- traceGradient2, 3, 4 -->
    </defs>
    <g id="browser">
      <rect class="browser-frame">...</rect>
      <rect class="browser-top">...</rect>
      <text class="loading-text">Loading...</text>
      <rect class="skeleton">...</rect>
      <!-- múltiplos rect.skeleton -->
    </g>
    <g id="traces">
      <path class="trace-flow" d="M100 300 H250 V120">...</path>
      <!-- 4 paths com trace-flow -->
    </g>
  </svg>
</div>
```

## CSS
Arquivo: `css/components/loaders.css` (classes: `.browser-loader`, `.browser-frame`, `.skeleton`, `.trace-flow`)

```css
.browser-loader .skeleton {
  fill: var(--skeleton-bg);
  animation: pulse 1.8s ease-in-out infinite;
}

.browser-loader .trace-flow {
  stroke-dasharray: 120 600;
  stroke-dashoffset: 720;
  animation: flow 5s linear infinite;
}
/* + keyframes pulse, flow */
```
