# FinOps – Análise Multi-Cloud

Módulo FinOps multi-cloud: redução de custos, velocidade/performance e segurança (FinOps + CloudOps + SecOps).

## Endpoints

### POST /finops/chat (entrada única do chat FinOps)

Mensagem em linguagem natural. Usa comprehension exclusivo do módulo para interpretar intent e extrair parâmetros (cloud, quick_win_mode, guardrails).

### POST /finops/analyze

Payload estruturado. Retorna texto em linguagem natural para chat (sem PDF, sem anexos).

## Requisição Chat (POST /finops/chat)

```json
{
  "mensagem": "analise custos da minha AWS e me mostre quick wins",
  "id_requisicao": "REQ-xxx",
  "usuario": "user@email.com",
  "aws_credentials": { "access_key_id": "...", "secret_access_key": "...", "region": "us-east-1" }
}
```

## Requisição Analyze (POST /finops/analyze)

```json
{
  "cloud": "aws",
  "aws_credentials": {
    "access_key_id": "...",
    "secret_access_key": "...",
    "region": "us-east-1"
  },
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "quick_win_mode": "quick_wins",
  "guardrails_mode": true
}
```

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| cloud | Sim | `aws` \| `azure` \| `gcp` \| `multi` |
| aws_credentials | Condicional | Quando cloud=aws ou multi |
| azure_credentials | Condicional | Quando cloud=azure ou multi |
| gcp_credentials | Condicional | Quando cloud=gcp ou multi |
| quick_win_mode | Não | `quick_wins` \| `compare_regions` \| `auto_shutdown_policies` \| `none` |
| guardrails_mode | Não | Incluir seção Guardrails recomendados |
| multi_cloud_compare | Não | Comparar drivers de custo (quando cloud=multi) |

## Resposta

```json
{
  "message": "<texto narrativo completo>",
  "cloud": "aws",
  "id_requisicao": "FINOP-20250212-123456-abc123"
}
```

## Estrutura

- `routers/finops/finops_routers.py` – endpoints /finops/chat e /finops/analyze
- `agents/finops/finops_agents.py` – orquestrador
- `services/finops/finops_services.py` – pipeline principal
- `services/finops/comprehension_finops.py` – comprehension exclusivo (classify_intent, extrair_params)
- `services/finops/finops_chat_service.py` – orquestrador do chat
- `services/finops/connectors/` – AWS, Azure, GCP
- `services/finops/heuristics_engine.py` – heurísticas
- `models/finops/finops_models.py` – Pydantic (analyze)
- `models/finops/finops_chat_models.py` – Pydantic (chat)
- `prompts/finops/finops_prompt.txt` – prompt

## Dependências

- AWS: `boto3`
- Azure: `azure-identity`, `azure-mgmt-costmanagement`, etc.
- GCP: `google-cloud-billing`, `google-cloud-compute`, etc.
