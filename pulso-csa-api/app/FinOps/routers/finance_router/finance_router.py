#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮SFAP – Sistema Financeiro Administrativo Pulso❯━━━━━━━━━
# Rotas só acessíveis para usuários cujo nome completo (conta) seja G!, E!, T! ou P!
# Banco: pulso_database, coleção Financeiro
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.login import verify_jwt_token
from storage.database.login.database_login import get_user_by_email, get_profile_by_id as get_profile_by_id_login
from services.finance.finance_service import (
    list_planos_service,
    create_plano_service,
    update_plano_service,
    delete_plano_service,
    list_movimentos_service,
    create_movimento_service,
    update_movimento_service,
    delete_movimento_service,
    dashboard_service,
)
from models.finance.finance_models import (
    PlanoCreate,
    PlanoUpdate,
    MovimentoCreate,
    MovimentoUpdate,
    DashboardResponse,
)

# Nomes completos (conta) autorizados a acessar o SFAP
SFAP_ALLOWED_USER_NAMES = {"G!", "E!", "T!", "P!"}

router = APIRouter(prefix="/sfap", tags=["SFAP – Sistema Financeiro Administrativo Pulso"])
security = HTTPBearer()


async def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        email = payload.get("data", {}).get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return email
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )


async def require_sfap_profile(
    user_email: str = Depends(get_current_user_email),
    x_profile_id: Optional[str] = Header(None, alias="X-Profile-Id"),
) -> str:
    """
    Exige que o nome completo do usuário (conta) seja G!, E!, T! ou P!.
    O frontend deve enviar o header X-Profile-Id com o id do perfil ativo.
    """
    user = await get_user_by_email(user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não encontrado.",
        )
    full_name = (user.get("name") or "").strip()
    if full_name not in SFAP_ALLOWED_USER_NAMES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso ao SFAP restrito a contas autorizadas (nome completo G!, E!, T!, P!).",
        )
    if not x_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SFAP exige o header X-Profile-Id com o perfil ativo.",
        )
    user_id = str(user.get("_id", ""))
    profile = await get_profile_by_id_login(x_profile_id, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil não encontrado ou não pertence ao usuário.",
        )
    return user_email


# ─── Dashboard ────────────────────────────────────────────────────────────
@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(_: str = Depends(require_sfap_profile)):
    """Totais: receita, custo operação e saldo (USD)."""
    return await dashboard_service()


# ─── Planos (tabela de preços / lucro por escala) ──────────────────────────
@router.get("/planos")
async def list_planos(
    tipo: Optional[str] = None,
    _: str = Depends(require_sfap_profile),
):
    """Lista planos. Query opcional: tipo (ex.: MENSAL, ANUAL) — pode repetir."""
    filtro = [tipo] if tipo else None
    return await list_planos_service(filtro_tipo=filtro)


@router.post("/planos", status_code=status.HTTP_201_CREATED)
async def create_plano(
    payload: PlanoCreate,
    _: str = Depends(require_sfap_profile),
):
    """Cria um plano (referência de preço e lucro por escala)."""
    return await create_plano_service(payload.model_dump())


@router.patch("/planos/{plano_id}")
async def update_plano(
    plano_id: str,
    payload: PlanoUpdate,
    _: str = Depends(require_sfap_profile),
):
    """Atualiza um plano."""
    out = await update_plano_service(plano_id, payload.model_dump(exclude_unset=True))
    if not out:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")
    return out


@router.delete("/planos/{plano_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plano(
    plano_id: str,
    _: str = Depends(require_sfap_profile),
):
    """Remove um plano."""
    ok = await delete_plano_service(plano_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")


# ─── Movimentos (receita = ganho, gasto = custo operação) ───────────────────
@router.get("/movimentos")
async def list_movimentos(
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    _: str = Depends(require_sfap_profile),
):
    """Lista movimentos. Query: tipo (ganho|gasto), categoria, data_inicio, data_fim (ISO)."""
    categorias = [categoria] if categoria else None
    return await list_movimentos_service(
        tipo=tipo,
        categoria=categorias,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.post("/movimentos", status_code=status.HTTP_201_CREATED)
async def create_movimento(
    payload: MovimentoCreate,
    _: str = Depends(require_sfap_profile),
):
    """Cria movimento (receita/ganho ou gasto). Receita pode vir de plano (categoria receita_plano)."""
    return await create_movimento_service(payload.model_dump())


@router.patch("/movimentos/{movimento_id}")
async def update_movimento(
    movimento_id: str,
    payload: MovimentoUpdate,
    _: str = Depends(require_sfap_profile),
):
    """Atualiza um movimento."""
    out = await update_movimento_service(movimento_id, payload.model_dump(exclude_unset=True))
    if not out:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimento não encontrado")
    return out


@router.delete("/movimentos/{movimento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movimento(
    movimento_id: str,
    _: str = Depends(require_sfap_profile),
):
    """Remove um movimento."""
    ok = await delete_movimento_service(movimento_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimento não encontrado")


# ─── Visibilidade (para o frontend esconder/mostrar item de menu) ───────────
@router.get("/visibility")
async def sfap_visibility(
    user_email: str = Depends(get_current_user_email),
):
    """
    Retorna { "allowed": true } se o nome completo do usuário (conta) for G!, E!, T!, P!.
    O frontend usa para exibir ou ocultar o item SFAP no menu (abaixo de Tema).
    """
    user = await get_user_by_email(user_email)
    if not user:
        return {"allowed": False}
    full_name = (user.get("name") or "").strip()
    return {"allowed": full_name in SFAP_ALLOWED_USER_NAMES}
