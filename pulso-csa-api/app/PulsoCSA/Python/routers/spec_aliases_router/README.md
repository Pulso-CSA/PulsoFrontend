# Spec Aliases Router

Expõe as rotas exatamente como na especificação (sem prefixo): `/input`, `/refinar`, `/validar`, `/analise-estrutura`, `/analise-backend`, `/analise-infra`, `/seguranca-infra`, `/seguranca-codigo`, `/criar-estrutura`, `/criar-codigo`.

As rotas com prefixo (`/governance/*`, `/backend/*`, `/infra/*`, `/execution/*`) continuam válidas.

## Estrutura

```
spec_aliases_router/
├── __init__.py
├── spec_aliases_router.py
└── README.md
```

## Relacionados

- [Analise Router](../analise_router/) (governance, backend, infra)
- [Creation Routers](../creation_routers/) (execution)
