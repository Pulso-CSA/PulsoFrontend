# Terraform – PulsoAPI Infra Module

Estrutura modular multi-cloud (AWS/Azure/GCP) gerada por PulsoAPI.

## Estrutura

```
terraform/
├── modules/
│   ├── aws/     # networking, compute, container, storage, iam, observability
│   ├── azure/   # networking, compute, container, storage, iam, observability
│   └── gcp/     # networking, compute, container, storage, iam, observability
├── stacks/
│   └── <env>/<provider>/   # main.tf (wiring)
└── policy/      # regras OPA/Conftest (opcional)
```

## Fluxo

1. `POST /infra/analyze` – analisa repo e gera InfraSpec
2. `POST /infra/generate` – gera artefatos Terraform
3. `POST /infra/validate` – fmt, validate, plan + deploy_token
4. `POST /infra/deploy` – apply (com confirm=true, token, frase)

## Segurança

- `INFRA_DEPLOY_TOKEN_SECRET` obrigatório para deploy
- `confirm_phrase="EU ENTENDO QUE ISTO CRIARÁ RECURSOS E CUSTOS"`
