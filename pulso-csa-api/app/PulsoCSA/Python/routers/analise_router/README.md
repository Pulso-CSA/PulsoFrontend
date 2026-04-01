# 📊 Analise Router - Endpoints de Análise

<div align="center">

![Analysis](https://img.shields.io/badge/Analysis-FF5722?style=for-the-badge&logoColor=white)
![AI](https://img.shields.io/badge/AI_Powered-412991?style=for-the-badge&logo=openai&logoColor=white)

**Endpoints de análise de governança, backend e infraestrutura**

</div>

---

## 📋 Visão Geral

O módulo `analise_router/` expõe os endpoints das **camadas de análise**:

- 🏛️ Análise de Governança (C1)
- 🔧 Análise de Backend (C2)
- 🏗️ Análise de Infraestrutura (C2)

## 📁 Estrutura

```
analise_router/
├── 📄 governance_router.py    # Análise de governança (C1)
├── 📄 backend_router.py       # Análise de backend (C2)
└── 📄 infra_router.py         # Análise de infraestrutura (C2)
```

## 🌐 Endpoints

### `POST /analise/governance`

Executa análise de governança (Camada 1).

```http
POST /analise/governance
Authorization: Bearer {token}
Content-Type: application/json

{
  "prompt": "Criar sistema de autenticação seguro",
  "project_id": "proj_123",
  "context": {
    "industry": "fintech",
    "compliance": ["PCI-DSS", "LGPD"]
  }
}
```

**Resposta (200 OK):**
```json
{
  "document_id": "gov_456",
  "analysis": {
    "refined_prompt": "...",
    "compliance_score": 0.92,
    "frameworks_applied": ["COBIT", "ISO 27001"]
  },
  "recommendations": [
    "Implementar MFA",
    "Adicionar audit logging"
  ]
}
```

### `POST /analise/backend`

Executa análise de backend (Camada 2).

```http
POST /analise/backend
Authorization: Bearer {token}
Content-Type: application/json

{
  "governance_doc_id": "gov_456",
  "project_id": "proj_123"
}
```

**Resposta (200 OK):**
```json
{
  "analysis_id": "backend_789",
  "framework": "FastAPI",
  "database": "PostgreSQL",
  "architecture": "Clean Architecture",
  "patterns": ["Repository", "Service Layer", "DTO"],
  "security_recommendations": [...]
}
```

### `POST /analise/infra`

Executa análise de infraestrutura (Camada 2).

```http
POST /analise/infra
Authorization: Bearer {token}
Content-Type: application/json

{
  "backend_analysis_id": "backend_789",
  "project_id": "proj_123"
}
```

**Resposta (200 OK):**
```json
{
  "analysis_id": "infra_101",
  "containerization": "Docker",
  "orchestration": "Docker Compose",
  "ci_cd": "GitHub Actions",
  "monitoring": "Prometheus + Grafana",
  "security_recommendations": [...]
}
```

## 🧪 Testes via cURL

> Base: `http://localhost:8000` | `id_req` = id retornado por `/governance/input`

### Governança (já documentado no README raiz)

```bash
# Input, Refine, Validate, Run - ver README.md raiz
curl -s -X POST http://localhost:8000/governance/run -H "Content-Type: application/json" -d "{\"prompt\":\"criar API Flask com JWT\",\"usuario\":\"teste\"}"
```

### Backend (prefix `/backend`)

```bash
# Análise de estrutura
curl -s -X POST http://localhost:8000/backend/analise-estrutura -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\"}"

# Análise de backend (precisa estrutura_arquivos do passo anterior)
curl -s -X POST http://localhost:8000/backend/analise-backend -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"estrutura_arquivos\":{\"app\":[\"main.py\"]}}"

# Segurança de código
curl -s -X POST http://localhost:8000/backend/seguranca-codigo -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"backend\":{\"arquivos\":{},\"funcionalidades\":[],\"conexoes\":[],\"otimizacoes\":[]}}"
```

### Infra (prefix `/infra`)

```bash
# Análise de infra
curl -s -X POST http://localhost:8000/infra/analise-infra -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"estrutura_arquivos\":{},\"backend\":{}}"

# Segurança de infra
curl -s -X POST http://localhost:8000/infra/seguranca-infra -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"infraestrutura\":{}}"
```

## 🔗 Links Relacionados

- [🤖 Agents Governance](../../agents/governance/README.md)
- [🔧 Analise Services](../../services/agents/analise_services/README.md)
- [📊 Analise Models](../../models/analise_models/README.md)

---

<div align="center">

**📊 Análise inteligente com IA**

</div>
