# 👤 Profile Service - Serviço de Perfis

<div align="center">

![Profile](https://img.shields.io/badge/Profile-9C27B0?style=for-the-badge&logoColor=white)
![Teams](https://img.shields.io/badge/Teams-2196F3?style=for-the-badge&logoColor=white)

**Lógica de negócio para gestão de perfis e equipes**

</div>

---

## 📋 Visão Geral

O `profile/` implementa a **lógica de gestão de perfis**:

- 👤 CRUD de perfis de usuário
- 📧 Sistema de convites
- 👥 Gestão de membros e times
- 🔐 Controle de permissões

## 📁 Estrutura

```
profile/
├── 📄 profile_service.py               # CRUD de perfis
├── 📄 profile_invite_service.py        # Sistema de convites
└── 📄 profile_authorization_service.py # Autorização e permissões
```

## 🔧 Serviços

### `profile_service.py`

```python
class ProfileService:
    """Serviço de gestão de perfis de usuário."""
    
    async def get_profile(self, user_id: str) -> Profile:
        """Obtém perfil do usuário."""
        pass
    
    async def update_profile(
        self, 
        user_id: str, 
        data: ProfileUpdate
    ) -> Profile:
        """Atualiza dados do perfil."""
        pass
    
    async def delete_profile(self, user_id: str) -> bool:
        """Remove perfil (soft delete)."""
        pass
```

### `profile_invite_service.py`

```python
class ProfileInviteService:
    """Serviço de convites para times."""
    
    async def send_invite(
        self, 
        inviter_id: str,
        email: str, 
        role: str
    ) -> Invite:
        """Envia convite por email."""
        pass
    
    async def accept_invite(
        self, 
        invite_token: str
    ) -> Member:
        """Aceita convite e adiciona ao time."""
        pass
```

### `profile_authorization_service.py`

```python
class ProfileAuthorizationService:
    """Serviço de autorização e permissões."""
    
    async def check_permission(
        self, 
        user_id: str, 
        resource: str,
        action: str
    ) -> bool:
        """Verifica se usuário tem permissão."""
        pass
    
    async def update_role(
        self, 
        member_id: str, 
        new_role: str
    ) -> Member:
        """Atualiza role de um membro."""
        pass
```

## 🔗 Links Relacionados

- [🌐 Profile Router](../../routers/profile_router/README.md)
- [📊 Profile Models](../../models/profile_models/README.md)
- [💾 Profile Database](../../storage/database/profile/README.md)

---

<div align="center">

**👤 Gestão completa de perfis e equipes**

</div>
