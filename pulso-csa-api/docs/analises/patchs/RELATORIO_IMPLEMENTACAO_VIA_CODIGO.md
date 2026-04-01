# Relatório: Implementação via Código — Patches e Versão

**Versão:** 1.0  
**Data:** 24/02/2025  
**Base:** RELATORIO_ANALISE_COMPLETA_PATCHES.md

---

## 1. Objetivo

Este documento detalha **o que pode ser implementado via código**, separando:

- **Backend (PulsoAPI):** Rotas, services, models, database
- **Frontend (PulsoFrontend):** Ajustes de configuração e componentes
- **CI/CD:** Workflows e scripts

A primeira execução prioriza o que pode ser subido imediatamente no backend.

---

## 2. Backend — Implementação Imediata

### 2.1 Endpoint de Versão (Cenário A)

**O que faz:** Expõe `minClientVersion` e `latestVersion` para o app Electron (e eventualmente web) verificar compatibilidade e forçar upgrade quando necessário.

**Arquivos a criar:**

| Arquivo | Descrição |
|---------|-----------|
| `api/app/models/version_models/version_models.py` | Pydantic models: VersionResponse |
| `api/app/services/version/version_service.py` | Lógica de leitura (env ou MongoDB) |
| `api/app/storage/database/version/database_version.py` | CRUD de app_versions (opcional) |
| `api/app/routers/version_router/version_router.py` | GET /api/version |

**Modelo de resposta:**
```json
{
  "minClientVersion": "1.0.0",
  "latestVersion": "1.0.2",
  "releaseNotes": "Correções de bugs e melhorias de performance.",
  "forceUpgrade": false
}
```

**Fonte de dados (prioridade):**
1. Variáveis de ambiente: `MIN_CLIENT_VERSION`, `LATEST_VERSION`, `RELEASE_NOTES`, `FORCE_UPGRADE`
2. MongoDB (collection `app_versions`): documento com versões, permitindo atualização sem redeploy

### 2.2 Estrutura de Código (Padrão Existente)

Seguindo o padrão de `subscription_router`, `profile_router`:

- **Router:** prefix `/version` ou `/api/version`, tag `Version`
- **Service:** funções async que retornam modelos Pydantic
- **Models:** Pydantic BaseModel com Field
- **Database:** collection `app_versions` com índice em `platform` (win, mac, linux)

### 2.3 Endpoints

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| GET | /api/version | Versão do cliente (Electron) | Não |
| GET | /api/version?platform=win | Filtro por plataforma | Não |
| PUT | /api/version | Atualizar configuração (admin) | Sim (VERSION_ADMIN_EMAILS) |

### 2.4 Integração no main.py

```python
from app.routers.version_router.version_router import router as version_router
app.include_router(version_router, prefix="/api", tags=["Version"])
```

---

## 3. Backend — Implementação Futura (Cenário B)

### 3.1 Hospedagem de Updates no Backend

**Requisitos:**
- Storage (S3, MinIO ou disco)
- Endpoint `GET /updates/win/latest.yml` (Content-Type: text/yaml)
- URLs públicas para download dos arquivos
- CORS configurado para origem do Electron

**Arquivos sugeridos:**
- `api/app/routers/updates_router/updates_router.py`
- `api/app/services/updates/updates_service.py`
- `api/app/storage/updates/` (ou integração S3)

**Complexidade:** Média. Só implementar se não for usar GitHub Releases.

---

## 4. Backend — Script de Release (Cenário C)

### 4.1 Script Python para CI

**Arquivo:** `scripts/release.py` (na raiz do PulsoFrontend ou PulsoAPI)

**Funcionalidades:**
- Receber versão por argumento: `python scripts/release.py 1.0.2` ou `--bump patch`
- Atualizar `package.json` (raiz e installer)
- Executar `npm run build:electron` e `installer:build`
- Criar release no GitHub via `gh release create` ou PyGithub
- Upload de artefatos

**Dependência:** `PyGithub>=2.0.0` (se usar API) ou `gh` CLI

**Uso no GitHub Actions:**
```yaml
- run: python scripts/release.py ${{ github.ref_name }}
```

---

## 5. Frontend — Instruções Completas

Consulte **[INSTRUCOES_FRONTEND_PATCHES.md](./INSTRUCOES_FRONTEND_PATCHES.md)** para:

- Comportamento esperado do app
- Onde fica cada funcionalidade (verificação, tela de update, tela de configuração admin)
- Variáveis de ambiente necessárias
- Estrutura de pastas sugerida
- Checklist de implementação

---

## 6. Frontend — O Que Pode Ser Feito via Código (Resumo)

### 6.1 Instalação e Configuração

| # | Ação | Arquivo | Conteúdo |
|---|------|---------|----------|
| 1 | Adicionar electron-updater | package.json (raiz) | `"electron-updater": "^6.1.0"` |
| 2 | Adicionar electron-updater | installer/package.json | Idem |
| 3 | Configurar publish | installer/package.json build | provider, owner, repo |
| 4 | Ajustar target | installer/package.json | Garantir NSIS com publish para gerar latest.yml |

### 6.2 Código no Main Process

**Arquivo:** `electron/main.cjs` (raiz) e `installer/electron/main.js`

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

app.whenReady().then(() => {
  // ... createWindow ...
  autoUpdater.checkForUpdates();
});
```

### 6.3 Tela de Atualização (React)

**Componente:** `UpdateAvailableScreen.tsx`

**Estados:**
- `available`: Nova versão disponível, botão "Instalar e reiniciar"
- `downloading`: Barra de progresso
- `ready`: "Atualização pronta. Reiniciar agora?"
- `error`: Mensagem + "Tentar novamente"

**IPC:** `ipcRenderer.on('update-available', ...)`, `ipcRenderer.on('update-downloaded', ...)`

### 6.4 Consumo do Backend (Opcional)

**Uso:** Verificar `minClientVersion` antes de permitir uso do app.

```typescript
const res = await fetch(`${API_URL}/api/version`);
const { minClientVersion, forceUpgrade } = await res.json();
if (forceUpgrade && semver.lt(currentVersion, minClientVersion)) {
  // Bloquear app, exibir tela de upgrade obrigatório
}
```

---

## 7. CI/CD — GitHub Actions

### 7.1 Workflow release.yml

**Arquivo:** `.github/workflows/release.yml` (no repositório PulsoFrontend)

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build:electron
      - run: cd installer && npm ci && npm run installer:build
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            installer/dist-installer/*.exe
            installer/dist-installer/latest.yml
            installer/dist-installer/*.blockmap
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 7.2 Ajustes Necessários

- Caminho exato dos artefatos após `installer:build`
- Garantir que `latest.yml` e `.blockmap` sejam gerados (config do electron-builder)
- Tag no formato `v1.0.1` para disparar o workflow

---

## 8. Resumo — Ordem de Execução

| Ordem | Item | Onde | Status |
|-------|------|------|--------|
| 1 | Models version | api/app/models/version_models/ | ✅ Implementar |
| 2 | Service version | api/app/services/version/ | ✅ Implementar |
| 3 | Database version (opcional) | api/app/storage/database/version/ | ✅ Implementar |
| 4 | Router version | api/app/routers/version_router/ | ✅ Implementar |
| 5 | Registrar no main.py | api/app/main.py | ✅ Implementar |
| 6 | Variáveis de ambiente | .env.example | Documentar |
| 7 | electron-updater (frontend) | PulsoFrontend | Manual |
| 8 | Tela de atualização (frontend) | PulsoFrontend | Manual |
| 9 | GitHub Actions | PulsoFrontend | Manual |
| 10 | Script release.py | scripts/ | Opcional |

---

## 9. Variáveis de Ambiente (Backend)

| Variável | Descrição | Exemplo | Obrigatório |
|----------|-----------|---------|-------------|
| MIN_CLIENT_VERSION | Versão mínima aceita do app | 1.0.0 | Não (default: 0.0.0) |
| LATEST_VERSION | Última versão disponível | 1.0.2 | Não (default: 1.0.0) |
| RELEASE_NOTES | Notas da última release | Texto | Não |
| FORCE_UPGRADE | Se true, força upgrade | false | Não |
| USE_VERSION_DB | Se true, usa MongoDB em vez de env | false | Não |

---

## 10. Coleção MongoDB (app_versions)

**Estrutura do documento:**
```json
{
  "_id": "...",
  "platform": "win",
  "minClientVersion": "1.0.0",
  "latestVersion": "1.0.2",
  "releaseNotes": "Correções e melhorias.",
  "forceUpgrade": false,
  "downloadUrl": "https://github.com/.../releases/...",
  "updatedAt": "2025-02-24T..."
}
```

**Índice:** `platform` (unique) para consulta rápida.
