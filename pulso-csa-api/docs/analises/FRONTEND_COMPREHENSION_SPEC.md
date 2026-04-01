# Especificação para o frontend – Sistema de Compreensão

Documento descrevendo **o que o front deve alterar** e os **parâmetros em JSON** (ida e volta). Nenhuma alteração de código backend é necessária.

---

## 1. O que deve alterar no frontend

### 1.1 Chamada ao backend

- **Antes (se existir):** chamada direta para `/governance/run` ou `/workflow/correct/run`.
- **Agora:** a **única entrada** do fluxo é **`POST /comprehension/run`**.
- O front envia **sempre** para `/comprehension/run` com: `usuario`, `prompt` e (quando tiver) `root_path`. O backend decide sozinho se dispara criação, correção ou só análise.

### 1.2 Envio do formulário (área “Descrição do projeto” + “Enviar Prompt”)

- Ao clicar em **“Enviar Prompt”**, o front deve:
  1. Montar o body com os campos abaixo (request JSON).
  2. Fazer `POST /comprehension/run` com esse body.
  3. Tratar a resposta com os campos abaixo (response JSON).
  4. Exibir no chat/área de resposta:
     - **message** como texto principal (sempre).
     - **file_tree** em bloco/seção “Árvore do projeto”, quando existir (com legenda: `*` = criado neste run).
     - Opcional: **next_action** como dica abaixo do input; **frontend_suggestion** como guia de UX.

### 1.3 Tratamento da resposta

- **intent === "ANALISAR"**  
  Mostrar só a **message** (análise/plano). Não há execução de workflow.

- **intent === "EXECUTAR" e should_execute === false**  
  Mostrar **message** pedindo confirmação e usar **next_action** (ex.: “Diga ‘faça’ para executar”). Não chamar outros endpoints.

- **intent === "EXECUTAR" e should_execute === true**  
  Mostrar **message** como sucesso e exibir **file_tree** (árvore com `*` nos arquivos novos).

### 1.4 Erros

- **400:** prompt vazio ou, no fluxo de correção, `root_path` ausente → exibir mensagem de validação.
- **500:** erro ao executar workflow → exibir mensagem genérica de erro.

### 1.5 Contrato em tempo de execução (opcional)

- O front pode obter o JSON de parâmetros (ida e volta) em: **`GET /comprehension/contract`**.
- Útil para gerar tipos, validação ou documentação dinâmica.

---

## 2. Parâmetros em JSON – ida (request)

**Método e URL:** `POST /comprehension/run`  
**Content-Type:** `application/json`

### Body (objeto)

| Campo       | Tipo           | Obrigatório | Descrição |
|------------|----------------|-------------|-----------|
| `usuario`  | string         | Sim         | Identificação do usuário. |
| `prompt`   | string         | Sim         | Texto do chat / descrição do projeto (não pode ser vazio). |
| `root_path`| string \| null | Não         | Caminho raiz do projeto. Obrigatório quando for executar fluxo de **correção** (projeto já com conteúdo). |

### Exemplo de payload (ida)

```json
{
  "usuario": "usuario@email.com",
  "prompt": "Criar API REST para gestão de pedidos",
  "root_path": "C:\\Users\\pytho\\Desktop\\MeuProjeto"
}
```

Para só **análise** (sem executar), `root_path` pode ser omitido ou `null`.

---

## 3. Parâmetros em JSON – volta (response)

**Content-Type:** `application/json`

### Body (objeto)

| Campo                 | Tipo             | Descrição |
|-----------------------|------------------|-----------|
| `intent`             | string           | `"ANALISAR"` ou `"EXECUTAR"`. |
| `project_state`      | string           | `"ROOT_VAZIA"` ou `"ROOT_COM_CONTEUDO"`. |
| `should_execute`     | boolean          | Se o usuário deu sinal de execução (ex.: “faça”, “executar”). |
| `target_endpoint`    | string \| null    | `"/governance/run"`, `"/workflow/correct/run"` ou `null`. |
| `explanation`        | string           | Explicação da decisão de roteamento. |
| `next_action`        | string           | Próximo passo descrito. |
| `message`            | string           | **Mensagem humanizada para exibir no chat** (sucesso, análise ou pedido de confirmação). |
| `file_tree`          | string \| null   | Árvore de arquivos em texto; arquivos novos com `*` ao lado do nome. `null` se não houver `root_path` válido. |
| `system_behavior`    | object \| null   | Contrato do sistema (input, output, parâmetros). |
| `frontend_suggestion`| string \| null   | Sugestão de como exibir as mudanças na área do chat. |

### Exemplo de payload (volta) – sucesso após execução

```json
{
  "intent": "EXECUTAR",
  "project_state": "ROOT_VAZIA",
  "should_execute": true,
  "target_endpoint": "/governance/run",
  "explanation": "Intenção: EXECUTAR. Projeto: ROOT_VAZIA. Sinal de execução: sim.",
  "next_action": "Disparar fluxo: /governance/run",
  "message": "Projeto criado com sucesso. Requisição: REQ-20250202-123456. Estrutura e código foram gerados conforme o planejamento.",
  "file_tree": "REQ-20250202-123456/\n  generated_code/\n    main.py *\n    requirements.txt *",
  "system_behavior": { },
  "frontend_suggestion": "Mostre a 'message' como mensagem de sucesso no chat. Exiba a 'file_tree' em um bloco colapsável ou seção 'Árvore do projeto' (novos arquivos com *)."
}
```

### Exemplo – só análise (sem execução)

```json
{
  "intent": "ANALISAR",
  "project_state": "ROOT_VAZIA",
  "should_execute": false,
  "target_endpoint": null,
  "explanation": "Intenção: ANALISAR. Projeto: ROOT_VAZIA.",
  "next_action": "Responder com análise e plano, sem executar workflow.",
  "message": "Análise: ... (texto gerado pelo backend)",
  "file_tree": null,
  "system_behavior": { },
  "frontend_suggestion": "Exiba a mensagem de análise no chat."
}
```

### Exemplo – execução pedindo confirmação

```json
{
  "intent": "EXECUTAR",
  "project_state": "ROOT_COM_CONTEUDO",
  "should_execute": false,
  "target_endpoint": "/workflow/correct/run",
  "explanation": "Intenção: EXECUTAR. Projeto: ROOT_COM_CONTEUDO. Sinal de execução: não.",
  "next_action": "Pedir confirmação ao usuário (ex.: diga 'faça' para executar).",
  "message": "Entendi o que você quer fazer (correção do projeto). Para executar de fato, confirme com: \"faça\", \"executar\", \"aplicar\" ou \"implementar\".",
  "file_tree": null,
  "system_behavior": { },
  "frontend_suggestion": "Mostre a 'message' no chat e destaque que o usuário pode confirmar com 'faça', 'executar' ou 'aplicar'."
}
```

---

## 4. Resumo para o front

| O que alterar | Detalhe |
|---------------|---------|
| Endpoint de envio | Usar **só** `POST /comprehension/run` (não chamar mais direto `/governance/run` nem `/workflow/correct/run`). |
| Request | Sempre enviar `usuario`, `prompt` e, quando existir, `root_path` (obrigatório para correção). |
| Resposta no chat | Exibir **message** como conteúdo principal; **file_tree** em seção “Árvore do projeto” (com `*` = novo); opcional **next_action** e **frontend_suggestion**. |
| Decisão de fluxo | Não decidir no front: o backend devolve `intent`, `should_execute`, `target_endpoint`; o front só exibe e, se quiser, usa **frontend_suggestion**. |
| Contrato JSON | Request e response conforme os JSON acima; opcional: `GET /comprehension/contract` para obter o contrato em tempo de execução. |

---

## 5. JSON único de referência (contrato completo)

```json
{
  "request": {
    "method": "POST",
    "path": "/comprehension/run",
    "body": {
      "usuario": { "type": "string", "required": true },
      "prompt": { "type": "string", "required": true },
      "root_path": { "type": "string | null", "required": false }
    }
  },
  "response": {
    "body": {
      "intent": { "type": "string", "enum": ["ANALISAR", "EXECUTAR"] },
      "project_state": { "type": "string", "enum": ["ROOT_VAZIA", "ROOT_COM_CONTEUDO"] },
      "should_execute": { "type": "boolean" },
      "target_endpoint": { "type": "string | null" },
      "explanation": { "type": "string" },
      "next_action": { "type": "string" },
      "message": { "type": "string" },
      "file_tree": { "type": "string | null" },
      "system_behavior": { "type": "object | null" },
      "frontend_suggestion": { "type": "string | null" }
    }
  }
}
```

O front pode usar este documento como especificação e os JSON acima como referência de parâmetros (ida e volta) sem precisar alterar código no backend.
