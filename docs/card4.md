# Elemento 16 - Card Sales

## O que é
Card de vendas com ícone de cifrão, título "Sales", percentual "+20%", valor "39,500" e barra de progresso verde preenchida em 76%.

## HTML

```html
<div class="card-sales">
  <div class="title">
    <span>
      <svg>...</svg>
    </span>
    <p class="title-text">Sales</p>
    <p class="percent">
      <svg>...</svg> 20%
    </p>
  </div>
  <div class="data">
    <p>39,500</p>
    <div class="range">
      <div class="fill"></div>
    </div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/cards.css` (classes: `.card-sales`, `.title`, `.data`, `.range`, `.fill`)

```css
.card-sales {
  padding: 1rem;
  background-color: var(--card-bg);
  max-width: 320px;
  border-radius: 20px;
}

.card-sales .data .range .fill {
  background-color: #10B981;
  width: 76%;
  height: 100%;
  border-radius: 0.25rem;
}
```
