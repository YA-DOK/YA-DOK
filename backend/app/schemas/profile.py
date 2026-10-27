
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id: UUID
    email: str | None
    full_name: str | None
    avatar_url: str | None
    role: str
    created_at: datetime
