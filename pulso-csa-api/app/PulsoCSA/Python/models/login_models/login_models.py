#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Login Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserModel(BaseModel):
    """User document stored in MongoDB."""
    id: Optional[str]
    name: str
    email: EmailStr
    picture: Optional[str] = None
    token: Optional[str] = None
    password_hash: Optional[str] = None  # used for local auth only

class TokenModel(BaseModel):
    """JWT response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    """Request model for refresh token."""
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Request model to confirm password reset."""
    token: str
    new_password: str = Field(..., min_length=6)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Request DTOs (Local Auth)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
class RegisterRequest(BaseModel):
    """Payload for local sign-up."""
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    """Payload for local sign-in."""
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserPublic(BaseModel):
    """Safe user projection to clients."""
    id: Optional[str]
    name: str
    email: EmailStr
    picture: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """Payload para atualizar dados do usuário (PUT /auth/me)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    new_password: Optional[str] = Field(None, min_length=6)
    picture: Optional[str] = Field(
        None,
        max_length=7_000_000,
    )  # data URL base64; alinhado ao teto de body em PUT /auth/me (ver AUTH_ME_MAX_BODY_MB)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
class ProfileCreate(BaseModel):
    """Payload for creating a profile."""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class ProfileUpdate(BaseModel):
    """Payload for updating a profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)

class ProfileResponse(BaseModel):
    """Profile response model."""
    id: str
    userId: str
    name: str
    description: Optional[str] = None
    createdAt: str
    updatedAt: str