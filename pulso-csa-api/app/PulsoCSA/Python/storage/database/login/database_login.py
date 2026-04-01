#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Login Database❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
import anyio
import os
import time
import threading
from typing import Optional, Dict, Any, List
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError
# database_core está em api/app/storage/database/ (compartilhado)
try:
    from storage.database.database_core import get_collection
except ImportError:
    # Fallback: importar de app se storage não estiver no path
    from app.storage.database.database_core import get_collection
from utils.log_manager import add_log

SOURCE = "database_login"

# Single collection for all auth (google + local)
users_collection = get_collection("login")

# Profiles collection
profiles_collection = get_collection("profiles")

# Token blacklist collection
blacklist_collection = get_collection("token_blacklist")

# Password reset tokens collection
reset_tokens_collection = get_collection("password_reset_tokens")

# Ensure unique index on email (case-insensitive)
try:
    # Normaliza email para lowercase no índice para evitar duplicatas case-sensitive
    users_collection.create_index("email", unique=True)
except Exception:
    pass

# Remove id_requisicao index if it exists (login collection doesn't use this field)
try:
    indexes = list(users_collection.list_indexes())
    for index in indexes:
        if "id_requisicao" in index.get("key", {}):
            users_collection.drop_index(index["name"])
except Exception:
    pass

# Remove id_requisicao index from profiles collection if it exists
try:
    indexes = list(profiles_collection.list_indexes())
    for index in indexes:
        index_key = index.get("key", {})
        if "id_requisicao" in index_key:
            try:
                profiles_collection.drop_index(index["name"])
            except Exception as e:
                # Tenta remover pelo nome do campo se o nome do índice falhar
                try:
                    profiles_collection.drop_index([("id_requisicao", 1)])
                except Exception:
                    pass
except Exception:
    pass

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Async wrappers (pymongo → async)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
async def _run_sync(fn, *args, **kwargs):
    """Run blocking pymongo calls without blocking the event loop."""
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Google Auth persistence❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
async def save_user_google(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save a Google user, normalizing email to lowercase."""
    # Normaliza email para lowercase
    email = user_data.get("email", "").lower().strip()
    doc = {
        "name": user_data.get("name"),
        "email": email,
        "picture": user_data.get("picture"),
    }
    try:
        result = await _run_sync(users_collection.insert_one, doc)
        doc["_id"] = str(result.inserted_id)
        return doc
    except DuplicateKeyError:
        # Usuário já existe (pode acontecer em race conditions)
        raise ValueError("E-mail já cadastrado")

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Local Auth persistence❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
async def save_user_local(name: str, email: str, password_hash: str) -> Dict[str, Any]:
    """Save a local user, normalizing email to lowercase."""
    # Normaliza email para lowercase para evitar duplicatas
    email_normalized = email.lower().strip()
    add_log("info", f"save_user_local | email={email_normalized}", SOURCE)
    doc = {"name": name, "email": email_normalized, "password_hash": password_hash}
    try:
        result = await _run_sync(users_collection.insert_one, doc)
        add_log("info", f"save_user_local | insert_one sucesso | id={result.inserted_id}", SOURCE)
        doc["_id"] = str(result.inserted_id)
        return doc
    except DuplicateKeyError as e:
        add_log("warn", f"save_user_local | DuplicateKeyError: {e}", SOURCE)
        # Proteção contra race condition - se dois requests tentarem criar o mesmo usuário simultaneamente
        raise ValueError("E-mail já cadastrado")

# Cache get_user_by_email (60s TTL) — reduz reads Mongo em auth (15–25% economia)
_USER_CACHE: Dict[str, tuple] = {}  # {email: (ts, user)}
try:
    _USER_CACHE_TTL = int(os.getenv("USER_CACHE_TTL_SEC", "60"))
except Exception:
    _USER_CACHE_TTL = 60
_USER_CACHE_LOCK = threading.Lock()

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email, normalizing to lowercase. Cache 60s para reduzir reads Mongo."""
    email_normalized = email.lower().strip()
    add_log("info", f"get_user_by_email | email={email_normalized}", SOURCE)
    now = time.monotonic()
    with _USER_CACHE_LOCK:
        if email_normalized in _USER_CACHE:
            ts, user = _USER_CACHE[email_normalized]
            if now - ts < _USER_CACHE_TTL:
                return user.copy() if user else None
            del _USER_CACHE[email_normalized]
    try:
        user = await _run_sync(users_collection.find_one, {"email": email_normalized})
    except Exception as e:
        add_log("error", f"get_user_by_email | find_one EXCEÇÃO: {type(e).__name__}: {e}", SOURCE)
        raise
    if not user:
        add_log("info", f"get_user_by_email | usuário não encontrado | email={email_normalized}", SOURCE)
        return None
    user["_id"] = str(user["_id"])
    add_log("info", f"get_user_by_email | usuário encontrado | id={user['_id']}", SOURCE)
    with _USER_CACHE_LOCK:
        _USER_CACHE[email_normalized] = (now, user.copy())
    return user

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Database❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

def _to_iso_date(val: Any) -> str:
    """Converte valor para ISO 8601 (YYYY-MM-DDTHH:mm:ss.sssZ) compatível com JavaScript Date."""
    if val is None:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if isinstance(val, datetime):
        ms = int(val.microsecond / 1000)
        return val.strftime(f"%Y-%m-%dT%H:%M:%S.{ms:03d}Z")
    if isinstance(val, (int, float)):
        try:
            return datetime.utcfromtimestamp(val).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except (ValueError, OSError):
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if isinstance(val, str) and val:
        if val.endswith("Z") or "+" in val[-6:] or "T" in val:
            return val
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")


async def create_profile(user_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Create a new profile in MongoDB."""
    now = datetime.utcnow()
    doc = {
        "userId": user_id,
        "name": name,
        "description": description,
        "createdAt": now,
        "updatedAt": now
    }
    result = await _run_sync(profiles_collection.insert_one, doc)
    doc["_id"] = str(result.inserted_id)
    doc["id"] = doc["_id"]
    doc["createdAt"] = _to_iso_date(now)
    doc["updatedAt"] = _to_iso_date(now)
    return doc

async def get_profile_by_id(profile_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get a profile by ID, validating it belongs to the user."""
    if not profile_id or not ObjectId.is_valid(profile_id):
        return None
    try:
        profile = await _run_sync(
            profiles_collection.find_one,
            {"_id": ObjectId(profile_id), "userId": user_id}
        )
        if not profile:
            return None
        profile["_id"] = str(profile["_id"])
        profile["id"] = profile["_id"]
        profile["createdAt"] = _to_iso_date(profile.get("createdAt") or profile.get("created_at"))
        profile["updatedAt"] = _to_iso_date(profile.get("updatedAt") or profile.get("updated_at"))
        return profile
    except Exception:
        return None

async def get_profiles_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Get all profiles for a user, ordered by creation date (newest first)."""
    def _get_profiles():
        profiles = list(profiles_collection.find({"userId": user_id}).sort("createdAt", -1))
        result = []
        for profile in profiles:
            profile["_id"] = str(profile["_id"])
            profile["id"] = profile["_id"]
            profile["createdAt"] = _to_iso_date(profile.get("createdAt") or profile.get("created_at"))
            profile["updatedAt"] = _to_iso_date(profile.get("updatedAt") or profile.get("updated_at"))
            result.append(profile)
        return result
    
    return await _run_sync(_get_profiles)

async def count_profiles_by_user(user_id: str) -> int:
    """Count how many profiles a user has."""
    count = await _run_sync(profiles_collection.count_documents, {"userId": user_id})
    return count

async def update_profile(profile_id: str, user_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update a profile, validating it belongs to the user."""
    if not profile_id or not ObjectId.is_valid(profile_id):
        return None
    try:
        update_data = {"updatedAt": datetime.utcnow()}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        
        result = await _run_sync(
            profiles_collection.find_one_and_update,
            {"_id": ObjectId(profile_id), "userId": user_id},
            {"$set": update_data},
            return_document=True
        )
        
        if not result:
            return None
        
        result["_id"] = str(result["_id"])
        result["id"] = result["_id"]
        result["createdAt"] = _to_iso_date(result.get("createdAt") or result.get("created_at"))
        result["updatedAt"] = _to_iso_date(result.get("updatedAt") or result.get("updated_at"))
        return result
    except Exception:
        return None

async def delete_profile(profile_id: str, user_id: str) -> bool:
    """Delete a profile, validating it belongs to the user."""
    if not profile_id or not ObjectId.is_valid(profile_id):
        return False
    try:
        result = await _run_sync(
            profiles_collection.delete_one,
            {"_id": ObjectId(profile_id), "userId": user_id}
        )
        return result.deleted_count > 0
    except Exception:
        return False

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Token Blacklist❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def add_token_to_blacklist(token: str, expires_at: datetime) -> bool:
    """Add a token to the blacklist."""
    try:
        doc = {
            "token": token,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        await _run_sync(blacklist_collection.insert_one, doc)
        return True
    except Exception:
        return False

async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is in the blacklist."""
    try:
        result = await _run_sync(
            blacklist_collection.find_one,
            {"token": token}
        )
        return result is not None
    except Exception:
        return False

async def cleanup_expired_blacklist_tokens():
    """Remove expired tokens from blacklist."""
    try:
        await _run_sync(
            blacklist_collection.delete_many,
            {"expires_at": {"$lt": datetime.utcnow()}}
        )
    except Exception:
        pass

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Password Reset❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def save_password_reset_token(email: str, token: str, expires_at: datetime) -> bool:
    """Save a password reset token."""
    try:
        # Remove any existing tokens for this email
        await _run_sync(
            reset_tokens_collection.delete_many,
            {"email": email}
        )
        doc = {
            "email": email,
            "token": token,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "used": False
        }
        await _run_sync(reset_tokens_collection.insert_one, doc)
        return True
    except Exception:
        return False

async def get_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """Get a password reset token if valid."""
    try:
        reset_token = await _run_sync(
            reset_tokens_collection.find_one,
            {"token": token, "used": False}
        )
        if not reset_token:
            return None
        
        # Check if expired
        if reset_token["expires_at"] < datetime.utcnow():
            return None
        
        return reset_token
    except Exception:
        return None

async def mark_password_reset_token_as_used(token: str) -> bool:
    """Mark a password reset token as used."""
    try:
        result = await _run_sync(
            reset_tokens_collection.update_one,
            {"token": token},
            {"$set": {"used": True}}
        )
        return result.modified_count > 0
    except Exception:
        return False

async def update_user_password(email: str, new_password_hash: str) -> bool:
    """Update user password."""
    try:
        result = await _run_sync(
            users_collection.update_one,
            {"email": email},
            {"$set": {"password_hash": new_password_hash}}
        )
        return result.modified_count > 0
    except Exception:
        return False


async def update_user(
    email: str,
    name: Optional[str] = None,
    new_email: Optional[str] = None,
    picture: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Atualiza nome, email e/ou picture do usuário. Retorna o doc atualizado ou None."""
    email_normalized = email.lower().strip()
    user = await _run_sync(users_collection.find_one, {"email": email_normalized})
    if not user:
        return None
    update_data = {}
    if name is not None:
        update_data["name"] = name.strip()
    if new_email is not None:
        new_email_norm = new_email.lower().strip()
        if new_email_norm != email_normalized:
            existing = await _run_sync(users_collection.find_one, {"email": new_email_norm})
            if existing:
                raise ValueError("E-mail já está em uso por outra conta")
            update_data["email"] = new_email_norm
    if picture is not None:
        update_data["picture"] = picture.strip() or None
    if not update_data:
        return user
    result = await _run_sync(
        users_collection.update_one,
        {"email": email_normalized},
        {"$set": update_data},
    )
    if result.modified_count == 0:
        return user
    updated = await _run_sync(users_collection.find_one, {"_id": user["_id"]})
    if updated:
        updated["_id"] = str(updated["_id"])
        with _USER_CACHE_LOCK:
            _USER_CACHE.pop(email_normalized, None)
            if "email" in update_data:
                _USER_CACHE.pop(update_data["email"], None)
    return updated