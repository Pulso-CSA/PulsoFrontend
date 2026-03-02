# Elemento 04 - Loader Book

## O que é
Tela de carregamento que simula um livro com páginas virando em sequência, exibindo ícones de documento. Animação em loop contínuo.

## HTML

```html
<div class="loader-book">
  <div>
    <ul>
      <li><svg fill="currentColor" viewBox="0 0 90 120"><path d="M90,0 L90,120 L11,120..."/></svg></li>
      <li><svg>...</svg></li>
      <!-- 6 páginas no total -->
    </ul>
  </div>
  <span>Loading</span>
</div>
```

## CSS
Arquivo: `css/components/loaders.css` (classes: `.loader-book`, `ul li`)

```css
.loader-book {
  --duration: 3s;
  width: 200px;
  height: 140px;
  position: relative;
}

.loader-book ul li {
  position: absolute;
  top: 10px;
  left: 10px;
  transform-origin: 100% 50%;
  animation: page-2, page-3, page-4, page-5 (conforme nth-child);
}
/* + keyframes page-2 a page-5 */
```
