#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional

from services.subscription.subscription_service import (
    get_subscription_service,
    get_invoices_service,
    cancel_subscription_service,
    resume_subscription_service,
    change_plan_service,
    get_portal_url_service,
    create_checkout_session_service,
    handle_stripe_webhook,
)
from models.subscription_models.subscription_models import (
    SubscriptionResponse,
    InvoicesResponse,
    SubscriptionUpdateResponse,
    PortalUrlResponse,
    CancelSubscriptionRequest,
    ChangePlanRequest,
    CheckoutRequest,
    CheckoutResponse,
)
from storage.database.login.database_login import get_user_by_email, is_token_blacklisted
from utils.login import verify_jwt_token
from core.entitlement.config import is_payment_exempt
from utils.path_validation import is_production
import os
import json

# Import condicional do Stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

router = APIRouter(prefix="/subscription", tags=["Subscription"])

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Authentication Dependency❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def get_current_user_id(authorization: Optional[str] = Header(None)):
    """Extract and validate JWT token, return user ID."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    
    try:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        if await is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token foi invalidado (logout)")
        
        token_data = verify_jwt_token(token)
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Sessão inválida. Faça login novamente ou crie uma conta.")
        
        return str(user.get("_id"))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Retorna user dict completo (para verificar is_exempt)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    try:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        if await is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token foi invalidado (logout)")
        token_data = verify_jwt_token(token)
        email = (token_data.get("data") or {}).get("email") or token_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Sessão inválida. Faça login novamente.")
        return {"_id": str(user.get("_id")), "email": user.get("email"), "name": user.get("name")}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription Routes❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

@router.get("", response_model=SubscriptionResponse)
async def get_subscription(user: dict = Depends(get_current_user)):
    """Retorna dados da assinatura atual. Usuários isentos (G!, E!, T!, V!, P!) retornam is_exempt=True."""
    if is_payment_exempt(user):
        return SubscriptionResponse(subscription=None, is_exempt=True)
    user_id = str(user.get("_id", ""))
    subscription = await get_subscription_service(user_id)
    return SubscriptionResponse(subscription=subscription, is_exempt=False)

@router.get("/invoices", response_model=InvoicesResponse)
async def get_invoices(user_id: str = Depends(get_current_user_id)):
    """Lista todas as faturas/invoices do usuário."""
    invoices = await get_invoices_service(user_id)
    return InvoicesResponse(invoices=invoices)

@router.post("/cancel", response_model=SubscriptionUpdateResponse)
async def cancel_subscription(
    payload: CancelSubscriptionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Cancela assinatura do usuário."""
    subscription = await cancel_subscription_service(user_id, payload.immediately)
    return SubscriptionUpdateResponse(subscription=subscription)

@router.post("/resume", response_model=SubscriptionUpdateResponse)
async def resume_subscription(user_id: str = Depends(get_current_user_id)):
    """Reativa assinatura cancelada."""
    subscription = await resume_subscription_service(user_id)
    return SubscriptionUpdateResponse(subscription=subscription)

@router.post("/change-plan", response_model=SubscriptionUpdateResponse)
async def change_plan(
    payload: ChangePlanRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Altera plano da assinatura."""
    subscription = await change_plan_service(user_id, payload.planId, payload.billingCycle)
    return SubscriptionUpdateResponse(subscription=subscription)

@router.get("/portal", response_model=PortalUrlResponse)
async def get_portal_url(user_id: str = Depends(get_current_user_id)):
    """Retorna URL do Stripe Customer Portal."""
    url = await get_portal_url_service(user_id)
    return PortalUrlResponse(url=url)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Cria sessão de checkout Stripe e retorna URL para redirecionamento."""
    checkout_url = await create_checkout_session_service(
        user_id=user_id,
        plan_id=payload.planId,
        billing_cycle=payload.billingCycle,
        success_url=payload.successUrl,
        cancel_url=payload.cancelUrl,
    )
    return CheckoutResponse(checkout_url=checkout_url)


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Stripe Webhook❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Endpoint para receber webhooks do Stripe."""
    from dotenv import load_dotenv
    
    # Garante que o .env seja carregado
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    ENV_PATH = os.path.join(ROOT_DIR, ".env")
    if os.path.isfile(ENV_PATH):
        load_dotenv(ENV_PATH, override=True)
    else:
        load_dotenv(override=True)
    
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500, 
            detail=f"Stripe webhook secret não configurado. Verifique se STRIPE_WEBHOOK_SECRET está no .env em: {ENV_PATH}"
        )
    
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Biblioteca Stripe não instalada")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Header stripe-signature não encontrado")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        detail = "Payload inválido." if is_production() else f"Payload inválido: {str(e)}"
        raise HTTPException(status_code=400, detail=detail)
    except stripe.error.SignatureVerificationError as e:
        detail = "Assinatura inválida." if is_production() else f"Assinatura inválida: {str(e)}"
        raise HTTPException(status_code=400, detail=detail)
    
    # Processa o evento com idempotência por event.id
    event_type = event.get("type")
    event_data = event.get("data", {})
    event_id = event.get("id")  # Stripe sempre inclui id único
    
    await handle_stripe_webhook(event_type, event_data, event_id=event_id)
    
    return {"status": "success"}
