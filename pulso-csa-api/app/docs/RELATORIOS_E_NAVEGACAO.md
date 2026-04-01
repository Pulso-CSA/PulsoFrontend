# Relatórios PDF e Navegação sem Bloquear

## Relatórios PDF por área

Quatro endpoints permitem baixar um **relatório em PDF** com as partes mais relevantes das conversas de cada área, com **marca d'água Pulso** (logo ou texto "PULSO"):

| Endpoint | Área | service_id no histórico |
|----------|------|--------------------------|
| `GET /reports/pulsocsa` | PulsoCSA (criação e correção de código) | `codigo` |
| `GET /reports/cloud-iac` | Cloud IAC (infraestrutura) | `infraestrutura` |
| `GET /reports/finops` | FinOps | `finops` |
| `GET /reports/inteligencia-dados` | Inteligência de Dados | `id` |

- Requer autenticação (Bearer token).
- Parâmetros opcionais: `session_id` (filtrar por sessão), `limit` (1–200, default 100).
- Resposta: `application/pdf` com `Content-Disposition: attachment; filename="relatorio-<area>.pdf"`.

Para o relatório incluir as conversas corretas, o frontend deve persistir o histórico com o **service_id** correspondente à área ao chamar `persist_chat` (ou equivalente): `codigo` para PulsoCSA, `infraestrutura` para Cloud IAC, `finops` para FinOps, `id` para Inteligência de Dados.

### Logo Pulso (marca d'água)

- Variável de ambiente opcional: `PULSO_LOGO_PATH` (caminho absoluto para imagem, ex.: PNG).
- Se não definida, usa `api/app/assets/pulso_logo.png`.
- Se o arquivo não existir, a marca d'água é o texto **PULSO**.

---

## Navegação sem bloquear a geração

Para que o usuário possa **ir para outras áreas sem parar o que está sendo gerado**:

1. **Frontend**
   - Ao enviar uma mensagem que dispara workflow pesado (ex.: comprehension → workflow/correct/run), exibir um estado "Processando em segundo plano" e permitir trocar de aba/módulo.
   - Quando o resultado estiver pronto (polling ou WebSocket), exibir no chat correspondente ou notificar.

2. **Backend (opcional)**
   - Oferecer modo assíncrono: por exemplo `POST /comprehension/run?async=1` retornar `202 Accepted` com `job_id` e processar em background; o cliente consulta `GET /jobs/{job_id}` até conclusão.
   - Hoje o fluxo é síncrono: a resposta só volta quando o workflow termina. Para não bloquear a navegação, a implementação recomendada é a do frontend (não bloquear a UI e, se desejado, polling/WebSocket quando houver endpoint de jobs).

3. **Persistência do histórico**
   - Garantir que toda resposta do chat (incluindo a do workflow) seja salva no histórico com o `service_id` correto, para que o usuário veja o resultado ao voltar à área e para que os relatórios PDF incluam essas conversas.
