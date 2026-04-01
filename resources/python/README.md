# Python embutido (Pulso CSA local)

Coloque aqui o **runtime Python** e o **site-packages** necessários para cada SO, gerados em CI, por exemplo:

- **Windows:** `python/python.exe` + `Lib/site-packages`
- **macOS/Linux:** `python/bin/python3` + `lib/python3.x/site-packages`

Variável opcional: `PULSO_LOCAL_PYTHON` apontando para o executável.

O motor CSA usa a pasta **`pulso-csa-api/`** na raiz do **PulsoFrontend**, **versionada neste repositório** (sem depender do repo PulsoAPI na build ou no runtime). Na **app instalada**, o `after-pack` copia `pulso-csa-api` para `resources/PulsoAPI/api`.

Script opcional de migração: `npm run sync:csa-api` (não faz parte da CI). Overrides: `PULSO_API_ROOT`.

Instalação de dependências CSA (na pasta **`pulso-csa-api/`** na raiz do PulsoFrontend):

```bash
cd pulso-csa-api
pip install -r requirements.txt
```

Para um pacote menor no futuro, use um `requirements-csa-local.txt` derivado por análise de imports.
