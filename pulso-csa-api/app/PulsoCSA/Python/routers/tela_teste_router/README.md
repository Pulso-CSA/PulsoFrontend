# Tela Teste Router (TTH – itens 9 e 10)

Endpoints da camada 3 – análise e criação da tela de testes (FrontendEX/Streamlit).

## Estrutura

```
tela_teste_router/
├── __init__.py
├── tela_teste_router.py
└── README.md
```

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/analise-tela-teste` | Analisa como deve ser a tela de testes para QA funcional |
| `POST` | `/criar-tela-teste` | Cria a pasta FrontendEX com app Streamlit (localhost:3000) |

## Relacionados

- [Tela Teste Services](../../services/tela_teste_services/)
- [Tela Teste Models](../../models/tela_teste_models/)
