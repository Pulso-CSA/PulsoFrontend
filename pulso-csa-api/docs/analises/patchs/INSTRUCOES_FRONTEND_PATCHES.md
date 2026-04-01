# Instruções para o Frontend — Patches e Configuração de Versão

**Versão:** 1.0  
**Data:** 24/02/2025  
**Destinatário:** PulsoFrontend (Electron + React)

---

## 1. Visão Geral

Este documento descreve como o frontend deve se comportar em relação a:

- **Verificação de versão** (backend)
- **Tela de atualização** (electron-updater)
- **Tela de configuração** (admin) — onde fica e como usar
- **Variáveis de ambiente** necessárias

---

## 2. Variáveis de Ambiente do Frontend

### 2.1 Obrigatórias para integração com o backend

| Variável | Descrição | Exemplo | Onde definir |
|----------|-----------|---------|--------------|
| `VITE_API_URL` | URL base da API PulsoAPI | `http://localhost:8000` ou `https://api.pulso.com` | `.env`, `.env.production` |
| `VITE_VERSION_CHECK_ENABLED` | Se true, consulta backend para minClientVersion/forceUpgrade | `true` | `.env` |
| `VITE_VERSION_CHECK_INTERVAL_MS` | Intervalo (ms) para rechecar versão em background | `3600000` (1h) | `.env` |

### 2.2 Exemplo de `.env`

```env
VITE_API_URL=http://localhost:8000
VITE_VERSION_CHECK_ENABLED=true
VITE_VERSION_CHECK_INTERVAL_MS=3600000
```

### 2.3 Exemplo de `.env.production`

```env
VITE_API_URL=https://pulsoapi-production-d109.up.railway.app
VITE_VERSION_CHECK_ENABLED=true
VITE_VERSION_CHECK_INTERVAL_MS=3600000
```

---

## 3. Comportamento Esperado do App

### 3.1 Fluxo ao iniciar

```
1. App inicia
2. [Opcional] GET {VITE_API_URL}/api/version?platform=win
   → Se forceUpgrade=true e versão atual < minClientVersion:
     → Exibir tela de upgrade obrigatório (bloqueia uso)
   → Se versão atual < latestVersion:
     → electron-updater já vai detectar e exibir tela de update
3. electron-updater.checkForUpdates() no main process
4. Se update disponível → exibir tela "Nova versão disponível"
```

### 3.2 Fluxo da tela de atualização

| Estado | Comportamento |
|--------|---------------|
| **Patch disponível** | Mensagem "Nova versão X.Y.Z disponível" + botão "Instalar e reiniciar" + "Depois" |
| **Baixando** | Barra de progresso + "Baixando atualização… X%" |
| **Pronto** | "Atualização pronta. Reiniciar agora?" + botão "Reiniciar" |
| **Erro** | Mensagem de erro + "Tentar novamente" / "Fechar" |
| **Upgrade obrigatório** | Tela bloqueante (forceUpgrade): "Atualização obrigatória. Feche e reinstale." + link de download |

### 3.3 Quando consultar o backend

- **Ao iniciar:** Uma vez, para verificar `minClientVersion` e `forceUpgrade`
- **Em background:** Opcional, a cada `VITE_VERSION_CHECK_INTERVAL_MS` (ex.: 1h)
- **Não substitui electron-updater:** O backend informa política (min/force); o electron-updater faz o download real

---

## 4. Onde Fica Cada Funcionalidade

### 4.1 Verificação de versão (backend)

| Local | Arquivo sugerido | Responsabilidade |
|-------|------------------|------------------|
| **Renderer** | `src/hooks/useVersionCheck.ts` | Hook que chama `GET /api/version`, compara versão, retorna `{ shouldBlock, forceUpgrade, latestVersion }` |
| **Renderer** | `src/contexts/VersionContext.tsx` | Context que usa o hook e expõe para a árvore |
| **App root** | `src/App.tsx` | Envolve com `VersionProvider`, renderiza `UpgradeRequiredScreen` se `shouldBlock` |

### 4.2 Tela de upgrade obrigatório (forceUpgrade)

| Local | Arquivo sugerido | Responsabilidade |
|-------|------------------|------------------|
| **Componente** | `src/components/UpgradeRequiredScreen.tsx` | Tela bloqueante quando `forceUpgrade` e versão < minClientVersion |
| **Conteúdo** | Mensagem, link de download (downloadUrl ou GitHub Releases), botão "Fechar app" |

### 4.3 Tela de atualização (electron-updater)

| Local | Arquivo sugerido | Responsabilidade |
|-------|------------------|------------------|
| **Main process** | `electron/main.cjs` | `autoUpdater` + eventos `update-available`, `update-downloaded`, `error` |
| **Preload** | `electron/preload.cjs` (ou equivalente) | Expor `ipcRenderer.on('update-available')` etc. via `contextBridge` |
| **Renderer** | `src/components/UpdateAvailableScreen.tsx` | Tela com estados: disponível, baixando, pronto, erro |
| **App** | `src/App.tsx` ou layout | Mostrar `UpdateAvailableScreen` quando `updateAvailable` no state |

### 4.4 Tela de configuração (admin)

| Local | Arquivo sugerido | Responsabilidade |
|-------|------------------|------------------|
| **Página** | `src/pages/SettingsPage.tsx` ou `src/pages/admin/VersionConfigPage.tsx` | Seção "Configuração de versão" (apenas para admins) |
| **Rota** | `/settings` ou `/admin/version` | Protegida: só visível se usuário estiver em `VERSION_ADMIN_EMAILS` |
| **Formulário** | Campos: platform, minClientVersion, latestVersion, releaseNotes, forceUpgrade, downloadUrl |
| **Chamada** | `PUT {VITE_API_URL}/api/version` com Bearer token | Enviar payload `VersionUpdateRequest` |

**Onde fica a funcionalidade de configuração:**

- **Rota sugerida:** `/settings` (aba "Versão") ou `/admin/version`
- **Quem vê:** Apenas usuários cujo email está em `VERSION_ADMIN_EMAILS` no backend
- **Como saber se é admin:** O backend retorna 403 se não for; o frontend pode esconder o link/aba se não tiver role (ou sempre mostrar e deixar o backend bloquear)

---

## 5. Estrutura de Pastas Sugerida

```
src/
├── components/
│   ├── UpgradeRequiredScreen.tsx   # forceUpgrade bloqueante
│   └── UpdateAvailableScreen.tsx   # electron-updater
├── hooks/
│   └── useVersionCheck.ts          # GET /api/version
├── contexts/
│   └── VersionContext.tsx
├── pages/
│   ├── SettingsPage.tsx             # ou AdminPage
│   └── admin/
│       └── VersionConfigPage.tsx    # formulário PUT /api/version
└── lib/
    └── api.ts                       # já tem VITE_API_URL
```

---

## 6. API do Backend — Resumo

### 6.1 GET /api/version (público)

```
GET {VITE_API_URL}/api/version?platform=win
```

**Resposta:**
```json
{
  "minClientVersion": "1.0.0",
  "latestVersion": "1.0.2",
  "releaseNotes": "Correções e melhorias.",
  "forceUpgrade": false,
  "downloadUrl": null,
  "platform": "win"
}
```

### 6.2 PUT /api/version (admin)

```
PUT {VITE_API_URL}/api/version
Authorization: Bearer {token}
Content-Type: application/json

{
  "platform": "win",
  "minClientVersion": "1.0.0",
  "latestVersion": "1.0.2",
  "releaseNotes": "Correções.",
  "forceUpgrade": false,
  "downloadUrl": "https://github.com/.../releases/..."
}
```

**Requisitos no backend:**
- `USE_VERSION_DB=true`
- `VERSION_ADMIN_EMAILS=admin@empresa.com,outro@empresa.com`
- Token JWT válido de usuário cujo email está na lista

---

## 7. Variáveis do Backend (para referência)

| Variável | Descrição | Necessária para |
|----------|-----------|-----------------|
| `USE_VERSION_DB` | `true` para usar MongoDB | PUT /api/version, leitura do DB |
| `VERSION_ADMIN_EMAILS` | Emails separados por vírgula | Acesso ao PUT /api/version |
| `MIN_CLIENT_VERSION` | Fallback quando não usa DB | GET /api/version |
| `LATEST_VERSION` | Fallback quando não usa DB | GET /api/version |
| `RELEASE_NOTES` | Fallback | GET /api/version |
| `FORCE_UPGRADE` | `true`/`false` | GET /api/version |
| `DOWNLOAD_URL` | URL do instalador | GET /api/version |

---

## 8. electron-updater — Configuração

### 8.1 package.json (raiz e installer)

```json
{
  "dependencies": {
    "electron-updater": "^6.1.0"
  },
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

### 8.2 electron/main.cjs

```javascript
const { autoUpdater } = require('electron-updater');

autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

autoUpdater.on('update-available', (info) => {
  mainWindow?.webContents?.send('update-available', info);
});

autoUpdater.on('update-downloaded', () => {
  mainWindow?.webContents?.send('update-downloaded');
});

autoUpdater.on('error', (err) => {
  mainWindow?.webContents?.send('update-error', err.message);
});

// Após createWindow, em app.whenReady:
autoUpdater.checkForUpdates();
```

---

## 9. Checklist de Implementação

| # | Item | Onde |
|---|------|------|
| 1 | Variáveis VITE_* no .env | Raiz do projeto |
| 2 | Hook useVersionCheck | src/hooks/ |
| 3 | VersionContext | src/contexts/ |
| 4 | UpgradeRequiredScreen | src/components/ |
| 5 | UpdateAvailableScreen | src/components/ |
| 6 | electron-updater no main | electron/main.cjs |
| 7 | IPC preload para update events | electron/preload |
| 8 | VersionConfigPage (admin) | src/pages/admin/ ou SettingsPage |
| 9 | Rota /settings ou /admin/version | Router |
| 10 | Integração no App.tsx | Bloquear se forceUpgrade |
