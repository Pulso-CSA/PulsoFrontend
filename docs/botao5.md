# Elemento 11 - Botão Project Structure

## O que é
Botão com dropdown que exibe estrutura de projeto (pastas e arquivos). Ícone de pasta amarela. Ao passar o mouse, mostra menu com itens como src, app, components, etc.

## HTML

```html
<div class="project-structure-btn">
  <div class="btn-content">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 18 14">...</svg>
    <p>Project Structure</p>
  </div>
  <div class="dropdown">
    <ul>
      <li>📁 src</li>
      <li>📁 app</li>
      <li>📄 layout.js</li>
      <li>📄 page.js</li>
      <li>📁 components</li>
      <!-- ... -->
    </ul>
  </div>
</div>
```

## CSS
Arquivo: `css/components/buttons.css` (classes: `.project-structure-btn`, `.btn-content`, `.dropdown`)

```css
.project-structure-btn .dropdown {
  position: absolute;
  left: 0;
  margin-top: 0.5rem;
  width: 256px;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s, visibility 0.3s;
}

.project-structure-btn:hover .dropdown {
  opacity: 1;
  visibility: visible;
}
```
