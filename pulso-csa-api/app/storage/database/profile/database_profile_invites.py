#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Invites Database❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

import anyio
from typing import Optional, Dict, Any, List
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from app.storage.database.database_core import get_collection

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Coleção❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

profile_invites_collection = get_collection("profile_invites")

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Índices❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

try:
    profile_invites_collection.create_index(
        [("profileId", 1), ("email", 1)],
        unique=True
    )
    profile_invites_collection.create_index("email")
    profile_invites_collection.create_index("profileId")
except Exception:
    pass

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Async wrapper❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def _run_sync(fn, *args, **kwargs):
    """Run blocking pymongo calls without blocking the event loop."""
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮CRUD Operations❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def create_profile_invite(
    profile_id: str,
    email: str,
    role: str,
    invited_by: str
) -> Dict[str, Any]:
    """Create an invitation for a profile by email."""
    now = datetime.utcnow()
    email_normalized = email.lower().strip()

    doc = {
        "profileId": profile_id,
        "email": email_normalized,
        "role": role,
        "invitedBy": invited_by,
        "createdAt": now,
        "updatedAt": now,
    }

    try:
        result = await _run_sync(profile_invites_collection.insert_one, doc)
        doc["_id"] = str(result.inserted_id)
        doc["createdAt"] = now.isoformat()
        doc["updatedAt"] = now.isoformat()
        return doc
    except DuplicateKeyError:
        raise ValueError("Invite already exists for this email and profile")

async def get_invite_by_profile_and_email(
    profile_id: str,
    email: str
) -> Optional[Dict[str, Any]]:
    """Get an invite by profile and email."""
    email_normalized = email.lower().strip()
    invite = await _run_sync(
        profile_invites_collection.find_one,
        {"profileId": profile_id, "email": email_normalized}
    )
    if not invite:
        return None

    invite["_id"] = str(invite["_id"])
    invite["createdAt"] = invite["createdAt"].isoformat()
    invite["updatedAt"] = invite["updatedAt"].isoformat()
    return invite

async def list_invites_by_profile(profile_id: str) -> List[Dict[str, Any]]:
    """List all pending invites for a profile."""
    def _list():
        docs = list(profile_invites_collection.find({"profileId": profile_id}))
        result = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            doc["createdAt"] = doc["createdAt"].isoformat()
            doc["updatedAt"] = doc["updatedAt"].isoformat()
            result.append(doc)
        return result

    return await _run_sync(_list)

async def delete_profile_invite(profile_id: str, email: str) -> bool:
    """Delete a profile invite."""
    email_normalized = email.lower().strip()
    result = await _run_sync(
        profile_invites_collection.delete_one,
        {"profileId": profile_id, "email": email_normalized}
    )
    return result.deleted_count > 0
