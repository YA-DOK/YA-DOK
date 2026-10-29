
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check configuration without printing any secret values.
    if not settings.supabase_url or not settings.supabase_key:
        print(
            "SUPABASE CONFIG ERROR:",
            f"URL configured={bool(settings.supabase_url)},",
            f"key configured={bool(settings.supabase_key)}",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication configuration is incomplete",
        )

    token = credentials.credentials
    auth_url = (
        f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                auth_url,
                headers={
                    "apikey": settings.supabase_key,
                    "Authorization": f"Bearer {token}",
                },
            )

    except httpx.RequestError as exc:
        # Log the exception type, never the access token or API key.
        print(
            "SUPABASE CONNECTION ERROR:",
            type(exc).__name__,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from None

    print("SUPABASE AUTH HTTP STATUS:", response.status_code)

    if response.status_code != 200:
        if response.status_code >= 500:
            print(
                "SUPABASE SERVER RESPONSE:",
                response.text[:500],
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = response.json()

    if not user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    return {
        "id": user["id"],
        "email": user.get("email"),
    }
