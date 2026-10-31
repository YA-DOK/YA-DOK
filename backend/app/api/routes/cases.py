"""Admin-only case ingestion. Read-only student routes will be added separately."""
from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.profile import Profile
from app.schemas.case_blueprint import CaseBlueprintV32, publication_issues
from app.services.case_import import import_case_draft

router = APIRouter(prefix="/admin/cases", tags=["Case Management (Admin)"])


class CaseImportResponse(BaseModel):
    case_id: str
    version_number: int
    status: Literal["draft", "published"]
    unchanged: bool
    publication_blocker_count: int


def require_admin(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Trust DB profile.role, never client-submitted role or JWT user_metadata."""
    try:
        user_id = UUID(current_user["id"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user") from None
    profile = db.get(Profile, user_id)
    if profile is None or profile.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.post(
    "/import",
    response_model=CaseImportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def import_draft(
    blueprint: CaseBlueprintV32,
    db: Annotated[Session, Depends(get_db)],
):
    """Accept v3.2 JSON body, create a draft version; no publishing performed."""
    if blueprint.meta.review_status != "draft":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Import requires meta.review_status='draft'; approval is a separate workflow",
        )
    try:
        result = import_case_draft(db, blueprint)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Concurrent import conflict; retry the request",
        ) from None
    except Exception:
        db.rollback()
        raise

    return CaseImportResponse(
        case_id=result.case_id,
        version_number=result.version_number,
        status=result.status,
        unchanged=result.unchanged,
        publication_blocker_count=len(publication_issues(blueprint)),
    )
