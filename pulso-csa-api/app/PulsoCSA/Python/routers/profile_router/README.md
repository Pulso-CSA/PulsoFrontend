# 👤 Profile Router - Gestão de Perfis

<div align="center">

![Profile](https://img.shields.io/badge/Profile-9C27B0?style=for-the-badge&logo=user&logoColor=white)
![Teams](https://img.shields.io/badge/Teams-2196F3?style=for-the-badge&logo=microsoft-teams&logoColor=white)

**Endpoints de gestão de perfis, convites e membros**

</div>

---

## 📋 Visão Geral

O módulo `profile_router/` gerencia **perfis de usuários** e **equipes**:

- 👤 CRUD de perfis
- 📧 Sistema de convites
- 👥 Gestão de membros
- 🔐 Permissões e roles

## 📁 Estrutura

```
profile_router/
├── 📄 router_profile.py         # CRUD de perfis
└── 📄 profile_invite_router.py  # Sistema de convites
```

## 🌐 Endpoints

### `GET /profile`

Obtém perfil do usuário atual.

```http
GET /profile
Authorization: Bearer {token}
```

**Resposta (200 OK):**
```json
{
  "id": "user_123",
  "email": "usuario@exemplo.com",
  "name": "João Silva",
  "avatar_url": "https://...",
  "subscription_tier": "professional",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### `PUT /profile`

Atualiza perfil do usuário.

```http
PUT /profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "João Silva Atualizado",
  "avatar_url": "https://nova-foto.jpg"
}
```

### `POST /profile/invite`

Envia convite para novo membro.

```http
POST /profile/invite
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "novo@exemplo.com",
  "role": "member"
}
```

### `GET /profile/members`

Lista membros do time/organização.

```http
GET /profile/members
Authorization: Bearer {token}
```

**Resposta (200 OK):**
```json
{
  "members": [
    {
      "id": "user_123",
      "name": "João Silva",
      "email": "joao@exemplo.com",
      "role": "admin",
      "joined_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "user_456",
      "name": "Maria Santos",
      "email": "maria@exemplo.com",
      "role": "member",
      "joined_at": "2024-01-15T00:00:00Z"
    }
  ]
}
```

### `DELETE /profile/members/{member_id}`

Remove membro do time.

```http
DELETE /profile/members/user_456
Authorization: Bearer {token}
```

## 🧪 Testes via cURL

> Requer `Authorization: Bearer TOKEN` | Base: `http://localhost:8000`

```bash
# Listar perfis
curl -s -X GET http://localhost:8000/profiles -H "Authorization: Bearer TOKEN"

# Criar perfil
curl -s -X POST http://localhost:8000/profiles -H "Content-Type: application/json" -H "Authorization: Bearer TOKEN" -d "{\"name\":\"Meu Perfil\",\"description\":\"Descrição do perfil\"}"

# Obter perfil por ID
curl -s -X GET http://localhost:8000/profiles/PROFILE_ID -H "Authorization: Bearer TOKEN"

# Atualizar perfil
curl -s -X PUT http://localhost:8000/profiles/PROFILE_ID -H "Content-Type: application/json" -H "Authorization: Bearer TOKEN" -d "{\"name\":\"Nome Atualizado\",\"description\":\"Nova descrição\"}"

# Deletar perfil
curl -s -X DELETE http://localhost:8000/profiles/PROFILE_ID -H "Authorization: Bearer TOKEN"
```

## 🔗 Links Relacionados

- [🔧 Profile Service](../../services/profile/README.md)
- [📊 Profile Models](../../models/profile_models/README.md)

---

<div align="center">

**👤 Gestão completa de perfis e equipes**

</div>
