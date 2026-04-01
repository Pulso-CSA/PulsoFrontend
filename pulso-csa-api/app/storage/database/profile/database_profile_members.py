#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Members Database❯━━━━━━━━━
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

profile_members_collection = get_collection("profile_members")

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Índices❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

try:
    profile_members_collection.create_index(
        [("profileId", 1), ("userId", 1)],
        unique=True
    )
    profile_members_collection.create_index("profileId")
    profile_members_collection.create_index("userId")
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

async def add_profile_member(
    profile_id: str,
    user_id: str,
    role: str,
    invited_by: Optional[str] = None
) -> Dict[str, Any]:
    """Add a user as a member of a profile."""
    now = datetime.utcnow()
    doc = {
        "profileId": profile_id,
        "userId": user_id,
        "role": role,
        "invitedBy": invited_by,
        "createdAt": now,
        "updatedAt": now,
    }

    try:
        result = await _run_sync(profile_members_collection.insert_one, doc)
        doc["_id"] = str(result.inserted_id)
        doc["createdAt"] = now.isoformat()
        doc["updatedAt"] = now.isoformat()
        return doc
    except DuplicateKeyError:
        raise ValueError("User is already a member of this profile")

async def create_profile_member(
    profile_id: str,
    user_id: str,
    role: str,
    invited_by_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Minimal compatibility wrapper requested by callers.

    Inserts a document using snake_case keys and returns the created doc.
    """
    now = datetime.utcnow()
    doc = {
        "profile_id": profile_id,
        "user_id": user_id,
        "role": role,
        "status": "active",
        "invited_by_user_id": invited_by_user_id,
        "created_at": now,
    }

    await _run_sync(profile_members_collection.insert_one, doc)
    # Normalize returned timestamps to isoformat for consistency with other functions
    doc["created_at"] = now.isoformat()
    return doc

async def get_member_by_profile_and_user(
    profile_id: str,
    user_id: str
) -> Optional[Dict[str, Any]]:
    """Get a specific member of a profile."""
    member = await _run_sync(
        profile_members_collection.find_one,
        {"profileId": profile_id, "userId": user_id}
    )
    if not member:
        return None

    member["_id"] = str(member["_id"])
    member["createdAt"] = member["createdAt"].isoformat()
    member["updatedAt"] = member["updatedAt"].isoformat()
    return member

async def list_members_by_profile(profile_id: str) -> List[Dict[str, Any]]:
    """List all members of a profile."""
    def _list():
        docs = list(profile_members_collection.find({"profileId": profile_id}))
        result = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            doc["createdAt"] = doc["createdAt"].isoformat()
            doc["updatedAt"] = doc["updatedAt"].isoformat()
            result.append(doc)
        return result

    return await _run_sync(_list)

async def remove_profile_member(profile_id: str, user_id: str) -> bool:
    """Remove a user from a profile."""
    result = await _run_sync(
        profile_members_collection.delete_one,
        {"profileId": profile_id, "userId": user_id}
    )
    return result.deleted_count > 0
