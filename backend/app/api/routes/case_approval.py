"""Clinical approval intake: authenticated ADMIN and independently verified reviewer only."""
from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.cases import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.case_blueprint import CaseBlueprintV32
from app.services.case_lifecycle import CaseArchived, CaseNotFound, PublicationBlocked
from app.services.case_review import approve_new_snapshot, clinician_is_allowed

router = APIRouter(prefix="/admin/cases", tags=["Case Management (Admin)"], dependencies=[Depends(require_admin)])


class ClinicalApprovalRequest(BaseModel):
    blueprint: CaseBlueprintV32
    evidence_reference: str = Field(min_length=8, max_length=500, description="Internal reference to clinician-signed review documentation; do not include patient identifiers")
    medical_accuracy_confirmed: Literal[True]
    privacy_review_confirmed: Literal[True]
    source_review_confirmed: Literal[True]


class ApprovalResponse(BaseModel):
    case_id: str
    version_number: int
    status: Literal["approved_pending_publication"]
    unchanged: bool


@router.post("/{case_code}/approve", response_model=ApprovalResponse, status_code=201)
def approve_case(
    case_code: str,
    request: ClinicalApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    reviewer_id = current_user.get("id", "")
    if not clinician_is_allowed(reviewer_id, settings.clinical_reviewer_user_ids):
        raise HTTPException(status_code=403, detail="Verified clinical reviewer access required")
    try:
        uid = UUID(reviewer_id)
        result = approve_new_snapshot(db, case_code, request.blueprint, uid, request.evidence_reference)
        db.commit()
        return ApprovalResponse(**result.__dict__)
    except CaseNotFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="Case not found") from None
    except CaseArchived:
        db.rollback()
        raise HTTPException(status_code=409, detail="Restore archived case first") from None
    except PublicationBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"message": "Approval blocked: correct content/review issues", "blocker_count": len(exc.issues)}) from None
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Concurrent review conflict; reload and retry") from None
    except Exception:
        db.rollback()
        raise
