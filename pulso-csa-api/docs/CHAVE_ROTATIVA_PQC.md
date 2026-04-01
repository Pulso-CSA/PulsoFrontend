# Chave Rotativa + Criptografia Pós-Quântica (PQC)

## Visão geral

Sistema de chave rotativa a cada 6 horas com HKDF-SHA384 e double-buffer (grace period) para proteger tokens JWT sem derrubar sessões durante a rotação.

## Ativação

Defina `KEY_SEED_WORDS` no `.env` com 20 palavras (ou mais) separadas por vírgula ou espaço:

```env
KEY_SEED_WORDS=palavra1,palavra2,palavra3,palavra4,palavra5,palavra6,palavra7,palavra8,palavra9,palavra10,palavra11,palavra12,palavra13,palavra14,palavra15,palavra16,palavra17,palavra18,palavra19,palavra20
```

**Suporta caracteres Unicode**: palavras com ç, ã, á, é, etc. são aceitas. Salve o `.env` em UTF-8.

- **Sem `KEY_SEED_WORDS`**: modo legacy (JWT_SECRET + HS256).
- **Com `KEY_SEED_WORDS`**: modo KeyRing (HKDF-SHA384 + HS384 + kid).

## Arquitetura

| Componente | Descrição |
|------------|-----------|
| **Janela** | 6 horas (21.600 segundos) |
| **Derivação** | HKDF-SHA384 (salt = epoch, info = "pulso-api-key-v1") |
| **Assinatura** | HS384 (SHA-384 resiste a Grover) |
| **Double-buffer** | current + previous key aceitas durante grace period |
| **Clock skew** | ±5 min tolerância |

## Fluxo

1. **Emissão de token**: usa chave atual, inclui `kid` no header JWT.
2. **Validação**: extrai `kid`, busca chave correspondente; se não achar, tenta current e previous.
3. **Rotação**: a cada 6h, `previous = current`, `current = nova_chave`.

## Comportamento

- **Operações longas**: tokens emitidos na janela anterior continuam válidos por até 6h após a rotação.
- **Múltiplas instâncias**: KeyRing deriva chaves deterministicamente por epoch; sem estado compartilhado necessário.
- **Deploy/restart**: chaves são recalculadas a partir do epoch atual.

## Dependências

- `cryptography>=42.0.0` (HKDF-SHA384)
- Fallback: HKDF manual com `hashlib` e `hmac` se `cryptography` não disponível

## Segurança

- Lista de palavras: tratar como material sensível (env/KMS).
- Não usar as palavras diretamente como chave; sempre derivar via HKDF.
- SHA-384 oferece margem contra ataques de Grover (criptografia pós-quântica).

## Recomendações para aumentar a segurança

| Medida | Descrição |
|--------|-----------|
| **Mais palavras** | Use 100+ palavras únicas. Mais entropia na escolha por janela. |
| **Evitar duplicatas** | Cada palavra deve aparecer uma vez. Duplicatas não aumentam a entropia. |
| **Palavras embaralhadas** | Ex.: `ãçudorop` em vez de `coração`. Desativa ataques por dicionário. |
| **Secret manager** | Em produção, use AWS Secrets Manager, HashiCorp Vault ou similar em vez de `.env` em plain text. |
| **`.env` fora do Git** | Garanta que `.env` está no `.gitignore` e nunca comite a lista. |
| **KEY_RING_DEBUG=0** | Em produção, desative o log da palavra (segurança por obscuridade adicional). |
| **Rotação mais curta** | Para dados sensíveis, considere janela de 6h (alterar `WINDOW_SECONDS` no código). |
| **HSTS + HTTPS** | Sempre use HTTPS em produção para proteger tokens em trânsito. |
