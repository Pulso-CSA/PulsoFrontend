# Relatório: CI/CD e Patches de Atualização

## Objetivo

Avaliar se as mudanças de patches de atualização devem ser aplicadas via **GitHub Actions**, se é possível fazer via **Python**, e quais instruções dar ao Cursor para o backend (se aplicável).

---

## 1. Devo aplicar essas mudanças via GitHub Actions?

### Recomendação: **Sim**

| Critério | GitHub Actions | Alternativa manual |
|----------|----------------|--------------------|
| Integração com GitHub Releases | Nativa | Upload manual |
| Disparo automático | Push/tag na `main` | Execução local |
| Reproduzibilidade | Ambiente padronizado | Depende da máquina |
| Manutenção | Workflow versionado no repo | Scripts soltos |
| Custo | Gratuito (limites generosos) | N/A |

### O que o GitHub Actions faria

1. **Trigger:** Ao fazer push na `main` ou ao criar tag `v*` (ex.: `v1.0.1`)
2. **Build:** Rodar `npm run build:electron` (raiz) e `installer:build` (pasta `installer`)
3. **Publicação:** Fazer upload para GitHub Releases de:
   - `Pulso Setup X.Y.Z.exe` (ou `.exe` do instalador)
   - `latest.yml`
   - `*.blockmap` (para delta updates)
4. **Versão:** Ler de `package.json` ou da tag Git

### Quando usar GitHub Actions

- Repositório no GitHub
- Releases publicadas no GitHub Releases
- `electron-updater` configurado com `provider: "github"`

### Quando considerar outra opção

- Repo em GitLab/Bitbucket → usar CI nativo (GitLab CI, Pipelines)
- Servidor de updates próprio (S3, servidor custom) → workflow pode chamar API/CLI
- Builds muito pesados ou específicos → avaliar runners self-hosted

---

## 2. É possível fazer via Python?

### Resposta: **Sim, com ressalvas**

Python pode participar do fluxo de patches de três formas:

### 2.1 Python como script de automação (local ou em CI)

| O que faz | Viável? | Observação |
|-----------|---------|------------|
| Bump de versão em `package.json` | Sim | `python -c` ou script com `json` |
| Chamar `npm run build:electron` | Sim | `subprocess.run()` |
| Chamar `installer:build` | Sim | Idem |
| Criar release no GitHub | Sim | `PyGithub` ou `gh` CLI |
| Upload de artefatos | Sim | `gh release upload` ou API |

Exemplo de fluxo:

```python
# pseudo-código
import subprocess
import json

# 1. Bump version
with open("package.json") as f:
    pkg = json.load(f)
pkg["version"] = "1.0.2"
with open("package.json", "w") as f:
    json.dump(pkg, f, indent=2)

# 2. Build
subprocess.run(["npm", "run", "build:electron"], check=True)
subprocess.run(["npm", "run", "installer:build"], cwd="installer", check=True)

# 3. Criar release e upload (via gh CLI ou PyGithub)
subprocess.run(["gh", "release", "create", "v1.0.2", "dist-installer/*.exe", ...])
```

### 2.2 Python no GitHub Actions

O workflow pode usar uma action ou step em Python para:

- Calcular próxima versão (semver)
- Validar changelog
- Gerar `latest.yml` customizado (se necessário)
- Chamar APIs externas

O build em si continua sendo Node/npm; Python só orquestra ou complementa.

### 2.3 Backend Python servindo updates

Se o backend for Python (FastAPI, Django, etc.) e você quiser **servir** os updates em vez do GitHub Releases:

| Aspecto | GitHub Releases | Backend Python |
|---------|-----------------|----------------|
| Onde ficam os arquivos | GitHub | S3, disco, CDN |
| Quem serve `latest.yml` | GitHub | Endpoint no backend |
| `electron-updater` | `provider: "github"` | `provider: "generic"` + URL |
| Complexidade | Baixa | Média (storage, URLs, CORS) |

É possível, mas exige:

- Armazenamento dos `.exe`, `latest.yml`, `.blockmap`
- Endpoint que devolva `latest.yml` ou equivalente
- URLs públicas para download
- Configuração do `electron-updater` com `provider: "generic"`

---

## 3. Instruções para o Cursor do Backend (se houver backend Python)

Se existir um **backend em Python** que precise participar do fluxo de patches, use as instruções abaixo.

### 3.1 Cenário A: Backend só consome versão (não publica)

O backend pode expor um endpoint para o app web (não Electron) saber a versão mínima suportada:

```
GET /api/version ou /api/health
→ { "minClientVersion": "1.0.0", "latestVersion": "1.0.2" }
```

**Instruções para o Cursor (backend):**

1. Criar endpoint `GET /api/version` (ou incluir em `/api/health`) que retorne:
   - `minClientVersion`: versão mínima aceita
   - `latestVersion`: última versão disponível
2. Versão pode vir de variável de ambiente, arquivo ou banco.
3. O app Electron continua usando `electron-updater` + GitHub Releases para baixar e instalar; esse endpoint é opcional (ex.: para forçar upgrade em cenários específicos).

### 3.2 Cenário B: Backend hospeda os arquivos de update

Se o backend for o servidor de updates (em vez do GitHub):

**Instruções para o Cursor (backend):**

1. **Storage:** Configurar armazenamento para:
   - `Pulso Setup X.Y.Z.exe`
   - `latest.yml`
   - `Pulso Setup X.Y.Z.exe.blockmap`
   - (Pode ser S3, MinIO, disco, etc.)

2. **Endpoint `latest.yml`:** Criar rota que sirva o conteúdo de `latest.yml`:
   - `GET /updates/latest.yml` ou `GET /updates/win/latest.yml`
   - Content-Type: `text/yaml` ou `application/x-yaml`
   - Conteúdo no formato esperado pelo electron-updater (ex.):
     ```yaml
     version: 1.0.2
     files:
       - url: Pulso Setup 1.0.2.exe
         sha512: ...
         size: 12345678
     path: Pulso Setup 1.0.2.exe
     sha512: ...
     releaseDate: '2025-02-22T...'
     ```

3. **URLs de download:** Garantir que os arquivos estejam acessíveis em URLs públicas (ou com auth, se o updater suportar).

4. **CORS:** Se o app Electron fizer requisições do renderer, configurar CORS para o domínio do backend.

5. **Frontend (Electron):** Configurar `electron-updater` com:
   ```json
   "publish": {
     "provider": "generic",
     "url": "https://seu-backend.com/updates/win"
   }
   ```

### 3.3 Cenário C: Backend orquestra o build (CI em Python)

Se o CI for um script Python que roda no GitHub Actions ou em outro runner:

**Instruções para o Cursor (backend/scripts):**

1. Criar script `scripts/release.py` que:
   - Receba versão por arg ou calcule (ex.: `bump patch`)
   - Atualize `package.json` e `installer/package.json`
   - Execute `npm run build:electron` e `npm run installer:build`
   - Crie release no GitHub via `gh` ou PyGithub
   - Faça upload dos artefatos em `dist-installer/`

2. Adicionar `requirements.txt` (se usar PyGithub): `PyGithub>=2.0.0`

3. Documentar uso: `python scripts/release.py 1.0.2` ou `python scripts/release.py --bump patch`

4. O workflow do GitHub Actions pode chamar: `python scripts/release.py ${{ github.ref_name }}`

---

## 4. Resumo e decisão sugerida

| Abordagem | Recomendação | Quando usar |
|-----------|--------------|-------------|
| **GitHub Actions** | ✅ Principal | Repo no GitHub, releases no GitHub Releases |
| **Python como script** | ✅ Complementar | Bump de versão, orquestração, validações |
| **Backend Python servindo updates** | ⚠️ Opcional | Se não quiser usar GitHub Releases (ex.: ambiente privado) |
| **Backend Python só com endpoint de versão** | ✅ Opcional | Se precisar de `minClientVersion` ou lógica extra |

### Fluxo recomendado

1. **CI:** GitHub Actions dispara em push na `main` ou em tag `v*`.
2. **Build:** `npm run build:electron` + `installer:build`.
3. **Publicação:** Upload automático para GitHub Releases (action `softprops/action-gh-release` ou similar).
4. **App:** `electron-updater` com `provider: "github"` consulta o GitHub e baixa o patch.
5. **Python:** Usar apenas se precisar de script de bump, validação ou backend servindo updates.

---

## 5. Próximos passos

1. Criar `.github/workflows/release.yml` para build e publish.
2. Configurar `publish` no `package.json` do installer com `provider: "github"` e dados do repo.
3. Adicionar `electron-updater` no main process e implementar a tela de atualização (conforme `PATCHES_ATUALIZACAO.md`).
4. Se houver backend Python: definir se ele só expõe versão (Cenário A) ou se hospedará os arquivos (Cenário B).
