# Elemento 01 - Loader Anel (Background)

## O que é
Tela de fundo com anel circular rotativo em gradiente roxo/rosa. Sem texto. Fixo no fundo da tela, ampliado, funcionando como background decorativo durante carregamento.

## HTML

```html
<div class="showcase-loader1-bg">
  <div class="showcase-loader1" aria-hidden />
</div>
```

## CSS
Arquivo: `src/styles/components-showcase.css` (classes: `.showcase-loader1-bg`, `.showcase-loader1`)

```css
.showcase-loader1-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.showcase-loader1-bg .showcase-loader1 {
  width: min(90vmin, 500px);
  height: min(90vmin, 500px);
  /* animação do anel roxo/rosa */
}
```

## Uso
- **Dentro de um container**: Use `.showcase-loader1-bg` em um elemento com `position: relative` para o anel preencher o fundo do container.
- **Tela inteira**: Adicione `.showcase-loader1-bg--fixed` para fixar no viewport (z-index: -1). O conteúdo fica sobreposto.
