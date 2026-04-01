# 🐍 Venv Routers - Gestão de Ambientes Virtuais

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Venv](https://img.shields.io/badge/Virtual_Env-4CAF50?style=for-the-badge)

**Endpoints para gestão de ambientes virtuais Python**

</div>

---

## 📋 Visão Geral

Endpoints para criar e gerenciar **ambientes virtuais Python**.

## 📁 Estrutura

```
venv_routers/
└── 📄 venv_router.py    # Endpoints de venv
```

## 🌐 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/venv/create` | Criar ambiente |
| `POST` | `/venv/install` | Instalar pacotes |
| `DELETE` | `/venv/{id}` | Remover ambiente |
| `GET` | `/venv/{id}/packages` | Listar pacotes |

## 🧪 Testes via cURL

> Base: `http://localhost:8000`

```bash
# Logs do venv
curl -s -X GET "http://localhost:8000/venv/logs?level=todos"

# Limpar logs
curl -s -X DELETE http://localhost:8000/venv/logs/clear

# Criar venv
curl -s -X POST http://localhost:8000/venv/create -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\"}"

# Recriar venv
curl -s -X POST http://localhost:8000/venv/recreate -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\"}"

# Executar (ativar) venv
curl -s -X POST http://localhost:8000/venv/execute -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\"}"

# Desativar venv
curl -s -X POST http://localhost:8000/venv/deactivate -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\"}"
```

## 🔗 Links Relacionados

- [🔧 Venv Service](../../services/venv_service/README.md)
- [📊 Venv Models](../../models/venv_models/README.md)

---

<div align="center">

**🐍 Gestão de ambientes Python**

</div>
