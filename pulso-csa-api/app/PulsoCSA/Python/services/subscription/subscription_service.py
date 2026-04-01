#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription Service❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from fastapi import HTTPException
from typing import Optional
# subscription está em api/app/storage/database/subscription/ (compartilhado)
try:
    from storage.database.subscription.database_subscription import (
        get_subscription_by_user_id,
        update_subscription,
        cancel_subscription,
        resume_subscription,
        get_invoices_by_subscription_id,
        create_subscription,
        get_subscription_by_stripe_subscription_id,
    )
except ImportError:
    from app.storage.database.subscription.database_subscription import (
        get_subscription_by_user_id,
        update_subscription,
        cancel_subscription,
        resume_subscription,
        get_invoices_by_subscription_id,
        create_subscription,
        get_subscription_by_stripe_subscription_id,
    )
from models.subscription_models.subscription_models import (
    Subscription,
    Invoice,
    CancelSubscriptionRequest,
    ChangePlanRequest,
)
from utils.path_validation import is_production
import os

# Configuração do Stripe (import condicional)
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if STRIPE_SECRET_KEY and STRIPE_AVAILABLE:
    stripe.api_key = STRIPE_SECRET_KEY

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription Services❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def get_subscription_service(user_id: str) -> Optional[Subscription]:
    """Busca assinatura atual do usuário."""
    subscription = await get_subscription_by_user_id(user_id)
    if not subscription:
        return None
    return Subscription(**subscription)

async def get_invoices_service(user_id: str) -> list[Invoice]:
    """Lista todas as faturas do usuário."""
    subscription = await get_subscription_by_user_id(user_id)
    if not subscription:
        return []
    
    invoices = await get_invoices_by_subscription_id(subscription["id"])
    return [Invoice(**invoice) for invoice in invoices]

async def cancel_subscription_service(user_id: str, immediately: bool = False) -> Subscription:
    """Cancela assinatura do usuário."""
    subscription = await get_subscription_by_user_id(user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    if subscription["status"] == "canceled":
        raise HTTPException(status_code=400, detail="Assinatura já está cancelada")
    
    # Se tiver integração com Stripe, cancela lá também
    if subscription.get("stripeSubscriptionId") and STRIPE_SECRET_KEY and STRIPE_AVAILABLE:
        try:
            if immediately:
                stripe.Subscription.delete(subscription["stripeSubscriptionId"])
            else:
                stripe.Subscription.modify(
                    subscription["stripeSubscriptionId"],
                    cancel_at_period_end=True
                )
        except Exception as e:
            # Log do erro mas continua com cancelamento local
            print(f"Erro ao cancelar no Stripe: {e}")
    
    updated = await cancel_subscription(user_id, immediately)
    if not updated:
        raise HTTPException(status_code=500, detail="Erro ao cancelar assinatura")
    
    return Subscription(**updated)

async def resume_subscription_service(user_id: str) -> Subscription:
    """Reativa assinatura cancelada."""
    subscription = await get_subscription_by_user_id(user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    if subscription["status"] != "canceled" and not subscription.get("cancelAtPeriodEnd"):
        raise HTTPException(status_code=400, detail="Assinatura não está cancelada")
    
    # Se tiver integração com Stripe, reativa lá também
    if subscription.get("stripeSubscriptionId") and STRIPE_SECRET_KEY and STRIPE_AVAILABLE:
        try:
            stripe.Subscription.modify(
                subscription["stripeSubscriptionId"],
                cancel_at_period_end=False
            )
        except Exception as e:
            # Log do erro mas continua com reativação local
            print(f"Erro ao reativar no Stripe: {e}")
    
    updated = await resume_subscription(user_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Erro ao reativar assinatura")
    
    return Subscription(**updated)

async def change_plan_service(user_id: str, plan_id: str, billing_cycle: str) -> Subscription:
    """Altera plano da assinatura."""
    subscription = await get_subscription_by_user_id(user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    # Validação de plan_id e billing_cycle
    valid_plans = ['basic', 'plus', 'pro', 'elite']
    valid_cycles = ['monthly', 'yearly']
    
    if plan_id not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Plano inválido. Deve ser um de: {valid_plans}")
    
    if billing_cycle not in valid_cycles:
        raise HTTPException(status_code=400, detail=f"Ciclo de cobrança inválido. Deve ser um de: {valid_cycles}")
    
    # Se tiver integração com Stripe, atualiza lá também
    if subscription.get("stripeSubscriptionId") and STRIPE_SECRET_KEY and STRIPE_AVAILABLE:
        try:
            # Aqui você precisaria mapear plan_id para price_id do Stripe
            # Por enquanto, apenas atualiza o status
            stripe.Subscription.modify(
                subscription["stripeSubscriptionId"],
                metadata={"planId": plan_id, "billingCycle": billing_cycle}
            )
        except Exception as e:
            # Log do erro mas continua com atualização local
            print(f"Erro ao atualizar plano no Stripe: {e}")
    
    updated = await update_subscription(
        user_id,
        plan_id=plan_id,
        billing_cycle=billing_cycle
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Erro ao alterar plano")
    
    return Subscription(**updated)

def _get_stripe_price_id(plan_id: str, billing_cycle: str) -> Optional[str]:
    """Retorna price_id do Stripe a partir de env vars. Ex.: STRIPE_PRICE_BASIC_MONTHLY, STRIPE_PRICE_PLUS_YEARLY."""
    key = f"STRIPE_PRICE_{plan_id.upper()}_{billing_cycle.upper()}"
    return os.getenv(key)


async def create_checkout_session_service(
    user_id: str,
    plan_id: str,
    billing_cycle: str,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> str:
    """Cria sessão de checkout Stripe e retorna checkout_url."""
    if not STRIPE_SECRET_KEY or not STRIPE_AVAILABLE:
        raise HTTPException(status_code=501, detail="Stripe não configurado. Defina STRIPE_SECRET_KEY e os price IDs (STRIPE_PRICE_*_MONTHLY/YEARLY).")
    price_id = _get_stripe_price_id(plan_id, billing_cycle)
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"Price ID não configurado para plano {plan_id} ({billing_cycle}). Configure STRIPE_PRICE_{plan_id.upper()}_{billing_cycle.upper()} no .env.",
        )
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
    success = success_url or f"{frontend_url}/dashboard?checkout=success"
    cancel = cancel_url or f"{frontend_url}/dashboard?checkout=cancel"
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success,
            cancel_url=cancel,
            metadata={"userId": user_id, "planId": plan_id, "billingCycle": billing_cycle},
            subscription_data={"metadata": {"userId": user_id, "planId": plan_id, "billingCycle": billing_cycle}},
        )
        return session.url or ""
    except Exception as e:
        msg = "Erro ao criar sessão de checkout." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "CHECKOUT_FAILED", "message": msg})


async def get_portal_url_service(user_id: str) -> str:
    """Gera URL do Stripe Customer Portal."""
    subscription = await get_subscription_by_user_id(user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    stripe_customer_id = subscription.get("stripeCustomerId")
    if not stripe_customer_id:
        raise HTTPException(status_code=400, detail="Cliente Stripe não encontrado")
    
    if not STRIPE_SECRET_KEY or not STRIPE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Stripe não configurado")
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=os.getenv("STRIPE_PORTAL_RETURN_URL", "https://app.pulso.com/subscription")
        )
        return session.url
    except Exception as e:
        msg = "Erro ao gerar URL do portal." if is_production() else str(e)
        raise HTTPException(status_code=500, detail={"code": "PORTAL_URL_FAILED", "message": msg})

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Webhook Services❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def handle_stripe_webhook(event_type: str, event_data: dict, event_id: str = None):
    """
    Processa eventos do Stripe webhook com idempotência por event_id.
    Se event_id já foi processado, retorna sem reprocessar.
    """
    if not STRIPE_AVAILABLE:
        print("Stripe não disponível, ignorando webhook")
        return
    
    from datetime import datetime
    
    # Idempotência: verificar se event_id já foi processado
    if event_id:
        try:
            from storage.database.database_core import get_collection
        except ImportError:
            from app.storage.database.database_core import get_collection
        webhook_events = get_collection("stripe_webhook_events")
        existing = webhook_events.find_one({"event_id": event_id})
        if existing:
            print(f"Webhook event {event_id} já processado, ignorando (idempotência)")
            return
        # Registrar event_id antes de processar
        webhook_events.insert_one({
            "event_id": event_id,
            "event_type": event_type,
            "processed_at": datetime.utcnow(),
        })
    
    if event_type == "checkout.session.completed":
        # Criar ou atualizar subscription
        session = event_data.get("object", {})
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        
        if subscription_id:
            # Busca dados da subscription no Stripe
            try:
                if not STRIPE_AVAILABLE:
                    return
                stripe_sub = stripe.Subscription.retrieve(subscription_id)
                user_id = session.get("metadata", {}).get("userId")
                
                if user_id:
                    # Verifica se já existe
                    existing = await get_subscription_by_stripe_subscription_id(subscription_id)
                    if existing:
                        await update_subscription(
                            user_id,
                            status=stripe_sub.status,
                            stripe_customer_id=customer_id,
                            stripe_subscription_id=subscription_id,
                            current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
                            current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end)
                        )
                    else:
                        await create_subscription(
                            user_id=user_id,
                            plan_id=stripe_sub.metadata.get("planId", "basic"),
                            billing_cycle=stripe_sub.metadata.get("billingCycle", "monthly"),
                            status=stripe_sub.status,
                            stripe_customer_id=customer_id,
                            stripe_subscription_id=subscription_id
                        )
            except Exception as e:
                print(f"Erro ao processar checkout.session.completed: {e}")
    
    elif event_type == "invoice.payment_succeeded":
        # Atualizar invoice para 'paid'
        invoice = event_data.get("object", {})
        stripe_invoice_id = invoice.get("id")
        subscription_id = invoice.get("subscription")
        
        if stripe_invoice_id:
            existing_invoice = await get_invoice_by_stripe_id(stripe_invoice_id)
            if existing_invoice:
                await update_invoice_status(
                    existing_invoice["id"],
                    status="paid",
                    paid_at=datetime.fromtimestamp(invoice.get("created", datetime.utcnow().timestamp()))
                )
            elif subscription_id:
                # Busca subscription para pegar o ID local
                sub = await get_subscription_by_stripe_subscription_id(subscription_id)
                if sub:
                    await create_invoice(
                        subscription_id=sub["id"],
                        amount=invoice.get("amount_paid", 0),
                        currency=invoice.get("currency", "usd"),
                        status="paid",
                        invoice_url=invoice.get("hosted_invoice_url"),
                        paid_at=datetime.fromtimestamp(invoice.get("created", datetime.utcnow().timestamp())),
                        stripe_invoice_id=stripe_invoice_id
                    )
    
    elif event_type == "invoice.payment_failed":
        # Atualizar invoice para 'failed' e subscription para 'past_due'
        invoice = event_data.get("object", {})
        stripe_invoice_id = invoice.get("id")
        subscription_id = invoice.get("subscription")
        
        if stripe_invoice_id:
            existing_invoice = await get_invoice_by_stripe_id(stripe_invoice_id)
            if existing_invoice:
                await update_invoice_status(existing_invoice["id"], status="failed")
        
        if subscription_id:
            sub = await get_subscription_by_stripe_subscription_id(subscription_id)
            if sub:
                await update_subscription(sub["userId"], status="past_due")
    
    elif event_type == "customer.subscription.updated":
        # Sincronizar mudanças na subscription
        stripe_sub = event_data.get("object", {})
        subscription_id = stripe_sub.get("id")
        
        if subscription_id:
            sub = await get_subscription_by_stripe_subscription_id(subscription_id)
            if sub:
                await update_subscription(
                    sub["userId"],
                    status=stripe_sub.get("status"),
                    cancel_at_period_end=stripe_sub.get("cancel_at_period_end", False),
                    current_period_start=datetime.fromtimestamp(stripe_sub.get("current_period_start", 0)),
                    current_period_end=datetime.fromtimestamp(stripe_sub.get("current_period_end", 0))
                )
    
    elif event_type == "customer.subscription.deleted":
        # Marcar subscription como cancelada
        stripe_sub = event_data.get("object", {})
        subscription_id = stripe_sub.get("id")
        
        if subscription_id:
            sub = await get_subscription_by_stripe_subscription_id(subscription_id)
            if sub:
                await update_subscription(sub["userId"], status="canceled")
