# 🎯 Orchestrator - Orquestração entre Camadas

<div align="center">

![Orchestrator](https://img.shields.io/badge/Orchestrator-673AB7?style=for-the-badge)
![Workflow](https://img.shields.io/badge/Workflow-4CAF50?style=for-the-badge)

**Orquestração da transição entre camadas do sistema**

</div>

---

## 📋 Visão Geral

Componentes de **orquestração** entre as camadas do sistema.

## 📁 Estrutura

```
orchestrator/
├── 📄 orchestrator_c1_to_c2.py    # Transição C1 → C2
└── 📄 workflow_manager.py         # Gerenciador de workflow
```

## 🔧 Componentes

### `orchestrator_c1_to_c2.py`

```python
class OrchestratorC1ToC2:
    """Gerencia transição da Camada 1 para Camada 2."""
    
    async def transition(
        self,
        governance_doc: GovernanceDocument
    ) -> C2Input:
        """Prepara contexto para Camada 2."""
        pass
```

### `workflow_manager.py`

```python
class WorkflowManager:
    """Gerencia fluxo entre agentes de planejamento."""
    
    async def execute_planning(
        self,
        c2_input: C2Input
    ) -> PlanningResult:
        """Executa agentes em paralelo/sequencial."""
        pass
```

## 🔗 Links Relacionados

- [📐 Architecture](../README.md)
- [🏛️ Governance](../../governance/README.md)

---

<div align="center">

**🎯 Orquestração inteligente de camadas**

</div>
