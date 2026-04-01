# Runtime Python / Node no instalador Windows

Para o **instalador Windows** (`npm run build:electron` / release), o runtime **não** se coloca manualmente aqui:

1. `npm run bundle:csa-runtime` (ou o **prebuild:electron** automático) gera `build/bundled-runtime/win/python` (Python 3.11 embeddable + `pip install -r pulso-csa-api/requirements.txt`) e `build/bundled-runtime/win/node` (Node LTS portátil com npm).
2. O hook **`after-pack`** copia essas pastas para `resources/python` e `resources/node` junto do `.exe`.

Build rápido **sem** empacotar Python/Node (motor usa Python/npm do sistema): defina `PULSO_SKIP_CSA_RUNTIME_BUNDLE=1` antes do `electron-builder` (o `after-pack` não exige o bundle).

Overrides em runtime: `PULSO_LOCAL_PYTHON`, `PULSO_API_ROOT`.

**Dev** (`npm run dev:app`): use Python e Node no PATH e `pip install -r pulso-csa-api/requirements.txt` num venv local.

Script opcional de migração de fontes: `npm run sync:csa-api`.
