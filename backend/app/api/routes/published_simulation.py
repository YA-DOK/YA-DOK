"""Start F03 from an approved F02 case version ? local integration phase."""
from __future__ import annotations

import os
from copy import deepcopy
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

from app.api.routes.simulation import _pg_service
from app.core.config import settings
from app.core.security import get_current_user
from app.models.case import ClinicalCase, CaseVersion
from app.models.case_review import CaseReviewApproval
from app.models.profile import Profile
from app.models.simulation_session import SimulationSessionModel
from app.schemas.case_blueprint import CaseBlueprintV32, publication_issues
from app.services.case_lifecycle import _public_metadata_issues
from app.services.case_review import blueprint_hash
from app.services.simulation_pg_service import _state
from app.services.simulation_service import _json_safe
from app.simulation.engine import create_session

router = APIRouter(prefix="/simulation", tags=["Simulation Integration"])


class StartPublishedCaseRequest(BaseModel):
    case_code: str = Field(
        min_length=3,
        max_length=120,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    mode: Literal["training", "test"] = "training"


def require_shared_integration():
    """Require the shared application PostgreSQL connection."""
    if (
        settings.app_env == "development"
        and os.getenv("YA_DOK_F03_RUNTIME") != "live"
    ):
        raise HTTPException(
            503, "Live simulation storage is not enabled."
        )

    if not settings.database_url:
        raise HTTPException(503, "Database not configured")


def engine_case_data(blueprint: CaseBlueprintV32) -> dict:
    """Convert v3.2 to F03's private engine representation."""
    data = blueprint.model_dump(mode="json")

    # The student diagnosis/evaluation answer key must never enter
    # the simulation session snapshot.
    data.pop("ground_truth", None)

    examinations = {}
    for item in blueprint.exam_items:
        if item.value is None and not item.finding:
            continue

        result = {
            "value": item.value,
            "unit": item.unit,
            "finding": item.finding,
        }
        examinations[item.id] = result
        examinations.setdefault(item.label, result)

    investigations = {}
    for item in blueprint.investigations:
        results = {}
        for result in item.results:
            if result.value is None:
                continue

            results[result.label] = {
                "value": result.value,
                "unit": result.unit,
                "ref_range": result.ref_range,
                "flag": result.flag,
            }

        if results:
            investigations[item.id] = results
            investigations.setdefault(item.label, results)

    data["physical_examination"] = examinations
    data["investigations"] = investigations
    return data


@router.post("/sessions/from-case", status_code=201)
def start_published_case(
    payload: StartPublishedCaseRequest,
    user: Annotated[dict, Depends(get_current_user)],
):
    require_shared_integration()

    try:
        user_id = UUID(str(user["id"]))
    except (KeyError, ValueError, TypeError):
        raise HTTPException(401, "Invalid authenticated user") from None

    service = _pg_service()
    if service is None:
        raise HTTPException(503, "PostgreSQL simulation storage required")

    from app.core.database import engine as shared_engine
    if service.session_factory.kw.get("bind") is not shared_engine:
        raise HTTPException(
            503, "Simulation and case databases are not unified."
        )

    with service.session_factory.begin() as db:
        # Authentication is external; profiles must already be provisioned.
        if db.get(Profile, user_id) is None:
            raise HTTPException(
                409, "Authenticated user profile is missing."
            )

        # SHARE lock prevents concurrent publication/archive while starting.
        case = db.scalar(
            select(ClinicalCase)
            .where(ClinicalCase.case_code == payload.case_code)
            .with_for_update(read=True)
        )

        if (
            case is None
            or case.archived_at is not None
            or case.published_version_number is None
        ):
            raise HTTPException(404, "Published case not found")

        version = db.scalar(
            select(CaseVersion).where(
                CaseVersion.case_id == case.id,
                CaseVersion.version_number == case.published_version_number,
                CaseVersion.published_at.is_not(None),
            )
        )

        if version is None:
            raise HTTPException(404, "Published case version not found")

        approval = db.scalar(
            select(CaseReviewApproval).where(
                CaseReviewApproval.case_version_id == version.id
            )
        )

        try:
            blueprint = CaseBlueprintV32.model_validate(version.blueprint)
            valid = (
                blueprint.case_id == case.case_code
                and not publication_issues(blueprint)
                and not _public_metadata_issues(blueprint)
            )
        except ValidationError:
            valid = False

        if (
            not valid
            or approval is None
            or approval.blueprint_sha256 != blueprint_hash(version.blueprint)
        ):
            raise HTTPException(409, "Case approval verification failed")

        # Confidential blueprint stays server-side in PostgreSQL.
        session = create_session(engine_case_data(blueprint))
        session.mode = payload.mode
        session.case_code = case.case_code
        session.case_version_id = str(version.id)
        session.version_number = version.version_number
        session.duration_minutes = (
            blueprint.meta.estimated_duration_minutes
        )

        row = SimulationSessionModel(
            id=UUID(session.session_id),
            user_id=user_id,
            case_version_id=version.id,
            case_data=_json_safe(session.case_data),
            state_json=_state(session),
            current_phase=session.current_phase.value,
            is_paused=False,
            is_completed=False,
        )

        db.add(row)
        db.flush()
        service._append_events(db, session, 0)

        response = {
            **session.to_dict(),
            "mode": payload.mode,
            "case_code": case.case_code,
            "case_version_id": str(version.id),
            "version_number": version.version_number,
            "duration_minutes": blueprint.meta.estimated_duration_minutes,
        }

    # to_dict() does not return case_data, blueprint or ground_truth.
    return response
