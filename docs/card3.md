# Elemento 15 - Card Post Views

## O que é
Card interativo com visualização de "Post views" (2012, 6012, 7012, 0). Gráfico SVG com curvas em gradiente. Ícone de coração. Áreas invisíveis ao redor que ao hover inclinam o card em 3D (rotação reduzida). Footer com horários (8am a 6pm).

## HTML

```html
<div class="card-post-views">
  <div class="grid-areas">
    <div class="area"></div>
    <!-- 15 áreas -->
    <div class="wrap">
      <div class="card">
        <div class="card-bg"></div>
        <div class="card-content">
          <header>
            <p class="title">Post views</p>
            <div class="views">
              <div class="number">...</div>
            </div>
            <div class="icon">
              <svg>...</svg>
            </div>
          </header>
          <div class="chart">
            <svg>...</svg>
          </div>
          <footer>
            <span data-label="8am"></span>
            <!-- 6 spans -->
          </footer>
        </div>
      </div>
    </div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/cards.css` (classes: `.card-post-views`, `.area`, `.wrap`, `.card`, `.path1`, `.path2`)

```css
.card-post-views .area:nth-child(N):hover ~ .wrap .card {
  transform: perspective(var(--perspective)) rotateX(±8deg) rotateY(±8deg);
}
/* Rotação reduzida (8deg em vez de 15deg) */
```
