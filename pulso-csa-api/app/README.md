# 📱 App - Core da Aplicação FastAPI

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

**Núcleo modular da aplicação PulsoAPI**

</div>

---

## 📋 Visão Geral

Este diretório contém o **core da aplicação FastAPI**, organizado em módulos especializados seguindo os princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**.

## 📁 Estrutura de Módulos

```
app/
├── 🤖 agents/         # Agentes de IA organizados por camada
├── ⚙️ core/           # Configurações, clientes e integrações
├── 📚 datasets/       # Dados para treinamento do sistema RAG
├── 📊 models/         # Schemas Pydantic (DTOs)
├── 📝 prompts/        # Templates de prompts para os agentes
├── 🌐 routers/        # Endpoints REST organizados por domínio
├── 🔧 services/       # Camada de lógica de negócio
├── 💾 storage/        # Acesso a dados (MongoDB, MySQL, FAISS)
├── 🧪 tests/          # Testes automatizados
├── 🛠️ utils/          # Utilitários e helpers
├── 🔄 workflow/       # Orquestração de workflows
└── 📄 main.py         # Ponto de entrada da aplicação
```

## 🏗️ Arquitetura

### Fluxo de Dados

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Routers   │───▶│  Services   │───▶│   Agents    │───▶│   Storage   │
│  (Entrada)  │    │  (Lógica)   │    │    (IA)     │    │   (Dados)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                 │                  │                   │
       ▼                 ▼                  ▼                   ▼
    Models           Validação          OpenAI/RAG       MongoDB/MySQL
```

### Camadas do Sistema

| Camada | Diretório | Responsabilidade |
|--------|-----------|------------------|
| **Apresentação** | `routers/` | Endpoints HTTP, validação de entrada |
| **Aplicação** | `services/` | Orquestração, regras de negócio |
| **Domínio** | `agents/` | Lógica de IA, processamento |
| **Infraestrutura** | `storage/`, `core/` | Persistência, integrações externas |

## 📄 Arquivo Principal: `main.py`

O arquivo `main.py` é responsável por:

- ✅ Inicialização da aplicação FastAPI
- ✅ Configuração de CORS
- ✅ Registro de todas as rotas
- ✅ Configuração de webhooks (Stripe)
- ✅ Middleware de logging

```python
# Exemplo de inicialização
from fastapi import FastAPI
from app.core.pulso.cors import configure_cors

app = FastAPI(title="PulsoAPI", version="1.0.0")
configure_cors(app)
```

## 🔗 Módulos Detalhados

| Módulo | Descrição | Documentação |
|--------|-----------|--------------|
| 🤖 **agents/** | Agentes de IA (Governança, Arquitetura, Execução) | [Ver README](./agents/README.md) |
| ⚙️ **core/** | Configurações e integrações | [Ver README](./core/README.md) |
| 📚 **datasets/** | Dados para treinamento RAG | [Ver README](./datasets/README.md) |
| 📊 **models/** | Schemas Pydantic | [Ver README](./models/README.md) |
| 📝 **prompts/** | Templates de prompts | [Ver README](./prompts/README.md) |
| 🌐 **routers/** | Endpoints da API | [Ver README](./routers/README.md) |
| 🔧 **services/** | Lógica de negócio | [Ver README](./services/README.md) |
| 💾 **storage/** | Persistência de dados | [Ver README](./storage/README.md) |
| 🛠️ **utils/** | Funções utilitárias | [Ver README](./utils/README.md) |
| 🔄 **workflow/** | Orquestração de workflows | [Ver README](./workflow/README.md) |

## 🚀 Execução

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest app/tests/

# Testes com cobertura
pytest app/tests/ --cov=app
```

### Testes via cURL

```bash
# Health check
curl -s http://localhost:8000/

# Workflow completo
curl -s -X POST http://localhost:8000/governance/run -H "Content-Type: application/json" -d "{\"prompt\":\"criar API Flask com JWT\",\"usuario\":\"teste\"}"
```

---

<div align="center">

**🔧 Módulo central do PulsoAPI**

</div>
