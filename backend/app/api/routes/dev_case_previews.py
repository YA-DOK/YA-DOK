"""LOCAL DEVELOPMENT ONLY: authenticated read-only safe previews of draft metadata.

Never include private blueprints, ground truth, images from medical charts, or
patient information. This endpoint must never be enabled against cloud DBs.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.case import CaseVersion, ClinicalCase

router = APIRouter(prefix="/dev/cases", tags=["Local Draft Previews (Development Only)"], dependencies=[Depends(get_current_user)])


def _only_local_db() -> None:
    try:
        host = make_url(settings.database_url).host
    except Exception:  # noqa: BLE001
        host = None
    if settings.app_env != "local" or host not in ("localhost", "127.0.0.1", "::1"):
        raise HTTPException(status_code=404, detail="Not found")


def _meta(field: str):
    return func.jsonb_extract_path_text(CaseVersion.blueprint, "meta", field)


def _draft_query():
    latest = (select(CaseVersion.case_id.label("cid"), func.max(CaseVersion.version_number).label("v"))
              .group_by(CaseVersion.case_id).subquery())
    return (select(
        ClinicalCase.case_code.label("case_id"), CaseVersion.version_number.label("version_number"),
        _meta("title").label("title"), _meta("subtitle").label("subtitle"),
        _meta("short_brief").label("short_brief"), _meta("specialty").label("specialty"),
        _meta("setting").label("setting"), _meta("difficulty").label("difficulty"),
        _meta("estimated_duration_minutes").label("duration_text"),
        _meta("anonymized").label("anonymized"),
    ).select_from(ClinicalCase)
    .join(latest, latest.c.cid == ClinicalCase.id)
    .join(CaseVersion, and_(CaseVersion.case_id == latest.c.cid, CaseVersion.version_number == latest.c.v))
    .where(ClinicalCase.archived_at.is_(None), ClinicalCase.published_version_number.is_(None)))


def _safe_preview(row) -> dict:
    item = dict(row)
    # Any draft without explicit anonymized=true must not expose its title,
    # brief, or other source-derived medical text even during local preview.
    safe = item.get("anonymized") == "true"
    return {
        "case_id": item["case_id"], "version_number": item["version_number"],
        "title": item["title"] if safe else "Restricted draft — anonymization pending",
        "subtitle": item["subtitle"] if safe else "Local development placeholder",
        "short_brief": item["short_brief"] if safe else "Clinical source and anonymization review required.",
        "specialty": item["specialty"] if safe else None,
        "setting": item["setting"] if safe else None,
        "difficulty": item["difficulty"] if safe else None,
        "estimated_duration_minutes": int(item["duration_text"]) if safe and (item.get("duration_text") or "").isdigit() else None,
        "demo": True, "restricted": not safe,
    }


@router.get("")
def list_local_drafts(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    _only_local_db()
    rows = db.execute(_draft_query().order_by(ClinicalCase.case_code).limit(limit + 1).offset(offset)).mappings().all()
    return {"items": [_safe_preview(row) for row in rows[:limit]], "limit": limit,
            "offset": offset, "has_more": len(rows) > limit, "development_only": True}


@router.get("/{case_code}")
def get_local_draft(case_code: str, db: Annotated[Session, Depends(get_db)]):
    _only_local_db()
    row = db.execute(_draft_query().where(ClinicalCase.case_code == case_code).limit(1)).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return _safe_preview(row)
