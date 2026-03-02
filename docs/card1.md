# Elemento 13 - Card Menu

## O que é
Card de menu contextual com opções: Rename, Add Member, Settings, Delete, Team Access. Separadores entre grupos. Hover em cada item destaca com cor (azul ou vermelho para Delete). Ícones SVG para cada ação.

## HTML

```html
<div class="card-menu">
  <ul class="list">
    <li class="element">
      <svg>...</svg>
      <p class="label">Rename</p>
    </li>
    <li class="element">
      <svg>...</svg>
      <p class="label">Add Member</p>
    </li>
  </ul>
  <div class="separator"></div>
  <ul class="list">
    <li class="element">
      <svg>...</svg>
      <p class="label">Settings</p>
    </li>
    <li class="element delete">
      <svg>...</svg>
      <p class="label">Delete</p>
    </li>
  </ul>
  <div class="separator"></div>
  <ul class="list">
    <li class="element">
      <svg>...</svg>
      <p class="label">Team Access</p>
    </li>
  </ul>
</div>
```

## CSS
Arquivo: `css/components/cards.css` (classes: `.card-menu`, `.list`, `.element`, `.separator`)

```css
.card-menu {
  width: 200px;
  background-color: var(--card-bg);
  border-radius: 10px;
  padding: 15px 0px;
}

.card-menu .list .element:hover {
  background-color: #5353ff;
  color: #ffffff;
  transform: translate(1px, -1px);
}

.card-menu .list .element.delete:hover {
  background-color: #8e2a2a;
}
```
