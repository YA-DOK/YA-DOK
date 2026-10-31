
from enum import Enum
from typing import Optional
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
    description: Optional[str] = None
    subcategory: Optional[str] = None


class InvestigationRequest(BaseModel):
    investigation_id: str = Field(min_length=1)


class ResultMeasurement(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None


class InvestigationResult(BaseModel):
    investigation_id: str
    status: InvestigationStatus
    findings: Optional[str] = None
    measurements: list[ResultMeasurement] = Field(default_factory=list)
    image_url: Optional[str] = None
    report_url: Optional[str] = None
    release_time: Optional[str] = None


class InvestigationResponse(BaseModel):
    message: str
    result: InvestigationResult
