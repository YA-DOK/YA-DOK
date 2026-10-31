"""Guard clinical approval. This is audit infrastructure, not credential verification.

The project owner MUST independently verify each clinician's identity/qualification
before adding their Auth UUID to CLINICAL_REVIEWER_USER_IDS in a server-side .env.
Without that explicit allowlist, approval is unavailable (fail closed).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import CaseVersion, ClinicalCase
from app.models.case_review import CaseReviewApproval
from app.schemas.case_blueprint import CaseBlueprintV32, publication_issues
from app.services.case_lifecycle import (
    CaseArchived,
    CaseNotFound,
    PublicationBlocked,
    _public_metadata_issues,
)


def blueprint_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def clinician_is_allowed(auth_id: str, configured_ids: str) -> bool:
    try:
        wanted = UUID(auth_id)
        return wanted in {UUID(part.strip()) for part in configured_ids.split(",") if part.strip()}
    except (ValueError, TypeError):
        return False


@dataclass(frozen=True)
class ApprovalResult:
    case_id: str
    version_number: int
    status: str
    unchanged: bool


def approve_new_snapshot(db: Session, case_code: str, blueprint: CaseBlueprintV32,
                         reviewer_user_id: UUID, evidence_reference: str) -> ApprovalResult:
    """Create an approved immutable NEW version, never edit an imported draft.

    Caller controls the transaction. A separate publish action is required.
    """
    if blueprint.case_id != case_code:
        raise PublicationBlocked(["blueprint case_id does not match URL"])
    issues = publication_issues(blueprint) + _public_metadata_issues(blueprint)
    if issues:
        raise PublicationBlocked(issues)

    case = db.scalar(select(ClinicalCase).where(ClinicalCase.case_code == case_code).with_for_update())
    if case is None:
        raise CaseNotFound()
    if case.archived_at is not None:
        raise CaseArchived()
    last = db.scalar(select(CaseVersion).where(CaseVersion.case_id == case.id).order_by(CaseVersion.version_number.desc()).limit(1))
    if last is None:
        raise CaseNotFound()
    payload = blueprint.model_dump(mode="json")
    digest = blueprint_hash(payload)
    if last.blueprint == payload:
        previous = db.scalar(select(CaseReviewApproval).where(CaseReviewApproval.case_version_id == last.id))
        if previous and previous.blueprint_sha256 == digest:
            return ApprovalResult(case_code, last.version_number, "approved_pending_publication", True)
        raise PublicationBlocked(["latest snapshot is missing its matching approval audit record"])

    version = CaseVersion(case_id=case.id, version_number=last.version_number + 1, blueprint=payload)
    db.add(version)
    db.flush()
    db.add(CaseReviewApproval(
        case_version_id=version.id, reviewer_user_id=reviewer_user_id,
        reviewer_name=blueprint.meta.reviewed_by.strip(), evidence_reference=evidence_reference.strip(),
        blueprint_sha256=digest,
    ))
    db.flush()
    return ApprovalResult(case_code, version.version_number, "approved_pending_publication", False)
