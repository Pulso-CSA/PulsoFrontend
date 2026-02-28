# Elemento 19 - Radio (Seleção única - 3 opções)

## O que é
Seletor de opção única com 3 escolhas: Free, Basic, Premium. Indicador amarelo (glider) desliza verticalmente conforme a opção selecionada. Linha lateral com gradiente.

## HTML

```html
<div class="radio-container">
  <input checked id="radio-free" name="radio" type="radio" />
  <label for="radio-free">Free</label>
  <input id="radio-basic" name="radio" type="radio" />
  <label for="radio-basic">Basic</label>
  <input id="radio-premium" name="radio" type="radio" />
  <label for="radio-premium">Premium</label>
  <div class="glider-container">
    <div class="glider"></div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/misc.css` (classes: `.radio-container`, `.glider-container`, `.glider`)

```css
.radio-container {
  --main-color: #f7e479;
  --total-radio: 3;
  display: flex;
  flex-direction: column;
}

.radio-container input:nth-of-type(1):checked ~ .glider-container .glider {
  transform: translateY(0);
}
.radio-container input:nth-of-type(2):checked ~ .glider-container .glider {
  transform: translateY(100%);
}
.radio-container input:nth-of-type(3):checked ~ .glider-container .glider {
  transform: translateY(200%);
}
```
