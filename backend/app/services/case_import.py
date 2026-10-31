"""Feature 02: transactional import of v3.2 case blueprints as draft versions.

Never edits a stored version. Never publishes a case. All submitted medical facts
remain private in JSONB; response contains only safe import metadata.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import ClinicalCase, CaseVersion
from app.schemas.case_blueprint import CaseBlueprintV32


@dataclass(frozen=True)
class ImportResult:
    case_id: str
    version_number: int
    status: str
    unchanged: bool


def import_case_draft(db: Session, blueprint: CaseBlueprintV32) -> ImportResult:
    """Caller owns transaction. Lock the parent to serialize version increments.

    First-ever concurrent imports of one case_id can race; the unique case_code
    constraint rejects the loser. Router maps this to HTTP 409; retry is safe.
    """
    if blueprint.meta.review_status != "draft":
        raise ValueError("Only draft blueprints can be imported via this endpoint")

    payload = blueprint.model_dump(mode="json")
    case = db.scalar(
        select(ClinicalCase)
        .where(ClinicalCase.case_code == blueprint.case_id)
        .with_for_update()
    )
    if case is None:
        case = ClinicalCase(case_code=blueprint.case_id)
        db.add(case)
        db.flush()  # obtains server-generated case UUID before inserting version

    last = db.scalar(
        select(CaseVersion)
        .where(CaseVersion.case_id == case.id)
        .order_by(CaseVersion.version_number.desc())
        .limit(1)
    )
    if last is not None and last.blueprint == payload:
        return ImportResult(
            case_id=blueprint.case_id,
            version_number=last.version_number,
            status="published" if last.published_at is not None else "draft",
            unchanged=True,
        )

    version_number = (last.version_number + 1) if last is not None else 1
    db.add(
        CaseVersion(
            case_id=case.id,
            version_number=version_number,
            blueprint=payload,
            # published_at is intentionally NULL. Publishing is a separate workflow.
        )
    )
    db.flush()
    return ImportResult(
        case_id=blueprint.case_id,
        version_number=version_number,
        status="draft",
        unchanged=False,
    )
