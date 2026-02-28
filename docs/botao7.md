# Elemento 22 - Botão Padrão (Gradient Border)

## O que é
Botão padrão do app com borda em gradiente (azul #03a9f4 → rosa #f441a5). Fundo preto, texto branco. No hover, glow suave com blur do gradiente. Efeito de blur reduzido no active.

## HTML

```html
<!-- From Uiverse.io by Spacious74 -->
<button class="btn-padrao-gradient">Hover me</button>
```

Implementação em elemento único (sem wrapper): o gradiente e o glow usam pseudo-elementos `::before` e `::after`.

## CSS
Arquivo: `src/styles/components-showcase.css` (classe: `.btn-padrao-gradient`)

Idêntico ao original (From Uiverse.io by Spacious74). Estrutura: container (gradiente) + button (preto) simulados com pseudo-elementos.

```css
/* container */
.btn-padrao-gradient {
  position: relative;
  padding: calc(3px + 0.6em) calc(3px + 0.8em);
  background: linear-gradient(90deg, #03a9f4, #f441a5);
  border-radius: 0.9em;
  font-size: 1.4em;
  color: #fff;
  border: none;
  cursor: pointer;
  transition: all 0.4s ease;
}
/* inner button (preto) */
.btn-padrao-gradient::before {
  content: "";
  position: absolute;
  inset: 3px;
  background-color: #000;
  border-radius: 0.5em;
  z-index: -1;
  box-shadow: 2px 2px 3px #000000b4;
}
/* glow */
.btn-padrao-gradient::after {
  content: "";
  position: absolute;
  inset: 0;
  margin: auto;
  border-radius: 0.9em;
  z-index: -10;
  filter: blur(0);
  transition: filter 0.4s ease;
}
.btn-padrao-gradient:hover:not(:disabled)::after {
  background: linear-gradient(90deg, #03a9f4, #f441a5);
  filter: blur(1.2em);
}
.btn-padrao-gradient:active:not(:disabled)::after {
  filter: blur(0.2em);
}
```

## Uso
Este é o **botão padrão** do aplicativo Pulso. Aplicado via variante `default` no componente `Button`.
