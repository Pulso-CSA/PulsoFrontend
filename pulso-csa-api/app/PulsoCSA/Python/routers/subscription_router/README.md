# 💳 Subscription Router - Assinaturas e Pagamentos

<div align="center">

![Stripe](https://img.shields.io/badge/Stripe-008CDD?style=for-the-badge&logo=stripe&logoColor=white)
![Payments](https://img.shields.io/badge/Payments-4CAF50?style=for-the-badge&logo=cashapp&logoColor=white)

**Endpoints de gestão de assinaturas, planos e pagamentos**

</div>

---

## 📋 Visão Geral

O módulo `subscription_router/` gerencia todos os aspectos de **monetização** da plataforma:

- 💰 Listagem de planos disponíveis
- 🛒 Checkout de assinaturas
- 🔄 Webhooks do Stripe
- 📊 Status de assinatura
- ❌ Cancelamento de planos

## 📁 Estrutura

```
subscription_router/
└── 📄 router_subscription.py    # Endpoints de assinatura
```

## 🌐 Endpoints

### `GET /subscription/plans`

Lista todos os planos disponíveis.

```http
GET /subscription/plans
```

**Resposta (200 OK):**
```json
{
  "plans": [
    {
      "id": "plan_basic",
      "name": "Basic",
      "price": 29.99,
      "currency": "USD",
      "interval": "month",
      "features": [
        "10 projetos",
        "5GB storage",
        "Suporte email"
      ]
    },
    {
      "id": "plan_pro",
      "name": "Professional",
      "price": 99.99,
      "currency": "USD",
      "interval": "month",
      "features": [
        "Projetos ilimitados",
        "50GB storage",
        "Suporte prioritário",
        "API access"
      ]
    }
  ]
}
```

### `POST /subscription/checkout`

Inicia processo de checkout com Stripe.

```http
POST /subscription/checkout
Authorization: Bearer {token}
Content-Type: application/json

{
  "plan_id": "plan_pro",
  "success_url": "https://app.pulso.com/success",
  "cancel_url": "https://app.pulso.com/cancel"
}
```

**Resposta (200 OK):**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/...",
  "session_id": "cs_live_..."
}
```

### `POST /subscription/webhook`

Endpoint para webhooks do Stripe.

```http
POST /subscription/webhook
Stripe-Signature: {stripe_signature}

{
  "type": "checkout.session.completed",
  "data": {...}
}
```

### `GET /subscription/status`

Obtém status da assinatura atual.

```http
GET /subscription/status
Authorization: Bearer {token}
```

**Resposta (200 OK):**
```json
{
  "status": "active",
  "plan": {
    "id": "plan_pro",
    "name": "Professional"
  },
  "current_period_start": "2024-01-01T00:00:00Z",
  "current_period_end": "2024-02-01T00:00:00Z",
  "cancel_at_period_end": false
}
```

### `POST /subscription/cancel`

Cancela a assinatura atual.

```http
POST /subscription/cancel
Authorization: Bearer {token}
```

## 🧪 Testes via cURL

> Requer token JWT em `Authorization: Bearer TOKEN` | Base: `http://localhost:8000`

```bash
# Status da assinatura
curl -s -X GET http://localhost:8000/subscription -H "Authorization: Bearer TOKEN"

# Invoices
curl -s -X GET http://localhost:8000/subscription/invoices -H "Authorization: Bearer TOKEN"

# Cancelar assinatura (immediately=false = cancela no fim do período)
curl -s -X POST http://localhost:8000/subscription/cancel -H "Content-Type: application/json" -H "Authorization: Bearer TOKEN" -d "{\"immediately\":false}"

# Reativar assinatura
curl -s -X POST http://localhost:8000/subscription/resume -H "Authorization: Bearer TOKEN"

# Trocar plano
curl -s -X POST http://localhost:8000/subscription/change-plan -H "Content-Type: application/json" -H "Authorization: Bearer TOKEN" -d "{\"planId\":\"plan_pro\",\"billingCycle\":\"monthly\"}"

# URL do portal Stripe
curl -s -X GET http://localhost:8000/subscription/portal -H "Authorization: Bearer TOKEN"
```

## 💰 Fluxo de Pagamento

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Usuário   │───▶│   Checkout  │───▶│   Stripe    │
│   Escolhe   │    │   Session   │    │   Payment   │
│   Plano     │    │             │    │   Page      │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                                             ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Acesso    │◀───│   Ativar    │◀───│   Webhook   │
│   Liberado  │    │   Assinatura│    │   Success   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔗 Links Relacionados

- [🔧 Subscription Service](../../services/subscription/README.md)
- [📊 Subscription Models](../../models/subscription_models/README.md)
- [💾 Subscription Database](../../storage/database/subscription/README.md)

---

<div align="center">

**💳 Monetização integrada com Stripe**

</div>
