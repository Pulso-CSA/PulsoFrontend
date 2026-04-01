# Objetivo Final – PulsoCSA Python

## Visão Geral

O **PulsoCSA Python** é o serviço de **compreensão e geração de código** voltado para projetos em **Python** (FastAPI, Flask, Django, Streamlit, CLI, bibliotecas). Seu objetivo final é permitir que o desenvolvedor descreva em linguagem natural o que deseja criar ou corrigir, e o sistema entregue código funcional, estruturado e seguro.

---

## Objetivo Final

**Transformar descrições em linguagem natural em projetos Python completos e funcionais**, cobrindo desde a criação do zero até a correção e evolução de código existente, com foco em boas práticas, segurança e arquitetura modular.

---

## Capacidades Principais

### 1. Criação de Projetos (Governance / Creator Workflow)

- **Refino de prompt**: Interpreta e clarifica a intenção do usuário.
- **Análise de arquitetura**: Gera blueprint de estrutura (pastas, arquivos), documento de backend, infraestrutura e relatórios de segurança.
- **Criação de estrutura**: Cria diretórios e arquivos conforme o plano.
- **Geração de código**: Produz código Python (rotas, services, models, config) via LLM, com suporte a FastAPI, Flask, Django, Streamlit, CLI, etc.
- **Testes automatizados**: Executa testes após a geração.

### 2. Correção de Projetos (Correct Workflow)

- **Plano de código**: Analisa o projeto existente e gera um plano de alterações em JSON.
- **Implementação**: Aplica correções cirúrgicas preservando estilo e API existente.
- **Alteração mínima**: Foca apenas no necessário para atender ao pedido do usuário.

### 3. Análise (Modo Analisar)

- Classifica a intenção do usuário (criar, corrigir, analisar).
- Gera texto de análise quando o usuário quer apenas entender o que seria feito, sem executar.

---

## Fluxo de Entrada

1. **POST /comprehension/run** – Recebe o prompt e `root_path`.
2. **Classificação de intenção** – Decide se é criar (projeto vazio) ou corrigir (projeto existente).
3. **Execução** – Dispara o workflow de criação ou correção conforme o caso.

---

## Tecnologias e Frameworks Suportados

- **API REST**: FastAPI, Flask
- **Web**: Django, Streamlit
- **CLI / Scripts**: argparse, click
- **Bibliotecas**: Módulos Python puros

---

## Prompts e Configuração

Os prompts de criação e correção ficam em:

```
PulsoCSA/Python/prompts/
├── analyse/      # Análise de estrutura, backend, infra, segurança
├── creation/     # Geração de código
├── correct/      # Correção e implementação
└── tela_teste/   # Especificação de tela de teste (Streamlit)
```

---

## Resultado Esperado

Ao final do fluxo, o desenvolvedor obtém:

- Projeto Python estruturado e modular
- Código funcional, tipado e documentado
- Boas práticas de segurança (env para segredos, validação de entrada)
- Pronto para execução e evolução contínua
