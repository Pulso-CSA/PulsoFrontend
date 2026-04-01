#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.profile.profile_service import (
    list_profiles_service,
    create_profile_service,
    update_profile_service,
    delete_profile_service
)
from models.profile_models.profile_models import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse
)
from utils.login import verify_jwt_token

router = APIRouter(prefix="/profiles", tags=["Profiles"])
security = HTTPBearer()

async def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extrai o email do usuário do token JWT.
    
    Valida o token de autenticação e retorna o e-mail do usuário para identificar
    qual usuário está fazendo a requisição. Isso garante que cada usuário só
    acesse seus próprios perfis.
    """
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        email = payload.get("data", {}).get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        return email
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

@router.get("", response_model=ProfileListResponse)
async def list_profiles(user_email: str = Depends(get_current_user_email)):
    """
    Lista todos os perfis do usuário autenticado.
    
    Retorna uma lista completa com todos os perfis de trabalho criados pelo usuário,
    ordenados por data de criação (mais recentes primeiro). Esta rota permite que o
    usuário visualize todos os seus perfis sincronizados, independente do dispositivo
    ou máquina que esteja usando.
    
    **Autenticação:** Requerida (Bearer Token no header Authorization)
    
    **Retorna:**
    - Lista de perfis com id, nome, descrição e datas de criação/atualização
    - Total de perfis do usuário
    
    **Erros possíveis:**
    - 401: Token inválido ou expirado
    - 500: Erro ao buscar perfis no banco de dados
    """
    return await list_profiles_service(user_email)

@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: ProfileCreate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Cria um novo perfil de trabalho para o usuário autenticado.
    
    Permite que o usuário crie um novo perfil com nome e descrição opcional.
    O perfil será salvo no banco de dados e ficará disponível em todos os
    dispositivos sincronizados. Cada usuário pode ter no máximo 5 perfis.
    
    **Autenticação:** Requerida (Bearer Token no header Authorization)
    
    **Dados do perfil:**
    - Nome: obrigatório, entre 1 e 50 caracteres
    - Descrição: opcional, até 200 caracteres
    
    **Validações:**
    - Limite máximo de 5 perfis por usuário
    - Nome não pode estar vazio
    
    **Retorna:**
    - Dados completos do perfil criado (id, nome, descrição, datas)
    
    **Erros possíveis:**
    - 400: Nome inválido ou muito longo
    - 401: Token inválido ou expirado
    - 409: Limite máximo de 5 perfis atingido
    - 500: Erro ao criar perfil no banco de dados
    """
    return await create_profile_service(user_email, payload)

@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    payload: ProfileUpdate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Atualiza um perfil existente do usuário autenticado.
    
    Permite modificar o nome e descrição de um perfil que pertence ao usuário.
    O perfil deve existir e pertencer ao usuário autenticado. A data de atualização
    é automaticamente atualizada quando o perfil é modificado.
    
    **Autenticação:** Requerida (Bearer Token no header Authorization)
    
    **Validações:**
    - Perfil deve existir e pertencer ao usuário autenticado
    - Nome: obrigatório, entre 1 e 50 caracteres
    - Descrição: opcional, até 200 caracteres
    
    **Retorna:**
    - Dados atualizados do perfil (id, nome, descrição, datas)
    
    **Erros possíveis:**
    - 401: Token inválido ou expirado
    - 403: Perfil não pertence ao usuário autenticado
    - 404: Perfil não encontrado
    - 500: Erro ao atualizar perfil no banco de dados
    """
    return await update_profile_service(user_email, profile_id, payload)

@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Deleta um perfil do usuário autenticado.
    
    Remove permanentemente um perfil do banco de dados. O perfil deve pertencer
    ao usuário autenticado. Por segurança, o usuário deve ter pelo menos 1 perfil,
    então não é possível deletar o último perfil restante.
    
    **Autenticação:** Requerida (Bearer Token no header Authorization)
    
    **Validações:**
    - Perfil deve existir e pertencer ao usuário autenticado
    - Usuário deve ter pelo menos 1 perfil (não pode deletar o último)
    
    **Retorna:**
    - Mensagem de sucesso e ID do perfil deletado
    
    **Erros possíveis:**
    - 400: Tentativa de deletar o último perfil
    - 401: Token inválido ou expirado
    - 403: Perfil não pertence ao usuário autenticado
    - 404: Perfil não encontrado
    - 500: Erro ao deletar perfil no banco de dados
    """
    return await delete_profile_service(user_email, profile_id)

