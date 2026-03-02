# Elemento 17 - Card Pricing

## O que é
Card de preço com título "Starter", descrição "Suitable to grow steadily.", valor "$25/mo" e botão "Get started". Estilo minimalista com borda preta no botão que inverte cores no hover.

## HTML

```html
<div class="card-pricing">
  <div class="pricing-content">
    <h2>Starter</h2>
    <p class="pricing-desc">Suitable to grow steadily.</p>
    <div class="price">
      <span class="price-value">$25</span>
      <span class="price-period">/mo</span>
    </div>
  </div>
  <div class="cta-wrap">
    <a href="#" class="cta-btn">Get started</a>
  </div>
</div>
```

## CSS
Arquivo: `css/components/cards.css` (classes: `.card-pricing`, `.pricing-content`, `.cta-btn`)

```css
.card-pricing .cta-btn {
  background: var(--text-primary);
  color: var(--bg-primary);
  border: 2px solid var(--text-primary);
  border-radius: 9999px;
}

.card-pricing .cta-btn:hover {
  background: transparent;
  color: var(--text-primary);
}
```
