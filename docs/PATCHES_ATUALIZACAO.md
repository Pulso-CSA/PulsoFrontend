# Patches de Atualização — Pulso

## Objetivo

Quando houver um novo patch disponível, o aplicativo deve exibir uma **tela de atualização** informando o usuário, permitindo **instalar** e **reiniciar** o app diretamente, sem precisar baixar o instalador manualmente.

---

## 1. Fluxo de tela (objetivo principal)

### 1.1 Cenário: nova versão disponível

1. O app detecta que há uma nova versão no servidor.
2. Uma **tela de atualização** é exibida (sobrepondo ou substituindo o conteúdo atual).
3. A tela mostra:
   - Mensagem: **"Nova versão disponível"**
   - Versão atual vs. nova versão (ex.: `1.0.0` → `1.0.1`)
   - Botão **"Instalar e reiniciar"** — aplica o patch e reinicia o app
   - Botão **"Depois"** (opcional) — fecha a tela e continua usando a versão atual
4. Ao clicar em **"Instalar e reiniciar"**:
   - O patch é baixado (se ainda não foi)
   - O instalador/patch é aplicado
   - O aplicativo **reinicia automaticamente** com a nova versão

### 1.2 Estados da tela

| Estado | Conteúdo |
|--------|----------|
| **Patch disponível** | "Nova versão 1.0.1 disponível. Deseja instalar agora?" + botões |
| **Baixando** | Barra de progresso + "Baixando atualização…" |
| **Pronto** | "Atualização pronta. Instalar e reiniciar?" + botão |
| **Erro** | Mensagem de erro + "Tentar novamente" ou "Fechar" |

---

## 2. Arquitetura

### Stack
- **Electron** + **electron-builder** para empacotamento
- **electron-updater** para verificação e aplicação de atualizações
- Servidor de releases: **GitHub Releases**, S3 ou servidor próprio

### Fluxo técnico
```
App em execução → Verifica versão no servidor → Há nova versão? 
  → Sim: Exibe tela "Nova versão disponível" → Usuário clica "Instalar e reiniciar"
       → Baixa patch → Aplica → Reinicia o app
  → Não: Continua normalmente (sem tela)
```

---

## 3. Tipos de atualização

### 3.1 Atualização completa (full)
- **O que é:** Download do instalador completo (ex.: `Pulso Setup 1.1.0.exe`)
- **Quando usar:** Mudanças grandes, troca de Electron, alterações nativas
- **Tamanho:** ~150–200 MB (tamanho do instalador)
- **Vantagem:** Simples, sempre funciona
- **Desvantagem:** Download pesado

### 3.2 Atualização delta (patch)
- **O que é:** Download apenas das partes alteradas (diff entre versões)
- **Quando usar:** Correções de bugs, ajustes de UI, mudanças em assets
- **Tamanho:** ~5–50 MB (depende do que mudou)
- **Vantagem:** Download menor e mais rápido
- **Desvantagem:** Requer suporte do electron-updater e formato correto

### 3.3 Atualização em background
- **O que é:** Download em segundo plano enquanto o usuário usa o app
- **Quando usar:** Sempre que possível
- **Comportamento:** Notifica o usuário quando a atualização está pronta e oferece “Reiniciar agora” ou “Depois”

---

## 4. Implementação com electron-updater

### 4.1 Dependências
```json
{
  "dependencies": {
    "electron-updater": "^6.1.0"
  }
}
```

### 4.2 Configuração no `package.json` (build)
```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "seu-usuario",
      "repo": "PulsoFrontend",
      "releaseType": "release",
      "vPrefixedTagName": true
    }
  }
}
```

Alternativas de `provider`: `generic`, `s3`, `spaces`, `bintray`.

### 4.3 Código no main process (`electron/main.cjs`)
```javascript
const { autoUpdater } = require('electron-updater');

// Desabilitar download automático (opcional)
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

// Eventos
autoUpdater.on('update-available', (info) => {
  // Enviar ao renderer: mainWindow.webContents.send('update-available', info)
  // Renderer exibe tela: "Nova versão X disponível" + botão "Instalar e reiniciar"
});

autoUpdater.on('update-downloaded', () => {
  // Enviar ao renderer: mainWindow.webContents.send('update-downloaded')
  // Renderer exibe: "Atualização pronta. Instalar e reiniciar?" + botão
});

autoUpdater.on('error', (err) => {
  console.error('Erro na atualização:', err);
});

// Verificar ao iniciar (e opcionalmente a cada X horas)
app.whenReady().then(() => {
  autoUpdater.checkForUpdates();
});
```

### 4.4 Arquivos no servidor (ex.: GitHub Releases)
- `Pulso Setup X.Y.Z.exe` — instalador NSIS
- `latest.yml` — metadados da última versão (nome, hash, tamanho, URL)
- `Pulso Setup X.Y.Z.exe.blockmap` — usado para atualizações delta

O `electron-builder` gera esses arquivos automaticamente ao publicar.

---

## 5. Formato dos patches (delta)

### 5.1 Blockmap
- Arquivo `.blockmap` gerado pelo electron-builder
- Divide o instalador em blocos
- Permite baixar só os blocos alterados

### 5.2 Fluxo delta
1. App consulta `latest.yml` e compara versão
2. Se há versão nova, verifica se existe `.blockmap` para ela
3. Compara blocos locais com os do servidor
4. Baixa apenas blocos diferentes
5. Reconstrói o instalador e aplica

### 5.3 Requisitos
- `latest.yml` e `.blockmap` publicados junto com o instalador
- Servidor com suporte a range requests (HTTP 206)
- GitHub Releases atende a isso

---

## 6. Versionamento semântico

Recomendação: **MAJOR.MINOR.PATCH** (ex.: `1.2.3`)

| Tipo de mudança | Exemplo        | Incremento |
|-----------------|----------------|------------|
| Correção de bug | Ajuste de UI   | PATCH (1.0.0 → 1.0.1) |
| Nova feature    | Novo layout    | MINOR (1.0.1 → 1.1.0) |
| Breaking change | Nova API       | MAJOR (1.1.0 → 2.0.0) |

Definir a versão em `package.json`:
```json
{
  "version": "1.0.0"
}
```

---

## 7. Fluxo de release

### 7.1 Build e publicação
```bash
# 1. Atualizar versão em package.json
# 2. Build do app
npm run build:electron

# 3. Build do instalador (se usar instalador customizado)
cd installer && npm run installer:build

# 4. Publicar no GitHub Releases (manual ou via CI)
# - Criar tag (ex.: v1.0.1)
# - Fazer upload de Pulso Setup 1.0.1.exe, latest.yml, .blockmap
```

### 7.2 CI/CD (GitHub Actions)
- Ao criar uma tag `v*`, disparar workflow
- Rodar `npm run build:electron` e `installer:build`
- Fazer upload dos artefatos para GitHub Releases
- Garantir que `latest.yml` e `.blockmap` sejam publicados

---

## 8. Tela de atualização (UX)

### 8.1 Objetivo
Sempre que houver um novo patch, o app deve exibir uma **tela dedicada** (não apenas um toast ou diálogo pequeno) com:
- Mensagem clara: **"Nova versão disponível"**
- Versão atual e nova versão
- Botão principal: **"Instalar e reiniciar"**
- Botão secundário (opcional): **"Depois"**

### 8.2 Conteúdo da tela
- **Título:** "Atualização disponível"
- **Texto:** "Uma nova versão do Pulso (X.Y.Z) está disponível. Instale agora para obter as últimas melhorias."
- **Botão:** "Instalar e reiniciar" - inicia o download (se necessário), aplica e reinicia
- **Botão:** "Depois" - fecha a tela e continua na versão atual

### 8.3 Estados durante o fluxo
- **Patch disponível:** Tela com botão "Instalar e reiniciar"
- **Baixando:** Barra de progresso + "Baixando atualização… X%"
- **Pronto:** "Atualização pronta. Reiniciar agora?" + botão "Reiniciar"
- **Erro:** "Não foi possível atualizar." + "Tentar novamente" / "Fechar"


---

## 9. Segurança e integridade

- **Assinatura:** `latest.yml` inclui `sha512` do instalador
- **HTTPS:** Sempre usar URLs HTTPS para downloads
- **Code signing (Windows):** Certificado EV/OV reduz avisos do SmartScreen
- **Verificação:** electron-updater valida o hash antes de instalar

---

## 10. Resumo

| Etapa                    | Ação                                                |
|--------------------------|-----------------------------------------------------|
| Detecção                 | App verifica versão no servidor ao iniciar          |
| Nova versão              | Exibe **tela** "Nova versão disponível"             |
| Usuário                  | Clica "Instalar e reiniciar"                        |
| Download                 | Patch baixado em background ou sob demanda          |
| Instalação               | Patch aplicado automaticamente                      |
| Reinício                 | App reinicia com a nova versão                      |

---

## 11. Referências

- [electron-updater](https://www.electron.build/auto-update)
- [electron-builder — Publish](https://www.electron.build/configuration/publish)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [NSIS — Atualizações](https://www.electron.build/auto-update#nsis)
