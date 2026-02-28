# Elemento 18 - Barra de Busca

## O que é
Campo de busca com bordas em gradiente animadas (roxo/rosa) que rotacionam no hover e focus. Ícone de lupa à esquerda, ícone de filtro à direita. Placeholder "Search...".

## HTML

```html
<div class="search-poda">
  <div class="glow"></div>
  <div class="darkBorderBg"></div>
  <div class="darkBorderBg"></div>
  <div class="darkBorderBg"></div>
  <div class="white"></div>
  <div class="border"></div>
  <div class="search-main">
    <input placeholder="Search..." type="text" class="search-input" />
    <div class="input-mask"></div>
    <div class="search-icon">
      <svg>...</svg>
    </div>
    <div class="filter-icon">
      <svg>...</svg>
    </div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/search.css` (classes: `.search-poda`, `.search-input`, `.search-icon`, `.filter-icon`)

```css
.search-poda .white::before,
.search-poda .border::before,
.search-poda .darkBorderBg::before {
  background-image: conic-gradient(...);
  transition: all 2s;
}

.search-poda:hover .darkBorderBg::before {
  transform: translate(-50%, -50%) rotate(262deg);
}

.search-poda:focus-within .darkBorderBg::before {
  transform: translate(-50%, -50%) rotate(442deg);
  transition: all 4s;
}
```
