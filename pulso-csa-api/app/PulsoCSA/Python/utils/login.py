import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
import jwt
import httpx
from requests_oauthlib import OAuth2Session

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# database_login está em PulsoCSA/Python/storage/database/login/
from storage.database.login.database_login import get_user_by_email


# ━━━━━━━━━❮Google OAuth❯━━━━━━━━━

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

# Singleton httpx.AsyncClient para reuso (evita criar conexão por request)
_httpx_client: Optional[httpx.AsyncClient] = None


def get_httpx_client() -> httpx.AsyncClient:
    """Retorna cliente httpx async singleton."""
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.AsyncClient(timeout=10.0)
    return _httpx_client


def get_google_auth(redirect_uri: Optional[str] = None) -> OAuth2Session:
    """Build OAuth2 client for Google flow."""
    return OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        redirect_uri=redirect_uri or REDIRECT_URI,
        scope=SCOPE,
    )


async def get_user_info(access_token: str) -> Dict[str, Any]:
    """Busca dados do usuário no Google (async, não bloqueia event loop)."""
    client = get_httpx_client()
    resp = await client.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        params={"access_token": access_token},
    )
    if resp.status_code != 200:
        raise Exception("Failed to fetch user info")
    return resp.json()


# ━━━━━━━━━❮JWT CONFIG❯━━━━━━━━━

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# HS384: pós-quântico (SHA-384 resiste a Grover). Usado quando KeyRing está ativo.
JWT_ALGORITHM_PQC = "HS384"

# Mantém o mesmo env que você já estava usando (segundos). Padrão: 12h = 43200s
JWT_EXPIRATION_SECONDS = int(os.getenv("JWT_EXPIRATION", "43200"))

# Chave rotativa: se KEY_SEED_WORDS definido, usa KeyRing (HKDF-SHA384 + double-buffer)
ROTATING_KEY_ENABLED = bool(os.getenv("KEY_SEED_WORDS", "").strip())

security = HTTPBearer()

# Validação suave: apenas avisa, não quebra o import
# A validação real acontece quando as funções são chamadas
if not JWT_SECRET and not ROTATING_KEY_ENABLED:
    import warnings
    warnings.warn("JWT_SECRET ou KEY_SEED_WORDS deve estar definido no ambiente. Autenticação pode falhar.", RuntimeWarning)


# ━━━━━━━━━❮JWT Functions (Chave Rotativa + PQC)❯━━━━━━━━━

def _get_signing_key_and_algo() -> tuple[str | bytes, str, dict]:
    """Retorna (key, algorithm, headers) para assinatura. KeyRing usa HS384 + kid."""
    if ROTATING_KEY_ENABLED:
        from core.security import get_key_ring
        key_id, key_bytes = get_key_ring().get_current_key()
        return key_bytes, JWT_ALGORITHM_PQC, {"kid": key_id}
    return (JWT_SECRET or "").encode() if isinstance(JWT_SECRET, str) else JWT_SECRET, JWT_ALGORITHM, {}


def create_jwt_token(data: Dict[str, Any]) -> str:
    """Create signed JWT token (HS384 + kid quando KeyRing ativo)."""
    now = datetime.utcnow()
    payload = {
        "exp": now + timedelta(seconds=JWT_EXPIRATION_SECONDS),
        "iat": now,
        "data": data,
    }
    key, algo, headers = _get_signing_key_and_algo()
    return jwt.encode(payload, key, algorithm=algo, headers=headers or None)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token with longer expiration (30 days)."""
    now = datetime.utcnow()
    payload = {
        "exp": now + timedelta(days=30),
        "iat": now,
        "type": "refresh",
        "data": data,
    }
    key, algo, headers = _get_signing_key_and_algo()
    return jwt.encode(payload, key, algorithm=algo, headers=headers or None)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Validate and decode JWT token.
    Se KeyRing ativo: valida com current ou previous key (grace period).
    Se legacy: valida com JWT_SECRET.
    """
    if ROTATING_KEY_ENABLED:
        from core.security import get_key_ring
        key_ring = get_key_ring()
        try:
            unverified = jwt.get_unverified_header(token)
            kid = unverified.get("kid")
            key_bytes = key_ring.get_key_by_id(kid) if kid else None
            if key_bytes is not None:
                return jwt.decode(token, key_bytes, algorithms=[JWT_ALGORITHM_PQC])
            for _kid, kbytes in key_ring.get_keys_for_validation():
                try:
                    return jwt.decode(token, kbytes, algorithms=[JWT_ALGORITHM_PQC])
                except jwt.InvalidTokenError:
                    continue
            raise jwt.InvalidTokenError("Nenhuma chave válida")
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
    # Legacy: JWT_SECRET + HS256
    try:
        key = JWT_SECRET
        if isinstance(key, str):
            key = key.encode()
        return jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Validate and decode refresh token (returns full payload)."""
    payload = verify_jwt_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não é um refresh token",
        )
    return payload


# ━━━━━━━━━❮FastAPI Dependency❯━━━━━━━━━

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    token = credentials.credentials
    payload = verify_jwt_token(token)

    user_data = payload.get("data")
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem dados do usuário",
        )

    user_id = user_data.get("id")
    email = user_data.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem email",
        )

    if user_id:
        return {"_id": user_id, "email": email, "name": user_data.get("name")}

    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida. Faça login novamente ou crie uma conta.",
        )

    return {"_id": user["_id"], "email": user["email"], "name": user.get("name")}


# ━━━━━━━━━❮Password Hashing❯━━━━━━━━━

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode(), salt).decode()


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), password_hash.encode())
    except Exception:
        return False


# ━━━━━━━━━❮Email Utils❯━━━━━━━━━

def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email. Returns True if sent successfully."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

        # Se não houver configuração SMTP, apenas loga (modo desenvolvimento)
        if not smtp_user or not smtp_password:
            print(f"[DEV MODE] Password reset token for {email}: {reset_token}")
            print(f"[DEV MODE] Reset URL: {frontend_url}/reset-password?token={reset_token}")
            return True

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = email
        msg["Subject"] = "Redefinição de Senha - PulsoAPI"

        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        body = f"""
Olá,

Você solicitou a redefinição de senha para sua conta PulsoAPI.

Clique no link abaixo para redefinir sua senha:
{reset_url}

Este link expira em 1 hora.

Se você não solicitou esta redefinição, ignore este email.

Atenciosamente,
Equipe PulsoAPI
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return True
