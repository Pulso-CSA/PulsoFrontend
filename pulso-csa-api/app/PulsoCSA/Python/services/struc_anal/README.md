# 📐 Struc Anal Services - Análise Estrutural

<div align="center">

![Analysis](https://img.shields.io/badge/Structural-FF5722?style=for-the-badge)
![Service](https://img.shields.io/badge/Service-4CAF50?style=for-the-badge)

**Lógica de negócio para análise estrutural de projetos**

</div>

---

## 📋 Visão Geral

Serviços de **análise estrutural** de projetos existentes.

## 📁 Estrutura

```
struc_anal/
├── 📄 structure_scanner_service.py  # Scanner de estrutura
└── 📄 change_plan_service.py        # Planejamento de mudanças
```

## 🔧 Serviços

### `structure_scanner_service.py`

```python
class StructureScannerService:
    """Escaneia estrutura de projetos."""
    
    async def scan(
        self,
        project_path: str
    ) -> StructureMap:
        """Mapeia estrutura completa."""
        pass
```

### `change_plan_service.py`

```python
class ChangePlanService:
    """Planeja mudanças estruturais."""
    
    async def plan_changes(
        self,
        current: StructureMap,
        target: StructureSpec
    ) -> ChangePlan:
        """Gera plano de mudanças."""
        pass
```

## 🔗 Links Relacionados

- [🌐 Struc Anal Router](../../routers/struc_anal/README.md)
- [📊 Struc Anal Models](../../models/struc_anal/README.md)

---

<div align="center">

**📐 Análise e planejamento estrutural**

</div>
