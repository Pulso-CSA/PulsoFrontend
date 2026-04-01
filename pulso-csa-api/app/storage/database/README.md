# 💾 Database - Acesso a Bancos de Dados

<div align="center">

![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**Camada de acesso a dados - Repositórios e conexões**

</div>

---

## 📋 Visão Geral

O diretório `database/` contém os **repositórios de acesso a dados**:

- 🍃 Repositórios MongoDB (principal)
- 🐬 Repositórios MySQL (consultas ID)
- 🔧 Conexões e configurações

## 📁 Estrutura de Diretórios

```
database/
├── 📄 database_core.py          # Conexão MongoDB core
├── 📄 fix_profiles_index.py     # Script de correção de índices
│
├── 📂 correct_analyse/          # Dados de correção
│   ├── autocor_database.py
│   ├── code_plan_database.py
│   └── code_writer_database.py
│
├── 📂 creation_analyse/         # Dados de criação (C1, C2, C3)
│   ├── database_c1.py              # Camada 1 - Governança
│   ├── database_c2.py              # Camada 2 - Arquitetura
│   └── database_c3.py              # Camada 3 - Execução
│
├── 📂 deploy_database/          # Dados de deploy
│   └── deploy_database.py
│
├── 📂 ID_database/              # Consultas MySQL
│   └── query_get_database.py
│
├── 📂 login/                    # Dados de autenticação
│   └── database_login.py
│
├── 📂 profile/                  # Dados de perfis
│   ├── database_profile.py
│   ├── database_profile_invites.py
│   └── database_profile_members.py
│
└── 📂 subscription/             # Dados de assinatura
    └── database_subscription.py
```

## 🔌 Conexão Principal

### `database_core.py`

```python
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class DatabaseCore:
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect(cls):
        """Estabelece conexão com MongoDB."""
        cls.client = AsyncIOMotorClient(settings.MONGODB_URI)
        
    @classmethod
    def get_database(cls):
        """Retorna instância do banco de dados."""
        return cls.client[settings.DATABASE_NAME]
    
    @classmethod
    async def close(cls):
        """Fecha conexão."""
        if cls.client:
            cls.client.close()
```

## 📊 Repositórios por Domínio

### Camadas de Criação

| Repositório | Coleção | Descrição |
|-------------|---------|-----------|
| `database_c1.py` | `governance_docs` | Documentos de governança |
| `database_c2.py` | `architecture_plans` | Planos de arquitetura |
| `database_c3.py` | `execution_results` | Resultados de execução |

### Correção de Código

| Repositório | Coleção | Descrição |
|-------------|---------|-----------|
| `autocor_database.py` | `auto_corrections` | Correções automáticas |
| `code_plan_database.py` | `correction_plans` | Planos de correção |
| `code_writer_database.py` | `code_writes` | Escritas de código |

### Autenticação e Perfis

| Repositório | Coleção | Descrição |
|-------------|---------|-----------|
| `database_login.py` | `users` | Dados de usuários |
| `database_profile.py` | `profiles` | Perfis de usuário |
| `database_profile_invites.py` | `invites` | Convites pendentes |
| `database_profile_members.py` | `members` | Membros de times |

### Assinaturas e Deploy

| Repositório | Coleção | Descrição |
|-------------|---------|-----------|
| `database_subscription.py` | `subscriptions` | Dados de assinatura |
| `deploy_database.py` | `deploys` | Histórico de deploys |

## 📝 Padrão de Repositório

```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from bson import ObjectId

class BaseRepository:
    """Repositório base com operações CRUD."""
    
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.collection = db[collection_name]
    
    async def find_by_id(self, id: str) -> Optional[dict]:
        """Busca documento por ID."""
        return await self.collection.find_one({"_id": ObjectId(id)})
    
    async def find_many(
        self, 
        filter: dict, 
        limit: int = 100
    ) -> List[dict]:
        """Busca múltiplos documentos."""
        cursor = self.collection.find(filter)
        return await cursor.to_list(length=limit)
    
    async def insert_one(self, document: dict) -> str:
        """Insere um documento."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def update_one(
        self, 
        id: str, 
        update: dict
    ) -> bool:
        """Atualiza um documento."""
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update}
        )
        return result.modified_count > 0
    
    async def delete_one(self, id: str) -> bool:
        """Remove um documento."""
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
```

## 🔗 Links Relacionados

- [⚙️ Core](../../core/README.md)
- [🔧 Services](../../services/README.md)
- [📊 Models](../../models/README.md)

---

<div align="center">

**💾 Acesso a dados confiável e eficiente**

</div>
