# pulso-csa-local

Serviço FastAPI mínimo para desktop (Electron). Não substitui `app/main.py`.

## Executar (desenvolvimento)

Na pasta `pulso-csa-api/` na raiz do PulsoFrontend (com `.env` e Mongo acessível, se aplicável):

```bash
python -m uvicorn app.pulso_csa_local.main:app --host 127.0.0.1 --port 8010 --reload
```

Variáveis úteis:

- `PULSO_LOCAL_RELAX_ROOT_ALLOWLIST=1` — não exige ficheiro de pastas autorizadas (dev no browser).
- `PULSO_ALLOWED_ROOTS_FILE` — JSON `["C:\\path\\proj"]` para validar `root_path`.
- `PULSO_LOCAL_SECRET` — se definido, o cliente deve enviar header `X-Pulso-Local-Token` com o mesmo valor.
