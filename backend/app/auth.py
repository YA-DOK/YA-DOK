
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .db import get_supabase

security = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token"
        )

    token = credentials.credentials

    try:
        response = get_supabase().auth.get_user(token)
        user = response.user

        if not user:
            raise ValueError("No user found")

        return user

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Supabase token"
        )


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):
    user = current_user(credentials)

    metadata = user.app_metadata or {}

    if metadata.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required"
        )

    return user
