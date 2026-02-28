# Elemento 23 - Glass Padrão (Inset Shadow)

## O que é
Efeito glass com sombras internas (inset box-shadow) que cria profundidade e volume. Adaptado para as cores da plataforma Pulso (ciano, roxo, magenta). Aplicado em todas as abas e elementos que usam `.glass` e `.glass-strong`.

## Referência original
```css
border-radius: 62px;
background: #4a274f;
box-shadow: inset 35px -35px 70px #1e1020,
            inset -35px 35px 70px #763e7e;
```

## CSS (adaptado para Pulso)
Arquivo: `src/index.css` (classes: `.glass`, `.glass-strong`)

```css
/* Variáveis de tema (em :root e temas) */
--glass-bg: hsl(var(--card) / 0.5);
--glass-shadow-dark: rgba(8, 5, 29, 0.6);
--glass-shadow-light: rgba(79, 159, 243, 0.12);

.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: inset 20px -20px 40px var(--glass-shadow-dark),
              inset -20px 20px 40px var(--glass-shadow-light);
  border-radius: var(--radius);
}

.glass-strong {
  background: var(--glass-bg);
  backdrop-filter: blur(32px);
  -webkit-backdrop-filter: blur(32px);
  box-shadow: inset 28px -28px 56px var(--glass-shadow-dark),
              inset -28px 28px 56px var(--glass-shadow-light);
  border-radius: var(--radius);
}
```

## Variante pill (border-radius: 62px)
Para elementos com formato pill/capsule:
```css
.glass-rounded-full {
  border-radius: 62px;
}
```

## Uso
- `.glass` — efeito suave (sidebars, cards secundários)
- `.glass-strong` — efeito mais intenso (área principal, modais, header)

## Elementos que usam
- ChatSidebar (CloudChat, DataChat, FinOpsChat, PromptPanel)
- pulso-chat-main
- Header (Index)
- ProfileDialog, ProfileManagement
- Auth, ForgotPassword, ResetPassword, AuthCallback
- Error, NotFound
- Billing, SubscriptionManagement
- LogsPanel, ProfileSelection
