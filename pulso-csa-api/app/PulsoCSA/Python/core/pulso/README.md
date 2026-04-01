# 🎯 Pulso Config - Configurações do Sistema

<div align="center">

![Config](https://img.shields.io/badge/Configuration-FF9800?style=for-the-badge&logoColor=white)
![CORS](https://img.shields.io/badge/CORS-4CAF50?style=for-the-badge&logoColor=white)

**Configurações centrais do sistema PulsoCSA**

</div>

---

## 📋 Visão Geral

O módulo `pulso/` contém as **configurações centrais** do sistema:

- ⚙️ Configurações gerais da aplicação
- 🌐 Configuração de CORS
- 🔧 Parâmetros de execução

## 📁 Estrutura

```
pulso/
├── 📄 config.py    # Configurações gerais
└── 📄 cors.py      # Configuração de CORS
```

## 🔍 Componentes

### `config.py`

Configurações gerais do sistema.

```python
from pydantic_settings import BaseSettings
from typing import List

class PulsoConfig(BaseSettings):
    """
    Configurações do sistema Pulso.
    """
    
    # Aplicação
    APP_NAME: str = "PulsoAPI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_PREFIX: str = "/api/v1"
    API_TIMEOUT: int = 30
    
    # Banco de dados
    MONGODB_URI: str
    DATABASE_NAME: str = "pulso"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo"
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 3600  # segundos
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # segundos
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instância global
settings = PulsoConfig()
```

### `cors.py`

Configuração de Cross-Origin Resource Sharing.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

def configure_cors(app: FastAPI) -> None:
    """
    Configura CORS para a aplicação FastAPI.
    
    Args:
        app: Instância da aplicação FastAPI
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining"]
    )
```

## 📝 Exemplo de Uso

```python
from app.core.pulso.config import settings
from app.core.pulso.cors import configure_cors
from fastapi import FastAPI

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configurar CORS
configure_cors(app)

# Usar configurações
@app.get("/info")
async def get_info():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
```

## 🔧 Variáveis de Ambiente

```env
# Aplicação
APP_NAME=PulsoAPI
DEBUG=false

# Banco de dados
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=pulso

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo

# Autenticação
JWT_SECRET=your-super-secret-key
JWT_EXPIRATION=3600

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# CORS
CORS_ORIGINS=["http://localhost:3000","https://app.pulso.com"]
```

## 🔗 Links Relacionados

- [⚙️ Core](../README.md)
- [🤖 OpenAI](../openai/README.md)
- [📱 App](../../README.md)

---

<div align="center">

**🎯 Configurações centralizadas do PulsoAPI**

</div>
