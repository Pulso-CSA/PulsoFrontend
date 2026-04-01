# 🏛️ Governance - Agentes de Governança (Camada 1)

<div align="center">

![Governance](https://img.shields.io/badge/Camada_1-Governança-2196F3?style=for-the-badge)
![RAG](https://img.shields.io/badge/RAG-Enabled-4CAF50?style=for-the-badge)

**Primeira camada de processamento - Refinamento e validação de requisitos**

</div>

---

## 📋 Visão Geral

O módulo `governance/` implementa a **Camada 1** do sistema, responsável por:

- ✅ Receber e sanitizar prompts do usuário
- ✅ Refinar requisitos usando RAG (Retrieval-Augmented Generation)
- ✅ Validar conformidade com padrões de governança
- ✅ Gerar documentos técnicos estruturados

## 📁 Estrutura de Arquivos

```
governance/
├── 🎯 agent_governance.py   # Orquestrador principal da Camada 1
├── 📥 agent_input.py        # Agente de recepção de prompts
├── 🔄 agent_refine.py       # Agente de refinamento com RAG
└── ✅ agent_validate.py     # Agente de validação e documentação
```

## 🔄 Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAMADA 1: GOVERNANÇA                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │  Input   │───▶│  Refine  │───▶│ Validate │───▶│   Doc    │ │
│   │  Agent   │    │  Agent   │    │  Agent   │    │ Técnico  │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│        │               │               │               │        │
│        ▼               ▼               ▼               ▼        │
│   Sanitização      RAG/FAISS      Conformidade     Estrutura   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Agentes Detalhados

### 🎯 `agent_governance.py` - Orquestrador

Coordena todo o fluxo da Camada 1.

```python
class GovernanceAgent:
    """
    Orquestrador principal da Camada de Governança.
    Coordena Input -> Refine -> Validate.
    """
    
    async def process(self, request: GovernanceRequest) -> GovernanceResponse:
        # 1. Receber e validar input
        input_result = await self.input_agent.process(request.prompt)
        
        # 2. Refinar com RAG
        refined = await self.refine_agent.refine(input_result)
        
        # 3. Validar e gerar documento
        document = await self.validate_agent.validate(refined)
        
        return GovernanceResponse(document=document)
```

### 📥 `agent_input.py` - Recepção de Prompts

Responsável pela primeira etapa de processamento.

```python
class InputAgent:
    """
    Agente de recepção e sanitização de prompts.
    """
    
    async def process(self, prompt: str) -> ProcessedInput:
        # Sanitizar entrada
        sanitized = self.sanitize(prompt)
        
        # Extrair intenções
        intentions = await self.extract_intentions(sanitized)
        
        # Identificar domínio
        domain = self.identify_domain(intentions)
        
        return ProcessedInput(
            original=prompt,
            sanitized=sanitized,
            intentions=intentions,
            domain=domain
        )
```

**Funcionalidades:**
- 🧹 Sanitização de input (remoção de caracteres especiais)
- 🎯 Extração de intenções do usuário
- 🏷️ Identificação do domínio de negócio
- ✅ Validação de formato básico

### 🔄 `agent_refine.py` - Refinamento com RAG

Enriquece o prompt com conhecimento da base de dados.

```python
class RefineAgent:
    """
    Agente de refinamento usando RAG (Retrieval-Augmented Generation).
    """
    
    def __init__(self):
        self.vectorstore = self.load_vectorstore()
        self.llm = self.get_llm()
    
    async def refine(self, input: ProcessedInput) -> RefinedPrompt:
        # Buscar documentos relevantes
        relevant_docs = self.vectorstore.similarity_search(
            input.sanitized,
            k=5
        )
        
        # Construir contexto
        context = self.build_context(relevant_docs)
        
        # Gerar prompt refinado
        refined = await self.llm.generate(
            prompt=input.sanitized,
            context=context
        )
        
        return RefinedPrompt(
            original=input.original,
            refined=refined,
            context_used=relevant_docs
        )
```

**Funcionalidades:**
- 🔍 Busca vetorial no FAISS
- 📚 Recuperação de documentos relevantes
- 🧠 Enriquecimento com contexto
- ✨ Geração de prompt refinado

### ✅ `agent_validate.py` - Validação e Documentação

Valida conformidade e gera documento técnico.

```python
class ValidateAgent:
    """
    Agente de validação de conformidade e geração de documento técnico.
    """
    
    async def validate(self, refined: RefinedPrompt) -> TechnicalDocument:
        # Verificar conformidade com padrões
        compliance = await self.check_compliance(refined)
        
        # Gerar recomendações
        recommendations = self.generate_recommendations(compliance)
        
        # Criar documento técnico
        document = self.create_technical_document(
            prompt=refined,
            compliance=compliance,
            recommendations=recommendations
        )
        
        return document
```

**Funcionalidades:**
- ✅ Verificação de conformidade (COBIT, ISO, NIST)
- 📊 Score de qualidade do requisito
- 💡 Geração de recomendações
- 📄 Criação de documento técnico estruturado

## 📊 Estrutura do Documento Técnico

```json
{
  "id": "gov_123",
  "version": "1.0",
  "created_at": "2024-01-15T10:30:00Z",
  "input": {
    "original_prompt": "...",
    "sanitized_prompt": "...",
    "domain": "backend"
  },
  "refinement": {
    "refined_prompt": "...",
    "context_sources": ["COBIT_2019.pdf", "ISO_27001.pdf"],
    "confidence_score": 0.92
  },
  "compliance": {
    "frameworks_checked": ["COBIT", "ISO 27001", "NIST"],
    "compliance_score": 0.88,
    "gaps": []
  },
  "recommendations": [
    "Adicionar autenticação multi-fator",
    "Implementar logging de auditoria"
  ],
  "status": "approved"
}
```

## 🔗 Links Relacionados

- [📐 Architecture (Camada 2)](../architecture/README.md)
- [⚡ Execution (Camada 3)](../execution/README.md)
- [📚 Datasets RAG](../../datasets/README.md)
- [⚙️ Core OpenAI](../../core/openai/README.md)

---

<div align="center">

**🏛️ Governança inteligente para requisitos de qualidade**

</div>
