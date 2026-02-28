# Elemento 12 - Botão Get Started

## O que é
Botão de call-to-action com fundo em gradiente (indigo, pink, yellow) que brilha ao hover. Texto "Get Started For Free" com seta. Efeito de glow no fundo.

## HTML

```html
<div class="get-started-btn-wrap">
  <div class="glow-bg"></div>
  <a href="#" class="get-started-btn" title="payment">
    Get Started For Free
    <svg viewBox="0 0 10 10">
      <path d="M0 5h7"></path>
      <path d="M1 1l4 4-4 4"></path>
    </svg>
  </a>
</div>
```

## CSS
Arquivo: `css/components/buttons.css` (classes: `.get-started-btn-wrap`, `.glow-bg`, `.get-started-btn`)

```css
.get-started-btn-wrap .glow-bg {
  position: absolute;
  inset: 0;
  border-radius: 0.75rem;
  background: linear-gradient(to right, #6366f1, #ec4899, #f59e0b);
  filter: blur(1rem);
  opacity: 0.6;
}

.get-started-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px var(--shadow);
}
```
