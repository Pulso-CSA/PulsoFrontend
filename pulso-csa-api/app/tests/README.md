# 🧪 Tests - Testes Automatizados

<div align="center">

![Testing](https://img.shields.io/badge/Testing-4CAF50?style=for-the-badge&logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-2196F3?style=for-the-badge)

**Testes automatizados da aplicação**

</div>

---

## 📋 Visão Geral

Diretório de **testes automatizados** da aplicação PulsoAPI.

## 📁 Estrutura

```
tests/
└── 📂 testes de regressão funcional local/
    └── run_all_tests.bat    # Script para executar testes
```

## 🔧 Execução

```bash
# Windows
cd tests
run_all_tests.bat

# Linux/Mac
pytest tests/ -v --cov=app
```

## 📝 Categorias de Testes

| Categoria | Descrição |
|-----------|-----------|
| **Unit** | Testes unitários de funções |
| **Integration** | Testes de integração |
| **E2E** | Testes end-to-end |
| **Regression** | Testes de regressão |

## 🔗 Links Relacionados

- [🧪 Test Runner Service](../services/test_runner_service/README.md)
- [🔄 Pipeline Services](../services/pipeline_services/README.md)

---

<div align="center">

**🧪 Qualidade garantida com testes**

</div>
