# Implementação de Perfis no Backend Python

## Estrutura de Arquivos a Criar

Seguindo o padrão modular existente (`services/login`, `routers/login`, `storage/database/login`), você deve criar:

```
backend/
├── routers/
│   └── profiles.py          # ✅ NOVO - Rotas de perfis
├── services/
│   └── profiles.py          # ✅ NOVO - Lógica de negócio
└── storage/
    └── database/
        └── profiles.py      # ✅ NOVO - Operações no MongoDB
```

---

## 1. Storage/Database - `storage/database/profiles.py`

**Responsabilidade**: Operações diretas com MongoDB

```python
from typing import Optional, List
from datetime import datetime
from pymongo.collection import Collection
from bson import ObjectId
from bson.errors import InvalidId

class ProfileRepository:
    """Repositório para operações de perfis no MongoDB"""
    
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def create_profile(
        self, 
        user_id: str, 
        name: str, 
        description: Optional[str] = None
    ) -> dict:
        """
        Cria um novo perfil no banco de dados
        
        Args:
            user_id: ID do usuário (string)
            name: Nome do perfil
            description: Descrição opcional do perfil
            
        Returns:
            dict: Perfil criado com _id convertido para string
        """
        profile_doc = {
            "userId": user_id,
            "name": name.strip(),
            "description": description.strip() if description else None,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        result = self.collection.insert_one(profile_doc)
        profile_doc["id"] = str(result.inserted_id)
        profile_doc["_id"] = str(result.inserted_id)
        
        # Remove ObjectId do documento
        if "_id" in profile_doc and isinstance(profile_doc["_id"], ObjectId):
            profile_doc["_id"] = str(profile_doc["_id"])
        
        return profile_doc
    
    def get_profile_by_id(self, profile_id: str, user_id: str) -> Optional[dict]:
        """
        Busca um perfil por ID, garantindo que pertence ao usuário
        
        Args:
            profile_id: ID do perfil
            user_id: ID do usuário (para validação de segurança)
            
        Returns:
            dict ou None: Perfil encontrado ou None
        """
        try:
            profile = self.collection.find_one({
                "_id": ObjectId(profile_id),
                "userId": user_id
            })
            
            if profile:
                profile["id"] = str(profile["_id"])
                profile["_id"] = str(profile["_id"])
            
            return profile
        except (InvalidId, TypeError):
            return None
    
    def get_profiles_by_user(self, user_id: str) -> List[dict]:
        """
        Busca todos os perfis de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            List[dict]: Lista de perfis do usuário
        """
        profiles = list(self.collection.find(
            {"userId": user_id},
            sort=[("createdAt", -1)]  # Mais recentes primeiro
        ))
        
        # Converte ObjectId para string
        for profile in profiles:
            profile["id"] = str(profile["_id"])
            profile["_id"] = str(profile["_id"])
        
        return profiles
    
    def count_profiles_by_user(self, user_id: str) -> int:
        """
        Conta quantos perfis um usuário possui
        
        Args:
            user_id: ID do usuário
            
        Returns:
            int: Número de perfis
        """
        return self.collection.count_documents({"userId": user_id})
    
    def update_profile(
        self, 
        profile_id: str, 
        user_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[dict]:
        """
        Atualiza um perfil
        
        Args:
            profile_id: ID do perfil
            user_id: ID do usuário (validação de segurança)
            name: Novo nome (opcional)
            description: Nova descrição (opcional)
            
        Returns:
            dict ou None: Perfil atualizado ou None se não encontrado
        """
        try:
            update_data = {"updatedAt": datetime.utcnow()}
            
            if name is not None:
                update_data["name"] = name.strip()
            if description is not None:
                update_data["description"] = description.strip() if description else None
            
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(profile_id), "userId": user_id},
                {"$set": update_data},
                return_document=True
            )
            
            if result:
                result["id"] = str(result["_id"])
                result["_id"] = str(result["_id"])
            
            return result
        except (InvalidId, TypeError):
            return None
    
    def delete_profile(self, profile_id: str, user_id: str) -> bool:
        """
        Deleta um perfil
        
        Args:
            profile_id: ID do perfil
            user_id: ID do usuário (validação de segurança)
            
        Returns:
            bool: True se deletado, False caso contrário
        """
        try:
            result = self.collection.delete_one({
                "_id": ObjectId(profile_id),
                "userId": user_id
            })
            return result.deleted_count > 0
        except (InvalidId, TypeError):
            return False
```

---

## 2. Services - `services/profiles.py`

**Responsabilidade**: Lógica de negócio e validações

```python
from typing import Optional
from fastapi import HTTPException, status
from storage.database.profiles import ProfileRepository

class ProfileService:
    """Serviço de negócio para perfis"""
    
    MAX_PROFILES_PER_USER = 5
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 50
    MAX_DESCRIPTION_LENGTH = 200
    
    def __init__(self, profile_repo: ProfileRepository):
        self.profile_repo = profile_repo
    
    def validate_profile_name(self, name: str) -> None:
        """
        Valida o nome do perfil
        
        Raises:
            HTTPException: Se o nome for inválido
        """
        name = name.strip()
        
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do perfil é obrigatório"
            )
        
        if len(name) < self.MIN_NAME_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nome deve ter no mínimo {self.MIN_NAME_LENGTH} caractere"
            )
        
        if len(name) > self.MAX_NAME_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nome deve ter no máximo {self.MAX_NAME_LENGTH} caracteres"
            )
    
    def validate_profile_description(self, description: Optional[str]) -> None:
        """
        Valida a descrição do perfil
        
        Raises:
            HTTPException: Se a descrição for inválida
        """
        if description and len(description.strip()) > self.MAX_DESCRIPTION_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Descrição deve ter no máximo {self.MAX_DESCRIPTION_LENGTH} caracteres"
            )
    
    def check_profile_limit(self, user_id: str) -> None:
        """
        Verifica se o usuário pode criar mais perfis
        
        Raises:
            HTTPException: Se o limite de perfis foi atingido
        """
        current_count = self.profile_repo.count_profiles_by_user(user_id)
        
        if current_count >= self.MAX_PROFILES_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite de {self.MAX_PROFILES_PER_USER} perfis atingido"
            )
    
    def create_profile(
        self, 
        user_id: str, 
        name: str, 
        description: Optional[str] = None
    ) -> dict:
        """
        Cria um novo perfil com todas as validações
        
        Args:
            user_id: ID do usuário
            name: Nome do perfil
            description: Descrição opcional
            
        Returns:
            dict: Perfil criado
            
        Raises:
            HTTPException: Se alguma validação falhar
        """
        # Validações
        self.validate_profile_name(name)
        self.validate_profile_description(description)
        self.check_profile_limit(user_id)
        
        # Cria o perfil
        profile = self.profile_repo.create_profile(
            user_id=user_id,
            name=name,
            description=description
        )
        
        return profile
    
    def get_user_profiles(self, user_id: str) -> list:
        """
        Busca todos os perfis de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            list: Lista de perfis
        """
        return self.profile_repo.get_profiles_by_user(user_id)
    
    def get_profile(self, profile_id: str, user_id: str) -> dict:
        """
        Busca um perfil específico
        
        Args:
            profile_id: ID do perfil
            user_id: ID do usuário
            
        Returns:
            dict: Perfil encontrado
            
        Raises:
            HTTPException: Se o perfil não for encontrado
        """
        profile = self.profile_repo.get_profile_by_id(profile_id, user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        return profile
    
    def update_profile(
        self,
        profile_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        """
        Atualiza um perfil
        
        Args:
            profile_id: ID do perfil
            user_id: ID do usuário
            name: Novo nome (opcional)
            description: Nova descrição (opcional)
            
        Returns:
            dict: Perfil atualizado
            
        Raises:
            HTTPException: Se validações falharem ou perfil não encontrado
        """
        # Validações
        if name is not None:
            self.validate_profile_name(name)
        if description is not None:
            self.validate_profile_description(description)
        
        # Atualiza
        profile = self.profile_repo.update_profile(
            profile_id=profile_id,
            user_id=user_id,
            name=name,
            description=description
        )
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        return profile
    
    def delete_profile(self, profile_id: str, user_id: str) -> None:
        """
        Deleta um perfil
        
        Args:
            profile_id: ID do perfil
            user_id: ID do usuário
            
        Raises:
            HTTPException: Se o perfil não for encontrado
        """
        deleted = self.profile_repo.delete_profile(profile_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
```

---

## 3. Routers - `routers/profiles.py`

**Responsabilidade**: Endpoints HTTP e integração com FastAPI

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Importações dos seus módulos existentes
from services.profiles import ProfileService
from storage.database.profiles import ProfileRepository
from routers.login import get_current_user  # Assumindo que você tem essa função

router = APIRouter(prefix="/profiles", tags=["profiles"])

# ========== SCHEMAS (Pydantic Models) ==========

class ProfileCreate(BaseModel):
    """Schema para criação de perfil"""
    name: str = Field(..., min_length=1, max_length=50, description="Nome do perfil")
    description: Optional[str] = Field(None, max_length=200, description="Descrição do perfil")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Produção",
                "description": "Perfil para ambiente de produção"
            }
        }

class ProfileUpdate(BaseModel):
    """Schema para atualização de perfil"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class ProfileResponse(BaseModel):
    """Schema de resposta do perfil"""
    id: str
    name: str
    description: Optional[str]
    userId: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

# ========== DEPENDENCIES ==========

def get_profile_service(db: Database = Depends(get_database)) -> ProfileService:
    """
    Dependency para obter o ProfileService
    
    Nota: Você precisa criar get_database() seguindo o padrão do seu projeto
    """
    collection = db["profiles"]  # Nome da coleção no MongoDB
    profile_repo = ProfileRepository(collection)
    return ProfileService(profile_repo)

# ========== ENDPOINTS ==========

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProfileResponse)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Cria um novo perfil para o usuário autenticado
    
    - **name**: Nome do perfil (obrigatório, 1-50 caracteres)
    - **description**: Descrição opcional (máximo 200 caracteres)
    
    Limite: 5 perfis por usuário
    """
    try:
        profile = profile_service.create_profile(
            user_id=current_user["id"],  # Ajuste conforme sua estrutura de usuário
            name=profile_data.name,
            description=profile_data.description
        )
        return ProfileResponse(**profile)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar perfil: {str(e)}"
        )

@router.get("", response_model=list[ProfileResponse])
async def get_profiles(
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Lista todos os perfis do usuário autenticado
    """
    profiles = profile_service.get_user_profiles(current_user["id"])
    return [ProfileResponse(**profile) for profile in profiles]

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Busca um perfil específico por ID
    """
    profile = profile_service.get_profile(profile_id, current_user["id"])
    return ProfileResponse(**profile)

@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Atualiza um perfil existente
    """
    profile = profile_service.update_profile(
        profile_id=profile_id,
        user_id=current_user["id"],
        name=profile_data.name,
        description=profile_data.description
    )
    return ProfileResponse(**profile)

@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Deleta um perfil
    """
    profile_service.delete_profile(profile_id, current_user["id"])
    return None
```

---

## 4. Integração no App Principal

No seu arquivo principal (ex: `main.py` ou `app.py`):

```python
from fastapi import FastAPI
from routers import profiles  # Importar o router de perfis

app = FastAPI()

# Registrar o router de perfis
app.include_router(profiles.router)

# Seus outros routers...
# app.include_router(login.router)
```

---

## 5. Estrutura no MongoDB

### Coleção: `profiles`

```javascript
{
  "_id": ObjectId("..."),
  "userId": "string",           // ID do usuário (string)
  "name": "string",             // Nome do perfil (1-50 caracteres)
  "description": "string",       // Descrição opcional (máximo 200 caracteres)
  "createdAt": ISODate("..."),   // Data de criação
  "updatedAt": ISODate("...")    // Data de atualização
}
```

### Índices Recomendados

```python
# No seu script de inicialização do banco
db.profiles.create_index([("userId", 1), ("name", 1)], unique=True)
db.profiles.create_index("userId")
db.profiles.create_index("createdAt")
```

---

## 6. Validações e Regras de Negócio

### Validações Implementadas:
- ✅ Nome obrigatório (1-50 caracteres)
- ✅ Descrição opcional (máximo 200 caracteres)
- ✅ Limite de 5 perfis por usuário
- ✅ Autenticação obrigatória (Bearer Token)
- ✅ Usuário só pode acessar seus próprios perfis
- ✅ Validação de ObjectId do MongoDB

### Códigos HTTP:
- `201 Created`: Perfil criado com sucesso
- `200 OK`: Listagem ou atualização bem-sucedida
- `204 No Content`: Perfil deletado
- `400 Bad Request`: Validação falhou ou limite atingido
- `401 Unauthorized`: Token inválido ou ausente
- `404 Not Found`: Perfil não encontrado
- `500 Internal Server Error`: Erro no servidor

---

## 7. Exemplo de Uso da API

### Criar Perfil
```bash
POST /profiles
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Produção",
  "description": "Perfil para ambiente de produção"
}
```

### Listar Perfis
```bash
GET /profiles
Authorization: Bearer <token>
```

### Buscar Perfil Específico
```bash
GET /profiles/{profile_id}
Authorization: Bearer <token>
```

### Atualizar Perfil
```bash
PUT /profiles/{profile_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Produção Atualizado",
  "description": "Nova descrição"
}
```

### Deletar Perfil
```bash
DELETE /profiles/{profile_id}
Authorization: Bearer <token>
```

---

## 8. Notas de Implementação

1. **get_current_user**: Ajuste conforme sua implementação de autenticação existente
2. **get_database**: Ajuste conforme sua conexão com MongoDB
3. **Estrutura de usuário**: Ajuste `current_user["id"]` conforme sua estrutura
4. **Tratamento de erros**: Personalize conforme suas necessidades
5. **Logging**: Considere adicionar logs nas operações críticas

---

## 9. Testes Recomendados

- ✅ Criar perfil válido
- ✅ Tentar criar perfil sem nome
- ✅ Tentar criar perfil com nome muito longo
- ✅ Tentar criar mais de 5 perfis
- ✅ Listar perfis do usuário
- ✅ Buscar perfil inexistente
- ✅ Tentar acessar perfil de outro usuário
- ✅ Atualizar perfil
- ✅ Deletar perfil

