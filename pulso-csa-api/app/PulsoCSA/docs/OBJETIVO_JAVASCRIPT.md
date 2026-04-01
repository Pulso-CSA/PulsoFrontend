# Objetivo Final – PulsoCSA JavaScript

## Visão Geral

O **PulsoCSA JavaScript** é o serviço de **compreensão e geração de código** voltado para projetos em **JavaScript**, **TypeScript**, **React**, **Vue** e **Angular**. Seu objetivo final é permitir que o desenvolvedor descreva em linguagem natural o que deseja criar ou corrigir, e o sistema entregue código frontend funcional e estruturado.

---

## Princípio Fundamental

**O pipeline JavaScript é idêntico ao pipeline Python.** A única diferença prática é a linguagem de programação usada para atender ao pedido (JavaScript/TypeScript/React em vez de Python). As mesmas etapas, fluxos e capacidades (refino, análise, Code Plan, Writer, Implementer, testes, autocorreção) são executadas em ambos.

---

## Objetivo Final

**Transformar descrições em linguagem natural em projetos JavaScript/TypeScript/React/Vue/Angular completos e funcionais**, cobrindo desde a criação do zero até a correção e evolução de código existente, com foco em componentes modernos, hooks, tipagem e boas práticas de frontend.

---

## Capacidades Principais (Pipeline = Python)

### 1. Criação de Projetos (Creator Workflow)

- **C1 – Governança**: Input → Refino → Validação (igual ao Python).
- **C2 – Arquitetura**: Estrutura, Backend, Infra, Segurança código/infra (adaptados para JS/TS/React).
- **C3 – Estrutura**: Criação de diretórios e arquivos base (package.json, src/, components/, etc.).
- **C2b – Code Plan**: Plano de código em JSON para arquivos .js/.tsx/.vue.
- **C3 – Code Writer**: Geração de código via LLM.
- **C4 – Code Implementer**: Implementação e ajustes.
- **C5 – Teste**: Testes automatizados (npm test, Vitest, Jest).
- **Boilerplate por framework**: React, Vue, Angular, Vanilla JS/TS.

### 2. Correção de Projetos (Correct Workflow)

- **C1 – Governança**: Input → Refino → Validação.
- **C2 – Análise estrutural**: Scan do projeto → Plano de mudanças.
- **C2b – Code Plan** → **C3 – Code Writer** → **C4 – Code Implementer** → **C5 – Teste**.
- **Autocorreção**: Análise de retorno → Correção de erros → Segurança código/infra (igual ao Python).

### 3. Análise (Modo Analisar)

- Classifica a intenção do usuário (criar, corrigir, analisar).
- Retorna mensagem humanizada sobre o que seria feito, sem executar.

---

## Fluxo de Entrada

1. **POST /comprehension-js/run** – Recebe o prompt, `root_path` e flags de framework (`use_react`, `use_vue`, `use_angular`, `use_typescript`).
2. **Classificação de intenção** – Decide se é criar (projeto vazio) ou corrigir (projeto existente).
3. **Execução** – Dispara o workflow de criação ou correção conforme o caso.

---

## Tecnologias e Frameworks Suportados

- **React**: Vite + React, JSX/TSX
- **Vue**: Vue 3, Composition API, single-file components (.vue)
- **Angular**: Angular 17+, componentes e módulos
- **Vanilla**: JavaScript ou TypeScript puro, Node.js

---

## Prompts e Configuração

Os prompts de criação e correção ficam em:

```
PulsoCSA/JavaScript/prompts/
├── creation/   # Geração de código (system, code_creation)
└── correct/   # Correção (implementation_system, implementation_user)
```

---

## Resultado Esperado

Ao final do fluxo, o desenvolvedor obtém:

- Projeto frontend estruturado e pronto para `npm install` e `npm run dev`
- Componentes funcionais, tipados (quando TypeScript) e com boas práticas
- Código seguro (sem `eval` em input de usuário, validação de props)
- Pronto para evolução e integração com APIs
