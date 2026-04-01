# 📚 Datasets - Dados de Treinamento e RAG

<div align="center">

![Data](https://img.shields.io/badge/Datasets-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-FF6F00?style=for-the-badge&logoColor=white)

**Base de conhecimento para treinamento do sistema RAG**

</div>

---

## 📋 Visão Geral

O diretório `datasets/` contém todos os **dados de treinamento** utilizados pelo sistema de **Retrieval-Augmented Generation (RAG)**. Estes dados alimentam os agentes de IA com conhecimento especializado em governança, arquitetura e segurança.

## 📁 Estrutura de Diretórios

```
datasets/
├── 📄 csv/                      # Dados estruturados em CSV
│   ├── compliance_risks.csv        # Riscos de compliance
│   ├── governance_metrics.csv      # Métricas de governança
│   └── strategic_alignment.csv     # Alinhamento estratégico
│
├── 📕 pdf/                      # Documentos PDF de referência
│   ├── architecture/               # Arquitetura e DevOps
│   │   ├── architecture/              # Frameworks técnicos
│   │   └── development/               # Livros de desenvolvimento
│   ├── governance/                 # Governança e compliance
│   └── Security/                   # Segurança da informação
│
└── 📝 training/                 # Dados de treinamento específicos
    ├── prompt_refino_examples.csv  # Exemplos de refinamento
    └── refinement_pairs.jsonl      # Pares de refinamento
```

## 📄 Dados CSV

### `compliance_risks.csv`

Catálogo de riscos de compliance e suas mitigações.

| Coluna | Descrição |
|--------|-----------|
| `risk_id` | Identificador único do risco |
| `category` | Categoria (LGPD, SOX, HIPAA, etc.) |
| `description` | Descrição do risco |
| `severity` | Severidade (low, medium, high, critical) |
| `mitigation` | Estratégia de mitigação |

### `governance_metrics.csv`

Métricas de governança de TI.

| Coluna | Descrição |
|--------|-----------|
| `metric_id` | Identificador da métrica |
| `domain` | Domínio (COBIT, ITIL, ISO) |
| `name` | Nome da métrica |
| `formula` | Fórmula de cálculo |
| `target` | Meta esperada |

### `strategic_alignment.csv`

Alinhamento estratégico de TI com negócios.

| Coluna | Descrição |
|--------|-----------|
| `objective_id` | Identificador do objetivo |
| `business_goal` | Meta de negócio |
| `it_capability` | Capacidade de TI necessária |
| `alignment_score` | Score de alinhamento |

## 📕 Documentos PDF

### `pdf/architecture/`

Documentos sobre arquitetura de software e infraestrutura.

#### `architecture/` - Frameworks Técnicos

- **NIST Cybersecurity Framework** - Framework de segurança cibernética
- **OWASP Top 10** - Principais vulnerabilidades web
- **Cloud Architecture Patterns** - Padrões de arquitetura cloud
- **Microservices Best Practices** - Boas práticas de microsserviços

#### `development/` - Desenvolvimento

- **Clean Code** - Princípios de código limpo
- **Design Patterns** - Padrões de projeto
- **Domain-Driven Design** - Design orientado a domínio
- **API Design Guidelines** - Diretrizes de design de APIs

### `pdf/governance/`

Documentos sobre governança de TI.

- **COBIT 2019** - Framework de governança
- **ISO 27001** - Gestão de segurança da informação
- **ISO 27002** - Controles de segurança
- **ITIL v4** - Gestão de serviços de TI

### `pdf/Security/`

Documentos sobre segurança da informação.

- **Ethical Hacking** - Hacking ético e pentest
- **Security Architecture** - Arquitetura de segurança
- **Incident Response** - Resposta a incidentes
- **Secure Coding** - Programação segura

## 📝 Dados de Treinamento

### `prompt_refino_examples.csv`

Exemplos de refinamento de prompts para treinamento.

| Coluna | Descrição |
|--------|-----------|
| `original_prompt` | Prompt original do usuário |
| `refined_prompt` | Prompt refinado |
| `context_used` | Contexto RAG utilizado |
| `quality_score` | Score de qualidade |

### `refinement_pairs.jsonl`

Pares de treinamento em formato JSON Lines.

```json
{"input": "fazer api", "output": "Criar API REST com autenticação JWT..."}
{"input": "banco dados", "output": "Implementar camada de persistência MongoDB..."}
```

## 🔧 Uso no Sistema RAG

### Carregamento de Documentos

```python
from app.utils.file_loader import load_pdf, load_csv

# Carregar PDFs para indexação
governance_docs = load_pdf("./datasets/pdf/governance/")
security_docs = load_pdf("./datasets/pdf/Security/")

# Carregar dados CSV
compliance_data = load_csv("./datasets/csv/compliance_risks.csv")
```

### Criação de Índice FAISS

```python
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Dividir documentos em chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(all_docs)

# Criar índice vetorial
vectorstore = FAISS.from_documents(
    chunks,
    embeddings=get_embeddings()
)

# Salvar índice
vectorstore.save_local("./storage/vectorstore/faiss_governance")
```

### Busca RAG

```python
# Buscar documentos relevantes
relevant_docs = vectorstore.similarity_search(
    query="Como implementar autenticação segura?",
    k=5
)

# Usar contexto na geração
context = "\n".join([doc.page_content for doc in relevant_docs])
```

## 📊 Estatísticas dos Dados

| Tipo | Quantidade | Tamanho |
|------|------------|---------|
| PDFs Governança | 8 | ~45 MB |
| PDFs Arquitetura | 12 | ~60 MB |
| PDFs Segurança | 6 | ~35 MB |
| CSVs | 3 | ~500 KB |
| Training Data | 2 | ~2 MB |

## 🔄 Atualização de Dados

Para adicionar novos documentos ao sistema RAG:

1. Adicione o arquivo na pasta apropriada
2. Execute o script de reindexação:

```bash
python -m app.core.openai.rag_trainer --reindex
```

## 🔗 Links Relacionados

- [📄 CSV Data](./csv/README.md)
- [📕 PDF Documents](./pdf/README.md)
- [📝 Training Data](./training/README.md)
- [⚙️ RAG Trainer](../core/openai/README.md)

---

<div align="center">

**📚 Conhecimento especializado para IA**

</div>
