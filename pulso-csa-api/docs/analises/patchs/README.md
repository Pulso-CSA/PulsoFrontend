# Análise e Implementação — Patches de Atualização

Documentação sobre automação de patches do app Pulso (Electron) e integração com o backend.

## Documentos

| Documento | Descrição |
|-----------|-----------|
| **[RELATORIO_ANALISE_COMPLETA_PATCHES.md](./RELATORIO_ANALISE_COMPLETA_PATCHES.md)** | Análise detalhada do frontend (PulsoFrontend) e backend (PulsoAPI) para CI/CD e patches. |
| **[RELATORIO_IMPLEMENTACAO_VIA_CODIGO.md](./RELATORIO_IMPLEMENTACAO_VIA_CODIGO.md)** | O que pode ser implementado via código: rotas, services, models, CI/CD. |
| **[INSTRUCOES_FRONTEND_PATCHES.md](./INSTRUCOES_FRONTEND_PATCHES.md)** | Instruções para o frontend: comportamento, onde fica cada funcionalidade, variáveis necessárias. |
| **[GUIA_FRONTEND_LOCAL_GITHUB_ACTIONS.md](./GUIA_FRONTEND_LOCAL_GITHUB_ACTIONS.md)** | Guia simplificado: frontend conectado ao backend, teste local, preparação para GitHub Actions. |

## Implementação Backend (Concluída)

- **GET /api/version** (público): Retorna minClientVersion, latestVersion, releaseNotes, forceUpgrade, downloadUrl
- **PUT /api/version** (admin): Atualiza configuração no MongoDB. Requer `USE_VERSION_DB=true` e `VERSION_ADMIN_EMAILS`
- **Fonte:** Variáveis de ambiente ou MongoDB (se `USE_VERSION_DB=true`)

### Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| MIN_CLIENT_VERSION | Versão mínima aceita | 0.0.0 |
| LATEST_VERSION | Última versão disponível | 1.0.0 |
| RELEASE_NOTES | Notas da release | - |
| FORCE_UPGRADE | Força upgrade obrigatório | false |
| USE_VERSION_DB | Usar MongoDB em vez de env | false |
| DOWNLOAD_URL | URL do instalador | - |
| VERSION_ADMIN_EMAILS | Emails (vírgula) permitidos a fazer PUT /api/version | - |

### Exemplo de Resposta

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
