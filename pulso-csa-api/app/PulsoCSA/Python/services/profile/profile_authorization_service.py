#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Profile Authorization Service (RBAC)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

from typing import Literal
from fastapi import HTTPException

# profile está em api/app/storage/database/profile/ (compartilhado)
try:
    from storage.database.profile.database_profile_members import (
        get_member_by_profile_and_user,
        list_members_by_profile,
    )
except ImportError:
    from app.storage.database.profile.database_profile_members import (
        get_member_by_profile_and_user,
        list_members_by_profile,
    )

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Tipos e Hierarquia de Roles❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

Role = Literal["owner", "admin", "editor", "viewer"]

ROLE_HIERARCHY: dict[Role, int] = {
    "owner": 4,
    "admin": 3,
    "editor": 2,
    "viewer": 1,
}

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Core Authorization❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def ensure_user_has_role(
    *,
    profile_id: str,
    user_id: str,
    required_role: Role,
) -> None:
    """
    Ensure that a user has at least the required role in a profile.

    Raises HTTPException(403) if access is denied.
    """

    member = await get_member_by_profile_and_user(
        profile_id=profile_id,
        user_id=user_id,
    )

    if not member:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of this profile",
        )

    user_role = member.get("role")

    if user_role not in ROLE_HIERARCHY:
        raise HTTPException(
            status_code=403,
            detail="Invalid role assigned to user",
        )

    if ROLE_HIERARCHY[user_role] < ROLE_HIERARCHY[required_role]:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions for this action",
        )

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Ownership Guards❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def ensure_user_is_owner(
    *,
    profile_id: str,
    user_id: str,
) -> None:
    """
    Ensure that the user is the owner of the profile.
    """

    await ensure_user_has_role(
        profile_id=profile_id,
        user_id=user_id,
        required_role="owner",
    )

async def ensure_not_last_owner(
    *,
    profile_id: str,
    user_id: str,
) -> None:
    """
    Prevent removal or downgrade of the last owner of a profile.
    """

    members = await list_members_by_profile(profile_id)

    owners = [
        member for member in members
        if member.get("role") == "owner"
    ]

    if len(owners) == 1 and owners[0]["userId"] == user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove or downgrade the last owner of the profile",
        )

#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━
#━━━━━━━━━❮Convenience Checks (Optional)❯━━━━━━━━━
#━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━

async def can_user_access_profile(
    *,
    profile_id: str,
    user_id: str,
) -> bool:
    """
    Check if the user is a member of the profile.
    """
    member = await get_member_by_profile_and_user(
        profile_id=profile_id,
        user_id=user_id,
    )
    return member is not None
