# 💾 Storage - Camada de Persistência

<div align="center">

![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-00ADD8?style=for-the-badge&logoColor=white)

**Acesso a bancos de dados e armazenamento vetorial**

</div>

---

## 📋 Visão Geral

O diretório `storage/` é responsável pela **persistência de dados** da aplicação, incluindo:

- ✅ Acesso ao MongoDB (banco principal)
- ✅ Acesso ao MySQL (consultas ID)
- ✅ Armazenamento vetorial FAISS (RAG)

## 📁 Estrutura de Diretórios

```
storage/
├── 📂 database/                 # Acesso a bancos de dados
│   ├── correct_analyse/            # Dados de correção
│   │   ├── autocor_database.py
│   │   ├── code_plan_database.py
│   │   └── code_writer_database.py
│   │
│   ├── creation_analyse/           # Dados de criação (C1, C2, C3)
│   │   ├── database_c1.py             # Camada 1 - Governança
│   │   ├── database_c2.py             # Camada 2 - Arquitetura
│   │   └── database_c3.py             # Camada 3 - Execução
│   │
│   ├── deploy_database/            # Dados de deploy
│   │   └── deploy_database.py
│   │
│   ├── ID_database/                # Consultas MySQL
│   │   └── query_get_database.py
│   │
│   ├── login/                      # Dados de autenticação
│   │   └── database_login.py
│   │
│   ├── profile/                    # Dados de perfis
│   │   ├── database_profile.py
│   │   ├── database_profile_invites.py
│   │   └── database_profile_members.py
│   │
│   ├── subscription/               # Dados de assinatura
│   │   └── database_subscription.py
│   │
│   ├── database_core.py            # Conexão MongoDB core
│   └── fix_profiles_index.py       # Script de correção de índices
│
└── 📦 vectorstore/              # Armazenamento vetorial
    └── faiss_governance/           # Índice FAISS para RAG
        ├── index.faiss
        └── index.pkl
```

## 🔌 Conexões de Banco de Dados

### MongoDB (Principal)

```python
from app.storage.database.database_core import get_database

# Obter conexão
db = get_database()

# Acessar coleção
users = db["users"]
result = await users.find_one({"email": "user@example.com"})
```

### MySQL (Consultas ID)

```python
from app.storage.database.ID_database.query_get_database import QueryDatabase

db = QueryDatabase()
result = db.execute("SELECT * FROM entities WHERE id = %s", [entity_id])
```

## 📊 Estrutura de Coleções MongoDB

### Coleções Principais

| Coleção | Descrição |
|---------|-----------|
| `users` | Dados de usuários |
| `profiles` | Perfis de usuários |
| `profile_invites` | Convites pendentes |
| `profile_members` | Membros de perfis |
| `subscriptions` | Dados de assinaturas |
| `projects` | Projetos criados |

### Coleções de Camadas

| Coleção | Camada | Descrição |
|---------|--------|-----------|
| `governance_docs` | C1 | Documentos de governança |
| `architecture_plans` | C2 | Planos de arquitetura |
| `execution_results` | C3 | Resultados de execução |

### Coleções de Correção

| Coleção | Descrição |
|---------|-----------|
| `correction_plans` | Planos de correção (C2b) |
| `code_writes` | Escritas de código (C3) |
| `implementations` | Implementações (C4) |

## 🔍 Repositórios por Domínio

### `database_login.py`

```python
class LoginDatabase:
    async def create_user(user_data: dict) -> str
    async def find_user_by_email(email: str) -> Optional[dict]
    async def update_user(user_id: str, data: dict) -> bool
    async def save_refresh_token(user_id: str, token: str) -> None
```

### `database_profile.py`

```python
class ProfileDatabase:
    async def get_profile(user_id: str) -> Optional[dict]
    async def update_profile(user_id: str, data: dict) -> bool
    async def delete_profile(user_id: str) -> bool
```

### `database_subscription.py`

```python
class SubscriptionDatabase:
    async def create_subscription(data: dict) -> str
    async def get_subscription(user_id: str) -> Optional[dict]
    async def update_subscription_status(sub_id: str, status: str) -> bool
    async def get_by_stripe_id(stripe_sub_id: str) -> Optional[dict]
```

### `creation_analyse/`

```python
# database_c1.py - Governança
class DatabaseC1:
    async def save_governance_doc(doc: dict) -> str
    async def get_governance_doc(doc_id: str) -> Optional[dict]

# database_c2.py - Arquitetura  
class DatabaseC2:
    async def save_architecture_plan(plan: dict) -> str
    async def get_architecture_plan(plan_id: str) -> Optional[dict]

# database_c3.py - Execução
class DatabaseC3:
    async def save_execution_result(result: dict) -> str
    async def get_execution_result(result_id: str) -> Optional[dict]
```

## 📦 Armazenamento Vetorial (FAISS)

O diretório `vectorstore/` armazena índices FAISS para busca vetorial no RAG.

### Estrutura do Índice

```
vectorstore/
└── faiss_governance/
    ├── index.faiss      # Vetores indexados
    └── index.pkl        # Metadados e mapeamentos
```

### Uso do FAISS

```python
from langchain.vectorstores import FAISS
from app.core.openai.openai_client import get_embeddings

# Carregar índice existente
vectorstore = FAISS.load_local(
    "app/storage/vectorstore/faiss_governance",
    embeddings=get_embeddings()
)

# Buscar documentos similares
docs = vectorstore.similarity_search(query, k=5)
```

## 🛡️ Boas Práticas

### Padrão Repository

```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List

class BaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.collection = db[collection_name]
    
    async def find_one(self, filter: dict) -> Optional[dict]:
        return await self.collection.find_one(filter)
    
    async def find_many(self, filter: dict) -> List[dict]:
        cursor = self.collection.find(filter)
        return await cursor.to_list(length=100)
    
    async def insert_one(self, document: dict) -> str:
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def update_one(self, filter: dict, update: dict) -> bool:
        result = await self.collection.update_one(filter, {"$set": update})
        return result.modified_count > 0
```

### Índices MongoDB

```python
# Script de criação de índices
async def create_indexes(db):
    # Índice único para email
    await db.users.create_index("email", unique=True)
    
    # Índice composto
    await db.projects.create_index([
        ("user_id", 1),
        ("created_at", -1)
    ])
```

## 🔗 Links Relacionados

- [📂 Database](./database/README.md)
- [📦 Vectorstore](./vectorstore/README.md)
- [⚙️ Core Connection](../core/README.md)

---

<div align="center">

**💾 Persistência confiável para o PulsoAPI**

</div>
