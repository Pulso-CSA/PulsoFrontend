#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription Database❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import anyio
from typing import Optional, Dict, Any, List
from bson import ObjectId
from datetime import datetime
from app.storage.database.database_core import get_collection

# Collections
subscriptions_collection = get_collection("subscriptions")
invoices_collection = get_collection("invoices")

# Ensure indexes
try:
    subscriptions_collection.create_index("userId", unique=True)
    subscriptions_collection.create_index("stripeCustomerId")
    subscriptions_collection.create_index("stripeSubscriptionId")
except Exception:
    pass

try:
    invoices_collection.create_index("subscriptionId")
    invoices_collection.create_index("stripeInvoiceId", unique=True, sparse=True)
except Exception:
    pass

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Async wrappers (pymongo → async)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
async def _run_sync(fn, *args, **kwargs):
    """Run blocking pymongo calls without blocking the event loop."""
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription CRUD❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def create_subscription(
    user_id: str,
    plan_id: str,
    billing_cycle: str,
    status: str = "active",
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    has_openai_key: bool = False
) -> Dict[str, Any]:
    """Cria uma nova assinatura."""
    now = datetime.utcnow()
    # Calcula período baseado no billing cycle
    if billing_cycle == "monthly":
        period_end = datetime(now.year, now.month + 1, now.day, now.hour, now.minute, now.second)
        if period_end.month > 12:
            period_end = datetime(now.year + 1, 1, now.day, now.hour, now.minute, now.second)
    else:  # yearly
        period_end = datetime(now.year + 1, now.month, now.day, now.hour, now.minute, now.second)
    
    doc = {
        "userId": user_id,
        "planId": plan_id,
        "status": status,
        "billingCycle": billing_cycle,
        "currentPeriodStart": now,
        "currentPeriodEnd": period_end,
        "cancelAtPeriodEnd": False,
        "hasOpenAIKey": has_openai_key,
        "stripeCustomerId": stripe_customer_id,
        "stripeSubscriptionId": stripe_subscription_id,
        "createdAt": now,
        "updatedAt": now
    }
    
    result = await _run_sync(subscriptions_collection.insert_one, doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = doc["_id"]
    doc["currentPeriodStart"] = now.isoformat()
    doc["currentPeriodEnd"] = period_end.isoformat()
    doc["createdAt"] = now.isoformat()
    doc["updatedAt"] = now.isoformat()
    return doc

async def get_subscription_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Busca assinatura por userId."""
    subscription = await _run_sync(
        subscriptions_collection.find_one,
        {"userId": user_id}
    )
    if not subscription:
        return None
    
    subscription["_id"] = str(subscription["_id"])
    subscription["id"] = subscription["_id"]
    subscription["currentPeriodStart"] = subscription["currentPeriodStart"].isoformat() if isinstance(subscription["currentPeriodStart"], datetime) else subscription["currentPeriodStart"]
    subscription["currentPeriodEnd"] = subscription["currentPeriodEnd"].isoformat() if isinstance(subscription["currentPeriodEnd"], datetime) else subscription["currentPeriodEnd"]
    subscription["createdAt"] = subscription["createdAt"].isoformat() if isinstance(subscription["createdAt"], datetime) else subscription["createdAt"]
    subscription["updatedAt"] = subscription["updatedAt"].isoformat() if isinstance(subscription["updatedAt"], datetime) else subscription["updatedAt"]
    return subscription

async def get_subscription_by_stripe_subscription_id(stripe_subscription_id: str) -> Optional[Dict[str, Any]]:
    """Busca assinatura por stripeSubscriptionId."""
    subscription = await _run_sync(
        subscriptions_collection.find_one,
        {"stripeSubscriptionId": stripe_subscription_id}
    )
    if not subscription:
        return None
    
    subscription["_id"] = str(subscription["_id"])
    subscription["id"] = subscription["_id"]
    subscription["currentPeriodStart"] = subscription["currentPeriodStart"].isoformat() if isinstance(subscription["currentPeriodStart"], datetime) else subscription["currentPeriodStart"]
    subscription["currentPeriodEnd"] = subscription["currentPeriodEnd"].isoformat() if isinstance(subscription["currentPeriodEnd"], datetime) else subscription["currentPeriodEnd"]
    subscription["createdAt"] = subscription["createdAt"].isoformat() if isinstance(subscription["createdAt"], datetime) else subscription["createdAt"]
    subscription["updatedAt"] = subscription["updatedAt"].isoformat() if isinstance(subscription["updatedAt"], datetime) else subscription["updatedAt"]
    return subscription

async def update_subscription(
    user_id: str,
    plan_id: Optional[str] = None,
    billing_cycle: Optional[str] = None,
    status: Optional[str] = None,
    cancel_at_period_end: Optional[bool] = None,
    has_openai_key: Optional[bool] = None,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    current_period_start: Optional[datetime] = None,
    current_period_end: Optional[datetime] = None
) -> Optional[Dict[str, Any]]:
    """Atualiza uma assinatura."""
    update_data = {"updatedAt": datetime.utcnow()}
    
    if plan_id is not None:
        update_data["planId"] = plan_id
    if billing_cycle is not None:
        update_data["billingCycle"] = billing_cycle
    if status is not None:
        update_data["status"] = status
    if cancel_at_period_end is not None:
        update_data["cancelAtPeriodEnd"] = cancel_at_period_end
    if has_openai_key is not None:
        update_data["hasOpenAIKey"] = has_openai_key
    if stripe_customer_id is not None:
        update_data["stripeCustomerId"] = stripe_customer_id
    if stripe_subscription_id is not None:
        update_data["stripeSubscriptionId"] = stripe_subscription_id
    if current_period_start is not None:
        update_data["currentPeriodStart"] = current_period_start
    if current_period_end is not None:
        update_data["currentPeriodEnd"] = current_period_end
    
    result = await _run_sync(
        subscriptions_collection.find_one_and_update,
        {"userId": user_id},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        return None
    
    result["_id"] = str(result["_id"])
    result["id"] = result["_id"]
    result["currentPeriodStart"] = result["currentPeriodStart"].isoformat() if isinstance(result["currentPeriodStart"], datetime) else result["currentPeriodStart"]
    result["currentPeriodEnd"] = result["currentPeriodEnd"].isoformat() if isinstance(result["currentPeriodEnd"], datetime) else result["currentPeriodEnd"]
    result["createdAt"] = result["createdAt"].isoformat() if isinstance(result["createdAt"], datetime) else result["createdAt"]
    result["updatedAt"] = result["updatedAt"].isoformat() if isinstance(result["updatedAt"], datetime) else result["updatedAt"]
    return result

async def cancel_subscription(user_id: str, immediately: bool = False) -> Optional[Dict[str, Any]]:
    """Cancela uma assinatura."""
    if immediately:
        return await update_subscription(user_id, status="canceled", cancel_at_period_end=False)
    else:
        return await update_subscription(user_id, cancel_at_period_end=True)

async def resume_subscription(user_id: str) -> Optional[Dict[str, Any]]:
    """Reativa uma assinatura cancelada."""
    return await update_subscription(user_id, status="active", cancel_at_period_end=False)

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Invoice CRUD❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def create_invoice(
    subscription_id: str,
    amount: int,
    currency: str,
    status: str,
    invoice_url: Optional[str] = None,
    paid_at: Optional[datetime] = None,
    stripe_invoice_id: Optional[str] = None
) -> Dict[str, Any]:
    """Cria uma nova fatura."""
    now = datetime.utcnow()
    doc = {
        "subscriptionId": subscription_id,
        "amount": amount,
        "currency": currency,
        "status": status,
        "invoiceUrl": invoice_url,
        "paidAt": paid_at,
        "stripeInvoiceId": stripe_invoice_id,
        "createdAt": now
    }
    
    result = await _run_sync(invoices_collection.insert_one, doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = doc["_id"]
    doc["paidAt"] = paid_at.isoformat() if paid_at and isinstance(paid_at, datetime) else (paid_at if paid_at else None)
    doc["createdAt"] = now.isoformat()
    return doc

async def get_invoices_by_subscription_id(subscription_id: str) -> List[Dict[str, Any]]:
    """Busca todas as faturas de uma assinatura."""
    def _get_invoices():
        invoices = list(invoices_collection.find({"subscriptionId": subscription_id}).sort("createdAt", -1))
        result = []
        for invoice in invoices:
            invoice["_id"] = str(invoice["_id"])
            invoice["id"] = invoice["_id"]
            invoice["paidAt"] = invoice["paidAt"].isoformat() if invoice.get("paidAt") and isinstance(invoice["paidAt"], datetime) else invoice.get("paidAt")
            invoice["createdAt"] = invoice["createdAt"].isoformat() if isinstance(invoice["createdAt"], datetime) else invoice["createdAt"]
            result.append(invoice)
        return result
    
    return await _run_sync(_get_invoices)

async def update_invoice_status(
    invoice_id: str,
    status: str,
    paid_at: Optional[datetime] = None
) -> Optional[Dict[str, Any]]:
    """Atualiza o status de uma fatura."""
    if not invoice_id or not ObjectId.is_valid(invoice_id):
        return None
    update_data = {"status": status}
    if paid_at is not None:
        update_data["paidAt"] = paid_at
    
    result = await _run_sync(
        invoices_collection.find_one_and_update,
        {"_id": ObjectId(invoice_id)},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        return None
    
    result["_id"] = str(result["_id"])
    result["id"] = result["_id"]
    result["paidAt"] = result["paidAt"].isoformat() if result.get("paidAt") and isinstance(result["paidAt"], datetime) else result.get("paidAt")
    result["createdAt"] = result["createdAt"].isoformat() if isinstance(result["createdAt"], datetime) else result["createdAt"]
    return result

async def get_invoice_by_stripe_id(stripe_invoice_id: str) -> Optional[Dict[str, Any]]:
    """Busca fatura por stripeInvoiceId."""
    invoice = await _run_sync(
        invoices_collection.find_one,
        {"stripeInvoiceId": stripe_invoice_id}
    )
    if not invoice:
        return None
    
    invoice["_id"] = str(invoice["_id"])
    invoice["id"] = invoice["_id"]
    invoice["paidAt"] = invoice["paidAt"].isoformat() if invoice.get("paidAt") and isinstance(invoice["paidAt"], datetime) else invoice.get("paidAt")
    invoice["createdAt"] = invoice["createdAt"].isoformat() if isinstance(invoice["createdAt"], datetime) else invoice["createdAt"]
    return invoice
