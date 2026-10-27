
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/me")
async def get_me(
    user: Annotated[dict, Depends(get_current_user)],
):
    return user
