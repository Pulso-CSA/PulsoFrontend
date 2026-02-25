# Status CI/CD – Frontend e Backend

## Frontend (PulsoFrontend)

### GitHub Actions

- **Arquivo:** `.github/workflows/release.yml`
- **Trigger:** Push de tags `v*` (ex.: `v1.0.0`)
- **Jobs:**
  1. Build do app Electron (`npm run build:electron`)
  2. Build do instalador (`cd installer && npm run installer:build`)
  3. Upload para GitHub Releases (`.exe`, `latest.yml`, `*.blockmap`)

### Conectividade com Backend

O workflow do frontend **não** chama o backend. Ele apenas:

- Faz build do app Electron
- Gera o instalador
- Publica artefatos no GitHub Releases

O frontend consome o backend em tempo de execução via `VITE_API_URL` (produção) ou proxy (desenvolvimento).

---

## Backend (PulsoAPI)

### GitHub Actions

- **Status:** Não há workflows em `.github/workflows/` no repositório PulsoAPI.
- **Recomendação:** Criar workflow para testes, lint e deploy (ex.: Railway, Docker).

### Integração Frontend ↔ Backend

| Aspecto | Status |
|---------|--------|
| API consumida pelo frontend | ✅ Endpoints documentados em `api.ts` |
| CORS configurado | ✅ Origens permitidas em `main.py` |
| Deploy independente | Frontend e backend podem ser deployados separadamente |

---

## Resumo

- **Frontend:** CI/CD ativo via GitHub Actions (release em tag).
- **Backend:** Sem CI/CD no repositório; configurar conforme necessidade (testes, deploy).
