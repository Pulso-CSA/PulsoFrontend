# 🔄 Pipeline Services - Serviços de Pipeline

<div align="center">

![Pipeline](https://img.shields.io/badge/Pipeline-673AB7?style=for-the-badge)
![Automation](https://img.shields.io/badge/Automation-4CAF50?style=for-the-badge)

**Serviços de pipeline automatizado de testes e correção**

</div>

---

## 📋 Visão Geral

O `pipeline_services/` implementa o **pipeline automatizado** de:

- 🧪 Testes automatizados
- 📊 Análise de retorno
- 🔧 Correção de erros
- 🔒 Verificação de segurança

## 📁 Estrutura

```
pipeline_services/
├── 📄 teste_automatizado_service.py    # Execução de testes
├── 📄 analise_retorno_service.py       # Análise dos resultados
├── 📄 correcao_erros_service.py        # Correção automática
├── 📄 seguranca_codigo_pos_service.py  # Segurança de código
└── 📄 seguranca_infra_pos_service.py   # Segurança de infra
```

## 🔄 Fluxo do Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE AUTOMATIZADO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │  Testes  │───▶│ Análise  │───▶│ Correção │───▶│Segurança │ │
│   │  Auto    │    │ Retorno  │    │  Erros   │    │   Pós    │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│        │               │               │               │        │
│        ▼               ▼               ▼               ▼        │
│   Executar         Identificar      Corrigir       Validar     │
│   pytest/jest     Falhas           Automático     Segurança   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Serviços

### `teste_automatizado_service.py`

```python
class TesteAutomatizadoService:
    """Executa testes automatizados no projeto."""
    
    async def run_tests(
        self,
        project_path: str,
        test_framework: str = "pytest"
    ) -> TestResult:
        """Executa suite de testes."""
        pass
```

### `analise_retorno_service.py`

```python
class AnaliseRetornoService:
    """Analisa resultados dos testes."""
    
    async def analyze(
        self,
        test_result: TestResult
    ) -> Analysis:
        """Analisa falhas e identifica causas."""
        pass
```

### `correcao_erros_service.py`

```python
class CorrecaoErrosService:
    """Corrige erros automaticamente."""
    
    async def correct(
        self,
        analysis: Analysis
    ) -> CorrectionResult:
        """Aplica correções automáticas."""
        pass
```

### `seguranca_codigo_pos_service.py`

```python
class SegurancaCodigoPosService:
    """Verifica segurança de código pós-correção."""
    
    async def verify(
        self,
        project_path: str
    ) -> SecurityReport:
        """Executa análise de segurança."""
        pass
```

## 🔗 Links Relacionados

- [🌐 Pipeline Router](../../routers/pipeline_router/README.md)
- [🧪 Test Runner](../test_runner_service/README.md)
- [🔧 Correct Services](./agents/correct_services/README.md)

---

<div align="center">

**🔄 Pipeline automatizado de qualidade**

</div>
