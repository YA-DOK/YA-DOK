"""Admin catalogue, including unpublished versions, with safe metadata only.

No private blueprint, patient details, investigations or ground_truth in responses.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.cases import require_admin
from app.core.database import get_db
from app.models.case import CaseVersion, ClinicalCase
from app.models.case_review import CaseReviewApproval
from app.schemas.case_blueprint import CaseBlueprintV32, publication_issues
from app.services.case_lifecycle import _public_metadata_issues
from app.services.case_review import blueprint_hash

router = APIRouter(prefix="/admin/cases", tags=["Case Management (Admin)"], dependencies=[Depends(require_admin)])


class AdminVersionSummary(BaseModel):
    version_number: int
    created_at: str | None = None
    is_published: bool
    has_clinical_approval: bool
    publication_blocker_count: int
    review_status: str


class AdminCaseSummary(BaseModel):
    case_id: str
    title: str | None = None
    short_brief: str | None = None
    specialty: str | None = None
    difficulty: str | None = None
    status: str
    latest_version_number: int | None
    published_version_number: int | None
    versions: list[AdminVersionSummary]


class AdminCasePage(BaseModel):
    items: list[AdminCaseSummary]
    limit: int
    offset: int
    has_more: bool


def _view(db: Session, case: ClinicalCase) -> AdminCaseSummary:
    versions = db.scalars(select(CaseVersion).where(CaseVersion.case_id == case.id).order_by(CaseVersion.version_number.desc()).limit(100)).all()
    # A case version never changes; review evidence is bound to its exact digest.
    review_lookup = {}
    if versions:
        reviews = db.scalars(select(CaseReviewApproval).where(CaseReviewApproval.case_version_id.in_([v.id for v in versions]))).all()
        review_lookup = {str(r.case_version_id): r for r in reviews}
    version_views = []
    for ver in versions:
        try:
            bp = CaseBlueprintV32.model_validate(ver.blueprint)
            issues = publication_issues(bp) + _public_metadata_issues(bp)
        except Exception:
            bp = None
            issues = ["Blueprint validation failed"]
        audit = review_lookup.get(str(ver.id))
        reviewed = bool(audit and audit.blueprint_sha256 == blueprint_hash(ver.blueprint))
        # A valid approved JSON is still not publishable without independent audit evidence.
        blockers = len(issues) + (0 if reviewed else 1)
        version_views.append(AdminVersionSummary(
            version_number=ver.version_number,
            created_at=ver.created_at.isoformat() if ver.created_at else None,
            is_published=case.published_version_number == ver.version_number and case.archived_at is None and ver.published_at is not None,
            has_clinical_approval=reviewed,
            publication_blocker_count=blockers,
            review_status=bp.meta.review_status if bp else "invalid",
        ))
    latest = versions[0] if versions else None
    safe_meta = (latest.blueprint or {}).get("meta", {}) if latest else {}
    return AdminCaseSummary(
        case_id=case.case_code,
        title=safe_meta.get("title") if isinstance(safe_meta, dict) else None,
        short_brief=safe_meta.get("short_brief") if isinstance(safe_meta, dict) else None,
        specialty=safe_meta.get("specialty") if isinstance(safe_meta, dict) else None,
        difficulty=safe_meta.get("difficulty") if isinstance(safe_meta, dict) else None,
        status="archived" if case.archived_at else "published" if case.published_version_number else "draft",
        latest_version_number=latest.version_number if latest else None,
        published_version_number=case.published_version_number,
        versions=version_views,
    )


@router.get("", response_model=AdminCasePage)
def list_admin_cases(db: Annotated[Session, Depends(get_db)],
                     limit: Annotated[int, Query(ge=1, le=50)] = 20,
                     offset: Annotated[int, Query(ge=0, le=10000)] = 0):
    cases = db.scalars(select(ClinicalCase).order_by(ClinicalCase.created_at.desc(), ClinicalCase.case_code).limit(limit+1).offset(offset)).all()
    return AdminCasePage(items=[_view(db, c) for c in cases[:limit]], limit=limit,
                         offset=offset, has_more=len(cases) > limit)


@router.get("/{case_code}", response_model=AdminCaseSummary)
def get_admin_case(case_code: str, db: Annotated[Session, Depends(get_db)]):
    case = db.scalar(select(ClinicalCase).where(ClinicalCase.case_code == case_code))
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return _view(db, case)
