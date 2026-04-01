## valid_questions
- Validar endpoint CloudIAC de analise de infraestrutura com entrada minima valida.
- Confirmar rota CloudIAC de validacao Terraform com resposta 2xx ou 4xx controlada.
- Verificar endpoint CloudIAC de geracao com parametros basicos e retorno estruturado.

## invalid_questions
- Enviar provider invalido no CloudIAC e confirmar erro de validacao.
- Omitir informacoes obrigatorias do stack Terraform e verificar resposta 4xx.
- Enviar modulo inexistente para endpoint CloudIAC e validar tratamento.

## edge_cases
- Testar configuracao multi-cloud no mesmo payload para robustez de parsing.
- Enviar variaveis de infraestrutura com tamanho elevado e observar estabilidade.
- Validar comportamento com tags repetidas e chaves opcionais ausentes.

## ambiguous_inputs
- Solicitar deploy sem definicao de ambiente e verificar orientacao de erro.
- Enviar objetivo infra generico sem provider e validar resposta guiada.
- Misturar comandos de analise e deploy no mesmo payload e observar estrategia de tratamento.
