# Python embutido (Pulso CSA local)

Coloque aqui o **runtime Python** e o **site-packages** necessários para cada SO, gerados em CI, por exemplo:

- **Windows:** `python/python.exe` + `Lib/site-packages`
- **macOS/Linux:** `python/bin/python3` + `lib/python3.x/site-packages`

Variável opcional: `PULSO_LOCAL_PYTHON` apontando para o executável.

Em **desenvolvimento**, o Electron usa `python` / `python3` do PATH e espera o repositório **PulsoAPI** ao lado de **PulsoFrontend**, ou defina `PULSO_API_ROOT` para a pasta `PulsoAPI/api`.

Instalação de dependências CSA (a partir da raiz do repo PulsoAPI):

```bash
cd api
pip install -r requirements.txt
```

Para um pacote menor no futuro, use um `requirements-csa-local.txt` derivado por análise de imports.
