from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

Difficulty = Literal["beginner", "intermediate", "advanced"]
Status = Literal["draft", "review", "published", "archived"]

class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=3, max_length=200)
    specialty: str | None = None
    difficulty: Difficulty | None = None
    blueprint_data: dict[str, Any]
    version_number: str = "1.0"
    status: Status = "draft"
    xray_path: str | None = None

class StatusUpdate(BaseModel):
    status: Status
