# Guia Simplificado — Frontend Conectado ao Backend (Teste Local → GitHub Actions)

**Versão:** 1.0  
**Data:** 24/02/2025  
**Objetivo:** Implementação mínima no frontend, já conectada ao backend, para teste local e preparação para GitHub Actions.

---

## 1. Cenário do Primeiro Teste

- **Backend:** Rodando em `http://localhost:8000` (PulsoAPI)
- **Frontend:** Rodando em `http://localhost:5173` ou `http://localhost:8080` (PulsoFrontend)
- **MongoDB:** Local (Docker ou instalado)
- **Objetivo:** Validar fluxo completo antes de subir chaves e configs para o GitHub

---

## 2. Configuração Mínima — Backend (PulsoAPI)

### 2.1 Variáveis no `.env` (raiz da PulsoAPI)

```env
# Já existentes
MONGO_URI=mongodb://localhost:27017
# ou mongodb://mongo:27017 se usar docker-compose

# Para teste local com env (sem MongoDB para versão)
MIN_CLIENT_VERSION=0.0.0
LATEST_VERSION=1.0.0

# Para usar MongoDB e tela de config admin (opcional no primeiro teste)
# USE_VERSION_DB=true
# VERSION_ADMIN_EMAILS=seu-email@exemplo.com
```

### 2.2 Subir o backend

```bash
cd PulsoAPI
python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2.3 Testar o endpoint

```bash
curl http://localhost:8000/api/version?platform=win
```

Resposta esperada:
```json
{
  "minClientVersion": "0.0.0",
  "latestVersion": "1.0.0",
  "releaseNotes": null,
  "forceUpgrade": false,
  "downloadUrl": null,
  "platform": "win"
}
```

---

## 3. Configuração Mínima — Frontend (PulsoFrontend)

### 3.1 Variáveis no `.env` (raiz da PulsoFrontend)

```env
VITE_API_URL=http://localhost:8000
VITE_VERSION_CHECK_ENABLED=true
```

### 3.2 Onde colocar no frontend (ideia simplória)

| O que | Onde | Descrição |
|-------|------|-----------|
| **Chamada ao backend** | `src/lib/version.ts` ou dentro de `src/lib/api.ts` | Função `fetchVersion()` → `GET ${VITE_API_URL}/api/version?platform=win` |
| **Hook de verificação** | `src/hooks/useVersionCheck.ts` | Chama `fetchVersion()` ao montar, retorna `{ data, loading, error }` |
| **Exibição no App** | `src/App.tsx` ou layout principal | Se `data.latestVersion` > versão atual (do package.json), exibir badge ou toast "Nova versão X disponível" |
| **Tela de config (admin)** | `src/pages/SettingsPage.tsx` ou nova aba em Settings | Formulário que faz `PUT /api/version` com token. Só aparece se backend retornar 200 (admin) |

### 3.3 Estrutura mínima de arquivos

```
PulsoFrontend/
├── .env                          # VITE_API_URL, VITE_VERSION_CHECK_ENABLED
├── src/
│   ├── lib/
│   │   └── version.ts             # fetchVersion(), updateVersion()
│   ├── hooks/
│   │   └── useVersionCheck.ts     # Hook que usa fetchVersion
│   ├── components/
│   │   └── VersionBanner.tsx      # Banner simples "Nova versão disponível" (opcional)
│   └── pages/
│       └── SettingsPage.tsx       # Adicionar seção "Versão" com form PUT (admin)
```

### 3.4 Código mínimo — `src/lib/version.ts`

```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface VersionInfo {
  minClientVersion: string;
  latestVersion: string;
  releaseNotes: string | null;
  forceUpgrade: boolean;
  downloadUrl: string | null;
  platform: string;
}

export async function fetchVersion(platform = 'win'): Promise<VersionInfo> {
  const res = await fetch(`${API_URL}/api/version?platform=${platform}`);
  if (!res.ok) throw new Error('Falha ao buscar versão');
  return res.json();
}

export async function updateVersion(
  token: string,
  payload: Partial<VersionInfo>
): Promise<VersionInfo> {
  const res = await fetch(`${API_URL}/api/version`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Falha ao atualizar versão');
  return res.json();
}
```

### 3.5 Código mínimo — `src/hooks/useVersionCheck.ts`

```typescript
import { useState, useEffect } from 'react';
import { fetchVersion, type VersionInfo } from '@/lib/version';

export function useVersionCheck(platform = 'win') {
  const [data, setData] = useState<VersionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (import.meta.env.VITE_VERSION_CHECK_ENABLED !== 'true') {
      setLoading(false);
      return;
    }
    fetchVersion(platform)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [platform]);

  return { data, loading, error };
}
```

### 3.6 Uso no App (exemplo simplificado)

```tsx
// Em App.tsx ou layout principal
const { data } = useVersionCheck('win');
const currentVersion = '1.0.0'; // ou importar de package.json

// Se há nova versão, exibir aviso (toast ou banner)
{data && data.latestVersion !== currentVersion && (
  <div className="text-sm text-amber-600">
    Nova versão {data.latestVersion} disponível. Reinicie o app para atualizar.
  </div>
)}
```

---

## 4. Preparação para GitHub Actions

### 4.1 O que você precisará configurar no repositório

| Onde | O que | Descrição |
|------|-------|-----------|
| **GitHub → Settings → Secrets and variables → Actions** | `GITHUB_TOKEN` | Já existe por padrão; usado para criar releases |
| **Opcional** | `GH_PAT` ou `RELEASE_TOKEN` | Personal Access Token com `repo` se precisar de permissões extras |
| **Opcional** | `VITE_API_URL` | URL da API em produção (para build do frontend) |

### 4.2 Variáveis que podem ir como GitHub Variables (não secrets)

| Variável | Valor exemplo | Uso |
|----------|---------------|-----|
| `REPO_OWNER` | `seu-usuario` | owner do repositório |
| `REPO_NAME` | `PulsoFrontend` | nome do repositório |
| `NODE_VERSION` | `20` | versão do Node no workflow |

### 4.3 Secrets para uso futuro (quando for publicar)

| Secret | Quando usar |
|--------|-------------|
| `GH_PAT` | Se `GITHUB_TOKEN` não tiver permissão para criar release em repo privado |
| `SIGNING_CERTIFICATE` | Para code signing no Windows (opcional) |

### 4.4 Workflow mínimo para primeiro teste no GitHub

Criar `.github/workflows/release.yml` no **PulsoFrontend**:

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

      - name: Upload Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            installer/dist-installer/*.exe
            installer/dist-installer/latest.yml
            installer/dist-installer/*.blockmap
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Para testar o workflow:** criar tag `v1.0.1` e dar push:

```bash
git tag v1.0.1
git push origin v1.0.1
```

### 4.5 Configurar `publish` no `installer/package.json`

Antes do workflow funcionar, adicionar no `installer/package.json`:

```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "SEU_USUARIO_GITHUB",
      "repo": "PulsoFrontend",
      "releaseType": "release",
      "vPrefixedTagName": true
    }
  }
}
```

Substituir `SEU_USUARIO_GITHUB` pelo seu usuário ou organização.

---

## 5. Ordem de Execução — Primeiro Teste Local

| # | Ação | Onde |
|---|------|------|
| 1 | Configurar `.env` do backend (MIN_CLIENT_VERSION, LATEST_VERSION) | PulsoAPI |
| 2 | Subir backend e MongoDB | PulsoAPI |
| 3 | Testar `curl http://localhost:8000/api/version` | Terminal |
| 4 | Configurar `.env` do frontend (VITE_API_URL, VITE_VERSION_CHECK_ENABLED) | PulsoFrontend |
| 5 | Criar `src/lib/version.ts` | PulsoFrontend |
| 6 | Criar `src/hooks/useVersionCheck.ts` | PulsoFrontend |
| 7 | Usar o hook no App ou layout | PulsoFrontend |
| 8 | Rodar frontend e verificar se busca versão | PulsoFrontend |
| 9 | (Opcional) Adicionar seção de config em Settings com PUT | PulsoFrontend |
| 10 | Configurar `USE_VERSION_DB=true` e `VERSION_ADMIN_EMAILS` no backend | PulsoAPI |
| 11 | Testar PUT /api/version com token de admin | Frontend ou Postman |

---

## 6. Resumo — O Que Fica Onde

| Funcionalidade | Local no Frontend | Conecta com |
|----------------|-------------------|-------------|
| Verificar versão ao abrir | `useVersionCheck` + `fetchVersion` | `GET /api/version` |
| Exibir "nova versão disponível" | Banner/toast no App | Dados do hook |
| Configurar versão (admin) | Form em Settings | `PUT /api/version` |
| electron-updater (download real) | `electron/main.cjs` | GitHub Releases (após workflow) |

---

## 7. Próximos Passos Após Teste Local

1. Adicionar `electron-updater` e configurar `publish` no `package.json`
2. Criar `.github/workflows/release.yml`
3. Configurar `publish.owner` e `publish.repo` com seus dados
4. Criar tag `v1.0.1` e dar push para disparar o workflow
5. Verificar se a release foi criada no GitHub com `.exe`, `latest.yml`, `.blockmap`
6. Rodar o app empacotado e testar se o electron-updater detecta a nova versão
