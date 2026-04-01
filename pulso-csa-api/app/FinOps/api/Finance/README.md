# Finance (SFAP) – Módulo na API

O **SFAP (Sistema Financeiro Administrativo Pulso)** é um módulo de backend na API Pulso que controla:

- **Planos**: tabela de preços, taxas Stripe e lucro por escala (100 / 1.000 / 10.000 usuários).
- **Movimentos**: receita (ganho, inclusive por plano de usuário pagante) e gastos (custo de operação), com recorrência opcional (mensal, anual, personalizada).

O código modular (sem Streamlit) está em:

- `api/app/routers/finance_router/` – rotas FastAPI sob o prefixo `/sfap`
- `api/app/services/finance/` – lógica de negócio
- `api/app/models/finance/` – modelos Pydantic
- `api/app/storage/database/finance/` – persistência na coleção **Financeiro** do MongoDB (`pulso_database`)

Acesso às rotas SFAP é restrito a perfis cujo **nome** seja **G!**, **E!**, **T!** ou **P!**. O frontend deve enviar o header `X-Profile-Id` com o id do perfil ativo.

Para integrar a área SFAP no app (menu do usuário, tela, estilo), use o documento **PROMPT_SFAP_APP.md** nesta pasta como prompt completo.
