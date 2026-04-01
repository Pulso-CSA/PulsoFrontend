# 🔧 Correct Workflow - Workflow de Correção

<div align="center">

![Correction](https://img.shields.io/badge/Code_Correction-E91E63?style=for-the-badge)
![Workflow](https://img.shields.io/badge/Automated-4CAF50?style=for-the-badge)

**Orquestração do pipeline de correção de código**

</div>

---

## 📋 Visão Geral

O `correct_workflow/` orquestra o **pipeline de correção de código**:

- 📋 Análise de erros e planejamento (C2b)
- ✍️ Geração de código corrigido (C3)
- ⚡ Aplicação das correções (C4)
- ✅ Validação e testes

## 📁 Estrutura

```
correct_workflow/
├── 📄 workflow_core_cor.py           # Core do workflow
├── 📄 structure_apply_service.py     # Aplicação de estrutura
└── 📄 workflow_structure_builder.py  # Construtor de estrutura
```

## 🔄 Fluxo do Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                   WORKFLOW DE CORREÇÃO                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│   │  Análise │───▶│   Plan   │───▶│  Write   │───▶│  Apply   │     │
│   │  Erros   │    │  (C2b)   │    │  (C3)    │    │  (C4)    │     │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│        │               │               │               │            │
│        ▼               ▼               ▼               ▼            │
│   Identificar     Estratégia      Código         Aplicar          │
│   Root Cause      Correção       Corrigido      Mudanças          │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                     VALIDAÇÃO                             │     │
│   │   ✓ Syntax Check  ✓ Lint  ✓ Tests  ✓ Type Check          │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔍 Componentes

### `workflow_core_cor.py`

Core principal do workflow de correção.

```python
class CorrectionWorkflow:
    """
    Orquestra o fluxo completo de correção de código.
    """
    
    async def execute(
        self,
        project_id: str,
        error_context: ErrorContext
    ) -> WorkflowResult:
        """
        Executa workflow de correção.
        
        Args:
            project_id: ID do projeto
            error_context: Contexto dos erros a corrigir
            
        Returns:
            Resultado do workflow com código corrigido
        """
        # 1. Analisar erros
        analysis = await self._analyze_errors(error_context)
        
        # 2. Criar plano de correção (C2b)
        plan = await self._create_plan(analysis)
        
        # 3. Gerar código corrigido (C3)
        corrected_code = await self._write_code(plan)
        
        # 4. Aplicar correções (C4)
        result = await self._apply_corrections(corrected_code)
        
        # 5. Validar
        await self._validate(result)
        
        return result
```

### `structure_apply_service.py`

Serviço para aplicar mudanças estruturais.

```python
class StructureApplyService:
    """
    Aplica mudanças estruturais no projeto.
    """
    
    async def apply_changes(
        self,
        project_path: str,
        changes: List[FileChange]
    ) -> ApplyResult:
        """
        Aplica lista de mudanças em arquivos.
        
        Args:
            project_path: Caminho do projeto
            changes: Lista de mudanças a aplicar
            
        Returns:
            Resultado da aplicação
        """
        pass
    
    async def create_backup(
        self,
        project_path: str
    ) -> str:
        """
        Cria backup antes de aplicar mudanças.
        """
        pass
    
    async def rollback(
        self,
        backup_path: str,
        project_path: str
    ) -> None:
        """
        Restaura backup em caso de falha.
        """
        pass
```

### `workflow_structure_builder.py`

Constrói estrutura para o workflow.

```python
class WorkflowStructureBuilder:
    """
    Constrói estrutura de contexto para o workflow.
    """
    
    def build_context(
        self,
        project_id: str,
        errors: List[Error]
    ) -> WorkflowContext:
        """
        Constrói contexto completo para execução.
        """
        pass
    
    def build_file_map(
        self,
        project_path: str
    ) -> Dict[str, FileInfo]:
        """
        Mapeia todos os arquivos do projeto.
        """
        pass
```

## 📊 Exemplo de Execução

```python
from app.workflow.correct_workflow.workflow_core_cor import CorrectionWorkflow

# Inicializar workflow
workflow = CorrectionWorkflow()

# Definir contexto de erro
error_context = ErrorContext(
    files=["main.py", "utils.py"],
    errors=[
        Error(
            type="TypeError",
            message="unsupported operand...",
            file="main.py",
            line=45
        )
    ]
)

# Executar workflow
result = await workflow.execute(
    project_id="proj_123",
    error_context=error_context
)

# Verificar resultado
print(f"Status: {result.status}")
print(f"Arquivos corrigidos: {result.files_modified}")
```

## 🔗 Links Relacionados

- [🌐 Workflow Router](../../routers/workflow/README.md)
- [🔧 Correct Services](../../services/agents/correct_services/README.md)
- [🤖 Agents](../../agents/README.md)

---

<div align="center">

**🔧 Correção automática e inteligente**

</div>
