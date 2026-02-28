# Elemento 20 - Checkbox (Múltipla seleção - 4 opções)

## O que é
Seletor de múltipla escolha com 4 opções numeradas (1, 2, 3, 4). Cada opção tem uma "bola" que desliza para dentro quando marcada. Container em estilo glass (vidro fosco). Permite selecionar mais de uma opção.

## HTML

```html
<div class="checkbox-multi">
  <div class="glass">
    <div class="glass-inner"></div>
  </div>
  <div class="selector">
    <div class="choice">
      <div>
        <input class="choice-circle" value="one" name="opt-one" id="one" type="checkbox" />
        <div class="ball"></div>
      </div>
      <label for="one" class="choice-name">1</label>
    </div>
    <div class="choice">
      <div>
        <input class="choice-circle" value="two" name="opt-two" id="two" type="checkbox" />
        <div class="ball"></div>
      </div>
      <label for="two" class="choice-name">2</label>
    </div>
    <div class="choice">
      <div>
        <input class="choice-circle" value="three" name="opt-three" id="three" type="checkbox" />
        <div class="ball"></div>
      </div>
      <label for="three" class="choice-name">3</label>
    </div>
    <div class="choice">
      <div>
        <input class="choice-circle" value="four" name="opt-four" id="four" type="checkbox" />
        <div class="ball"></div>
      </div>
      <label for="four" class="choice-name">4</label>
    </div>
  </div>
</div>
```

## CSS
Arquivo: `css/components/misc.css` (classes: `.checkbox-multi`, `.glass`, `.choice`, `.choice-circle`, `.ball`)

```css
.checkbox-multi .ball {
  transform: translateX(-95px);
  transition: transform 400ms cubic-bezier(1, -0.4, 0, 1.4);
}

.checkbox-multi .choice-circle:checked + .ball {
  transform: translateX(0px);
}
```
