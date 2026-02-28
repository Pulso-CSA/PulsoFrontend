# Elemento 02 - Loader Words

## O que é
Tela de carregamento que exibe "loading" seguido de palavras que rotacionam verticalmente (buttons, forms, switches, cards) em um card com efeito de fade nas bordas.

## HTML

```html
<div class="loader-words-card">
  <div class="loader-words">
    <p>loading</p>
    <div class="words">
      <span class="word">buttons</span>
      <span class="word">forms</span>
      <span class="word">switches</span>
      <span class="word">cards</span>
      <span class="word">buttons</span>
    </div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/loaders.css` (classes: `.loader-words-card`, `.loader-words`, `.words`, `.word`)

```css
.loader-words-card {
  --loader-bg: var(--bg-tertiary);
  background-color: var(--loader-bg);
  padding: 1rem 2rem;
  border-radius: 1.25rem;
}

.loader-words .word {
  display: block;
  color: #956afa;
  animation: spin_4991 4s infinite;
}
/* + keyframes spin_4991 */
```
