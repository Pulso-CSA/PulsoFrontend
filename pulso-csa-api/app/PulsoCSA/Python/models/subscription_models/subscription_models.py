#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Subscription Models❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class Subscription(BaseModel):
    """Modelo de assinatura."""
    id: str
    userId: str
    planId: Literal['basic', 'plus', 'pro', 'elite']
    status: Literal['active', 'canceled', 'past_due', 'trialing', 'incomplete', 'incomplete_expired', 'unpaid']
    billingCycle: Literal['monthly', 'yearly']
    currentPeriodStart: str  # ISO date
    currentPeriodEnd: str    # ISO date
    cancelAtPeriodEnd: bool
    hasOpenAIKey: bool
    stripeCustomerId: Optional[str] = None
    stripeSubscriptionId: Optional[str] = None
    createdAt: str
    updatedAt: str

class Invoice(BaseModel):
    """Modelo de fatura/invoice."""
    id: str
    subscriptionId: str
    amount: int  # em centavos (ex: 2999 = $29.99)
    currency: str  # 'USD', 'BRL', etc
    status: Literal['paid', 'pending', 'failed']
    invoiceUrl: Optional[str] = None  # URL do PDF da fatura no Stripe
    paidAt: Optional[str] = None
    createdAt: str

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Request DTOs❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class CancelSubscriptionRequest(BaseModel):
    """Payload para cancelar assinatura."""
    immediately: bool = False

class ChangePlanRequest(BaseModel):
    """Payload para alterar plano."""
    planId: Literal['basic', 'plus', 'pro', 'elite'] = Field(..., description="ID do novo plano")
    billingCycle: Literal['monthly', 'yearly'] = Field(..., description="Ciclo de cobrança")


class CheckoutRequest(BaseModel):
    """Payload para criar sessão de checkout Stripe."""
    planId: Literal['basic', 'plus', 'pro', 'elite'] = Field(..., description="ID do plano")
    billingCycle: Literal['monthly', 'yearly'] = Field(default='monthly', description="Ciclo de cobrança")
    successUrl: Optional[str] = Field(None, description="URL de redirecionamento após sucesso")
    cancelUrl: Optional[str] = Field(None, description="URL de redirecionamento se cancelar")


#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Response DTOs❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

class SubscriptionResponse(BaseModel):
    """Resposta com dados da assinatura."""
    subscription: Optional[Subscription] = None
    is_exempt: bool = Field(default=False, description="True se usuário isento (sócio/exceção)")

class InvoicesResponse(BaseModel):
    """Resposta com lista de faturas."""
    invoices: list[Invoice]

class SubscriptionUpdateResponse(BaseModel):
    """Resposta após atualização de assinatura."""
    subscription: Subscription

class PortalUrlResponse(BaseModel):
    """Resposta com URL do Stripe Customer Portal."""
    url: str


class CheckoutResponse(BaseModel):
    """Resposta com URL da sessão de checkout Stripe."""
    checkout_url: str
