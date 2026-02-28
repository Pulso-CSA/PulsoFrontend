# Elemento 08 - Botão Save

## O que é
Botão de salvar com ícone de documento/floppy disk. Ao passar o mouse, o ícone anima com efeito de "salvando" (box preenche, linhas animam).

## HTML

```html
<button class="action_has has_saved" aria-label="save" type="button">
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" fill="none">
    <path d="m19,21H5c-1.1,0-2-.9-2-2V5..." data-path="box"></path>
    <path d="M7 3L7 8L15 8" data-path="line-top"></path>
    <path d="M17 20L17 13L7 13L7 20" data-path="line-bottom"></path>
  </svg>
</button>
```

## CSS
Arquivo: `css/components/buttons.css` (classes: `.action_has`, `.has_saved`)

```css
.action_has {
  --color-has: 211deg 100% 48%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  height: calc(var(--sz) * 2.5);
  width: calc(var(--sz) * 2.5);
  border-radius: 0.375rem;
}

.action_has:hover path[data-path="box"] {
  animation: has-saved var(--duration) var(--ease) forwards;
  fill: hsl(var(--color-has) / 0.35);
}
/* + keyframes has-saved, has-saved-line-top, has-saved-line-bottom */
```
