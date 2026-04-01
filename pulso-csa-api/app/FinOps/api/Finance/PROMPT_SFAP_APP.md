# Prompt: Criar a área SFAP no app (frontend + integração)

Use este documento como **prompt completo** para implementar a área **SFAP (Sistema Financeiro Administrativo Pulso)** no aplicativo (frontend), mantendo o estilo visual existente e integrando ao menu do usuário.

---

## 1. Objetivo

Criar no app uma área chamada **SFAP (Sistema Financeiro Administrativo Pulso)** que permita:

- Ver **dashboard** (receita total, custo de operação, saldo).
- Gerenciar **planos** (tabela de preços, taxas Stripe, lucro por escala de usuários).
- Gerenciar **movimentos**: **receita** (ganhos, incluindo receita por plano de usuário pagante) e **gastos** (custo de operação, com recorrência: único, mensal, anual ou personalizado).
- Filtrar e exportar dados (conforme contratos da API abaixo).

Os dados são persistidos no **MongoDB**, banco **pulso_database**, coleção **Financeiro**. O backend já expõe a API sob o prefixo **`/sfap`** (módulo em `api/app/routers/finance_router/`, serviços, models e storage em `api/app/services/finance/`, `api/app/models/finance/`, `api/app/storage/database/finance/`).

---

## 2. Quem pode ver o SFAP

O SFAP **só pode aparecer** para perfis cujo **nome completo** (campo `name` do perfil) seja exatamente um dos seguintes:

- **G!**
- **E!**
- **T!**
- **P!**

Regras:

- O app já possui um **menu dropdown** do usuário (ícone de perfil no header) com itens como: **Tema**, **Conta**, **Configurações**, **Convidar usuário**, **Trocar de Perfil**, **Sair**.
- O item **SFAP** deve ser adicionado **logo abaixo de "Tema"**, na mesma lista, com o mesmo padrão visual (ícone + texto).
- O texto do item deve ser: **SFAP (Sistema Financeiro Administrativo Pulso)** ou, se o menu for curto, **SFAP** com tooltip/subtítulo explicando “Sistema Financeiro Administrativo Pulso”.
- **Exibir o item SFAP apenas** quando o perfil atualmente selecionado tiver `name` em `["G!", "E!", "T!", "P!"]`. Caso contrário, não mostrar o item.
- Para saber se o perfil atual tem permissão, o frontend pode:
  - Chamar **GET /sfap/visibility** com o header **X-Profile-Id** (id do perfil ativo) e **Authorization: Bearer &lt;token&gt;**; a API retorna `{ "allowed": true }` ou `{ "allowed": false }`.
  - Ou, se o app já carrega o perfil ativo (incluindo `name`), esconder/mostrar o item com base em `name in ["G!", "E!", "T!", "P!"]`.

Todas as demais rotas do SFAP exigem **Authorization: Bearer &lt;token&gt;** e **X-Profile-Id**; caso o perfil não seja G!, E!, T! ou P!, a API responde **403 Forbidden**.

---

## 3. Estilo visual

- Manter o **mesmo estilo visual** já existente no app (tema escuro do dropdown, ícones à esquerda do texto, tipografia e cores atuais).
- O item de menu SFAP deve seguir o mesmo padrão dos itens existentes (ex.: Tema, Conta, Configurações).
- As telas internas do SFAP (dashboard, listagens, formulários) devem usar o mesmo design system do app (cores, bordas, cards, botões, inputs) para consistência.

---

## 4. Rotas da API (backend já implementado)

Base URL: mesma da API do app (ex.: `https://api.pulso.com` ou `http://localhost:8000`).  
Prefix: **`/sfap`**.  
Headers obrigatórios nas rotas protegidas: **`Authorization: Bearer <JWT>`** e **`X-Profile-Id: <id_do_perfil_ativo>`**.

### 4.1 Visibilidade (público para decidir se mostra o item de menu)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/sfap/visibility` | Retorna `{ "allowed": true \| false }` conforme o perfil (X-Profile-Id) ser G!, E!, T!, P! ou não. Usar para exibir/ocultar o item SFAP no menu. |

### 4.2 Dashboard

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/sfap/dashboard` | Retorna totais: `receita_total_usd`, `custo_total_usd`, `saldo_usd`. |

### 4.3 Planos (tabela de preços / lucro por escala)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/sfap/planos` | Lista todos os planos. Query opcional: `tipo` (ex.: MENSAL, ANUAL). |
| POST | `/sfap/planos` | Cria plano. Body: `tipo_plano`, `preco_unit_usd`, `taxa_stripe_unit_usd`, `taxa_stripe_total_10k_usd`, `lucro_100_usd`, `lucro_1000_usd`, `lucro_10000_usd`. |
| PATCH | `/sfap/planos/{plano_id}` | Atualiza plano (campos enviados no body). |
| DELETE | `/sfap/planos/{plano_id}` | Remove plano. |

### 4.4 Movimentos (receita e gastos)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/sfap/movimentos` | Lista movimentos. Query opcional: `tipo` (ganho \| gasto), `categoria`, `data_inicio`, `data_fim` (ISO). |
| POST | `/sfap/movimentos` | Cria movimento. Body: `data` (ISO), `tipo` (ganho \| gasto), `categoria`, `descricao`, `valor_usd`, `moeda`, `notas`, `recorrencia` (único \| mensal \| anual \| personalizado), `recorrencia_intervalo`, `recorrencia_unidade` (meses \| dias), e opcionalmente `plano_tipo`, `plano_preco`, `num_usuarios` para receita de plano. |
| PATCH | `/sfap/movimentos/{movimento_id}` | Atualiza movimento (campos enviados no body). |
| DELETE | `/sfap/movimentos/{movimento_id}` | Remove movimento. |

Categorias de gasto sugeridas: **infra**, **taxa**, **marketing**, **folha**, **outros**. Receita vinculada a plano pode usar categoria **receita_plano**.

---

## 5. Estrutura da coleção MongoDB "Financeiro"

Banco: **pulso_database**.  
Coleção: **Financeiro** (ou o valor de `FINANCEIRO_COLLECTION` no .env).

Cada documento tem um campo **`tipo_doc`**:

- **`tipo_doc: "plano"`** – Referência de plano (preço, taxas Stripe, lucro por 100 / 1k / 10k usuários). Campos: `tipo_plano`, `preco_unit_usd`, `taxa_stripe_unit_usd`, `taxa_stripe_total_10k_usd`, `lucro_100_usd`, `lucro_1000_usd`, `lucro_10000_usd`, `created_at`, `updated_at`.
- **`tipo_doc: "movimento"`** – Receita (ganho) ou gasto. Campos: `data`, `tipo` (ganho \| gasto), `categoria`, `descricao`, `valor_usd`, `moeda`, `notas`, `recorrencia`, `recorrencia_intervalo`, `recorrencia_unidade`, opcionalmente `plano_tipo`, `plano_preco`, `num_usuarios`, `created_at`, `updated_at`.

Essa coleção é a **fonte única** dos dados principais de usuários pagantes (receita por plano) e dos gastos da operação. O backend já implementa leitura/escrita nessa coleção.

---

## 6. O que o frontend deve fazer (resumo)

1. **Menu (dropdown do perfil)**  
   - Inserir o item **SFAP (Sistema Financeiro Administrativo Pulso)** **logo abaixo de "Tema"**.  
   - Mesmo estilo dos outros itens (ícone + texto, tema escuro).  
   - Mostrar o item apenas se o perfil ativo tiver nome **G!**, **E!**, **T!** ou **P!** (via GET `/sfap/visibility` com `X-Profile-Id` ou via dado do perfil já carregado).

2. **Ao clicar em SFAP**  
   - Navegar para a área/tela do SFAP (rota interna do app, ex.: `/sfap` ou `/settings/sfap`).

3. **Telas do SFAP**  
   - **Dashboard**: exibir receita total, custo total e saldo (GET `/sfap/dashboard`).  
   - **Planos**: listar, criar, editar e excluir planos (GET/POST/PATCH/DELETE `/sfap/planos`).  
   - **Movimentos**: listar com filtros (tipo, categoria, datas), criar (receita ou gasto, com recorrência opcional), editar e excluir (GET/POST/PATCH/DELETE `/sfap/movimentos`).  
   - Em todas as chamadas, enviar **Authorization: Bearer &lt;token&gt;** e **X-Profile-Id: &lt;id do perfil ativo&gt;**.

4. **UX**  
   - Manter o mesmo estilo visual do app; usar o mesmo design system para cards, tabelas, formulários e botões.

---

## 7. Nome e posição (recapitulação)

- **Nome no app**: **SFAP (Sistema Financeiro Administrativo Pulso)** (ou só **SFAP** no menu, com tooltip/nome completo onde couber).
- **Posição no menu**: **Logo abaixo de "Tema"** no dropdown do perfil (ícone de perfil no header).
- **Perfis autorizados**: apenas **G!**, **E!**, **T!**, **P!** (por nome do perfil).

Com essas informações, é possível implementar a área SFAP no app de forma consistente com o backend e com o restante da interface.
