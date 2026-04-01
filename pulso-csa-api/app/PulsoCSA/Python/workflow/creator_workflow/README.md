# 🏗️ Creator Workflow - Workflow de Criação

<div align="center">

![Creation](https://img.shields.io/badge/Project_Creation-2196F3?style=for-the-badge)
![Full Auto](https://img.shields.io/badge/Full_Auto-4CAF50?style=for-the-badge)

**Orquestração do pipeline de criação de projetos**

</div>

---

## 📋 Visão Geral

O `creator_workflow/` orquestra o **pipeline de criação de projetos**:

- 🏛️ Governança e refinamento (C1)
- 📐 Planejamento de arquitetura (C2)
- ⚡ Criação de estrutura e código (C3)
- 🚀 Deploy opcional

## 📁 Estrutura

```
creator_workflow/
├── 📄 workflow_core.py      # Core do workflow de criação
└── 📄 workflow_steps.py     # Definição das etapas
```

## 🔄 Fluxo do Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   WORKFLOW DE CRIAÇÃO (FULL-AUTO)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │   C1     │───▶│   C2     │───▶│   C3a    │───▶│   C3b    │     │
│   │Governance│    │  Arch    │    │ Structure│    │   Code   │     │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│        │               │               │               │            │
│        ▼               ▼               ▼               ▼            │
│    Doc Técnico    Plano Arq.    Diretórios      Código           │
│    Refinado       Completo      Criados        Funcional         │
│                                                                      │
│                     ┌──────────┐                                    │
│                     │  Deploy  │  (Opcional)                        │
│                     │   Auto   │                                    │
│                     └──────────┘                                    │
│                          │                                          │
│                          ▼                                          │
│                    Projeto Live                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔍 Componentes

### `workflow_core.py`

Core principal do workflow de criação.

```python
class CreatorWorkflow:
    """
    Orquestra o fluxo completo de criação de projetos.
    """
    
    def __init__(self):
        self.governance_agent = GovernanceAgent()
        self.architecture_agent = ArchitectureAgent()
        self.execution_agent = ExecutionAgent()
        self.deploy_service = DeployService()
    
    async def execute(
        self,
        prompt: str,
        config: ProjectConfig
    ) -> WorkflowResult:
        """
        Executa workflow completo de criação.
        
        Args:
            prompt: Descrição do projeto desejado
            config: Configurações do projeto
            
        Returns:
            Resultado com projeto criado
        """
        context = {"prompt": prompt, "config": config}
        
        # Camada 1: Governança
        context = await self._step_governance(context)
        
        # Camada 2: Arquitetura
        context = await self._step_architecture(context)
        
        # Camada 3a: Estrutura
        context = await self._step_structure(context)
        
        # Camada 3b: Código
        context = await self._step_code(context)
        
        # Deploy (opcional)
        if config.auto_deploy:
            context = await self._step_deploy(context)
        
        return WorkflowResult(**context)
    
    async def _step_governance(self, context: dict) -> dict:
        """Etapa de governança (C1)."""
        result = await self.governance_agent.process(context["prompt"])
        context["governance_doc"] = result
        return context
    
    async def _step_architecture(self, context: dict) -> dict:
        """Etapa de arquitetura (C2)."""
        result = await self.architecture_agent.plan(context["governance_doc"])
        context["architecture_plan"] = result
        return context
```

### `workflow_steps.py`

Definição das etapas do workflow.

```python
from enum import Enum
from dataclasses import dataclass

class WorkflowStep(Enum):
    """Etapas do workflow de criação."""
    GOVERNANCE = "governance"
    ARCHITECTURE = "architecture"
    STRUCTURE = "structure"
    CODE = "code"
    DEPLOY = "deploy"

@dataclass
class StepConfig:
    """Configuração de uma etapa."""
    name: WorkflowStep
    required: bool
    timeout_seconds: int
    retry_count: int

WORKFLOW_STEPS = [
    StepConfig(WorkflowStep.GOVERNANCE, required=True, timeout_seconds=60, retry_count=3),
    StepConfig(WorkflowStep.ARCHITECTURE, required=True, timeout_seconds=120, retry_count=3),
    StepConfig(WorkflowStep.STRUCTURE, required=True, timeout_seconds=30, retry_count=2),
    StepConfig(WorkflowStep.CODE, required=True, timeout_seconds=300, retry_count=2),
    StepConfig(WorkflowStep.DEPLOY, required=False, timeout_seconds=600, retry_count=1),
]
```

## 📊 Exemplo de Uso

```python
from app.workflow.creator_workflow.workflow_core import CreatorWorkflow

# Inicializar workflow
workflow = CreatorWorkflow()

# Configurar projeto
config = ProjectConfig(
    framework="fastapi",
    database="mongodb",
    auth="jwt",
    auto_deploy=True
)

# Executar workflow completo
result = await workflow.execute(
    prompt="Criar API REST para e-commerce com gestão de produtos e pedidos",
    config=config
)

# Acessar artefatos
print(f"Projeto criado: {result.project_path}")
print(f"Deploy URL: {result.deploy_url}")
```

## 🔗 Links Relacionados

- [🌐 Workflow Router](../../routers/workflow/README.md)
- [🤖 Agents](../../agents/README.md)
- [🔧 Services](../../services/README.md)

---

<div align="center">

**🏗️ Criação de projetos de ponta a ponta**

</div>
