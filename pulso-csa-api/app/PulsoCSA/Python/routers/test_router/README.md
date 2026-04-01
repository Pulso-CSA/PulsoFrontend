# 🧪 Test Router - Testes Automatizados

<div align="center">

![Testing](https://img.shields.io/badge/Testing-4CAF50?style=for-the-badge&logo=pytest&logoColor=white)
![Automation](https://img.shields.io/badge/Automation-2196F3?style=for-the-badge)

**Endpoints para execução de testes automatizados**

</div>

---

## 📋 Visão Geral

Endpoints para executar e gerenciar **testes automatizados**.

## 📁 Estrutura

```
test_router/
└── 📄 test_router.py    # Endpoints de teste
```

## 🌐 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/test/run` | Executar testes |
| `GET` | `/test/results/{id}` | Obter resultados |
| `GET` | `/test/history/{project}` | Histórico de testes |

## 🧪 Testes via cURL

> Base: `http://localhost:8000`

```bash
# Executar teste automatizado (venv ou docker)
curl -s -X POST http://localhost:8000/test/run -H "Content-Type: application/json" -d "{\"project_path\":\"/caminho/projeto\",\"prefer_docker\":true}"
```

## 🔗 Links Relacionados

- [🔧 Test Runner Service](../../services/test_runner_service/README.md)
- [📊 Test Models](../../models/test_models/README.md)

---

<div align="center">

**🧪 Qualidade garantida com testes**

</div>
