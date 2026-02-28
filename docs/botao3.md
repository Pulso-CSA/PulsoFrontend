# Elemento 09 - Botão Documents

## O que é
Botão com ícone de pasta de documentos em camadas (fileBack, filePage, fileFront). Ao passar o mouse, a página e a pasta frontal animam (translateY e rotateX).

## HTML

```html
<button class="Documents-btn">
  <span class="folderContainer">
    <svg class="fileBack" width="146" height="113" viewBox="0 0 146 113">...</svg>
    <svg class="filePage" width="88" height="99" viewBox="0 0 88 99">...</svg>
    <svg class="fileFront" width="160" height="79" viewBox="0 0 160 79">...</svg>
  </span>
  <p class="text">Documents</p>
</button>
```

## CSS
Arquivo: `css/components/buttons.css` (classes: `.Documents-btn`, `.folderContainer`, `.fileBack`, `.filePage`, `.fileFront`)

```css
.Documents-btn {
  display: flex;
  align-items: center;
  background-color: rgb(49, 49, 83);
  padding: 0px 15px;
  border-radius: 5px;
  gap: 10px;
}

.Documents-btn:hover .filePage {
  transform: translateY(-5px);
}

.Documents-btn:hover .fileFront {
  transform: rotateX(30deg);
}
```
