# 💳 Subscription Service - Serviço de Assinaturas

<div align="center">

![Stripe](https://img.shields.io/badge/Stripe-008CDD?style=for-the-badge&logo=stripe&logoColor=white)
![Payments](https://img.shields.io/badge/Payments-4CAF50?style=for-the-badge&logoColor=white)

**Lógica de negócio para assinaturas e pagamentos**

</div>

---

## 📋 Visão Geral

O `subscription/` implementa a **lógica de monetização**:

- 💰 Gestão de planos
- 🛒 Processamento de checkout
- 🔄 Tratamento de webhooks
- 📊 Status de assinaturas

## 📁 Estrutura

```
subscription/
└── 📄 subscription_service.py    # Serviço de assinaturas
```

## 🔧 Métodos Principais

```python
class SubscriptionService:
    """Serviço de gestão de assinaturas Stripe."""
    
    def __init__(self):
        self.stripe = stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    async def get_plans(self) -> List[Plan]:
        """Lista todos os planos disponíveis."""
        pass
    
    async def create_checkout_session(
        self,
        user_id: str,
        plan_id: str,
        success_url: str,
        cancel_url: str
    ) -> CheckoutSession:
        """Cria sessão de checkout no Stripe."""
        pass
    
    async def handle_webhook(
        self, 
        payload: bytes, 
        signature: str
    ) -> None:
        """Processa webhook do Stripe."""
        pass
    
    async def get_subscription_status(
        self, 
        user_id: str
    ) -> SubscriptionStatus:
        """Obtém status da assinatura do usuário."""
        pass
    
    async def cancel_subscription(
        self, 
        subscription_id: str,
        at_period_end: bool = True
    ) -> None:
        """Cancela assinatura."""
        pass
```

## 💳 Integração Stripe

```python
# Exemplo de criação de checkout
async def create_checkout_session(self, ...):
    session = stripe.checkout.Session.create(
        customer_email=user.email,
        line_items=[{
            'price': plan.stripe_price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={'user_id': user_id}
    )
    return CheckoutSession(
        checkout_url=session.url,
        session_id=session.id
    )
```

## 🔗 Links Relacionados

- [🌐 Subscription Router](../../routers/subscription_router/README.md)
- [📊 Subscription Models](../../models/subscription_models/README.md)
- [💾 Subscription Database](../../storage/database/subscription/README.md)

---

<div align="center">

**💳 Monetização integrada com Stripe**

</div>
