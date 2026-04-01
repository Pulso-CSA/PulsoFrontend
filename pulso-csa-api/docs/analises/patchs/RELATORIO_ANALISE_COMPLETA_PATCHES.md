# Relatório: Análise Completa — CI/CD e Patches de Atualização

**Versão:** 1.0  
**Data:** 24/02/2025  
**Escopo:** PulsoFrontend (Electron) + PulsoAPI (Backend Python/FastAPI)

---

## 1. Objetivo

Este documento consolida a análise detalhada do fluxo de **patches de atualização** do aplicativo Pulso (Electron), avaliando:

- O que deve ser feito via **GitHub Actions**
- O que pode ser feito via **Python** (scripts e backend)
- Integração entre **frontend** e **backend** para controle de versão
- Instruções para implementação completa

---

## 2. Análise do Frontend (PulsoFrontend)

### 2.1 Estrutura Atual

| Componente | Localização | Estado |
|------------|-------------|--------|
| App principal | `package.json` (raiz) | React + Vite + Electron |
| Build Electron | `npm run build:electron` | `build:icon` → `vite build` → `electron-builder --win dir` |
| Instalador | `installer/` | Instalador customizado com telas (Welcome, EULA, Permissões, Tutorial) |
| Build instalador | `installer/installer:build` | `build:main-app` → `vite build` → `electron-builder` |
| Versão | `package.json` → `"version": "0.0.0"` | Raiz e installer em `1.0.0` |
| electron-updater | **Não instalado** | Pendente |
| GitHub Actions | **Não existe** | `.github/workflows/` vazio |

### 2.2 Artefatos Gerados

| Artefato | Onde | Formato |
|----------|------|---------|
| App empacotado | `dist-electron/win-unpacked/` | Pasta com executável |
| Instalador | `installer/dist-installer/` | `Pulso Installer.exe` (portable/NSIS) |
| latest.yml | **Não gerado** | Necessário para electron-updater |
| .blockmap | **Não gerado** | Necessário para delta updates |

### 2.3 Configuração do electron-builder

**Raiz (`package.json`):**
```json
"build": {
  "appId": "com.pulso.app",
  "productName": "Pulso",
  "directories": { "output": "dist-electron" },
  "win": { "target": "dir", ... }
}
```

**Instalador (`installer/package.json`):**
```json
"build": {
  "appId": "com.pulso.installer",
  "productName": "Pulso Installer",
  "directories": { "output": "dist-installer" },
  "win": {
    "target": [{"target":"portable","arch":["x64"]},{"target":"nsis","arch":["x64"]}],
    ...
  }
}
```

**Gaps identificados:**
- Falta `publish` no `build` (provider, owner, repo)
- `target: "dir"` na raiz não gera instalador final; o instalador real está em `installer/`
- Sem `electron-updater`, não há verificação automática de updates

### 2.4 Fluxo de Build Atual

```
1. Raiz: npm run build:electron
   → build:icon (scripts/build-icon.cjs)
   → vite build
   → electron-builder --win dir → dist-electron/win-unpacked/

2. Installer: npm run installer:build
   → build:main-app (cd .. && npm run build:electron && cd installer)
   → vite build
   → electron-builder → dist-installer/
   → Gera: win-unpacked/, Pulso Installer.exe (portable), NSIS
```

### 2.5 Requisitos para Patches

| Requisito | Status | Ação |
|-----------|--------|------|
| electron-updater | ❌ | Adicionar dependência |
| publish no build | ❌ | Configurar provider (github/generic) |
| latest.yml | ❌ | Gerar com target NSIS + publish |
| .blockmap | ❌ | Idem (delta updates) |
| Tela de atualização | ❌ | Implementar no renderer |
| Eventos no main process | ❌ | autoUpdater.on('update-available', ...) |
| CI/CD | ❌ | GitHub Actions workflow |

### 2.6 Tipos de Atualização

| Tipo | Descrição | Tamanho | Requisitos |
|------|-----------|---------|------------|
| **Full** | Instalador completo | ~150–200 MB | latest.yml + .exe |
| **Delta** | Apenas blocos alterados | ~5–50 MB | latest.yml + .blockmap + range requests |
| **Background** | Download em segundo plano | - | electron-updater config |

---

## 3. Análise do Backend (PulsoAPI)

### 3.1 Estrutura Atual

| Componente | Localização | Tecnologia |
|------------|-------------|------------|
| API | `api/app/main.py` | FastAPI |
| Versão API | `app/core/pulso/config.py` | `APP_VERSION = "1.0.0"` |
| Health | `GET /health`, `GET /health/ready` | Liveness + Readiness (MongoDB) |
| CORS | `ALLOWED_ORIGINS` | Configurável via `FRONTEND_ORIGINS` |
| Storage | MongoDB | `database_core.py` |

### 3.2 Endpoints Existentes Relevantes

| Endpoint | Função |
|----------|--------|
| `GET /` | Info básica (status, name, version, description) |
| `GET /health` | Liveness |
| `GET /health/ready` | Readiness (MongoDB) |

**Gap:** Não existe endpoint dedicado para versão do **cliente** (app Electron), nem `minClientVersion` ou `latestVersion`.

### 3.3 Cenários de Integração Backend

| Cenário | Descrição | Complexidade | Recomendação |
|---------|------------|--------------|--------------|
| **A** | Backend expõe versão mínima/última | Baixa | ✅ Implementar |
| **B** | Backend hospeda arquivos de update | Média | ⚠️ Opcional |
| **C** | Backend orquestra build (script Python) | Média | ⚠️ Complementar |

### 3.4 Cenário A (Recomendado)

O backend pode expor um endpoint para o app Electron saber:
- `minClientVersion`: versão mínima aceita (ex.: forçar upgrade em vulnerabilidades)
- `latestVersion`: última versão disponível
- `releaseNotes`: notas da release (opcional)
- `downloadUrl`: URL do instalador (opcional, se não usar GitHub)

**Uso:** O app Electron continua usando `electron-updater` + GitHub Releases para baixar; o endpoint serve para lógica extra (ex.: bloquear versões antigas, exibir aviso).

### 3.5 Cenário B (Opcional)

Se o backend for o servidor de updates (em vez do GitHub):

- **Storage:** S3, MinIO ou disco para `.exe`, `latest.yml`, `.blockmap`
- **Endpoint:** `GET /updates/win/latest.yml` (Content-Type: text/yaml)
- **URLs de download:** Públicas ou com auth
- **electron-updater:** `provider: "generic"`, `url: "https://api.pulso.com/updates/win"`

### 3.6 Cenário C (Complementar)

Script Python para CI:
- Bump de versão em `package.json`
- Executar `npm run build:electron` e `installer:build`
- Criar release no GitHub via `gh` CLI ou PyGithub
- Upload de artefatos

---

## 4. Fluxo Recomendado (Visão Geral)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GITHUB ACTIONS (CI/CD)                            │
├─────────────────────────────────────────────────────────────────────────┤
│ Trigger: push main / tag v*                                              │
│ 1. Checkout repo                                                         │
│ 2. Setup Node.js                                                         │
│ 3. npm ci                                                                │
│ 4. Bump version (script ou manual na tag)                                 │
│ 5. npm run build:electron (raiz)                                         │
│ 6. cd installer && npm run installer:build                                │
│ 7. Upload: Pulso Setup X.Y.Z.exe, latest.yml, *.blockmap → GitHub Release│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     GITHUB RELEASES                                      │
│ - Pulso Setup 1.0.1.exe                                                  │
│ - latest.yml                                                             │
│ - Pulso Setup 1.0.1.exe.blockmap                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     APP ELECTRON (PulsoFrontend)                          │
│ - electron-updater consulta GitHub (ou backend se generic)                │
│ - Exibe tela "Nova versão disponível"                                    │
│ - Download → Aplicar → Reiniciar                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PULSOAPI (Backend)                                   │
│ - GET /api/version → minClientVersion, latestVersion                     │
│ - Usado para: forçar upgrade, exibir avisos, compatibilidade              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Detalhamento por Componente

### 5.1 Frontend — Checklist de Implementação

| # | Item | Arquivo(s) | Descrição |
|---|------|------------|-----------|
| 1 | electron-updater | package.json, installer/package.json | `"electron-updater": "^6.1.0"` |
| 2 | publish config | installer/package.json build | `provider: "github"`, owner, repo |
| 3 | target NSIS | installer/package.json | Garantir target que gera latest.yml |
| 4 | autoUpdater no main | electron/main.cjs, installer/electron/main.js | Eventos update-available, update-downloaded, error |
| 5 | IPC para renderer | main + preload | Enviar eventos ao renderer |
| 6 | Tela de atualização | Componente React | Estados: disponível, baixando, pronto, erro |
| 7 | Verificação ao iniciar | main process | `autoUpdater.checkForUpdates()` em app.whenReady |
| 8 | Consumo opcional do backend | Renderer | GET /api/version para minClientVersion |

### 5.2 Backend — Checklist de Implementação

| # | Item | Descrição |
|---|------|-----------|
| 1 | GET /api/version | Retorna minClientVersion, latestVersion, releaseNotes |
| 2 | Fonte de dados | Env vars ou MongoDB (collection app_versions) |
| 3 | Inclusão em /health | Opcional: adicionar version info ao health |
| 4 | CORS | Garantir que origem do Electron seja permitida |

### 5.3 CI/CD — Checklist de Implementação

| # | Item | Descrição |
|---|------|-----------|
| 1 | .github/workflows/release.yml | Workflow para build e publish |
| 2 | Trigger | push na main ou tag v* |
| 3 | Jobs | build-frontend, upload-release |
| 4 | Secrets | GITHUB_TOKEN (automático) ou PAT |
| 5 | Artefatos | .exe, latest.yml, .blockmap |

---

## 6. Versionamento Semântico

| Tipo | Exemplo | Incremento |
|------|---------|------------|
| PATCH | Correção de bug | 1.0.0 → 1.0.1 |
| MINOR | Nova feature | 1.0.1 → 1.1.0 |
| MAJOR | Breaking change | 1.1.0 → 2.0.0 |

**Sincronização:** Manter `package.json` (raiz), `installer/package.json` e tag Git alinhados.

---

## 7. Segurança

| Aspecto | Medida |
|---------|--------|
| Integridade | latest.yml inclui sha512 do instalador |
| Transporte | HTTPS para todos os downloads |
| Code signing | Certificado EV/OV no Windows (reduz SmartScreen) |
| Verificação | electron-updater valida hash antes de instalar |

---

## 8. Resumo Executivo

| Área | Status Atual | Ação Principal |
|------|--------------|----------------|
| **Frontend** | Sem electron-updater, sem tela de update | Adicionar electron-updater, config publish, tela |
| **Backend** | Sem endpoint de versão | Criar GET /api/version |
| **CI/CD** | Sem workflow | Criar .github/workflows/release.yml |
| **Instalador** | Funcional | Ajustar target para gerar latest.yml + blockmap |

---

## 9. Referências

- [electron-updater](https://www.electron.build/auto-update)
- [electron-builder — Publish](https://www.electron.build/configuration/publish)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
