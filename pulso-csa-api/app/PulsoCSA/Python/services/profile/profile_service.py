#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Service❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from fastapi import HTTPException, status
from typing import List, Optional
# profile está em api/app/storage/database/profile/ (compartilhado)
try:
    from storage.database.profile.database_profile import (
        get_profiles_by_user_email,
        create_profile,
        get_profile_by_id,
        update_profile,
        delete_profile,
        count_profiles_by_user_email,
    )
except ImportError:
    from app.storage.database.profile.database_profile import (
        get_profiles_by_user_email,
        create_profile,
        get_profile_by_id,
        update_profile,
        delete_profile,
        count_profiles_by_user_email,
    )
from models.profile_models.profile_models import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse
)
from utils.path_validation import is_production

MAX_PROFILES_PER_USER = 5

async def list_profiles_service(user_email: str) -> ProfileListResponse:
    """Lista todos os perfis do usuário."""
    try:
        profiles_data = await get_profiles_by_user_email(user_email)
        profiles = [
            ProfileResponse(
                id=p["id"],
                name=p["name"],
                description=p.get("description") or None,
                created_at=p["created_at"],
                updated_at=p["updated_at"]
            )
            for p in profiles_data
        ]
        return ProfileListResponse(profiles=profiles, total=len(profiles))
    except Exception as e:
        msg = "Erro ao buscar perfis." if is_production() else str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROFILE_LIST_FAILED", "message": msg}
        )

async def create_profile_service(user_email: str, payload: ProfileCreate) -> ProfileResponse:
    """Cria um novo perfil."""
    # Validar limite
    current_count = await count_profiles_by_user_email(user_email)
    if current_count >= MAX_PROFILES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Limite máximo de {MAX_PROFILES_PER_USER} perfis atingido"
        )
    
    try:
        profile_data = await create_profile(
            user_email=user_email,
            name=payload.name.strip(),
            description=payload.description.strip() if payload.description else None
        )
        return ProfileResponse(
            id=profile_data["id"],
            name=profile_data["name"],
            description=profile_data.get("description") or None,
            created_at=profile_data["created_at"],
            updated_at=profile_data["updated_at"]
        )
    except Exception as e:
        msg = "Erro ao criar perfil." if is_production() else str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROFILE_CREATE_FAILED", "message": msg}
        )

async def update_profile_service(
    user_email: str,
    profile_id: str,
    payload: ProfileUpdate
) -> ProfileResponse:
    """Atualiza um perfil existente."""
    # Verificar se perfil existe e pertence ao usuário
    existing = await get_profile_by_id(profile_id, user_email)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )
    
    try:
        updated = await update_profile(
            profile_id=profile_id,
            user_email=user_email,
            name=payload.name.strip(),
            description=payload.description.strip() if payload.description else None
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao atualizar perfil"
            )
        
        return ProfileResponse(
            id=updated["id"],
            name=updated["name"],
            description=updated.get("description") or None,
            created_at=updated["created_at"],
            updated_at=updated["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        msg = "Erro ao atualizar perfil." if is_production() else str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROFILE_UPDATE_FAILED", "message": msg}
        )

async def delete_profile_service(user_email: str, profile_id: str) -> dict:
    """Deleta um perfil."""
    # Verificar se perfil existe e pertence ao usuário
    existing = await get_profile_by_id(profile_id, user_email)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )
    
    # Verificar se é o último perfil
    current_count = await count_profiles_by_user_email(user_email)
    if current_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você deve ter pelo menos 1 perfil. Não é possível deletar o último perfil."
        )
    
    try:
        success = await delete_profile(profile_id, user_email)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao deletar perfil"
            )
        
        return {
            "message": "Perfil deletado com sucesso",
            "deleted_id": profile_id
        }
    except HTTPException:
        raise
    except Exception as e:
        msg = "Erro ao deletar perfil." if is_production() else str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROFILE_DELETE_FAILED", "message": msg}
        )

