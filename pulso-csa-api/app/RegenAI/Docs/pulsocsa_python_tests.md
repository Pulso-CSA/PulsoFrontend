## valid_questions
- Validar se a rota principal de autenticacao Python responde com status 2xx para requisicao minima valida.
- Confirmar se endpoints Python protegidos retornam erro de autorizacao quando token nao e enviado.
- Verificar se payload minimo esperado para criacao de recurso Python retorna resposta estruturada.

## invalid_questions
- Enviar body vazio para endpoint Python que exige campos obrigatorios e validar erro 4xx.
- Enviar tipo invalido (numero em campo texto) em endpoint Python e confirmar validacao.
- Chamar endpoint Python inexistente do modulo e verificar tratamento de erro.

## edge_cases
- Enviar strings longas em campos de entrada Python e validar limite sem quebra do endpoint.
- Enviar valores nulos em campos opcionais e validar comportamento padrao.
- Testar query params extras nao esperados e verificar se sao ignorados ou rejeitados corretamente.

## ambiguous_inputs
- Solicitar acao generica sem contexto de recurso e avaliar mensagem de orientacao do endpoint Python.
- Usar valores parcialmente validos e parcialmente invalidos no mesmo payload para medir robustez.
- Simular entrada com formato misto (texto + objeto) e verificar consistencia da resposta.
