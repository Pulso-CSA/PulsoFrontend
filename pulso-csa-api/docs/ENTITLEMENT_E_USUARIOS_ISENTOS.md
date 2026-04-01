# Entitlement e Usuários Isentos

## Usuários Isentos (Sócios e Exceções)

Usuários com os seguintes **nomes** ou **emails** têm acesso 100% à plataforma sem pagamento:

| Usuário | Descrição |
|---------|-----------|
| **G!** | Sócio |
| **E!** | Sócio |
| **T!** | Sócio |
| **V!** | Sócio |
| **P!** | Sócio |

### Configuração

A lista é configurável via variável de ambiente:

```
PAYMENT_EXEMPT_USERS=G!,E!,T!,V!,P!
```

Valores adicionais podem ser incluídos separados por vírgula.

### Como Criar Usuários Isentos

1. Crie o usuário na plataforma (signup com email/senha ou OAuth)
2. Defina o **nome** do usuário como um dos valores acima (ex: `G!`)
3. Ou use o **email** exatamente como um dos valores (ex: `G!` como email)

A verificação é feita nos campos `name` e `email` do usuário autenticado.

---

## Feature Gating

- **Usuários isentos**: acesso total a todos os serviços
- **Usuários com assinatura ativa**: acesso conforme plano
- **Usuários sem assinatura**: recebem `403 SUBSCRIPTION_REQUIRED`

---

## Histórico de Chats

- Persistido por `tenant_id` + `service_id` + `session_id`
- Endpoints:
  - `GET /chat-history/{service_id}/sessions` – lista sessões
  - `GET /chat-history/{service_id}/messages?session_id=xxx` – lista mensagens

---

## Planos e Serviços

| Plano | Max Serviços |
|-------|--------------|
| Basic | 1 |
| Plus | 2 |
| Pro | 3 |
| Elite | 4 |

Serviços disponíveis: `id`, `finops`, `comprehension`, `governance`, `workflow`, `infra`, `pipeline`, `creation`, `deploy`, `venv`, `test`, `analise`, `correct`, `tela_teste`.
