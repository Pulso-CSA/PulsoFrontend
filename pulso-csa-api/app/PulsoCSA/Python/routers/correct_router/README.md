# 🔧 Correct Router - Correção de Código

<div align="center">

![Correction](https://img.shields.io/badge/Code_Correction-E91E63?style=for-the-badge&logoColor=white)
![AI](https://img.shields.io/badge/AI_Assisted-412991?style=for-the-badge&logo=openai&logoColor=white)

**Endpoints de correção automática de código (C2b, C3, C4)**

</div>

---

## 📋 Visão Geral

O módulo `correct_router/` implementa o **pipeline de correção de código**:

- 📋 C2b: Planejamento de correção
- ✍️ C3: Escrita de código corrigido
- ⚡ C4: Implementação final das correções

## 📁 Estrutura

```
correct_router/
├── 📄 code_plan_router.py          # C2b - Planejamento
├── 📄 code_writer_router.py        # C3 - Escrita
└── 📄 code_implementer_router.py   # C4 - Implementação
```

## 🌐 Endpoints

### `POST /correct/plan` (C2b)

Cria plano de correção baseado em erros identificados.

```http
POST /correct/plan
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "error_context": {
    "file": "main.py",
    "line": 45,
    "error_type": "TypeError",
    "message": "unsupported operand type(s) for +: 'int' and 'str'"
  },
  "code_snippet": "result = count + name"
}
```

**Resposta (200 OK):**
```json
{
  "plan_id": "plan_456",
  "analysis": {
    "root_cause": "Type mismatch in concatenation",
    "affected_code": "result = count + name",
    "suggested_fix": "Convert int to str before concatenation"
  },
  "correction_steps": [
    "Add type conversion: str(count)",
    "Update variable assignment",
    "Add type hints"
  ]
}
```

### `POST /correct/write` (C3)

Gera código corrigido baseado no plano.

```http
POST /correct/write
Authorization: Bearer {token}
Content-Type: application/json

{
  "plan_id": "plan_456",
  "target_file": "main.py"
}
```

**Resposta (200 OK):**
```json
{
  "write_id": "write_789",
  "corrected_code": "result = str(count) + name",
  "full_file_content": "...",
  "changes": [
    {
      "line": 45,
      "original": "result = count + name",
      "corrected": "result = str(count) + name"
    }
  ]
}
```

### `POST /correct/implement` (C4)

Aplica as correções no projeto.

```http
POST /correct/implement
Authorization: Bearer {token}
Content-Type: application/json

{
  "write_id": "write_789",
  "apply_changes": true,
  "create_backup": true
}
```

**Resposta (200 OK):**
```json
{
  "implementation_id": "impl_101",
  "status": "success",
  "files_modified": ["main.py"],
  "backup_path": "/backups/proj_123/2024-01-15/",
  "verification": {
    "syntax_valid": true,
    "tests_passed": true
  }
}
```

## 🧪 Testes via cURL

> Base: `http://localhost:8000` | `root_path` = caminho absoluto do projeto

```bash
# Code Plan (C2b)
curl -s -X POST http://localhost:8000/code-plan/run -H "Content-Type: application/json" -d "{\"prompt\":\"corrigir erro de import\",\"root_path\":\"/caminho/projeto\",\"usuario\":\"teste\"}"

# Code Writer (C3) - usar id_requisicao retornado pelo Code Plan
curl -s -X POST http://localhost:8000/code-writer/run -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"root_path\":\"/caminho/projeto\",\"usuario\":\"teste\",\"dry_run\":false}"

# Code Implementer (C4)
curl -s -X POST http://localhost:8000/code-implementer/run -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"root_path\":\"/caminho/projeto\",\"usuario\":\"teste\",\"dry_run\":true}"
```

## 🔄 Fluxo de Correção

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Erro    │───▶│   Plan   │───▶│  Write   │───▶│Implement │
│Detectado │    │  (C2b)   │    │  (C3)    │    │  (C4)    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
  Análise       Estratégia      Código         Aplicação
  de Erro       de Correção    Corrigido       Final
```

## 🔗 Links Relacionados

- [🔧 Correct Services](../../services/agents/correct_services/README.md)
- [📊 Correct Models](../../models/correct_models/README.md)
- [🔄 Correct Workflow](../../workflow/correct_workflow/README.md)

---

<div align="center">

**🔧 Correção automática inteligente**

</div>
