# Elemento 05 - Loader Typewriter

## O que é
Tela de carregamento que simula uma máquina de escrever: teclado, carret (slide) e papel que sobe com linhas de texto. Animação em loop.

## HTML

```html
<div class="typewriter-loader">
  <div class="slide"><i></i></div>
  <div class="paper"></div>
  <div class="keyboard"></div>
</div>
```

## CSS
Arquivo: `css/components/loaders.css` (classes: `.typewriter-loader`, `.slide`, `.paper`, `.keyboard`)

```css
.typewriter-loader {
  --duration: 3s;
  position: relative;
  animation: bounce05 var(--duration) linear infinite;
}

.typewriter-loader .slide {
  background: linear-gradient(var(--blue), var(--blue-dark));
  animation: slide05 var(--duration) ease infinite;
}

.typewriter-loader .paper {
  animation: paper05 var(--duration) linear infinite;
}

.typewriter-loader .keyboard::after {
  animation: keyboard05 var(--duration) linear infinite;
}
/* + keyframes bounce05, slide05, paper05, keyboard05 */
```
