
from enum import Enum

from pydantic import BaseModel, Field


class InvestigationCategory(str, Enum):
    GENERAL = "general"
    SYSTEM = "system"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    URINALYSIS = "urinalysis"
    MICROBIOLOGY = "microbiology"
    HORMONES = "hormones"
    CARDIAC = "cardiac"
    OTHER = "other"


class InvestigationStatus(str, Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"


class InvestigationItem(BaseModel):
    id: str
    name: str
    category: InvestigationCategory
    description: str | None = None
    subcategory: str | None = None


class InvestigationRequest(BaseModel):
    investigation_id: str = Field(min_length=1)


class ResultMeasurement(BaseModel):
    name: str
    value: str
    unit: str | None = None
    reference_range: str | None = None


class InvestigationResult(BaseModel):
    investigation_id: str
    status: InvestigationStatus
    findings: str | None = None
    measurements: list[ResultMeasurement] = Field(default_factory=list)
    image_url: str | None = None
    report_url: str | None = None
    release_time: str | None = None


class InvestigationResponse(BaseModel):
    message: str
    result: InvestigationResult
