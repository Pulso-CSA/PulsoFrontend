# 📐 Architecture - Agentes de Arquitetura (Camada 2)

<div align="center">

![Architecture](https://img.shields.io/badge/Camada_2-Arquitetura-9C27B0?style=for-the-badge)
![Planning](https://img.shields.io/badge/Planning-Enabled-FF9800?style=for-the-badge)

**Segunda camada de processamento - Planejamento técnico e arquitetural**

</div>

---

## 📋 Visão Geral

O módulo `architecture/` implementa a **Camada 2** do sistema, responsável por:

- ✅ Orquestrar a transição da Camada 1 para Camada 2
- ✅ Planejar arquitetura de backend
- ✅ Planejar infraestrutura
- ✅ Analisar segurança de código e infraestrutura
- ✅ Definir estrutura do projeto

## 📁 Estrutura de Diretórios

```
architecture/
├── 🎯 orchestrator/             # Orquestração entre camadas
│   ├── orchestrator_c1_to_c2.py    # Transição C1 → C2
│   └── workflow_manager.py         # Gerenciador de workflow
│
└── 📐 planning/                 # Agentes de planejamento
    ├── agent_backend.py            # Planejamento de backend
    ├── agent_infra.py              # Planejamento de infraestrutura
    ├── agent_sec_code.py           # Segurança de código
    ├── agent_sec_infra.py          # Segurança de infraestrutura
    └── agent_structure.py          # Estrutura do projeto
```

## 🔄 Fluxo de Processamento

```
                    ┌─────────────────────┐
                    │  Documento C1       │
                    │  (Governança)       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Orchestrator      │
                    │   C1 → C2           │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    Backend      │  │     Infra       │  │   Structure     │
│    Planning     │  │    Planning     │  │    Planning     │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                     │                     │
         │    ┌────────────────┴────────────────┐   │
         │    │                                  │   │
         ▼    ▼                                  ▼   ▼
┌─────────────────┐                    ┌─────────────────┐
│   Sec Code      │                    │   Sec Infra     │
│   Analysis      │                    │   Analysis      │
└─────────────────┘                    └─────────────────┘
```

## 🎯 Orchestrator

### `orchestrator_c1_to_c2.py`

Gerencia a transição entre Camada 1 e Camada 2.

```python
class OrchestratorC1ToC2:
    """
    Orquestra a transição do documento de Governança (C1)
    para o planejamento de Arquitetura (C2).
    """
    
    async def transition(self, governance_doc: GovernanceDocument) -> C2Input:
        # Extrair requisitos técnicos
        tech_requirements = self.extract_tech_requirements(governance_doc)
        
        # Preparar contexto para C2
        c2_context = self.prepare_c2_context(
            requirements=tech_requirements,
            compliance=governance_doc.compliance
        )
        
        return C2Input(context=c2_context)
```

### `workflow_manager.py`

Gerencia o fluxo de trabalho entre os agentes de planejamento.

```python
class WorkflowManager:
    """
    Gerencia a execução paralela/sequencial dos agentes de planejamento.
    """
    
    async def execute_planning(self, c2_input: C2Input) -> PlanningResult:
        # Executar agentes em paralelo
        results = await asyncio.gather(
            self.backend_agent.plan(c2_input),
            self.infra_agent.plan(c2_input),
            self.structure_agent.plan(c2_input)
        )
        
        # Executar análise de segurança
        security = await asyncio.gather(
            self.sec_code_agent.analyze(results),
            self.sec_infra_agent.analyze(results)
        )
        
        return PlanningResult(
            backend=results[0],
            infra=results[1],
            structure=results[2],
            security=security
        )
```

## 📐 Planning Agents

### `agent_backend.py` - Planejamento de Backend

```python
class BackendPlanningAgent:
    """
    Agente especializado em planejamento de arquitetura backend.
    """
    
    async def plan(self, context: C2Input) -> BackendPlan:
        return BackendPlan(
            framework=self.select_framework(context),
            database=self.select_database(context),
            api_design=self.design_api(context),
            authentication=self.plan_auth(context),
            patterns=self.select_patterns(context)
        )
```

**Responsabilidades:**
- 🔧 Seleção de framework (FastAPI, Django, Flask)
- 💾 Design de banco de dados
- 🌐 Design de API REST/GraphQL
- 🔐 Estratégia de autenticação
- 📐 Padrões de arquitetura (MVC, Clean Architecture)

### `agent_infra.py` - Planejamento de Infraestrutura

```python
class InfraPlanningAgent:
    """
    Agente especializado em planejamento de infraestrutura.
    """
    
    async def plan(self, context: C2Input) -> InfraPlan:
        return InfraPlan(
            containerization=self.plan_docker(context),
            orchestration=self.plan_orchestration(context),
            ci_cd=self.plan_pipeline(context),
            monitoring=self.plan_monitoring(context),
            scaling=self.plan_scaling(context)
        )
```

**Responsabilidades:**
- 🐳 Containerização (Docker)
- ☸️ Orquestração (Kubernetes, Docker Compose)
- 🔄 CI/CD (GitHub Actions, GitLab CI)
- 📊 Monitoramento (Prometheus, Grafana)
- 📈 Estratégia de escalabilidade

### `agent_structure.py` - Estrutura do Projeto

```python
class StructurePlanningAgent:
    """
    Agente especializado em definição de estrutura de projeto.
    """
    
    async def plan(self, context: C2Input) -> StructurePlan:
        return StructurePlan(
            directories=self.define_directories(context),
            files=self.define_files(context),
            modules=self.define_modules(context),
            dependencies=self.define_dependencies(context)
        )
```

**Responsabilidades:**
- 📂 Estrutura de diretórios
- 📄 Arquivos principais
- 📦 Organização de módulos
- 📋 Definição de dependências

### `agent_sec_code.py` - Segurança de Código

```python
class SecCodeAgent:
    """
    Agente de análise de segurança de código.
    """
    
    async def analyze(self, plans: List[Plan]) -> SecurityAnalysis:
        return SecurityAnalysis(
            vulnerabilities=self.identify_vulnerabilities(plans),
            owasp_compliance=self.check_owasp(plans),
            recommendations=self.generate_recommendations(plans)
        )
```

**Responsabilidades:**
- 🔍 Identificação de vulnerabilidades (OWASP Top 10)
- ✅ Verificação de boas práticas
- 🛡️ Recomendações de segurança

### `agent_sec_infra.py` - Segurança de Infraestrutura

```python
class SecInfraAgent:
    """
    Agente de análise de segurança de infraestrutura.
    """
    
    async def analyze(self, plans: List[Plan]) -> InfraSecurityAnalysis:
        return InfraSecurityAnalysis(
            network_security=self.analyze_network(plans),
            container_security=self.analyze_containers(plans),
            secrets_management=self.analyze_secrets(plans),
            compliance=self.check_compliance(plans)
        )
```

**Responsabilidades:**
- 🌐 Segurança de rede
- 🐳 Segurança de containers
- 🔐 Gestão de secrets
- ✅ Conformidade (NIST, CIS)

## 📊 Estrutura do Plano de Arquitetura

```json
{
  "id": "arch_456",
  "governance_doc_id": "gov_123",
  "backend": {
    "framework": "FastAPI",
    "database": "MongoDB",
    "api_style": "REST",
    "auth": "JWT + OAuth2"
  },
  "infrastructure": {
    "container": "Docker",
    "orchestration": "Docker Compose",
    "ci_cd": "GitHub Actions"
  },
  "structure": {
    "directories": [...],
    "files": [...],
    "modules": [...]
  },
  "security": {
    "code": {...},
    "infra": {...}
  }
}
```

## 🔗 Links Relacionados

- [🏛️ Governance (Camada 1)](../governance/README.md)
- [⚡ Execution (Camada 3)](../execution/README.md)
- [🎯 Orchestrator](./orchestrator/README.md)
- [📐 Planning](./planning/README.md)

---

<div align="center">

**📐 Arquitetura inteligente e segura**

</div>
