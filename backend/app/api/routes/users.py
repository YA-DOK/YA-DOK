
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.profile import Profile
from app.schemas.profile import ProfileResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Get the authenticated user's profile
    profile = db.get(Profile, UUID(current_user["id"]))

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return ProfileResponse(
        id=profile.id,
        email=current_user["email"],
        full_name=profile.full_name,
        avatar_url=profile.avatar_url,
        role=profile.role,
        created_at=profile.created_at,
    )
