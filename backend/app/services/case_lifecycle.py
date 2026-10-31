"""Admin lifecycle for existing case/version records; no schema change.

Publish requires a separately reviewed, approved blueprint already stored as a
version. This code cannot certify medical accuracy or reviewer identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import CaseVersion, ClinicalCase
from app.schemas.case_blueprint import CaseBlueprintV32, publication_issues


class CaseNotFound(Exception):
    pass


class VersionNotFound(Exception):
    pass


class PublicationBlocked(Exception):
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("Case version cannot be published")


class CaseArchived(Exception):
    pass


@dataclass(frozen=True)
class LifecycleResult:
    case_id: str
    status: str
    published_version_number: int | None
    unchanged: bool


def _locked_case(db: Session, case_code: str) -> ClinicalCase:
    case = db.scalar(
        select(ClinicalCase)
        .where(ClinicalCase.case_code == case_code)
        .with_for_update()
    )
    if case is None:
        raise CaseNotFound()
    return case


def _status(case: ClinicalCase) -> str:
    if case.archived_at is not None:
        return "archived"
    return "published" if case.published_version_number is not None else "draft"


def _result(case: ClinicalCase, *, unchanged: bool) -> LifecycleResult:
    return LifecycleResult(
        case_id=case.case_code,
        status=_status(case),
        published_version_number=case.published_version_number,
        unchanged=unchanged,
    )


def _public_metadata_issues(blueprint: CaseBlueprintV32) -> list[str]:
    """Cheap defense against obvious answer leaks in student-visible metadata.

    This cannot replace a clinician/editor reviewing the student's first view.
    """
    public_text = " ".join(
        str(s or "") for s in (
            blueprint.meta.title,
            blueprint.meta.subtitle,
            blueprint.meta.short_brief,
        )
    ).casefold()
    diagnosis = blueprint.ground_truth.final_diagnosis
    terms = [diagnosis.label, *diagnosis.leak_terms]
    return [
        "public metadata reveals a diagnosis/leak term"
        for term in terms
        if isinstance(term, str) and len(term.strip()) >= 3 and term.strip().casefold() in public_text
    ][:1]


def publish_case_version(db: Session, case_code: str, version_number: int) -> LifecycleResult:
    """Atomically choose an approved version, preserving every old version.

    Caller commits/rolls back. Parent row lock serializes publish/archive/restore.
    """
    case = _locked_case(db, case_code)
    if case.archived_at is not None:
        raise CaseArchived()
    version = db.scalar(
        select(CaseVersion).where(
            CaseVersion.case_id == case.id,
            CaseVersion.version_number == version_number,
        )
    )
    if version is None:
        raise VersionNotFound()
    try:
        blueprint = CaseBlueprintV32.model_validate(version.blueprint)
    except ValidationError:
        raise PublicationBlocked(["stored blueprint fails v3.2 structural validation"]) from None
    if blueprint.case_id != case.case_code:
        raise PublicationBlocked(["blueprint case ID does not match stored case"])
    issues = publication_issues(blueprint) + _public_metadata_issues(blueprint)
    if issues:
        raise PublicationBlocked(issues)
    # Validate independent server-recorded approval for the EXACT immutable snapshot.
    # Importing JSON with review_status='approved' alone must never enable publication.
    from app.models.case_review import CaseReviewApproval
    from app.services.case_review import blueprint_hash
    audit = db.scalar(select(CaseReviewApproval).where(CaseReviewApproval.case_version_id == version.id))
    if audit is None or audit.blueprint_sha256 != blueprint_hash(version.blueprint):
        raise PublicationBlocked(["verified clinical approval audit record is missing or invalid"])
    unchanged = case.published_version_number == version_number and version.published_at is not None
    if not unchanged:
        if version.published_at is None:
            version.published_at = datetime.now(UTC)
        case.published_version_number = version_number
    return _result(case, unchanged=unchanged)


def archive_case(db: Session, case_code: str) -> LifecycleResult:
    case = _locked_case(db, case_code)
    unchanged = case.archived_at is not None
    if not unchanged:
        case.archived_at = datetime.now(UTC)
    # Preserve the pointer, all versions, and session references.
    return _result(case, unchanged=unchanged)


def restore_case(db: Session, case_code: str) -> LifecycleResult:
    case = _locked_case(db, case_code)
    unchanged = case.archived_at is None
    if not unchanged:
        case.archived_at = None
    return _result(case, unchanged=unchanged)
