# ⚙️ Core - Núcleo do Sistema

<div align="center">

![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**Configurações centrais, clientes e integrações do sistema**

</div>

---

## 📋 Visão Geral

O diretório `core/` contém as **configurações fundamentais** e **integrações essenciais** que sustentam toda a aplicação PulsoAPI. Aqui estão centralizados os clientes de serviços externos, configurações de ambiente e componentes de infraestrutura.

## 📁 Estrutura de Diretórios

```
core/
├── 📂 app/                  # Configurações da aplicação
│   └── config.py               # Variáveis de ambiente e settings
│
├── 🔌 ID_core/              # Conexão com banco MySQL
│   └── mysql_connection.py     # Cliente MySQL para consultas ID
│
├── 🤖 openai/               # Integração com OpenAI e RAG
│   ├── agent_base.py           # Classe base abstrata para agentes
│   ├── generative_trainer.py   # Treinamento generativo
│   ├── openai_client.py        # Wrapper do cliente OpenAI
│   └── rag_trainer.py          # Treinamento RAG com FAISS
│
├── 🎯 pulso/                # Configurações PulsoCSA
│   ├── config.py               # Configurações gerais do Pulso
│   └── cors.py                 # Configuração de CORS
│
└── 📦 storage/              # Armazenamento vetorial
    └── vectorstore/
        └── faiss_governance/   # Índice FAISS para RAG
```

## 🔌 Módulos Detalhados

### 📂 `app/` - Configurações da Aplicação

Gerencia variáveis de ambiente e configurações globais.

```python
# Exemplo de uso
from app.core.app.config import settings

DATABASE_URL = settings.MONGODB_URI
OPENAI_KEY = settings.OPENAI_API_KEY
```

### 🔌 `ID_core/` - Conexão MySQL

Módulo especializado para consultas ao banco de dados MySQL.

| Arquivo | Função |
|---------|--------|
| `mysql_connection.py` | Gerencia conexões e queries MySQL |

```python
from app.core.ID_core.mysql_connection import MySQLConnection

conn = MySQLConnection()
result = conn.execute_query("SELECT * FROM users")
```

### 🤖 `openai/` - Integração OpenAI & RAG

Núcleo de inteligência artificial do sistema.

| Arquivo | Responsabilidade |
|---------|------------------|
| `agent_base.py` | Classe base abstrata para todos os agentes |
| `openai_client.py` | Wrapper do cliente OpenAI com retry e logging |
| `rag_trainer.py` | Treinamento e indexação RAG com FAISS |
| `generative_trainer.py` | Treinamento de modelos generativos |

#### Diagrama de Integração

```
┌─────────────────┐
│   OpenAI API    │
└────────┬────────┘
         │
┌────────▼────────┐
│  openai_client  │  ◄── Wrapper com retry, logging, rate limiting
└────────┬────────┘
         │
┌────────▼────────┐
│   agent_base    │  ◄── Classe base para agentes
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│  RAG  │ │ Gen.  │  ◄── Trainers especializados
│Trainer│ │Trainer│
└───────┘ └───────┘
```

### 🎯 `pulso/` - Configurações Pulso

Configurações específicas do sistema PulsoCSA.

| Arquivo | Função |
|---------|--------|
| `config.py` | Configurações gerais (timeouts, limites, etc.) |
| `cors.py` | Configuração de Cross-Origin Resource Sharing |

```python
from app.core.pulso.cors import configure_cors

app = FastAPI()
configure_cors(app)  # Aplica configurações CORS
```

### 📦 `storage/` - Armazenamento Vetorial

Diretório para armazenamento de índices FAISS.

```
storage/
└── vectorstore/
    └── faiss_governance/
        ├── index.faiss      # Índice vetorial
        └── index.pkl        # Metadados
```

## 🔧 Configurações de Ambiente

Variáveis de ambiente necessárias:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `OPENAI_API_KEY` | Chave da API OpenAI | `sk-...` |
| `MONGODB_URI` | URI de conexão MongoDB | `mongodb://localhost:27017` |
| `MYSQL_HOST` | Host do banco MySQL | `localhost` |
| `MYSQL_USER` | Usuário MySQL | `root` |
| `MYSQL_PASSWORD` | Senha MySQL | `****` |
| `JWT_SECRET` | Segredo para tokens JWT | `your-secret-key` |

## 🚀 Inicialização

```python
# Exemplo de inicialização do core
from app.core.openai.openai_client import OpenAIClient
from app.core.ID_core.mysql_connection import MySQLConnection
from app.core.pulso.config import PulsoConfig

# Inicializar cliente OpenAI
openai = OpenAIClient()

# Inicializar conexão MySQL
mysql = MySQLConnection()

# Carregar configurações
config = PulsoConfig()
```

## 🔗 Links Relacionados

- [🤖 OpenAI Integration](./openai/README.md)
- [🔌 ID Core](./ID_core/README.md)
- [🎯 Pulso Config](./pulso/README.md)
- [📦 Storage](./storage/README.md)

---

<div align="center">

**⚙️ Fundação sólida para o PulsoAPI**

</div>
