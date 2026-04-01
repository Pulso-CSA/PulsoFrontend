from fastapi import HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional

from utils.log_manager import add_log
from utils.login import (
    get_google_auth, get_user_info, create_jwt_token, create_refresh_token,
    verify_refresh_token, hash_password, verify_password, send_password_reset_email
)
from storage.database.login.database_login import (
    save_user_local as save_user,
    get_user_by_email,
    create_profile as db_create_profile,
    get_profile_by_id as db_get_profile_by_id,
    get_profiles_by_user as db_get_profiles_by_user,
    count_profiles_by_user as db_count_profiles_by_user,
    update_profile as db_update_profile,
    delete_profile as db_delete_profile,
    add_token_to_blacklist,
    is_token_blacklisted,
    save_password_reset_token,
    get_password_reset_token,
    mark_password_reset_token_as_used,
    update_user_password,
    update_user as db_update_user,
)
# profile está em api/app/storage/database/profile/ (compartilhado)
try:
    from storage.database.profile.database_profile_members import add_profile_member
except ImportError:
    from app.storage.database.profile.database_profile_members import add_profile_member
from models.login_models.login_models import UserPublic, TokenModel
from datetime import datetime, timedelta
import secrets
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
AUTHORIZED_EMAILS = ["ericdelucass@gmail.com", "pulsocsa@gmail.com"]
SOURCE = "login_service"

async def login_with_google_service():
    google = get_google_auth(GOOGLE_REDIRECT_URI)
    auth_url, _ = google.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline",
        prompt="consent"
    )
    return RedirectResponse(auth_url)

async def google_callback_service(code: str):
    google = get_google_auth(GOOGLE_REDIRECT_URI)
    token = google.fetch_token(
        "https://oauth2.googleapis.com/token",
        code=code
    )
    profile = await get_user_info(token["access_token"])

    # Normaliza email para verificação
    email_normalized = profile["email"].lower().strip()
    if email_normalized not in [e.lower() for e in AUTHORIZED_EMAILS]:
        raise HTTPException(status_code=403, detail="E-mail não autorizado")

    user = await get_user_by_email(email_normalized)
    if not user:
        try:
            user = await save_user(
                profile.get("name"),
                email_normalized,
                None
            )
        except ValueError:
            # Usuário foi criado por outro processo (race condition)
            user = await get_user_by_email(email_normalized)

    access_token = create_jwt_token({"email": user["email"]})
    refresh_token = create_refresh_token({"email": user["email"]})
    return JSONResponse({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Local Auth persistence❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def register_local_service(payload):
    # Normaliza email antes de verificar
    email_normalized = payload.email.lower().strip()
    add_log("info", f"register_local_service | email={email_normalized}", SOURCE)
    try:
        existing = await get_user_by_email(email_normalized)
        add_log("info", f"register_local_service | get_user_by_email retornou: {'existe' if existing else 'não existe'}", SOURCE)
    except Exception as e:
        add_log("error", f"register_local_service | get_user_by_email EXCEÇÃO: {type(e).__name__}: {e}", SOURCE)
        err_msg = str(e).lower()
        if "connection" in err_msg or "timeout" in err_msg or "mongo" in err_msg or "application" in err_msg:
            raise HTTPException(
                status_code=503,
                detail="Banco de dados indisponível. Verifique se o MongoDB está rodando e se MONGO_URI está configurado no .env (ex: mongodb://localhost:27017).",
            )
        raise

    if existing:
        raise HTTPException(status_code=409, detail="E-mail already registered")

    pwd_hash = hash_password(payload.password)

    add_log("info", f"register_local_service | chamando save_user", SOURCE)
    try:
        doc = await save_user(
            payload.name,
            email_normalized,
            pwd_hash
        )
        add_log("info", f"register_local_service | save_user sucesso | id={doc.get('_id')}", SOURCE)
    except ValueError as e:
        add_log("error", f"register_local_service | save_user ValueError: {e}", SOURCE)
        # Trata erro de duplicata do MongoDB (race condition)
        if "já cadastrado" in str(e):
            raise HTTPException(status_code=409, detail="E-mail already registered")
        raise

    # Usar sempre email normalizado do doc para evitar "Usuário não encontrado" em /me ou refresh
    email_stored = doc["email"]
    access_token = create_jwt_token({"email": email_stored})
    refresh_token = create_refresh_token({"email": email_stored})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "id": str(doc.get("_id")),
        "name": doc["name"],
        "email": doc["email"],
        "picture": doc.get("picture")
    }

async def login_local_service(payload):
    # Normaliza email antes de buscar
    email_normalized = payload.email.lower().strip()
    add_log("info", f"login_local_service | email={email_normalized}", SOURCE)
    try:
        user = await get_user_by_email(email_normalized)
        add_log("info", f"login_local_service | get_user_by_email retornou: {'user' if user else 'None'}", SOURCE)
    except Exception as e:
        add_log("error", f"login_local_service | get_user_by_email EXCEÇÃO: {type(e).__name__}: {e}", SOURCE)
        err_msg = str(e).lower()
        if "connection" in err_msg or "timeout" in err_msg or "mongo" in err_msg or "application" in err_msg:
            raise HTTPException(
                status_code=503,
                detail="Banco de dados indisponível. Verifique se o MongoDB está rodando e se MONGO_URI está configurado no .env (ex: mongodb://localhost:27017).",
            )
        raise

    if not user or not user.get("password_hash"):
        add_log("warn", f"login_local_service | usuário não encontrado ou sem senha | email={email_normalized}", SOURCE)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user["password_hash"]):
        add_log("warn", f"login_local_service | senha inválida | email={email_normalized}", SOURCE)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    add_log("info", f"login_local_service | credenciais OK, gerando tokens", SOURCE)
    # ⭐ ADIÇÃO MÍNIMA (igual ao /register)
    access_token = create_jwt_token({"email": user["email"]})
    refresh_token = create_refresh_token({"email": user["email"]})
    token = create_jwt_token({"id": str(user.get("_id")), "email": user["email"]})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "id": str(user.get("_id")),
        "name": user["name"],
        "email": user["email"],
        "picture": user.get("picture")
    }

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Service❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def validate_profile_name(name: str):
    """Validate profile name."""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Nome do perfil não pode estar vazio")
    if len(name) < 1 or len(name) > 50:
        raise HTTPException(status_code=400, detail="Nome do perfil deve ter entre 1 e 50 caracteres")

def validate_profile_description(description: Optional[str]):
    """Validate profile description."""
    if description is not None and len(description) > 200:
        raise HTTPException(status_code=400, detail="Descrição do perfil deve ter no máximo 200 caracteres")

async def check_profile_limit(user_id: str):
    """Check if user has reached the maximum number of profiles (5)."""
    count = await db_count_profiles_by_user(user_id)
    if count >= 5:
        raise HTTPException(status_code=400, detail="Limite de 5 perfis por usuário atingido")

async def create_profile_service(user_id: str, name: str, description: Optional[str] = None):
    """Create a new profile."""
    validate_profile_name(name)
    validate_profile_description(description)
    await check_profile_limit(user_id)
    
    profile = await db_create_profile(user_id, name, description)
    # After creating profile, add the creator as admin member
    try:
        await add_profile_member(
            profile_id=profile["id"],
            user_id=user_id,
            role="admin",
            invited_by=None,
        )
    except ValueError:
        # If the member already exists (unlikely for a new profile), ignore
        pass
    return profile

async def get_user_profiles_service(user_id: str):
    """Get all profiles for a user."""
    profiles = await db_get_profiles_by_user(user_id)
    return profiles

async def get_profile_service(profile_id: str, user_id: str):
    """Get a specific profile by ID."""
    profile = await db_get_profile_by_id(profile_id, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return profile

async def update_profile_service(profile_id: str, user_id: str, name: Optional[str] = None, description: Optional[str] = None):
    """Update a profile."""
    if name is not None:
        validate_profile_name(name)
    validate_profile_description(description)
    
    profile = await db_update_profile(profile_id, user_id, name, description)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return profile

async def delete_profile_service(profile_id: str, user_id: str):
    """Delete a profile."""
    deleted = await db_delete_profile(profile_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return {"message": "Perfil deletado com sucesso"}

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Auth Services❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def logout_service(token: str):
    """Logout user by blacklisting the token."""
    try:
        from utils.login import verify_jwt_token
        token_data = verify_jwt_token(token)
        # Token expires in 12 hours by default
        expires_at = datetime.utcnow() + timedelta(hours=12)
        await add_token_to_blacklist(token, expires_at)
        return {"message": "Logout realizado com sucesso"}
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

async def refresh_token_service(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        token_data = verify_refresh_token(refresh_token)
        email = token_data.get("email")
        
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Sessão inválida. Faça login novamente ou crie uma conta."
            )

        # Generate new tokens
        new_access_token = create_jwt_token({"email": email})
        new_refresh_token = create_refresh_token({"email": email})
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token de refresh inválido ou expirado")

async def request_password_reset_service(email: str):
    """Request password reset - sends email with reset token."""
    email_normalized = email.lower().strip()
    user = await get_user_by_email(email_normalized)
    
    # Por segurança, sempre retorna sucesso mesmo se o email não existir
    if not user:
        return {"message": "Se o email existir, você receberá um link de redefinição de senha"}
    
    # Gera token de reset
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Salva token no banco
    await save_password_reset_token(email_normalized, reset_token, expires_at)
    
    # Envia email
    send_password_reset_email(email_normalized, reset_token)
    
    return {"message": "Se o email existir, você receberá um link de redefinição de senha"}

async def reset_password_service(token: str, new_password: str):
    """Reset password using reset token."""
    reset_token_data = await get_password_reset_token(token)
    
    if not reset_token_data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")
    
    email = reset_token_data["email"]
    
    # Hash da nova senha
    new_password_hash = hash_password(new_password)
    
    # Atualiza senha
    success = await update_user_password(email, new_password_hash)
    
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao atualizar senha")
    
    # Marca token como usado
    await mark_password_reset_token_as_used(token)
    
    return {"message": "Senha redefinida com sucesso"}

async def get_current_user_service(email: str):
    """Get current user data. Retorna 401 (não 404) se o usuário do token não existir (sessão inválida)."""
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida. Faça login novamente ou crie uma conta."
        )
    return {
        "id": str(user.get("_id")),
        "name": user["name"],
        "email": user["email"],
        "picture": user.get("picture")
    }


async def update_user_service(
    email: str,
    name: Optional[str] = None,
    new_email: Optional[str] = None,
    new_password: Optional[str] = None,
    picture: Optional[str] = None,
):
    """Atualiza dados do usuário (nome, email, senha, picture). Retorna dados atualizados."""
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida. Faça login novamente ou crie uma conta."
        )
    if new_password:
        pwd_hash = hash_password(new_password)
        await update_user_password(email, pwd_hash)
    try:
        updated = await db_update_user(
            email=email,
            name=name,
            new_email=new_email,
            picture=picture,
        )
    except ValueError as e:
        if "já está em uso" in str(e):
            raise HTTPException(status_code=409, detail="E-mail já está em uso por outra conta")
        raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=500, detail="Erro ao atualizar perfil")
    return {
        "id": str(updated.get("_id")),
        "name": updated["name"],
        "email": updated["email"],
        "picture": updated.get("picture"),
    }
