# Documentação de análises do app

Nesta pasta estão os documentos de **análise e planejamento** da aplicação (pasta `app`), com impacto global ou no Sistema de Compreensão.

## Documentos principais (api/docs/)

| Documento | Conteúdo |
|-----------|----------|
| **[AUDITORIA_TECNICA_PRODUCAO.md](../AUDITORIA_TECNICA_PRODUCAO.md)** | Auditoria técnica completa; checklist de readiness para produção (atualizado 12/02/2025). |
| **[REANALISE_COMPLETA_FINAL.md](../REANALISE_COMPLETA_FINAL.md)** | Estado atual otimizado: segurança, performance, custos e qualidade (~95% cobertura). |
| **[CORRECOES_SEGURANCA_APLICADAS.md](./CORRECOES_SEGURANCA_APLICADAS.md)** | Correções de segurança e gaps aplicadas (inclui headers, lock, sanitização). |

## Análises desta pasta

| Documento | Conteúdo |
|-----------|----------|
| **ANALISE_APP_NOVA_2025.md** | Análise final: multi-usuário, velocidade, segurança e economia (estado atual e verificação). |
| **ANALISE_APP_MULTIUSUARIO_VELOCIDADE_SEGURANCA_CUSTO.md** | Análise anterior das mesmas dimensões (histórico). |
| **ANALISE_ORGANIZACAO_SISTEMA.md** | Organização da pasta `app`: camadas, domínios, nomenclatura e checklist de melhorias. |
| **PLANO_MELHORIAS.md** | Plano de melhorias com impacto global (Parte I) e detalhamento do Sistema de Compreensão (Parte II). |
| **ANALISE_AGENTES_MODELO_BARATO.md** | Quais agentes podem usar modelo mais barato (economia de custo); mapeamento de uso de LLM e prioridades. |
| **ANALISE_IMPACTO_TEMPO_RESUMO_PRATICO.md** | Impacto em percentual de tempo ao aplicar cada item do resumo prático (velocidade e custo). |

## Subpasta patchs/

| Documento | Conteúdo |
|-----------|-----------|
| **[RELATORIO_ANALISE_COMPLETA_PATCHES.md](./patchs/RELATORIO_ANALISE_COMPLETA_PATCHES.md)** | Análise completa CI/CD e patches (frontend Electron + backend). |
| **[RELATORIO_IMPLEMENTACAO_VIA_CODIGO.md](./patchs/RELATORIO_IMPLEMENTACAO_VIA_CODIGO.md)** | O que pode ser implementado via código (rotas, services, CI/CD). |
| **[INSTRUCOES_FRONTEND_PATCHES.md](./patchs/INSTRUCOES_FRONTEND_PATCHES.md)** | Instruções para o frontend: comportamento, onde fica cada funcionalidade, variáveis. |
| **[GUIA_FRONTEND_LOCAL_GITHUB_ACTIONS.md](./patchs/GUIA_FRONTEND_LOCAL_GITHUB_ACTIONS.md)** | Guia simplificado: teste local + preparação para GitHub Actions. |

---

*Documentação centralizada em `api/docs/`. Última atualização: 24/02/2025.*
