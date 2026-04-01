#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Serviço – Criação da Tela Teste FrontendEX (item 10)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import os
from typing import Dict, List, Any
from pathlib import Path

from utils.log_manager import add_log


FRONTENDEX_DIR = "FrontendEX"
STREAMLIT_PORT = 3000


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _write(path: str, content: str) -> None:
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _streamlit_config(port: int = STREAMLIT_PORT) -> str:
    return f'''[server]
port = {port}
address = "localhost"
headless = true

[browser]
gatherUsageStats = false
'''


def _requirements_txt() -> str:
    return """streamlit>=1.28.0
requests>=2.28.0
""" 


def _api_client_py(base_url: str) -> str:
    return f'''"""
Cliente HTTP para consumir os endpoints do backend do usuário.
Base URL configurável (padrão: backend do usuário em outro processo).
"""
import requests

BASE_URL = "{base_url}".rstrip("/")

def get(path: str, params: dict = None) -> requests.Response:
    return requests.get(f"{{BASE_URL}}{{path}}", params=params, timeout=10)

def post(path: str, json: dict = None) -> requests.Response:
    return requests.post(f"{{BASE_URL}}{{path}}", json=json, timeout=10)
'''


def _app_py(tela_teste: Dict[str, Any], funcionalidades: List[str]) -> str:
    funcs = funcionalidades or ["login", "consulta de dados"]
    testes_cruciais = tela_teste.get("testes_cruciais") or []
    dados = tela_teste.get("dados_ficticios") or {}
    layout = tela_teste.get("layout") or "dashboard simples"

    sections = "".join(
        '''
st.subheader("''' + fn + '''")
with st.expander("Testar ''' + fn + '''"):
    st.info("Chame os endpoints do backend relacionados a: ''' + fn + '''")
    if st.button("Executar teste (exemplo)", key="''' + fn.replace(" ", "_") + '''"):
        st.write("Configure as chamadas em `api_client` e aqui.")
'''
        for fn in funcs
    )

    dados_repr = repr(dados)
    testes_literal = repr(testes_cruciais)
    return f'''"""
FrontendEX – Tela de teste humanizada para QA.
Layout: {layout}
Consome o backend do usuário. Subir com: streamlit run app.py
Porta: {STREAMLIT_PORT}
"""
import streamlit as st

from api_client import get, post

st.set_page_config(page_title="FrontendEX – Tela Teste", layout="wide")
st.title("FrontendEX – Tela de Teste QA")
st.caption("Layout: {layout} | Dados fictícios disponíveis para testes.")

st.subheader("Testes cruciais")
testes_cruciais = {testes_literal}
for t in testes_cruciais:
    st.markdown(f"- {{t}}")

st.subheader("Dados fictícios (exemplo)")
dados_ficticios = {dados_repr}
st.json(dados_ficticios)

st.divider()
{sections}
'''


def _readme_md(id_requisicao: str) -> str:
    return f"""# FrontendEX – Tela de Teste

Gerado para requisição: {id_requisicao}

## Como rodar

1. Ative um ambiente com as dependências: `pip install -r requirements.txt`
2. Suba o backend do usuário em outro terminal (ex.: porta 8000).
3. Execute: `streamlit run app.py`
4. A tela sobe em **localhost:{STREAMLIT_PORT}**
"""


def run_criar_tela_teste(
    id_requisicao: str,
    root_path: str,
    tela_teste: Dict[str, Any],
    backend_base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """
    Cria a pasta FrontendEX na raiz do usuário com app Streamlit modularizado,
    configurado para porta 3000 e consumo dos endpoints do backend.
    """
    root = Path(root_path).resolve()
    frontendex = root / FRONTENDEX_DIR

    if not root.exists():
        raise FileNotFoundError(f"Pasta raiz não existe: {root_path}")

    _ensure_dir(str(frontendex))

    # Config Streamlit – porta 3000
    streamlit_dir = frontendex / ".streamlit"
    _ensure_dir(str(streamlit_dir))
    _write(str(streamlit_dir / "config.toml"), _streamlit_config(STREAMLIT_PORT))

    # requirements.txt
    _write(str(frontendex / "requirements.txt"), _requirements_txt())

    # Módulo api_client
    _write(str(frontendex / "api_client.py"), _api_client_py(backend_base_url))

    # app principal
    funcionalidades = tela_teste.get("funcionalidades") or []
    _write(str(frontendex / "app.py"), _app_py(tela_teste, funcionalidades))

    # README
    _write(str(frontendex / "README.md"), _readme_md(id_requisicao))

    # __init__.py para pacote (opcional)
    _write(str(frontendex / "__init__.py"), '"""FrontendEX – Tela de teste QA (Streamlit)."""\n')

    arquivos = [
        "app.py",
        "api_client.py",
        "requirements.txt",
        "README.md",
        ".streamlit/config.toml",
    ]

    relatorio = {
        "objetivo_backend": "Validar funcionalidades do backend via UI humanizada",
        "arquivos_utilizados": arquivos,
        "estrutura_tela": ["header", "testes cruciais", "dados fictícios"] + [f"seção: {f}" for f in funcionalidades],
        "testes": tela_teste.get("testes_cruciais") or [],
        "porta": STREAMLIT_PORT,
        "backend_base_url": backend_base_url,
    }

    add_log("info", f"FrontendEX criado em {frontendex} (porta {STREAMLIT_PORT})", "tela_teste")

    return {
        "id_requisicao": id_requisicao,
        "tela_teste_criada": {
            "arquivos": arquivos,
            "framework": "streamlit",
            "pasta": str(frontendex),
            "porta": STREAMLIT_PORT,
        },
        "relatorio": relatorio,
    }
