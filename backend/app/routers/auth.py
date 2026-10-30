
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

from ..config import SUPABASE_URL, SUPABASE_ANON_KEY

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginRequest):

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase configuration is missing"
        )

    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_ANON_KEY
        )

        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if not response.session:
            raise ValueError("No session returned")

        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "expires_in": response.session.expires_in
        }

    except Exception as e:
        print("\n========== SUPABASE LOGIN ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("==========================================\n")

        raise HTTPException(
            status_code=401,
            detail="Login failed. Check server terminal."
        )
