# 🔄 Workflow - Orquestração de Fluxos de Trabalho

<div align="center">

![Workflow](https://img.shields.io/badge/Workflow-673AB7?style=for-the-badge&logoColor=white)
![Automation](https://img.shields.io/badge/Automation-4CAF50?style=for-the-badge&logoColor=white)

**Sistema de orquestração de workflows automatizados**

</div>

---

## 📋 Visão Geral

O diretório `workflow/` contém a **lógica de orquestração** que coordena a execução de múltiplas etapas em sequência ou paralelo. Os workflows automatizam processos complexos que envolvem várias camadas do sistema.

## 📁 Estrutura de Diretórios

```
workflow/
├── 🔧 correct_workflow/         # Workflow de correção de código
│   ├── structure_apply_service.py    # Aplicação de estrutura
│   ├── workflow_core_cor.py          # Core do workflow de correção
│   └── workflow_structure_builder.py # Construtor de estrutura
│
├── 🏗️ creator_workflow/         # Workflow de criação de projetos
│   ├── workflow_core.py              # Core do workflow de criação
│   └── workflow_steps.py             # Etapas do workflow
│
└── 🎯 orquestrador_workflow.py  # Orquestrador principal
```

## 🔄 Tipos de Workflows

### 🔧 Workflow de Correção (`correct_workflow/`)

Automatiza o processo de correção de código em projetos existentes.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Análise   │───▶│ Planejamento│───▶│   Escrita   │───▶│Implementação│
│   (C2b)     │    │  de Código  │    │   (C3)      │    │    (C4)     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### Arquivos

| Arquivo | Responsabilidade |
|---------|------------------|
| `workflow_core_cor.py` | Orquestra todo o fluxo de correção |
| `structure_apply_service.py` | Aplica mudanças estruturais |
| `workflow_structure_builder.py` | Constrói estrutura de arquivos |

#### Exemplo de Uso

```python
from app.workflow.correct_workflow.workflow_core_cor import CorrectionWorkflow

workflow = CorrectionWorkflow()

# Iniciar workflow de correção
result = await workflow.execute(
    project_id="proj_123",
    error_context={
        "files": ["main.py", "utils.py"],
        "errors": ["TypeError", "ImportError"]
    }
)
```

### 🏗️ Workflow de Criação (`creator_workflow/`)

Automatiza o processo de criação de novos projetos do zero.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Governança  │───▶│ Arquitetura │───▶│  Estrutura  │───▶│   Código    │
│    (C1)     │    │    (C2)     │    │    (C3a)    │    │   (C3b)     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### Arquivos

| Arquivo | Responsabilidade |
|---------|------------------|
| `workflow_core.py` | Orquestra todo o fluxo de criação |
| `workflow_steps.py` | Define etapas individuais do workflow |

#### Exemplo de Uso

```python
from app.workflow.creator_workflow.workflow_core import CreatorWorkflow

workflow = CreatorWorkflow()

# Iniciar workflow de criação
result = await workflow.execute(
    prompt="Criar API REST para gestão de usuários",
    config={
        "framework": "fastapi",
        "database": "mongodb",
        "auth": "jwt"
    }
)
```

### 🎯 Orquestrador Principal

O arquivo `orquestrador_workflow.py` é o ponto central de coordenação.

```python
from app.workflow.orquestrador_workflow import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()

# Executar workflow completo
result = await orchestrator.run(
    workflow_type="full_auto",  # ou "correction", "creation"
    params={...}
)

# Verificar status
status = await orchestrator.get_status(workflow_id)
```

## 📊 Estados do Workflow

```python
class WorkflowStatus(Enum):
    PENDING = "pending"         # Aguardando início
    RUNNING = "running"         # Em execução
    PAUSED = "paused"           # Pausado
    COMPLETED = "completed"     # Concluído com sucesso
    FAILED = "failed"           # Falhou
    CANCELLED = "cancelled"     # Cancelado pelo usuário
```

## 🔧 Workflow de Correção Detalhado

### Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW DE CORREÇÃO                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1️⃣ ANÁLISE DE ERROS                                                │
│     ├── Identificar arquivos afetados                               │
│     ├── Classificar tipos de erros                                  │
│     └── Priorizar correções                                         │
│                                                                      │
│  2️⃣ PLANEJAMENTO (C2b)                                              │
│     ├── Analisar contexto do erro                                   │
│     ├── Gerar plano de correção                                     │
│     └── Validar dependências                                        │
│                                                                      │
│  3️⃣ ESCRITA DE CÓDIGO (C3)                                          │
│     ├── Gerar código corrigido                                      │
│     ├── Aplicar boas práticas                                       │
│     └── Validar sintaxe                                             │
│                                                                      │
│  4️⃣ IMPLEMENTAÇÃO (C4)                                              │
│     ├── Aplicar mudanças nos arquivos                               │
│     ├── Executar testes                                             │
│     └── Validar correção                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### `workflow_core_cor.py`

```python
class CorrectionWorkflow:
    async def execute(self, project_id: str, error_context: dict) -> WorkflowResult:
        """
        Executa o workflow completo de correção.
        """
        # Etapa 1: Análise
        analysis = await self.analyze_errors(error_context)
        
        # Etapa 2: Planejamento
        plan = await self.create_correction_plan(analysis)
        
        # Etapa 3: Escrita
        code = await self.write_corrected_code(plan)
        
        # Etapa 4: Implementação
        result = await self.implement_changes(code)
        
        return result
```

## 🏗️ Workflow de Criação Detalhado

### `workflow_steps.py`

```python
class WorkflowSteps:
    GOVERNANCE = "governance"      # C1: Análise de governança
    ARCHITECTURE = "architecture"  # C2: Planejamento de arquitetura
    STRUCTURE = "structure"        # C3a: Criação de estrutura
    CODE = "code"                  # C3b: Geração de código
    DEPLOY = "deploy"              # Opcional: Deploy automatizado
```

### `workflow_core.py`

```python
class CreatorWorkflow:
    async def execute(self, prompt: str, config: dict) -> WorkflowResult:
        """
        Executa o workflow completo de criação.
        """
        steps = [
            self.step_governance,
            self.step_architecture,
            self.step_structure,
            self.step_code
        ]
        
        context = {"prompt": prompt, "config": config}
        
        for step in steps:
            context = await step(context)
            if context.get("error"):
                return WorkflowResult(status="failed", error=context["error"])
        
        return WorkflowResult(status="completed", data=context)
```

## 🔗 Links Relacionados

- [🔧 Correct Workflow](./correct_workflow/README.md)
- [🏗️ Creator Workflow](./creator_workflow/README.md)
- [🤖 Agents](../agents/README.md)
- [🔧 Services](../services/README.md)

---

<div align="center">

**🔄 Automação inteligente do PulsoAPI**

</div>
