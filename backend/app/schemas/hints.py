
from pydantic import BaseModel, Field


class HintResponse(BaseModel):
    allowed: bool

    hint_level: int | None = Field(
        default=None,
        ge=1,
        le=3
    )

    hint: str | None = None

    remaining_hints: int | None = Field(
        default=None,
        ge=0
    )

    reason: str | None = None
