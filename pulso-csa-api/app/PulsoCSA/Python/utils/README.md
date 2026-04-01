# 🛠️ Utils - Funções Utilitárias

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tools](https://img.shields.io/badge/Utilities-FF9800?style=for-the-badge&logoColor=white)

**Funções auxiliares e utilitários reutilizáveis**

</div>

---

## 📋 Visão Geral

O diretório `utils/` contém **funções utilitárias** que são reutilizadas em diversas partes da aplicação. São helpers genéricos que não pertencem a um domínio específico.

## 📁 Estrutura de Arquivos

```
utils/
├── 🐳 docker_utils.py       # Utilitários para Docker
├── 📄 file_loader.py        # Carregamento de arquivos (PDF, CSV)
├── 📝 log_manager.py        # Gerenciamento de logs
├── 📋 logger.py             # Configuração de logging
├── 🔐 login.py              # Utilitários de autenticação
├── 📊 report_writer.py      # Geração de relatórios
├── 🐍 venv_utils.py         # Utilitários para venv
└── 🔢 versioning.py         # Controle de versão
```

## 🔍 Utilitários Detalhados

### 🐳 `docker_utils.py` - Utilitários Docker

Funções para interação com Docker e containers.

```python
from app.utils.docker_utils import (
    build_image,
    run_container,
    stop_container,
    get_container_logs
)

# Construir imagem
image_id = build_image(
    dockerfile_path="./Dockerfile",
    tag="myapp:latest"
)

# Executar container
container_id = run_container(
    image="myapp:latest",
    ports={"8000": "8000"},
    env_vars={"DEBUG": "true"}
)

# Obter logs
logs = get_container_logs(container_id, tail=100)
```

### 📄 `file_loader.py` - Carregamento de Arquivos

Funções para carregar e processar diferentes tipos de arquivos.

```python
from app.utils.file_loader import (
    load_pdf,
    load_csv,
    load_json,
    extract_text_from_pdf
)

# Carregar PDF para RAG
documents = load_pdf("./datasets/pdf/governance/COBIT.pdf")

# Carregar CSV
df = load_csv("./datasets/csv/governance_metrics.csv")

# Extrair texto de PDF
text = extract_text_from_pdf("./document.pdf")
```

### 📝 `log_manager.py` - Gerenciamento de Logs

Sistema centralizado de gerenciamento de logs.

```python
from app.utils.log_manager import LogManager

logger = LogManager("module_name")

# Níveis de log
logger.info("Operação concluída com sucesso")
logger.warning("Atenção: recurso quase esgotado")
logger.error("Erro ao processar requisição", exc_info=True)
logger.debug("Dados de debug: %s", data)

# Log estruturado
logger.log_event(
    event="user_login",
    user_id="123",
    ip_address="192.168.1.1"
)
```

### 📋 `logger.py` - Configuração de Logging

Configuração base do sistema de logging.

```python
from app.utils.logger import setup_logger, get_logger

# Configurar logger global
setup_logger(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file_path="./logs/app.log"
)

# Obter logger
logger = get_logger(__name__)
```

### 🔐 `login.py` - Utilitários de Autenticação

Funções relacionadas à autenticação e autorização.

```python
from app.utils.login import (
    get_current_user,
    create_access_token,
    verify_token,
    hash_password,
    verify_password
)

# Dependency para rotas protegidas
from fastapi import Depends

@router.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.id}

# Criar token JWT
token = create_access_token(
    data={"sub": user_id},
    expires_delta=timedelta(hours=24)
)

# Hash de senha
hashed = hash_password("minha_senha")
is_valid = verify_password("minha_senha", hashed)
```

### 📊 `report_writer.py` - Geração de Relatórios

Funções para gerar relatórios em diversos formatos.

```python
from app.utils.report_writer import ReportWriter

writer = ReportWriter()

# Gerar relatório JSON
report = writer.generate_json_report(
    title="Análise de Governança",
    data=analysis_results,
    metadata={"version": "1.0"}
)

# Gerar relatório Markdown
md_report = writer.generate_markdown_report(
    title="Relatório de Segurança",
    sections=[
        {"title": "Vulnerabilidades", "content": vulns},
        {"title": "Recomendações", "content": recs}
    ]
)

# Salvar relatório
writer.save_report(report, "./reports/analysis.json")
```

### 🐍 `venv_utils.py` - Utilitários de Ambiente Virtual

Funções para gerenciar ambientes virtuais Python.

```python
from app.utils.venv_utils import (
    create_venv,
    activate_venv,
    install_packages,
    get_installed_packages,
    delete_venv
)

# Criar ambiente virtual
venv_path = create_venv(
    path="./projects/myproject/venv",
    python_version="3.11"
)

# Instalar pacotes
install_packages(
    venv_path=venv_path,
    packages=["fastapi", "uvicorn", "pydantic"]
)

# Listar pacotes instalados
packages = get_installed_packages(venv_path)
```

### 🔢 `versioning.py` - Controle de Versão

Funções para gerenciar versionamento de projetos.

```python
from app.utils.versioning import (
    get_version,
    increment_version,
    parse_version,
    compare_versions
)

# Obter versão atual
current = get_version("./pyproject.toml")  # "1.2.3"

# Incrementar versão
new_version = increment_version(current, "minor")  # "1.3.0"

# Comparar versões
is_newer = compare_versions("2.0.0", "1.9.9")  # True
```

## 📝 Boas Práticas

### Funções Puras

```python
# ✅ Bom: Função pura sem efeitos colaterais
def format_date(dt: datetime, format: str = "%Y-%m-%d") -> str:
    return dt.strftime(format)

# ❌ Evitar: Funções com efeitos colaterais ocultos
def format_date_bad(dt: datetime) -> str:
    logging.info(f"Formatando data: {dt}")  # Efeito colateral
    return dt.strftime("%Y-%m-%d")
```

### Type Hints

```python
from typing import Optional, List, Dict, Any

def process_data(
    data: Dict[str, Any],
    filters: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Processa dados aplicando filtros opcionais.
    
    Args:
        data: Dicionário com dados a processar
        filters: Lista opcional de campos a manter
    
    Returns:
        Dicionário processado
    """
    if filters:
        return {k: v for k, v in data.items() if k in filters}
    return data
```

## 🔗 Links Relacionados

- [⚙️ Core](../core/README.md)
- [🔧 Services](../services/README.md)
- [🌐 Routers](../routers/README.md)

---

<div align="center">

**🛠️ Ferramentas auxiliares para o PulsoAPI**

</div>
