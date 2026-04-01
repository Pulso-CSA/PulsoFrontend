# 🔄 Pipeline Router - Pipeline Automatizado

<div align="center">

![Pipeline](https://img.shields.io/badge/Pipeline-673AB7?style=for-the-badge)
![CI/CD](https://img.shields.io/badge/CI_CD-2196F3?style=for-the-badge)

**Endpoints do pipeline automatizado de testes e correção**

</div>

---

## 📋 Visão Geral

Endpoints para o **pipeline automatizado** de testes, análise e correção.

## 📁 Estrutura

```
pipeline_router/
└── 📄 pipeline_router.py    # Endpoints do pipeline
```

## 🌐 Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/pipeline/run` | Executar pipeline completo |
| `GET` | `/pipeline/status/{id}` | Status do pipeline |
| `POST` | `/pipeline/stop/{id}` | Parar pipeline |

## 🧪 Testes via cURL

> Base: `http://localhost:8000` | `id_requisicao` = ID da requisição

```bash
# 11 - Teste automatizado
curl -s -X POST http://localhost:8000/pipeline/teste-automatizado -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"root_path\":\"/caminho/projeto\",\"prefer_docker\":true}"

# 12 - Análise de retorno (relatorio_testes = saída do teste-automatizado)
curl -s -X POST http://localhost:8000/pipeline/analise-retorno -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"relatorio_testes\":{\"status\":\"reprovado\",\"erros\":[],\"vulnerabilidades\":[],\"logs\":[]}}"

# 13 - Correção de erros
curl -s -X POST http://localhost:8000/pipeline/correcao-erros -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"analise_retorno\":{\"objetivo_final\":\"não atingido\",\"falhas\":[],\"vulnerabilidades\":[],\"faltantes\":[]},\"root_path\":\"/caminho/projeto\",\"usuario\":\"pipeline\"}"

# 13.1 - Segurança código (pós-correção)
curl -s -X POST http://localhost:8000/pipeline/seguranca-codigo-pos -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"relatorio_correcao\":{\"erros_corrigidos\":[],\"funcionalidades_atualizadas\":[],\"estrutura_atualizada\":[],\"status\":\"corrigido\"}}"

# 13.2 - Segurança infra (pós-correção)
curl -s -X POST http://localhost:8000/pipeline/seguranca-infra-pos -H "Content-Type: application/json" -d "{\"id_requisicao\":\"REQ-20250101-120000-abcd\",\"relatorio_correcao\":{\"erros_corrigidos\":[],\"funcionalidades_atualizadas\":[],\"estrutura_atualizada\":[],\"status\":\"corrigido\"}}"
```

## 🔗 Links Relacionados

- [🔧 Pipeline Services](../../services/pipeline_services/README.md)
- [📊 Pipeline Models](../../models/pipeline_models/README.md)

---

<div align="center">

**🔄 Automação completa de qualidade**

</div>
