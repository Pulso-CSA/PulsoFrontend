# 🧪 Test Runner Service - Execução de Testes

<div align="center">

![Testing](https://img.shields.io/badge/Testing-4CAF50?style=for-the-badge&logo=pytest&logoColor=white)
![Service](https://img.shields.io/badge/Service-2196F3?style=for-the-badge)

**Lógica de negócio para execução de testes automatizados**

</div>

---

## 📋 Visão Geral

Serviço para executar **testes automatizados** em projetos.

## 📁 Estrutura

```
test_runner_service/
└── 📄 test_runner_service.py    # Serviço principal
```

## 🔧 Métodos

```python
class TestRunnerService:
    """Executa testes automatizados."""
    
    async def run_tests(
        self,
        project_path: str,
        framework: str = "pytest"
    ) -> TestResult:
        """Executa suite de testes."""
        pass
    
    async def get_coverage(
        self,
        project_path: str
    ) -> CoverageReport:
        """Obtém relatório de cobertura."""
        pass
    
    async def run_specific_test(
        self,
        project_path: str,
        test_path: str
    ) -> TestResult:
        """Executa teste específico."""
        pass
```

## 🔗 Links Relacionados

- [🌐 Test Router](../../routers/test_router/README.md)
- [🔄 Pipeline Services](../pipeline_services/README.md)

---

<div align="center">

**🧪 Testes automatizados confiáveis**

</div>
