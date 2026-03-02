# Elemento 03 - Loader Liquid

## O que é
Tela de carregamento com texto "Loading..." com pontos piscando e uma barra de progresso em formato líquido com gradiente colorido que preenche e muda de cor.

## HTML

```html
<div class="liquid-loader">
  <div class="loading-text">
    Loading<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
  </div>
  <div class="loader-track">
    <div class="liquid-fill"></div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/loaders.css` (classes: `.liquid-loader`, `.loader-track`, `.liquid-fill`, `.loading-text`, `.dot`)

```css
.liquid-loader .loader-track {
  width: 180px;
  height: 32px;
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
  border-radius: 16px;
  overflow: hidden;
}

.liquid-loader .liquid-fill {
  background: linear-gradient(90deg, #4f46e5, #7c3aed, #ec4899, #f59e0b);
  animation: fillProgress 4s ease-out infinite, colorShift 3s linear infinite;
}
/* + keyframes fillProgress, colorShift, blink, textGlow */
```
