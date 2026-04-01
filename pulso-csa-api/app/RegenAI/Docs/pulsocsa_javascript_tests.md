## valid_questions
- Validar endpoint JavaScript de compreensao com payload basico e retorno 2xx.
- Confirmar se rota JavaScript de analise retorna estrutura JSON consistente.
- Verificar se endpoint JavaScript aceita query minima esperada sem erro interno.

## invalid_questions
- Enviar payload invalido para endpoint JavaScript e confirmar erro de validacao.
- Omitir campo obrigatorio em requisicao JavaScript e validar codigo 4xx.
- Usar metodo HTTP incorreto em rota JavaScript e verificar resposta apropriada.

## edge_cases
- Testar entrada JavaScript com caracteres especiais e acentos para robustez.
- Enviar lista grande de itens para endpoint JavaScript e observar degradacao.
- Repetir chamada identica em alta frequencia para observar consistencia de respostas.

## ambiguous_inputs
- Enviar prompt JavaScript generico sem contexto de dominio e validar orientacao.
- Misturar campos de diferentes formatos no mesmo payload e avaliar estabilidade.
- Enviar entrada parcialmente truncada e verificar estrategia de tratamento.
