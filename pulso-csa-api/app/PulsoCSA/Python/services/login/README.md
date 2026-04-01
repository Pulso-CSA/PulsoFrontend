# 🔐 Login Service - Serviço de Autenticação

<div align="center">

![Auth](https://img.shields.io/badge/Authentication-FF5722?style=for-the-badge&logo=auth0&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)

**Lógica de negócio para autenticação e autorização**

</div>

---

## 📋 Visão Geral

O `login_service/` implementa a **lógica de autenticação**, incluindo:

- 🔑 Validação de credenciais
- 🎫 Geração e validação de tokens JWT
- 🌐 Integração OAuth (Google)
- 🔒 Hash e verificação de senhas

## 📁 Estrutura

```
login/
└── 📄 login_service.py    # Serviço de autenticação
```

## 🔧 Métodos Principais

```python
class LoginService:
    """Serviço de autenticação e gestão de sessões."""
    
    async def authenticate(
        self, 
        email: str, 
        password: str
    ) -> TokenResponse:
        """
        Autentica usuário com email/senha.
        
        Args:
            email: Email do usuário
            password: Senha em texto plano
            
        Returns:
            TokenResponse com access e refresh tokens
            
        Raises:
            AuthenticationError: Credenciais inválidas
        """
        pass
    
    async def register(
        self, 
        user_data: UserCreate
    ) -> User:
        """
        Registra novo usuário no sistema.
        """
        pass
    
    async def google_auth(
        self, 
        google_token: str
    ) -> TokenResponse:
        """
        Autentica via Google OAuth 2.0.
        """
        pass
    
    async def refresh_token(
        self, 
        refresh_token: str
    ) -> TokenResponse:
        """
        Renova access token usando refresh token.
        """
        pass
    
    async def logout(
        self, 
        user_id: str, 
        token: str
    ) -> None:
        """
        Invalida tokens e encerra sessão.
        """
        pass
```

## 🔒 Segurança

- **Bcrypt** para hash de senhas
- **JWT RS256** para tokens
- **Refresh tokens** rotacionados
- **Rate limiting** em endpoints sensíveis

## 🔗 Links Relacionados

- [🌐 Login Router](../../routers/login_router/README.md)
- [📊 Login Models](../../models/login_models/README.md)
- [💾 Login Database](../../storage/database/login/README.md)

---

<div align="center">

**🔐 Autenticação segura e escalável**

</div>
