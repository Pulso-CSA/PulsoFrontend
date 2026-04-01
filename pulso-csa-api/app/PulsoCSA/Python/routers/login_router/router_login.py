from fastapi import APIRouter, Depends, HTTPException, Header

from typing import Optional

from utils.log_manager import add_log
from services.login.login_service import (
    login_with_google_service,
    google_callback_service,
    register_local_service,
    login_local_service,
    create_profile_service,
    get_user_profiles_service,
    get_profile_service,
    update_profile_service,
    delete_profile_service,
    logout_service,
    refresh_token_service,
    request_password_reset_service,
    reset_password_service,
    get_current_user_service,
    update_user_service,
)
from models.login_models.login_models import (
    RegisterRequest,
    LoginRequest,
    UserPublic,
    UserUpdateRequest,
    TokenModel,
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from storage.database.login.database_login import get_user_by_email, is_token_blacklisted
from utils.login import verify_jwt_token

router = APIRouter(prefix="/auth", tags=["Login"])
SOURCE = "auth_router"

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Authentication Dependency❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract and validate JWT token, return user ID."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    try:
        # Remove "Bearer " prefix if present
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

        # Check if token is blacklisted
        if await is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token foi invalidado (logout)")

        token_data = verify_jwt_token(token)

        # ✅ Prefer the canonical structure used across the project: data.email
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")

        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")

        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Sessão inválida. Faça login novamente ou crie uma conta."
            )

        return str(user.get("_id"))

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

async def get_current_user_email(authorization: Optional[str] = Header(None)):
    """Extract and validate JWT token, return user email."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    try:
        # Remove "Bearer " prefix if present
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

        # Check if token is blacklisted
        if await is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token foi invalidado (logout)")

        token_data = verify_jwt_token(token)

        # ✅ Prefer data.email; keep fallback for older tokens
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")

        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")

        return email
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

@router.get("/login/google")
async def login_with_google():
    return await login_with_google_service()

@router.get("/login/google/callback")
async def google_callback(code: str):
    return await google_callback_service(code)

@router.post("/signup")
async def signup(payload: RegisterRequest):
    """Cadastro de novo usuário."""
    add_log("info", f"POST /auth/signup recebido | email={payload.email}", SOURCE)
    try:
        result = await register_local_service(payload)
        add_log("info", f"POST /auth/signup sucesso | email={payload.email}", SOURCE)
        return result
    except Exception as e:
        add_log("error", f"POST /auth/signup falhou | email={payload.email} | error={type(e).__name__}: {e}", SOURCE)
        raise

@router.post("/login")
async def login_local(payload: LoginRequest):
    """Login local - retorna access_token e refresh_token."""
    add_log("info", f"POST /auth/login recebido | email={payload.email}", SOURCE)
    try:
        result = await login_local_service(payload)
        add_log("info", f"POST /auth/login sucesso | email={payload.email}", SOURCE)
        return result
    except Exception as e:
        add_log("error", f"POST /auth/login falhou | email={payload.email} | error={type(e).__name__}: {e}", SOURCE)
        raise

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout - invalida o token atual."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    return await logout_service(token)

@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest):
    """Refresh access token usando refresh token."""
    return await refresh_token_service(payload.refresh_token)

@router.post("/request-password-reset")
async def request_password_reset(payload: PasswordResetRequest):
    """Solicita reset de senha - envia email com token."""
    return await request_password_reset_service(payload.email)

@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirm):
    """Redefine senha usando token de reset."""
    return await reset_password_service(payload.token, payload.new_password)

@router.get("/me")
async def get_me(email: str = Depends(get_current_user_email)):
    """Retorna dados do usuário autenticado. Requer Authorization: Bearer <access_token>.
    Após signup/login, use o token retornado no header antes de chamar /me."""
    return await get_current_user_service(email)


@router.put("/me")
async def put_me(
    payload: UserUpdateRequest,
    email: str = Depends(get_current_user_email),
):
    """Atualiza nome, email, senha e/ou avatar do usuário autenticado.
    Campos opcionais: name, email, new_password, picture."""
    return await update_user_service(
        email=email,
        name=payload.name,
        new_email=payload.email,
        new_password=payload.new_password,
        picture=payload.picture,
    )


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Routes❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

@router.post("/profiles", status_code=201, response_model=ProfileResponse)
async def create_profile(
    payload: ProfileCreate,
    user_id: str = Depends(get_current_user)
):
    profile = await create_profile_service(user_id, payload.name, payload.description)
    return ProfileResponse(**profile)

@router.get("/profiles", response_model=list[ProfileResponse])
async def get_profiles(user_id: str = Depends(get_current_user)):
    profiles = await get_user_profiles_service(user_id)
    return [ProfileResponse(**profile) for profile in profiles]

@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user)
):
    profile = await get_profile_service(profile_id, user_id)
    return ProfileResponse(**profile)

@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    payload: ProfileUpdate,
    user_id: str = Depends(get_current_user)
):
    profile = await update_profile_service(
        profile_id,
        user_id,
        payload.name,
        payload.description
    )
    return ProfileResponse(**profile)

@router.delete("/profiles/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: str,
    user_id: str = Depends(get_current_user)
):
    await delete_profile_service(profile_id, user_id)
    return None
