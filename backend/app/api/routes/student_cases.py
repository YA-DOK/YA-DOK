"""Authenticated student case catalogue.

Only explicit, learner-safe metadata from a CURRENT published and unarchived
case version is returned. The private blueprint must never be serialized.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Integer, and_, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.case import CaseVersion, ClinicalCase

router = APIRouter(
    prefix="/cases",
    tags=["Case Library (Student)"],
    dependencies=[Depends(get_current_user)],
)


class StudentCaseSummary(BaseModel):
    """Never add ground_truth, exam, investigations or the full blueprint."""

    model_config = ConfigDict(extra="ignore")

    case_id: str
    version_number: int
    title: str | None = None
    subtitle: str | None = None
    short_brief: str | None = None
    specialty: str | None = None
    setting: str | None = None
    difficulty: str | None = None
    estimated_duration_minutes: int | None = None


class StudentCasePage(BaseModel):
    items: list[StudentCaseSummary]
    limit: int
    offset: int
    has_more: bool


def _meta_text(field: str):
    """Ask PostgreSQL only for an allowlisted public metadata field."""
    return func.jsonb_extract_path_text(CaseVersion.blueprint, "meta", field)


def _published_query():
    """Server-side publication boundary, never trust frontend filtering."""
    return (
        select(
            ClinicalCase.case_code.label("case_id"),
            CaseVersion.version_number.label("version_number"),
            _meta_text("title").label("title"),
            _meta_text("subtitle").label("subtitle"),
            _meta_text("short_brief").label("short_brief"),
            _meta_text("specialty").label("specialty"),
            _meta_text("setting").label("setting"),
            _meta_text("difficulty").label("difficulty"),
            # Missing metadata stays NULL instead of causing JSON parsing failures.
            func.jsonb_extract_path_text(
                CaseVersion.blueprint, "meta", "estimated_duration_minutes"
            ).cast(Integer).label("estimated_duration_minutes"),
        )
        .select_from(ClinicalCase)
        .join(
            CaseVersion,
            and_(
                CaseVersion.case_id == ClinicalCase.id,
                CaseVersion.version_number == ClinicalCase.published_version_number,
            ),
        )
        .where(
            ClinicalCase.archived_at.is_(None),
            ClinicalCase.published_version_number.is_not(None),
            CaseVersion.published_at.is_not(None),
        )
    )


@router.get("", response_model=StudentCasePage)
def list_student_cases(
    db: Annotated[Session, Depends(get_db)],
    specialty: Annotated[str | None, Query(max_length=100)] = None,
    difficulty: Annotated[str | None, Query(max_length=60)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    stmt = _published_query()
    if specialty:
        stmt = stmt.where(func.lower(_meta_text("specialty")) == specialty.strip().lower())
    if difficulty:
        stmt = stmt.where(func.lower(_meta_text("difficulty")) == difficulty.strip().lower())
    stmt = stmt.order_by(ClinicalCase.case_code).limit(limit + 1).offset(offset)
    rows = db.execute(stmt).mappings().all()
    return StudentCasePage(
        items=[StudentCaseSummary.model_validate(dict(row)) for row in rows[:limit]],
        limit=limit,
        offset=offset,
        has_more=len(rows) > limit,
    )


@router.get("/{case_code}", response_model=StudentCaseSummary)
def get_student_case(case_code: str, db: Annotated[Session, Depends(get_db)]):
    # The preview is public METADATA only; simulation content requires a session-scoped API.
    stmt = _published_query().where(ClinicalCase.case_code == case_code).limit(1)
    row = db.execute(stmt).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return StudentCaseSummary.model_validate(dict(row))
