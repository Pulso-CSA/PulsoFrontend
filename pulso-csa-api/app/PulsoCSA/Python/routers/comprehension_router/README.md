# Sistema de Compreensão (Intent Router) – PulsoCSA

Router de entrada do workflow **PulsoCSA** (Cursor-like sem IDE): classifica a intenção (ANALISAR/EXECUTAR), decide o modo do projeto e dispara `governance/run` (criação) ou `workflow/correct/run` (correção). Objetivos: criar código do zero com melhores práticas, documentação, otimização e segurança; corrigir código existente com alteração mínima, velocidade e qualidade. Ver [PulsoCSA – Objetivo](../../docs/PULSOCSA_OBJETIVO.md).

## Estrutura

```
comprehension_router/
├── __init__.py
├── comprehension_router.py
└── README.md
```

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/comprehension/contract` | Contrato da rota (request/response) para o frontend |
| `POST` | `/comprehension/run` | Entrada principal: classificação de intenção e execução opcional |

## Relacionados

- [Comprehension Services](../../services/comprehension_services/)
- [Comprehension Models](../../models/comprehension_models/)

## Documentação de análises do app

As análises de multi-usuário, velocidade, segurança, economia e organização do sistema estão em **[api/docs/analises/](../../../docs/analises/)**:

- `ANALISE_APP_NOVA_2025.md` – Análise final (multi-usuário, velocidade, segurança, economia)
- `ANALISE_APP_MULTIUSUARIO_VELOCIDADE_SEGURANCA_CUSTO.md` – Análise anterior
- `ANALISE_ORGANIZACAO_SISTEMA.md` – Organização da pasta app
- `PLANO_MELHORIAS.md` – Plano de melhorias global e Sistema de Compreensão
