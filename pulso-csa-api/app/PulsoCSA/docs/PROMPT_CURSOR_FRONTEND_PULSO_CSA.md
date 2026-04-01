# Prompt Cursor – Alterações de Frontend Pulso CSA

Este documento descreve **apenas** as alterações de comportamento do frontend relacionadas ao preview.

> **Tela preta no painel "Preview do Frontend"?** Ver análise em `docs/PREVIEW_IFRAME_PANEL_PULSO_CSA.md` (raiz do repo).

---

## Campo `preview_auto_open`

O backend **sempre** retorna `preview_auto_open: false`. O frontend deve **NUNCA** abrir nova aba, terminal ou navegador automaticamente.

O backend retorna `preview_auto_open` nas respostas de:
- `POST /comprehension-js/run` (campo em `ComprehensionJSResponse`)
- `POST /preview/start` (campo em `PreviewStartResponse`)

| Valor | Comportamento obrigatório do frontend |
|-------|---------------------------------------|
| `false` (sempre) | **NÃO** abrir nova aba do app, **NÃO** abrir terminal, **NÃO** abrir navegador automaticamente. Apenas exibir o link `preview_url` para o usuário clicar. |
| `true` | (não utilizado atualmente) O frontend pode abrir `preview_url` em nova aba ou iframe. |

---

## Regras de implementação (OBRIGATÓRIAS)

Com `preview_auto_open === false` (valor fixo do backend):

1. **NUNCA abrir nova aba** do aplicativo Pulso ou do navegador.
2. **NUNCA abrir o terminal** (o backend já inicia o servidor em background sem janela).
3. **NUNCA abrir no navegador** automaticamente.
4. **SEMPRE exibir** o link `preview_url` (ou `preview_frontend_url`) como texto clicável para o usuário acessar manualmente.
5. **Exibir** a mensagem de sucesso (ex.: "Servidor de desenvolvimento iniciado. O preview estará disponível em breve.").

---

## Fluxo do botão "Testar Preview"

1. Usuário clica em "Testar Preview".
2. Frontend chama `POST /preview/start` com `root_path` e `project_type`.
3. Se `success === true`:
   - Se `preview_auto_open === true`: pode abrir `preview_url` em nova aba/iframe.
   - Se `preview_auto_open === false`: **não** abrir nada; exibir `message` e o link para o usuário clicar.
4. Se `success === false`: exibir `message` e `details` como erro.
