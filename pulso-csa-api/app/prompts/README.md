# 📝 Prompts - Templates de Prompts para Agentes

<div align="center">

![AI](https://img.shields.io/badge/Prompts-412991?style=for-the-badge&logo=openai&logoColor=white)
![Templates](https://img.shields.io/badge/Templates-FF9800?style=for-the-badge&logoColor=white)

**Templates estruturados para comunicação com modelos de linguagem**

</div>

---

## 📋 Visão Geral

O diretório `prompts/` contém os **templates de prompts** utilizados pelos agentes de IA. Estes templates definem como os modelos de linguagem devem processar e responder às requisições.

## 📁 Estrutura de Diretórios

```
prompts/
├── 📊 analyse/                  # Prompts de análise
│   ├── base_refine.txt             # Prompt base para refinamento
│   └── structure_blueprint.txt     # Blueprint de estrutura
│
├── 🔧 correct/                  # Prompts de correção
│   └── (prompts de correção de código)
│
├── 🏗️ creation/                 # Prompts de criação
│   ├── code_creation.txt           # Criação de código geral
│   ├── code_creation_compose.txt   # Criação de docker-compose
│   ├── code_creation_docker.txt    # Criação de Dockerfile
│   └── code_creation_env.txt       # Criação de variáveis de ambiente
│
└── 🔍 ID_prompts/               # Prompts de consulta ID (.txt)
    ├── query_get_system_rules.txt
    ├── query_get_schema_context.txt
    ├── query_get_user_request.txt
    └── query_get_few_shot_examples.txt
    # Builder: app.utils.query_get_prompt.QueryGetPromptBuilder
```

## 📊 Prompts de Análise (`analyse/`)

### `base_refine.txt`

Template base para refinamento de prompts com RAG.

```
Você é um especialista em refinamento de requisitos de software.

CONTEXTO DO SISTEMA:
{system_context}

CONHECIMENTO RAG:
{rag_context}

PROMPT ORIGINAL DO USUÁRIO:
{user_prompt}

SUA TAREFA:
1. Analisar o prompt original
2. Identificar requisitos implícitos
3. Adicionar detalhes técnicos relevantes
4. Estruturar o prompt de forma clara

FORMATO DE SAÍDA:
{output_format}
```

### `structure_blueprint.txt`

Template para geração de blueprints de estrutura.

```
Gere um blueprint de estrutura de projeto baseado em:

REQUISITOS:
{requirements}

TECNOLOGIAS:
{technologies}

PADRÕES DE ARQUITETURA:
{architecture_patterns}

SAÍDA ESPERADA:
- Estrutura de diretórios
- Arquivos principais
- Dependências sugeridas
```

## 🏗️ Prompts de Criação (`creation/`)

### `code_creation.txt`

Template principal para criação de código.

```
Você é um desenvolvedor sênior especializado em {technology}.

CONTEXTO DO PROJETO:
{project_context}

REQUISITOS TÉCNICOS:
{technical_requirements}

PADRÕES A SEGUIR:
- Clean Code
- SOLID Principles
- Design Patterns apropriados

CÓDIGO A GERAR:
{code_specification}

REGRAS:
1. Código deve ser production-ready
2. Incluir tratamento de erros
3. Adicionar docstrings/comentários
4. Seguir convenções da linguagem
```

### `code_creation_docker.txt`

Template para criação de Dockerfiles.

```
Crie um Dockerfile otimizado para:

APLICAÇÃO: {app_type}
LINGUAGEM: {language}
DEPENDÊNCIAS: {dependencies}

REQUISITOS:
- Multi-stage build quando apropriado
- Imagem base mínima
- Layer caching otimizado
- Security best practices
- Health check configurado
```

### `code_creation_compose.txt`

Template para docker-compose.

```
Crie um docker-compose.yml para:

SERVIÇOS:
{services}

REDES:
{networks}

VOLUMES:
{volumes}

VARIÁVEIS DE AMBIENTE:
{env_vars}

REQUISITOS:
- Configuração de restart
- Healthchecks
- Dependências entre serviços
- Configuração de rede
```

### `code_creation_env.txt`

Template para variáveis de ambiente.

```
Gere um arquivo .env.example com:

CATEGORIAS:
- Configuração da aplicação
- Banco de dados
- Serviços externos
- Segurança

FORMATO:
# Categoria
VARIAVEL=valor_exemplo  # Descrição

REQUISITOS:
- Valores de exemplo seguros
- Comentários explicativos
- Organização lógica
```

## 🔍 Prompts de Consulta ID (`ID_prompts/`)

Arquivos `.txt` consumidos pelo **QueryGetPromptBuilder** em `app.utils.query_get_prompt`. Prompts dinâmicos para consultas ao banco ID.

```python
class QueryPrompts:
    @staticmethod
    def get_entity_prompt(entity_type: str) -> str:
        return f"""
        Analise a consulta e extraia informações sobre {entity_type}.
        
        CONSULTA: {{query}}
        
        EXTRAIA:
        - Identificadores
        - Relacionamentos
        - Atributos relevantes
        
        FORMATO: JSON estruturado
        """
    
    @staticmethod
    def get_relationship_prompt() -> str:
        return """
        Identifique relacionamentos entre entidades na consulta.
        
        CONSULTA: {query}
        
        RELACIONAMENTOS A BUSCAR:
        - Hierárquicos
        - Associativos
        - Dependências
        """
```

## 🔧 Boas Práticas para Prompts

### Estrutura Recomendada

```
1. CONTEXTO - Defina o papel do modelo
2. ENTRADA - Especifique os dados de entrada
3. TAREFA - Descreva claramente o que deve ser feito
4. FORMATO - Defina o formato de saída esperado
5. REGRAS - Liste restrições e diretrizes
```

### Variáveis de Template

Use placeholders claros:

```
{variable_name}     # Variável simples
{list:items}        # Lista de itens
{optional:field}    # Campo opcional
{{escaped}}         # Chaves literais
```

### Exemplo de Prompt Bem Estruturado

```
# PAPEL
Você é um arquiteto de software especializado em {domain}.

# CONTEXTO
Projeto: {project_name}
Tecnologias: {technologies}
Requisitos: {requirements}

# TAREFA
{task_description}

# FORMATO DE SAÍDA
```json
{
  "architecture": {...},
  "components": [...],
  "recommendations": [...]
}
```

# REGRAS
1. {rule_1}
2. {rule_2}
3. {rule_3}
```

## 📊 Uso no Código

```python
from pathlib import Path

def load_prompt(prompt_name: str, **kwargs) -> str:
    """Carrega e formata um template de prompt."""
    prompt_path = Path(__file__).parent / f"{prompt_name}.txt"
    template = prompt_path.read_text(encoding="utf-8")
    return template.format(**kwargs)

# Uso
prompt = load_prompt(
    "creation/code_creation",
    technology="Python/FastAPI",
    project_context="API REST",
    technical_requirements="Autenticação JWT",
    code_specification="Endpoint de login"
)
```

## 🔗 Links Relacionados

- [📊 Analyse Prompts](./analyse/README.md)
- [🏗️ Creation Prompts](./creation/README.md)
- [🤖 Agents](../agents/README.md)
- [⚙️ OpenAI Core](../core/openai/README.md)

---

<div align="center">

**📝 Comunicação estruturada com IA**

</div>
