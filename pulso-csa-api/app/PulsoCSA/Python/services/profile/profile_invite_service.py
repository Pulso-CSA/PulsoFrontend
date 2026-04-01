#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Invite Service❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Dict, Any
from datetime import datetime
from fastapi import HTTPException

from storage.database.login.database_login import get_user_by_email
# profile está em api/app/storage/database/profile/ (compartilhado)
try:
    from storage.database.profile.database_profile_members import (
        add_profile_member,
        get_member_by_profile_and_user,
    )
except ImportError:
    from app.storage.database.profile.database_profile_members import (
        add_profile_member,
        get_member_by_profile_and_user,
    )
try:
    from storage.database.profile.database_profile_invites import (
        create_profile_invite,
        get_invite_by_profile_and_email,
        delete_profile_invite,
    )
except ImportError:
    from app.storage.database.profile.database_profile_invites import (
        create_profile_invite,
        get_invite_by_profile_and_email,
        delete_profile_invite,
    )

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Invite User by Email❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def invite_user_to_profile(
    *,
    profile_id: str,
    email: str,
    role: str,
    invited_by_user_id: str,
) -> Dict[str, Any]:
    """
    Invite a user to a profile by email.

    If the user already exists, the invitation is immediately
    converted into a profile membership.
    """

    email_normalized = email.lower().strip()

    # 1️⃣ Check if user already exists
    user = await get_user_by_email(email_normalized)

    if user:
        user_id = user["_id"]

        # 2️⃣ Check if user is already a member
        existing_member = await get_member_by_profile_and_user(
            profile_id=profile_id,
            user_id=user_id,
        )
        if existing_member:
            raise HTTPException(
                status_code=400,
                detail="User is already a member of this profile",
            )

        # 3️⃣ Add directly as member
        member = await add_profile_member(
            profile_id=profile_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by_user_id,
        )

        return {
            "status": "member_added",
            "member": member,
        }

    # 4️⃣ User does not exist → check for existing invite
    existing_invite = await get_invite_by_profile_and_email(
        profile_id=profile_id,
        email=email_normalized,
    )

    if existing_invite:
        raise HTTPException(
            status_code=400,
            detail="An invitation for this email already exists",
        )

    # 5️⃣ Create invitation
    invite = await create_profile_invite(
        profile_id=profile_id,
        email=email_normalized,
        role=role,
        invited_by=invited_by_user_id,
    )

    return {
        "status": "invite_created",
        "invite": invite,
    }

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Accept Invite❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def accept_profile_invite(
    *,
    profile_id: str,
    user_id: str,
    email: str,
) -> Dict[str, Any]:
    """
    Accept a profile invitation.

    Converts an existing invite into a profile membership.
    """

    email_normalized = email.lower().strip()

    # 1️⃣ Get invite
    invite = await get_invite_by_profile_and_email(
        profile_id=profile_id,
        email=email_normalized,
    )

    if not invite:
        raise HTTPException(
            status_code=404,
            detail="Invitation not found",
        )

    # 2️⃣ Check if already a member (safety)
    existing_member = await get_member_by_profile_and_user(
        profile_id=profile_id,
        user_id=user_id,
    )
    if existing_member:
        raise HTTPException(
            status_code=400,
            detail="User is already a member of this profile",
        )

    # 3️⃣ Add member
    member = await add_profile_member(
        profile_id=profile_id,
        user_id=user_id,
        role=invite["role"],
        invited_by=invite.get("invitedBy"),
    )

    # 4️⃣ Remove invite
    await delete_profile_invite(
        profile_id=profile_id,
        email=email_normalized,
    )

    return {
        "status": "invite_accepted",
        "member": member,
    }
