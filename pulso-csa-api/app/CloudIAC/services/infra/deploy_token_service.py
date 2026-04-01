#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Deploy Token – HMAC + expiração❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional

# Frase de confirmação obrigatória (modo ultra-seguro)
CONFIRM_PHRASE = "EU ENTENDO QUE ISTO CRIARÁ RECURSOS E CUSTOS"

TOKEN_EXPIRATION_SEC = int(os.getenv("INFRA_DEPLOY_TOKEN_EXPIRATION_SEC", "600"))


def _get_secret() -> str:
    secret = os.getenv("INFRA_DEPLOY_TOKEN_SECRET")
    if not secret:
        raise ValueError("INFRA_DEPLOY_TOKEN_SECRET não configurada no ambiente")
    return secret


def generate_deploy_token(
    tenant_id: str,
    id_requisicao: str,
    env: str,
    providers: list[str],
    repo_fingerprint: str,
    terraform_tree_hash: str,
) -> str:
    """
    Gera deploy_token com HMAC.
    Escopo: tenant_id, id_requisicao, env, providers, repo_fingerprint, terraform_tree_hash.
    Expiração: TOKEN_EXPIRATION_SEC (default 10 min).
    """
    payload = {
        "tenant_id": tenant_id,
        "id_requisicao": id_requisicao,
        "env": env,
        "providers": sorted(providers),
        "repo_fingerprint": repo_fingerprint,
        "terraform_tree_hash": terraform_tree_hash,
        "exp": int(time.time()) + TOKEN_EXPIRATION_SEC,
    }
    msg = json.dumps(payload, sort_keys=True)
    sig = hmac.new(
        _get_secret().encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    token_data = {"p": payload, "s": sig}
    return _b64_encode(json.dumps(token_data))


def validate_deploy_token(
    token: str,
    tenant_id: str,
    id_requisicao: str,
    repo_fingerprint: Optional[str] = None,
    terraform_tree_hash: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Valida deploy_token.
    Retorna (is_valid, error_message).
    """
    if not token:
        return False, "deploy_token ausente"
    try:
        raw = _b64_decode(token)
        data = json.loads(raw)
        payload = data.get("p")
        sig = data.get("s")
        if not payload or not sig:
            return False, "token inválido"
        if time.time() > payload.get("exp", 0):
            return False, "token expirado"
        if payload.get("tenant_id") != tenant_id:
            return False, "tenant_id não confere"
        if payload.get("id_requisicao") != id_requisicao:
            return False, "id_requisicao não confere"
        if repo_fingerprint and payload.get("repo_fingerprint") != repo_fingerprint:
            return False, "repo_fingerprint alterado; execute validate novamente"
        if terraform_tree_hash and payload.get("terraform_tree_hash") != terraform_tree_hash:
            return False, "terraform_tree_hash alterado; execute validate novamente"
        msg = json.dumps(payload, sort_keys=True)
        expected = hmac.new(
            _get_secret().encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False, "assinatura inválida"
        return True, None
    except Exception as e:
        return False, f"token inválido: {e}"


def validate_confirm_phrase(phrase: Optional[str]) -> bool:
    """Verifica se a frase de confirmação bate exatamente."""
    return phrase is not None and phrase.strip() == CONFIRM_PHRASE


def _b64_encode(s: str) -> str:
    import base64
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii").rstrip("=")


def _b64_decode(s: str) -> str:
    import base64
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s.encode("ascii")).decode("utf-8")
