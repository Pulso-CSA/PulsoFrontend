from fastapi import APIRouter

# Router principal (já existente no seu projeto)
from routers.profile_router.router_profile import router as router

# Router de convites (novo)
from routers.profile_router.profile_invite_router import router as invite_router

# Inclui as rotas de convite dentro do router principal
router.include_router(invite_router)