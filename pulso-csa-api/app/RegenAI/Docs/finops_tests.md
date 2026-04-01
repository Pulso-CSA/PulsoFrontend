## valid_questions
- Validar endpoint FinOps de analise de custos com parametros minimos e status 2xx.
- Confirmar rota FinOps de relatorio com resposta JSON consistente.
- Verificar endpoint financeiro com filtro simples e retorno sem erro.

## invalid_questions
- Enviar provedor cloud invalido para rota FinOps e confirmar erro 4xx.
- Omitir periodo obrigatorio na consulta de custos e validar resposta de validacao.
- Enviar credenciais simuladas malformadas e observar tratamento seguro.

## edge_cases
- Testar janela de datas ampla em FinOps para observar limite de processamento.
- Enviar combinacao de filtros raros no endpoint FinOps e verificar consistencia.
- Usar valores monetarios extremos e validar robustez do calculo.

## ambiguous_inputs
- Solicitar reducao de custos sem indicar escopo cloud e verificar mensagem orientativa.
- Enviar pergunta de otimização sem informacao temporal e avaliar tratamento.
- Misturar termos de billing e observabilidade no mesmo payload e observar resposta.
