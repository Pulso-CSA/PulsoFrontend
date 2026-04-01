#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Routers Infra❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter

from .analyze_router import router as analyze_router
from .generate_router import router as generate_router
from .validate_router import router as validate_router
from .deploy_router import router as deploy_router

router = APIRouter(tags=["Infra – Terraform"])
router.include_router(analyze_router)
router.include_router(generate_router)
router.include_router(validate_router)
router.include_router(deploy_router)
