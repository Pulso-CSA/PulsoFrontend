# Alterações Necessárias no Backend para Implementar Perfis

## ⚠️ IMPORTANTE: Não Criar Novos Arquivos

**Todas as funcionalidades de perfis devem ser adicionadas aos arquivos existentes do módulo de login. NÃO crie novos arquivos ou pastas.**

## Visão Geral

Para implementar o sistema de perfis que salva no MongoDB, você precisa **adicionar as funcionalidades aos arquivos existentes** do módulo de login. Ao invés de criar novos arquivos, você vai adicionar as funcionalidades de perfis nos mesmos arquivos do login.

---

## 1. `api\app\models\login_models\login_models.py`

### O que fazer:
**ADICIONAR modelos de perfil no arquivo existente**: `api\app\models\login_models\login_models.py`

### Descrição:
Você precisa **adicionar** modelos Pydantic para perfis no mesmo arquivo dos modelos de login. Os modelos devem incluir:

- **ProfileCreate**: Modelo para receber dados na criação (nome obrigatório, descrição opcional)
- **ProfileUpdate**: Modelo para atualização (ambos os campos opcionais)
- **ProfileResponse**: Modelo de resposta com todos os campos do perfil (id, nome, descrição, userId, datas)

**Campos importantes:**
- `name`: string, obrigatório, mínimo 1 caractere, máximo 50 caracteres
- `description`: string opcional, máximo 200 caracteres
- `userId`: string (vem do token de autenticação)
- `createdAt` e `updatedAt`: timestamps

**Validações a implementar:**
- Nome não pode ser vazio
- Nome deve ter entre 1 e 50 caracteres
- Descrição pode ser None ou ter no máximo 200 caracteres

---

## 2. `api\app\storage\database\login\database_login.py`

### O que fazer:
**ADICIONAR métodos de perfil no arquivo existente**: `api\app\storage\database\login\database_login.py`

### Descrição:
Você deve **adicionar métodos** para operações diretas com o MongoDB relacionadas a perfis na mesma classe do login. Adicione os seguintes métodos:

**Métodos a implementar:**

1. **create_profile**: 
   - Recebe userId, name e description
   - Insere documento na coleção "profiles"
   - Adiciona timestamps (createdAt, updatedAt)
   - Retorna o perfil criado com o ID convertido para string

2. **get_profile_by_id**:
   - Recebe profile_id e user_id
   - Busca o perfil no banco
   - **Importante**: Valida que o perfil pertence ao usuário (segurança)
   - Retorna o perfil ou None

3. **get_profiles_by_user**:
   - Recebe apenas user_id
   - Busca todos os perfis desse usuário
   - Ordena por data de criação (mais recentes primeiro)
   - Retorna lista de perfis

4. **count_profiles_by_user**:
   - Recebe user_id
   - Conta quantos perfis o usuário possui
   - Usado para validar limite de 5 perfis

5. **update_profile**:
   - Recebe profile_id, user_id e campos opcionais (name, description)
   - Atualiza apenas os campos fornecidos
   - Atualiza o campo updatedAt
   - Valida que o perfil pertence ao usuário
   - Retorna perfil atualizado ou None

6. **delete_profile**:
   - Recebe profile_id e user_id
   - Deleta o perfil
   - Valida que o perfil pertence ao usuário
   - Retorna True se deletado, False caso contrário

**Estrutura do documento no MongoDB:**
```
{
  "_id": ObjectId,
  "userId": "string",
  "name": "string",
  "description": "string ou null",
  "createdAt": datetime,
  "updatedAt": datetime
}
```

**Observações importantes:**
- Sempre validar que o perfil pertence ao usuário (segurança)
- Converter ObjectId para string ao retornar
- Tratar erros de ObjectId inválido
- Usar a mesma conexão/instância do MongoDB que você usa no login

---

## 3. `api\app\services\login\login_service.py`

### O que fazer:
**ADICIONAR métodos de perfil no arquivo existente**: `api\app\services\login\login_service.py`

### Descrição:
Você deve **adicionar métodos** de lógica de negócio e validações para perfis no mesmo arquivo do serviço de login. É aqui que você implementa as regras antes de salvar no banco.

**Métodos a implementar:**

1. **validate_profile_name**:
   - Valida se o nome não está vazio
   - Valida se tem entre 1 e 50 caracteres
   - Levanta exceção HTTPException se inválido

2. **validate_profile_description**:
   - Valida se a descrição tem no máximo 200 caracteres (se fornecida)
   - Levanta exceção HTTPException se inválido

3. **check_profile_limit**:
   - Verifica quantos perfis o usuário já possui
   - Se já tiver 5 perfis, levanta exceção HTTPException
   - Limite máximo: 5 perfis por usuário

4. **create_profile**:
   - Método principal para criar perfil
   - Chama todas as validações acima
   - Chama o método do database para criar
   - Retorna o perfil criado

5. **get_user_profiles**:
   - Busca todos os perfis do usuário
   - Retorna lista de perfis

6. **get_profile**:
   - Busca um perfil específico por ID
   - Valida que o perfil existe e pertence ao usuário
   - Levanta exceção 404 se não encontrado
   - Retorna o perfil

7. **update_profile**:
   - Atualiza um perfil existente
   - Valida os campos fornecidos
   - Chama o método do database para atualizar
   - Levanta exceção 404 se não encontrado
   - Retorna o perfil atualizado

8. **delete_profile**:
   - Deleta um perfil
   - Valida que o perfil existe e pertence ao usuário
   - Levanta exceção 404 se não encontrado

**Regras de negócio:**
- Máximo de 5 perfis por usuário
- Nome obrigatório (1-50 caracteres)
- Descrição opcional (máximo 200 caracteres)
- Usuário só pode acessar seus próprios perfis
- Todos os métodos devem validar autenticação (via dependency)

---

## 4. `api\app\routers\login_router\router_login.py`

### O que fazer:
**ADICIONAR rotas de perfil no arquivo existente**: `api\app\routers\login_router\router_login.py`

### Descrição:
Você deve **adicionar rotas** RESTful para gerenciar perfis no mesmo router do login. Adicione os seguintes endpoints:

**Endpoints a criar:**

1. **POST /profiles**:
   - Cria um novo perfil
   - Requer autenticação (Bearer Token)
   - Recebe: name (obrigatório), description (opcional)
   - Retorna: perfil criado (status 201)
   - Validações: nome válido, limite de 5 perfis

2. **GET /profiles**:
   - Lista todos os perfis do usuário autenticado
   - Requer autenticação
   - Retorna: lista de perfis (status 200)
   - Ordena por data de criação (mais recentes primeiro)

3. **GET /profiles/{profile_id}**:
   - Busca um perfil específico por ID
   - Requer autenticação
   - Valida que o perfil pertence ao usuário
   - Retorna: perfil encontrado (status 200)
   - Retorna 404 se não encontrado

4. **PUT /profiles/{profile_id}**:
   - Atualiza um perfil existente
   - Requer autenticação
   - Recebe: name e/ou description (opcionais)
   - Valida que o perfil pertence ao usuário
   - Retorna: perfil atualizado (status 200)
   - Retorna 404 se não encontrado

5. **DELETE /profiles/{profile_id}**:
   - Deleta um perfil
   - Requer autenticação
   - Valida que o perfil pertence ao usuário
   - Retorna: status 204 (sem conteúdo)
   - Retorna 404 se não encontrado

**Dependencies necessárias:**
- Usar a mesma função de autenticação do login (get_current_user)
- Reutilizar as dependencies existentes do login (service e database)
- Se necessário, adicionar métodos de perfil nas mesmas classes de service e database do login

**Códigos de status HTTP:**
- 201: Perfil criado
- 200: Sucesso (listagem, busca, atualização)
- 204: Perfil deletado
- 400: Validação falhou ou limite atingido
- 401: Não autenticado
- 404: Perfil não encontrado
- 500: Erro interno

**Observações:**
- Todos os endpoints devem usar a mesma autenticação do login
- Prefixo da rota: `/profiles`
- Tag para documentação: `profiles` (ou pode usar a mesma tag do login)
- Incluir tratamento de erros adequado
- **Importante:** Adicione as rotas no mesmo router do login, não crie um router separado

---

## 5. Integração no App Principal

### O que fazer:
**Nenhuma alteração necessária** no arquivo principal (provavelmente `main.py` ou `app.py`)

### Descrição:
Como as rotas de perfis foram adicionadas no mesmo router do login, não é necessário registrar um novo router. As rotas de perfis já estarão disponíveis através do router de login existente.

**Ação:**
- ❌ **Não é necessário fazer nada** - As rotas já estarão disponíveis no router existente

---

## 6. Estrutura de Pastas Final

Após adicionar as funcionalidades, sua estrutura permanece a mesma (sem novos arquivos):

```
api/
├── app/
│   ├── models/
│   │   └── login_models/
│   │       └── login_models.py        # ✅ ADICIONAR modelos de perfil aqui
│   │
│   ├── routers/
│   │   └── login_router/
│   │       └── router_login.py       # ✅ ADICIONAR rotas de perfil aqui
│   │
│   ├── services/
│   │   └── login/
│   │       └── login_service.py      # ✅ ADICIONAR lógica de perfil aqui
│   │
│   └── storage/
│       └── database/
│           └── login/
│               └── database_login.py  # ✅ ADICIONAR métodos de perfil aqui
```

**Observação:** Nenhum arquivo novo será criado. Todas as funcionalidades serão adicionadas aos arquivos existentes.

---

## 7. Resumo das Alterações

### Arquivos a ALTERAR (adicionar funcionalidades):
1. ✅ `api\app\models\login_models\login_models.py` - **ADICIONAR** modelos Pydantic de perfil
2. ✅ `api\app\storage\database\login\database_login.py` - **ADICIONAR** métodos de operações MongoDB para perfis
3. ✅ `api\app\services\login\login_service.py` - **ADICIONAR** lógica de negócio de perfis
4. ✅ `api\app\routers\login_router\router_login.py` - **ADICIONAR** endpoints HTTP de perfis

### Arquivos a CRIAR:
- ❌ **Nenhum arquivo novo** - Todas as funcionalidades serão adicionadas aos arquivos existentes

### Arquivo Principal:
- ❌ **Nenhuma alteração necessária** - As rotas já estarão disponíveis no router existente

---

## 8. Checklist de Implementação

- [ ] **Adicionar** modelos Pydantic de perfil em `login_models.py`
- [ ] **Adicionar** métodos de perfil em `database_login.py` (create_profile, get_profile_by_id, get_profiles_by_user, count_profiles_by_user, update_profile, delete_profile)
- [ ] **Adicionar** métodos de serviço de perfil em `login_service.py` (validate_profile_name, validate_profile_description, check_profile_limit, create_profile, get_user_profiles, get_profile, update_profile, delete_profile)
- [ ] **Adicionar** rotas de perfil em `router_login.py` (POST /profiles, GET /profiles, GET /profiles/{profile_id}, PUT /profiles/{profile_id}, DELETE /profiles/{profile_id})
- [ ] Criar coleção "profiles" no MongoDB (ou deixar criar automaticamente)
- [ ] Criar índices no MongoDB (userId, userId+name único)
- [ ] Testar criação de perfil
- [ ] Testar validações (nome vazio, muito longo, limite de 5)
- [ ] Testar listagem de perfis
- [ ] Testar busca, atualização e deleção
- [ ] Testar segurança (usuário não pode acessar perfis de outros)

---

## 9. Pontos de Atenção

1. **Segurança**: Sempre validar que o perfil pertence ao usuário autenticado
2. **Validações**: Implementar todas as validações antes de salvar no banco
3. **Tratamento de erros**: Tratar ObjectId inválido, perfis não encontrados, etc.
4. **Consistência**: Seguir o mesmo padrão de código do módulo de login
5. **MongoDB**: Usar a mesma conexão/instância que o login usa
6. **Autenticação**: Reutilizar a mesma função de autenticação do login

---

## 10. Fluxo Completo

1. Frontend envia POST `/profiles` com token JWT
2. Router valida autenticação via `get_current_user`
3. Router chama `ProfileService.create_profile`
4. Service valida nome, descrição e limite de perfis
5. Service chama `ProfileRepository.create_profile`
6. Repository insere no MongoDB
7. Repository retorna perfil criado
8. Service retorna perfil
9. Router retorna resposta HTTP 201 com perfil criado
10. Frontend recebe e salva no localStorage (compatibilidade)

