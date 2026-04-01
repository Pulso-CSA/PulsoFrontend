# 🏗️ Creation Routers - Criação de Projetos

<div align="center">

![Creation](https://img.shields.io/badge/Creation-2196F3?style=for-the-badge)
![Execution](https://img.shields.io/badge/Execution-4CAF50?style=for-the-badge)

**Endpoints para execução de criação de projetos**

</div>

---

## 📋 Visão Geral

Endpoints para **criação de novos projetos** (Camada 3).

## 📁 Estrutura

```
creation_routers/
└── 📄 execution_router.py    # Endpoints de execução
```

## 🌐 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/creation/execute` | Executar criação |
| `GET` | `/creation/status/{id}` | Status da criação |

## 🧪 Testes via cURL

> Base: `http://localhost:8000` | `id_requisicao` = ID da governança (C1)

```bash
# Criar estrutura (C3a)
curl -s -X POST http://localhost:8000/execution/create-structure -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"root_path\":\"/caminho/projeto\"}"

# Criar código (C3b) - query params
curl -s -X POST "http://localhost:8000/execution/create-code?id_requisicao=REQ-20250101-120000-abcd&root_path=/caminho/projeto"
```

## 🔗 Links Relacionados

- [⚡ Execution Agents](../../agents/execution/README.md)
- [🏗️ Creator Workflow](../../workflow/creator_workflow/README.md)

---

<div align="center">

**🏗️ Criação automatizada de projetos**

</div>
