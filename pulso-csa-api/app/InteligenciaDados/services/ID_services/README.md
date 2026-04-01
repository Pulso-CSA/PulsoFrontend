# 🔍 ID Services - Serviços de Consulta

<div align="center">

![Query](https://img.shields.io/badge/Query-2196F3?style=for-the-badge)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

**Lógica de negócio para consultas de identificação**

</div>

---

## 📋 Visão Geral

Serviços para **consultas ao banco MySQL** de identificação.

## 📁 Estrutura

```
ID_services/
└── 📄 query_get_service.py    # Serviço de consultas
```

## 🔧 Métodos

```python
class QueryGetService:
    """Serviço de consultas ID."""
    
    async def execute_query(
        self,
        query: str,
        params: dict = None
    ) -> List[dict]:
        """Executa consulta SQL."""
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
- [💾 ID Database](../../storage/database/ID_database/README.md)

---

<div align="center">

**🔍 Consultas eficientes de dados**

</div>
