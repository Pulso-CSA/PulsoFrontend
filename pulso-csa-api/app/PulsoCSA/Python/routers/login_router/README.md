# 🔐 Login Router - Autenticação e Autorização

<div align="center">

![Auth](https://img.shields.io/badge/Authentication-FF5722?style=for-the-badge&logo=auth0&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)

**Endpoints de autenticação, registro e gestão de sessões**

</div>

---

## 📋 Visão Geral

O módulo `login_router/` contém os **endpoints de autenticação** da API, incluindo:

- 🔑 Login com email/senha
- 📝 Registro de novos usuários
- 🌐 Autenticação OAuth (Google)
- 🔄 Refresh de tokens JWT
- 🚪 Logout e invalidação de sessões

## 📁 Estrutura

```
login_router/
└── 📄 router_login.py    # Endpoints de autenticação
```

## 🌐 Endpoints

### `POST /login`

Autentica um usuário com email e senha.

```http
POST /login
Content-Type: application/json

{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

**Resposta (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### `POST /signup`

Registra um novo usuário no sistema.

```http
POST /signup
Content-Type: application/json

{
  "email": "novo@exemplo.com",
  "password": "senha123",
  "name": "Novo Usuário"
}
```

**Resposta (201 Created):**
```json
{
  "id": "user_123",
  "email": "novo@exemplo.com",
  "name": "Novo Usuário",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### `POST /google-auth`

Autentica usando Google OAuth 2.0.

```http
POST /google-auth
Content-Type: application/json

{
  "token": "google_oauth_token..."
}
```

### `POST /refresh`

Renova o access token usando refresh token.

```http
POST /refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### `POST /logout`

Encerra a sessão e invalida tokens.

```http
POST /logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## 🧪 Testes via cURL

> Base URL: `http://localhost:8000` | Endpoints: `/auth/*`

```bash
# Signup (registro)
curl -s -X POST http://localhost:8000/auth/signup -H "Content-Type: application/json" -d "{\"email\":\"teste@exemplo.com\",\"password\":\"senha123\",\"name\":\"Usuario Teste\"}"

# Login
curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d "{\"email\":\"teste@exemplo.com\",\"password\":\"senha123\"}"

# Refresh token (substitua TOKEN pelo refresh_token)
curl -s -X POST http://localhost:8000/auth/refresh -H "Content-Type: application/json" -d "{\"refresh_token\":\"TOKEN\"}"

# Me (requer Bearer token - substitua TOKEN pelo access_token)
curl -s -X GET http://localhost:8000/auth/me -H "Authorization: Bearer TOKEN"

# Logout
curl -s -X POST http://localhost:8000/auth/logout -H "Authorization: Bearer TOKEN"
```

## 🔒 Fluxo de Autenticação

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Cliente   │───▶│   /login    │───▶│   Validar   │
│             │    │             │    │  Credenciais│
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                                             ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Usar API  │◀───│   Retornar  │◀───│   Gerar     │
│ c/ Token    │    │   Tokens    │    │   JWT       │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔗 Links Relacionados

- [🔧 Login Service](../../services/login/README.md)
- [📊 Login Models](../../models/login_models/README.md)
- [🛠️ Login Utils](../../utils/README.md)

---

<div align="center">

**🔐 Autenticação segura para PulsoAPI**

</div>
