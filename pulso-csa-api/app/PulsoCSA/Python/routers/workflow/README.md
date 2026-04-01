# 🔄 Workflow Router - Workflows Automatizados

<div align="center">

![Workflow](https://img.shields.io/badge/Workflow-673AB7?style=for-the-badge&logoColor=white)
![Automation](https://img.shields.io/badge/Full_Auto-4CAF50?style=for-the-badge&logoColor=white)

**Endpoints para execução de workflows automatizados**

</div>

---

## 📋 Visão Geral

O módulo `workflow/` expõe endpoints para execução de **workflows automatizados**:

- 🔧 Workflow de correção de código
- 🚀 Workflow completo automático (full-auto)
- 📊 Monitoramento de execução

## 📁 Estrutura

```
workflow/
├── 📄 correct_workflow_router.py      # Workflow de correção
└── 📄 full_auto_workflow_router.py    # Workflow completo
```

## 🌐 Endpoints

### `POST /workflow/correct`

Inicia workflow de correção de código.

```http
POST /workflow/correct
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "error_context": {
    "files": ["main.py", "utils.py"],
    "errors": [
      {"type": "TypeError", "line": 45, "file": "main.py"},
      {"type": "ImportError", "line": 3, "file": "utils.py"}
    ]
  },
  "auto_apply": true
}
```

**Resposta (202 Accepted):**
```json
{
  "workflow_id": "wf_correct_456",
  "status": "running",
  "started_at": "2024-01-15T10:30:00Z",
  "steps": [
    {"name": "analysis", "status": "running"},
    {"name": "planning", "status": "pending"},
    {"name": "writing", "status": "pending"},
    {"name": "implementation", "status": "pending"}
  ]
}
```

### `POST /workflow/full-auto`

Inicia workflow completo automático (C1 → C2 → C3).

```http
POST /workflow/full-auto
Authorization: Bearer {token}
Content-Type: application/json

{
  "prompt": "Criar API REST para gestão de produtos",
  "config": {
    "framework": "fastapi",
    "database": "mongodb",
    "auth": "jwt",
    "deploy": true
  }
}
```

**Resposta (202 Accepted):**
```json
{
  "workflow_id": "wf_full_789",
  "status": "running",
  "stages": [
    {"name": "governance", "status": "running"},
    {"name": "architecture", "status": "pending"},
    {"name": "execution", "status": "pending"},
    {"name": "deploy", "status": "pending"}
  ]
}
```

### `GET /workflow/status/{workflow_id}`

Obtém status de um workflow em execução.

```http
GET /workflow/status/wf_full_789
Authorization: Bearer {token}
```

**Resposta (200 OK):**
```json
{
  "workflow_id": "wf_full_789",
  "type": "full_auto",
  "status": "running",
  "progress": 45,
  "current_stage": "architecture",
  "stages": [
    {"name": "governance", "status": "completed", "duration_ms": 15000},
    {"name": "architecture", "status": "running", "progress": 60},
    {"name": "execution", "status": "pending"},
    {"name": "deploy", "status": "pending"}
  ],
  "artifacts": {
    "governance_doc_id": "gov_123",
    "architecture_plan_id": "arch_456"
  }
}
```

### `POST /workflow/cancel/{workflow_id}`

Cancela um workflow em execução.

```http
POST /workflow/cancel/wf_full_789
Authorization: Bearer {token}
```

## 🔄 Fluxo do Workflow Full-Auto

```
┌─────────────────────────────────────────────────────────────────────┐
│                      WORKFLOW FULL-AUTO                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │   C1     │───▶│   C2     │───▶│   C3     │───▶│  Deploy  │     │
│   │Governance│    │  Arch    │    │Execution │    │  Auto    │     │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│        │               │               │               │            │
│        ▼               ▼               ▼               ▼            │
│    Doc Técnico    Plano Arq.     Código      Projeto Live          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🧪 Testes via cURL

> Base: `http://localhost:8000` | `root_path` = caminho absoluto do projeto

```bash
# Workflow de correção completo
curl -s -X POST http://localhost:8000/workflow/correct/run -H "Content-Type: application/json" -d "{\"usuario\":\"teste\",\"prompt\":\"corrigir erro de tipo no main.py\",\"root_path\":\"/caminho/projeto\"}"

# Full Auto (Code Plan + Code Writer)
curl -s -X POST http://localhost:8000/workflow/correct/full-run -H "Content-Type: application/json" -d "{\"usuario\":\"teste\",\"prompt\":\"adicionar endpoint de health\",\"root_path\":\"/caminho/projeto\",\"dry_run\":false}"
```

## 🔗 Links Relacionados

- [🔄 Workflow Core](../../workflow/README.md)
- [🤖 Agents](../../agents/README.md)
- [🔧 Services](../../services/README.md)

---

<div align="center">

**🔄 Automação completa de ponta a ponta**

</div>
