#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Invite Router❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from fastapi import APIRouter, Depends
from typing import Dict, Any

from services.profile.profile_invite_service import (
    invite_user_to_profile,
    accept_profile_invite,
)
from services.profile.profile_authorization_service import (
    ensure_user_has_role,
)
# profile está em api/app/storage/database/profile/ (compartilhado)
try:
    from storage.database.profile.database_profile_members import list_members_by_profile
except ImportError:
    from app.storage.database.profile.database_profile_members import list_members_by_profile

from utils.login import get_current_user  # retorna user com _id e email

router = APIRouter(tags=["Profiles - Invites"])

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Invite User to Profile❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

@router.post("/{profile_id}/invite")
async def invite_user(
    profile_id: str,
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Invite a user to a profile by email.
    Required role: admin
    """

    await ensure_user_has_role(
        profile_id=profile_id,
        user_id=current_user["_id"],
        required_role="admin",
    )

    return await invite_user_to_profile(
        profile_id=profile_id,
        email=payload["email"],
        role=payload.get("role", "viewer"),
        invited_by_user_id=current_user["_id"],
    )

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Accept Invite❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

@router.post("/{profile_id}/accept-invite")
async def accept_invite(
    profile_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Accept an invite for the authenticated user.
    """

    return await accept_profile_invite(
        profile_id=profile_id,
        user_id=current_user["_id"],
        email=current_user["email"],
    )

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮List Profile Members❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

@router.get("/{profile_id}/members")
async def list_members(
    profile_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List all members of a profile.
    Required role: viewer
    """

    await ensure_user_has_role(
        profile_id=profile_id,
        user_id=current_user["_id"],
        required_role="viewer",
    )

    return {
        "members": await list_members_by_profile(profile_id)
    }
