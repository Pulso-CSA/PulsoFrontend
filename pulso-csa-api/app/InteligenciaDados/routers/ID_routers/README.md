# 🔍 ID Routers - Endpoints de Consulta

<div align="center">

![Query](https://img.shields.io/badge/Query-2196F3?style=for-the-badge)
![Database](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**Endpoints para consultas de identificação**

</div>

---

## 📋 Visão Geral

Endpoints para **consultas de identificação** no banco MySQL.

## 📁 Estrutura

```
ID_routers/
└── 📄 query_get_router.py    # Endpoints de consulta
```

## 🌐 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/id/query` | Executar consulta |
| `GET` | `/id/entity/{type}/{id}` | Obter entidade |

## 🧪 Testes via cURL

> Base: `http://localhost:8000`

```bash
# Query em linguagem natural (requer config do banco MySQL)
curl -s -X POST http://localhost:8000/inteligencia-dados/query -H "Content-Type: application/json" -d "{\"prompt\":\"Quantos usuários existem?\",\"db_config\":{\"host\":\"localhost\",\"port\":3306,\"user\":\"root\",\"password\":\"senha\",\"database\":\"mydb\"}}"
```

## 🔗 Links Relacionados

- [🔧 ID Services](../../services/ID_services/README.md)
- [🤖 ID Agents](../../agents/ID/README.md)

---

<div align="center">

**🔍 Consultas de identificação**

</div>
