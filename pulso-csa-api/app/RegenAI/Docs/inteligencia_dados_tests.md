## valid_questions
- Validar consulta basica de InteligenciaDados com retorno estruturado e status 2xx.
- Confirmar endpoint de analise estatistica com parametros minimos validos.
- Verificar endpoint de previsao com input simples e resposta sem erro.

## invalid_questions
- Enviar dataset invalido para rota de analise e confirmar erro de validacao.
- Omitir metadados obrigatorios na rota de modelos ML e validar retorno 4xx.
- Enviar formato de data inconsistente e verificar resposta de erro clara.

## edge_cases
- Testar volume maior de registros em consulta para observar tempo e estabilidade.
- Enviar dados com campos faltantes opcionais e validar fallback seguro.
- Usar valores extremos (muito altos/baixos) em campos numericos e observar comportamento.

## ambiguous_inputs
- Fazer pergunta analitica ampla sem metrica definida e avaliar orientacao do endpoint.
- Enviar instrucao que mistura previsao e limpeza no mesmo payload e verificar tratamento.
- Informar objetivo de negocio sem dataset explicito e validar mensagem de apoio.
