"""Admin-only publish/archive/restore endpoints, with no direct DB access by clients."""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.cases import require_admin
from app.core.database import get_db
from app.services.case_lifecycle import (
    CaseArchived,
    CaseNotFound,
    LifecycleResult,
    PublicationBlocked,
    VersionNotFound,
    archive_case,
    publish_case_version,
    restore_case,
)

router = APIRouter(
    prefix="/admin/cases",
    tags=["Case Management (Admin)"],
    dependencies=[Depends(require_admin)],
)


class CaseLifecycleResponse(BaseModel):
    case_id: str
    status: Literal["draft", "published", "archived"]
    published_version_number: int | None
    unchanged: bool


def _apply(db: Session, action) -> CaseLifecycleResponse:
    try:
        result: LifecycleResult = action()
        db.commit()
    except CaseNotFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="Case not found") from None
    except VersionNotFound:
        db.rollback()
        raise HTTPException(status_code=404, detail="Case version not found") from None
    except CaseArchived:
        db.rollback()
        raise HTTPException(status_code=409, detail="Restore archived case before publishing") from None
    except PublicationBlocked as exc:
        db.rollback()
        # Never expose private medical contents in error details.
        raise HTTPException(
            status_code=409,
            detail={"message": "Publication blocked: resolve review issues first", "blocker_count": len(exc.issues)},
        ) from None
    except Exception:
        db.rollback()
        raise
    return CaseLifecycleResponse.model_validate(result.__dict__)


@router.post("/{case_code}/versions/{version_number}/publish", response_model=CaseLifecycleResponse)
def publish(
    case_code: str,
    version_number: int,
    db: Annotated[Session, Depends(get_db)],
):
    if version_number < 1:
        raise HTTPException(status_code=422, detail="version_number must be >= 1")
    return _apply(db, lambda: publish_case_version(db, case_code, version_number))


@router.post("/{case_code}/archive", response_model=CaseLifecycleResponse)
def archive(case_code: str, db: Annotated[Session, Depends(get_db)]):
    return _apply(db, lambda: archive_case(db, case_code))


@router.post("/{case_code}/restore", response_model=CaseLifecycleResponse)
def restore(case_code: str, db: Annotated[Session, Depends(get_db)]):
    return _apply(db, lambda: restore_case(db, case_code))
