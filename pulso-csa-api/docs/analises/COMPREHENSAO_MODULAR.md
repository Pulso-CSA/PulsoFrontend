# Sistema de Compreensão Modular – PulsoAPI

**Data:** 12 de fevereiro de 2025  
**Módulos:** código, infraestrutura, inteligencia-dados

---

## 1. Visão Geral

O sistema de compreensão foi refatorado em **três módulos** independentes, cada um com classificação de intenção e roteamento específicos:

| Módulo | Descrição | Targets principais |
|--------|------------|---------------------|
| **codigo** | Desenvolvimento (criar projeto, corrigir, implementar) | `/governance/run`, `/workflow/correct/run` |
| **infraestrutura** | Terraform, AWS, Azure, GCP, deploy | `/infra/analyze`, `/infra/generate`, `/infra/validate`, `/infra/deploy` |
| **inteligencia-dados** | Dados, ML, consultas, previsão | `/inteligencia-dados/chat`, `/inteligencia-dados/query`, etc. |

---

## 2. Melhorias Aplicadas

### 2.1 Base compartilhada
- **force_execute**: parâmetro opcional para executar sem confirmação (ex.: botão "Executar")
- **Confirmação expandida**: aceita "sim", "ok", "pode ser", "vai", "bora", emojis (👍, ✅)
- **Cache isolado por usuário** em todos os módulos
- **Histórico de conversa**: parâmetro `history` para contexto (preparado para uso futuro)

### 2.2 Módulo Código
- Mantém intents ANALISAR e EXECUTAR
- Cache de análise de projetos **isolado por usuário**
- Usa `comprehension_base.detect_execute_signal` (sinais expandidos)

### 2.3 Módulo Infraestrutura
- **Intents**: ANALISAR_INFRA, GERAR_TERRAFORM, VALIDAR_INFRA, DEPLOY_INFRA
- **Targets**: `/infra/analyze`, `/infra/generate`, `/infra/validate`, `/infra/deploy`
- Classificação por regex + LLM fallback
- Palavras-chave: terraform, aws, azure, gcp, deploy, provisionar

### 2.4 Módulo Inteligência de Dados
- **Intents**: CHAT_ID, QUERY, CAPTURA, ESTATISTICA, CRIAR_MODELO, PREVER
- **Target principal**: `/inteligencia-dados/chat` (orquestrador)
- Sub-intents para sugerir endpoint ao frontend
- Palavras-chave: dados, banco, sql, modelo ml, treinar, previsão, churn

---

## 3. Fluxo de Roteamento

```
POST /comprehension/run
    ↓
detect_module(prompt, usuario, force_module)
    ↓
route_to_module → route_decision_codigo | route_decision_infra | route_decision_id
    ↓
Retorna: module, intent, target_endpoint, should_execute, explanation, next_action
```

---

## 4. Request Estendido

```json
{
  "usuario": "user@email.com",
  "prompt": "gerar terraform para AWS",
  "root_path": null,
  "force_execute": false,
  "force_module": "infraestrutura",
  "history": [],
  "id_requisicao": null
}
```

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| usuario | Sim | Identificação do usuário |
| prompt | Sim | Mensagem do usuário |
| root_path | Não | Caminho do projeto (obrigatório para correção) |
| force_execute | Não | Se true, executa sem confirmação |
| force_module | Não | Força módulo: codigo, infraestrutura, inteligencia-dados |
| history | Não | Histórico [{role, content}] para contexto |
| id_requisicao | Não | Para módulo ID |

---

## 5. Response com Módulo

```json
{
  "intent": "ANALISAR_INFRA",
  "project_state": "ROOT_COM_CONTEUDO",
  "should_execute": false,
  "target_endpoint": "/infra/analyze",
  "explanation": "Módulo: infraestrutura. Intenção: ANALISAR_INFRA...",
  "next_action": "Confirme com 'faça' ou 'executar' para prosseguir.",
  "message": "Módulo Infraestrutura detectado...",
  "module": "infraestrutura",
  "intent_confidence": 0.9,
  "intent_warning": null,
  "processing_time_ms": 150
}
```

---

## 6. Arquivos Criados/Modificados

| Arquivo | Tipo |
|---------|------|
| `comprehension_base.py` | Novo – cache, confirmação, force_execute |
| `comprehension_orchestrator.py` | Novo – detecção de módulo, roteamento |
| `comprehension_codigo.py` | Novo – módulo código |
| `comprehension_infra.py` | Novo – módulo infraestrutura |
| `comprehension_id.py` | Novo – módulo inteligência de dados |
| `comprehension_service.py` | Modificado – route_decision delega, cache com usuario |
| `comprehension_router.py` | Modificado – usa orquestrador, suporta módulos |
| `comprehension_models.py` | Modificado – force_execute, force_module, history, module |

---

## 7. Exemplos de Uso

### Código (criar projeto)
```
Prompt: "crie uma API REST com Flask"
→ module: codigo, intent: EXECUTAR, target: /governance/run
```

### Infraestrutura (analisar)
```
Prompt: "analise a infra do projeto"
→ module: infraestrutura, intent: ANALISAR_INFRA, target: /infra/analyze
```

### Inteligência de Dados (estatística)
```
Prompt: "qual a correlação entre vendas e marketing"
→ module: inteligencia-dados, intent: ESTATISTICA, target: /inteligencia-dados/analise-estatistica
```

---

*Documento gerado em 12/02/2025.*
