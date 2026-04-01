# 🤖 Agents Services - Serviços dos Agentes de IA

<div align="center">

![AI](https://img.shields.io/badge/AI_Services-412991?style=for-the-badge&logo=openai&logoColor=white)
![Services](https://img.shields.io/badge/Business_Logic-4CAF50?style=for-the-badge)

**Camada de serviços para os agentes de inteligência artificial**

</div>

---

## 📋 Visão Geral

O diretório `agents/` contém os **serviços de negócio** que orquestram os agentes de IA:

- 📊 Serviços de análise (governança, backend, infra)
- 🔧 Serviços de correção (plan, write, implement)
- 🏗️ Serviços de criação (code, structure)

## 📁 Estrutura

```
agents/
├── 📂 analise_services/         # Serviços de análise
│   ├── governance_service.py       # Análise de governança
│   ├── backend_service.py          # Análise de backend
│   ├── infra_service.py            # Análise de infra
│   ├── input_service.py            # Processamento de input
│   ├── refine_service.py           # Refinamento RAG
│   ├── validate_service.py         # Validação
│   ├── sec_code_service.py         # Segurança de código
│   ├── sec_infra_service.py        # Segurança de infra
│   └── structure_service.py        # Análise de estrutura
│
├── 📂 correct_services/         # Serviços de correção
│   ├── code_implementer_services/  # C4 - Implementação
│   ├── code_plan_services/         # C2b - Planejamento
│   └── code_writer_services/       # C3 - Escrita
│
└── 📂 creator_services/         # Serviços de criação
    ├── code_creator_service.py     # Criação de código
    └── structure_creator_service.py # Criação de estrutura
```

## 🔄 Relação Agentes × Serviços

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARQUITETURA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐       │
│   │  Router  │────────▶│ Service  │────────▶│  Agent   │       │
│   │(Endpoint)│         │ (Lógica) │         │   (IA)   │       │
│   └──────────┘         └──────────┘         └──────────┘       │
│        │                    │                    │              │
│        ▼                    ▼                    ▼              │
│   Validação            Orquestração         Processamento      │
│   de Input             de Fluxo             com OpenAI         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Serviços de Análise

| Serviço | Agente | Função |
|---------|--------|--------|
| `governance_service` | `governance/` | Orquestra análise C1 |
| `backend_service` | `architecture/planning/` | Planeja backend |
| `infra_service` | `architecture/planning/` | Planeja infra |
| `sec_code_service` | `architecture/planning/` | Segurança de código |
| `sec_infra_service` | `architecture/planning/` | Segurança de infra |

## 🔧 Serviços de Correção

| Serviço | Fase | Função |
|---------|------|--------|
| `code_plan_services/` | C2b | Planejamento de correção |
| `code_writer_services/` | C3 | Escrita de código |
| `code_implementer_services/` | C4 | Aplicação de correções |

## 🏗️ Serviços de Criação

| Serviço | Função |
|---------|--------|
| `code_creator_service` | Gera código-fonte |
| `structure_creator_service` | Cria estrutura de projeto |

## 🔗 Links Relacionados

- [🤖 Agents](../../agents/README.md)
- [🌐 Routers](../../routers/README.md)
- [📊 Models](../../models/README.md)

---

<div align="center">

**🤖 Lógica de negócio para IA**

</div>
