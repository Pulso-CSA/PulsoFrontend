# 🔍 ID Agents - Agentes de Consulta

<div align="center">

![Query](https://img.shields.io/badge/Query-2196F3?style=for-the-badge)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**Agentes especializados em consultas de identificação**

</div>

---

## 📋 Visão Geral

O módulo `ID/` contém agentes para **consultas de identificação** no banco MySQL.

## 📁 Estrutura

```
ID/
└── 📄 query_get_agent.py    # Agente de consultas
```

## 🔧 Funcionalidades

```python
class QueryGetAgent:
    """Agente para consultas de identificação."""
    
    async def query(
        self,
        query: str,
        params: dict = None
    ) -> List[dict]:
        """Executa consulta no banco ID."""
        pass
    
    async def get_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[dict]:
        """Obtém entidade por ID."""
        pass
```

## 🔗 Links Relacionados

- [🌐 ID Router](../../routers/ID_routers/README.md)
- [🔧 ID Service](../../services/ID_services/README.md)
- [💾 ID Database](../../storage/database/ID_database/README.md)

---

<div align="center">

**🔍 Consultas inteligentes de dados**

</div>
