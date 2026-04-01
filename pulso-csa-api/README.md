# Microsserviço CSA (PulsoFrontend)

Esta pasta é a **fonte única** do backend usado pelo motor local Electron (`app.pulso_csa_local`): FastAPI, `app/PulsoCSA`, comprehension, etc.

- **Versionada neste repositório** — o release **não** clona nem puxa o repositório PulsoAPI.
- O hook `after-pack` copia este conteúdo para `resources/PulsoAPI/api` no instalador.
- **Não commite** `.venv`, `__pycache__`, `.pyc` ou `.env` daqui (estão no `.gitignore`).

## Script opcional (só migração / cópia manual)

Se precisares de alinhar com outra árvore `api` noutra máquina (legado), existe `npm run sync:csa-api`, que copia de `PULSO_SYNC_CSA_SOURCE` ou de pastas locais — **não faz parte da CI**.

## Dependências Python

Na pasta `pulso-csa-api`: `pip install -r requirements.txt` (ou o assistente em Configurações → Ambiente local).
