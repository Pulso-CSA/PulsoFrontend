# 🚀 Deploy Router - Deploy Automatizado

<div align="center">

![Deploy](https://img.shields.io/badge/Deploy-2196F3?style=for-the-badge&logo=rocket&logoColor=white)
![Automation](https://img.shields.io/badge/Automation-4CAF50?style=for-the-badge&logoColor=white)

**Endpoints para deploy automatizado de projetos**

</div>

---

## 📋 Visão Geral

O módulo `deploy_router/` gerencia o **deploy automatizado** de projetos:

- 🚀 Iniciar deploy de projetos
- 📊 Monitorar status de deploy
- 🔙 Rollback de versões
- 📋 Histórico de deploys

## 📁 Estrutura

```
deploy_router/
└── 📄 deploy_router.py    # Endpoints de deploy
```

## 🌐 Endpoints

### `POST /deploy/start`

Inicia um novo deploy.

```http
POST /deploy/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "environment": "staging",
  "config": {
    "replicas": 2,
    "resources": {
      "memory": "512Mi",
      "cpu": "500m"
    }
  }
}
```

**Resposta (202 Accepted):**
```json
{
  "deploy_id": "deploy_456",
  "status": "pending",
  "started_at": "2024-01-15T10:30:00Z",
  "logs_url": "/deploy/deploy_456/logs"
}
```

### `GET /deploy/status/{deploy_id}`

Obtém status de um deploy.

```http
GET /deploy/status/deploy_456
Authorization: Bearer {token}
```

**Resposta (200 OK):**
```json
{
  "deploy_id": "deploy_456",
  "status": "deploying",
  "progress": 65,
  "message": "Building container image...",
  "started_at": "2024-01-15T10:30:00Z",
  "steps": [
    {"name": "checkout", "status": "completed"},
    {"name": "build", "status": "running"},
    {"name": "test", "status": "pending"},
    {"name": "deploy", "status": "pending"}
  ]
}
```

### `POST /deploy/rollback/{deploy_id}`

Executa rollback para versão anterior.

```http
POST /deploy/rollback/deploy_456
Authorization: Bearer {token}
```

### `GET /deploy/history/{project_id}`

Lista histórico de deploys de um projeto.

```http
GET /deploy/history/proj_123
Authorization: Bearer {token}
```

## 🧪 Testes via cURL

> Base: `http://localhost:8000`

```bash
# Iniciar containers
curl -s -X POST http://localhost:8000/deploy/docker/start -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\",\"root_path\":\"/caminho/raiz\"}"

# Rebuild containers
curl -s -X POST http://localhost:8000/deploy/docker/rebuild -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\"}"

# Parar containers
curl -s -X POST http://localhost:8000/deploy/docker/stop -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\"}"

# Logs (level: todos|info|warning|error)
curl -s -X GET "http://localhost:8000/deploy/docker/logs?level=todos"

# Limpar logs
curl -s -X DELETE http://localhost:8000/deploy/docker/logs/clear
```

## 🔄 Fluxo de Deploy

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Checkout │──▶│  Build   │──▶│   Test   │──▶│  Deploy  │──▶│  Health  │
│   Code   │   │  Image   │   │   Run    │   │ Container│   │  Check   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

## 🔗 Links Relacionados

- [🔧 Deploy Service](../../services/deploy/README.md)
- [📊 Deploy Models](../../models/deploy_models/README.md)

---

<div align="center">

**🚀 Deploy contínuo automatizado**

</div>
