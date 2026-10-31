
import os
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.ai.llm.openrouter import OpenRouterProvider
from app.core.config import settings
from app.core.security import get_current_user
from app.services.simulation_pg_service import (
    PostgresSimulationService,
    SessionNotFound,
)
from app.services.simulation_service import SimulationService
from app.simulation.action_request import IdempotencyConflict
from app.simulation.engine import (
    InvalidPhaseTransition,
    SimulationError,
    SimulationPhase,
    SimulationSession,
    advance_phase,
    ask_patient_async,
    complete_session,
    create_session,
    pause_session,
    request_examination,
    request_investigation,
    resume_session,
    submit_diagnosis_and_plan,
)
from app.simulation.patient_agent import PatientAgent

router = APIRouter(prefix="/simulation", tags=["Simulation"])

# Keep in-memory storage for compatibility and fast access.
# SQLite is the persistent local development store.
sessions: dict[str, SimulationSession] = {}
session_owners: dict[str, str] = {}

simulation_service = SimulationService()


from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


@lru_cache(maxsize=1)
def _isolated_pg_factory():
    raw_url = os.getenv("F03_TEST_DATABASE_URL", "").strip()

    if not raw_url:
        raise HTTPException(
            503, "F03_TEST_DATABASE_URL is required."
        )

    try:
        url = make_url(raw_url)
    except Exception as exc:
        raise HTTPException(
            503, "Invalid isolated PostgreSQL URL."
        ) from exc

    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or url.database in {None, "postgres", "template0", "template1"}
    ):
        raise HTTPException(
            503,
            "F03 requires a dedicated local PostgreSQL test database.",
        )

    engine = create_engine(raw_url, pool_pre_ping=True)

    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


@lru_cache(maxsize=1)
def _shared_pg_factory():
    from app.core.database import engine

    if engine is None:
        raise HTTPException(
            503, "PostgreSQL database is not configured."
        )

    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def _pg_service():
    if (
        os.getenv("YA_DOK_F03_RUNTIME") == "live"
        or settings.app_env not in ("development", "test")
    ):
        return PostgresSimulationService(_shared_pg_factory())


    if os.getenv("YA_DOK_F03_STORAGE") != "postgres":
        if settings.app_env != "development":
            raise HTTPException(
                503,
                "Legacy simulation storage is disabled outside development.",
            )
        return None

    return PostgresSimulationService(_isolated_pg_factory())


def _pg_action(user, session_id, request, action, payload, handler):
    service = _pg_service()
    key = request.headers.get("Idempotency-Key")

    if not key:
        raise HTTPException(400, "Idempotency-Key header is required.")

    try:
        UUID(key)
        UUID(str(session_id))
        UUID(str(user.get("id")))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(422, "Invalid request, session or user ID.") from exc

    try:
        return service.apply_action(
            user_id=str(user["id"]),
            session_id=session_id,
            request_id=key,
            action=action,
            payload=payload,
            handler=handler,
        )
    except SessionNotFound as exc:
        raise HTTPException(404, "Simulation session not found.") from exc
    except IdempotencyConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except (InvalidPhaseTransition, SimulationError) as exc:
        handle_simulation_error(exc)


def _pg_change_phase(session, phase):
    advance_phase(session, phase)
    return session.to_dict()


def _pg_examination(session, name):
    result = request_examination(session, name)
    return {"session_id": session.session_id, **result}


def _pg_investigation(session, name):
    result = request_investigation(session, name)
    return {"session_id": session.session_id, **result}


def _pg_diagnosis(session, diagnosis, treatment_plan):
    result = submit_diagnosis_and_plan(
        session, diagnosis, treatment_plan
    )
    return {"session_id": session.session_id, **result}



CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


class CreateSessionRequest(BaseModel):
    mode: Literal["training", "test"] = "training"
    case_data: dict[str, Any] = Field(
        ...,
        description="Medical case data supplied by the case/blueprint module.",
    )


class PhaseRequest(BaseModel):
    phase: SimulationPhase


class PatientQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=3000)


class ExaminationRequest(BaseModel):
    examination_name: str = Field(..., min_length=1, max_length=200)


class InvestigationRequest(BaseModel):
    investigation_name: str = Field(..., min_length=1, max_length=200)


class DiagnosisRequest(BaseModel):
    diagnosis: str = Field(..., min_length=1, max_length=3000)
    treatment_plan: str = Field(default="", max_length=5000)


def get_session(session_id: str) -> SimulationSession:
    """Get a session from memory only."""
    session = sessions.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation session not found.",
        )

    return session


def get_owned_session(
    session_id: str,
    user: dict[str, Any],
) -> SimulationSession:
    """Return a session only when it belongs to the authenticated user."""
    user_id = user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=404,
            detail="Simulation session not found.",
        )

    user_id = str(user_id)
    session = sessions.get(session_id)

    # If the session is in memory, verify its owner before returning it.
    if session is not None:
        if session_owners.get(session_id) != user_id:
            raise HTTPException(
                status_code=404,
                detail="Simulation session not found.",
            )
        return session

    # If the server restarted, attempt to restore the session from SQLite.
    try:
        session = simulation_service.restore_session(
            session_id=session_id,
            user_id=user_id,
        )
    except (ValueError, KeyError):
        session = None

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation session not found.",
        )

    sessions[session_id] = session
    session_owners[session_id] = user_id

    return session


def persist_session(
    session: SimulationSession,
    user: dict[str, Any],
) -> None:
    """Save the current state and append newly created events to SQLite."""
    user_id = user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=404,
            detail="Simulation session not found.",
        )

    try:
        simulation_service.sync_session(
            user_id=str(user_id),
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to persist the simulation session.",
        ) from exc


def handle_simulation_error(exc: Exception) -> None:
    """Convert simulation errors into appropriate HTTP responses."""
    if isinstance(exc, InvalidPhaseTransition):
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SimulationError):
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("/demo-ready")
def demo_ready(user: CurrentUser):
    """Require authenticated, isolated PostgreSQL demo mode."""
    if (
        settings.app_env != "development"
        or os.getenv("F03_ALLOW_SYNTHETIC") != "1"
    ):
        raise HTTPException(503, "Synthetic demo is disabled.")

    pg = _pg_service()
    if pg is None:
        raise HTTPException(
            503, "F03 requires isolated PostgreSQL storage."
        )

    return {"ready": True, "storage": "postgres"}


@router.post("/sessions", status_code=201)
def start_simulation(
    payload: CreateSessionRequest,
    user: CurrentUser,
):
    """Create a simulation owned by the authenticated user."""

    if (pg := _pg_service()) is not None:
        if (
            settings.app_env != "development"
            or os.getenv("YA_DOK_F03_RUNTIME") == "live"
            or os.getenv("F03_ALLOW_SYNTHETIC") != "1"
        ):
            raise HTTPException(
                503,
                "Case Provider integration required to create sessions.",
            )
        try:
            # LOCAL TEST DB ONLY: the real authenticated user's
            # UUID must satisfy the local profiles foreign key.
            # Never run this path against shared Supabase Cloud.
            if isinstance(pg, PostgresSimulationService):
                with pg.session_factory.begin() as db:
                    db.execute(
                        text(
                            "INSERT INTO public.profiles (id) "
                            "VALUES (:uid) ON CONFLICT (id) DO NOTHING"
                        ),
                        {"uid": UUID(str(user["id"]))},
                    )

            created = pg.create(
                str(user["id"]),
                payload.case_data,
                mode=payload.mode,
            )
            return {
                **created.to_dict(),
                "mode": created.mode,
            }
        except SimulationError as exc:
            handle_simulation_error(exc)
    user_id = user.get("id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user ID is missing.",
        )

    try:
        session = create_session(payload.case_data)
    except SimulationError as exc:
        handle_simulation_error(exc)
        raise

    # Register in memory first, preserving existing API behavior.
    sessions[session.session_id] = session
    session_owners[session.session_id] = str(user_id)

    try:
        simulation_service.persist_new_session(
            user_id=str(user_id),
            session=session,
        )
    except Exception as exc:
        # Avoid leaving an in-memory session that was not persisted.
        sessions.pop(session.session_id, None)
        session_owners.pop(session.session_id, None)
        raise HTTPException(
            status_code=500,
            detail="Unable to save the new simulation session.",
        ) from exc

    return session.to_dict()


@router.get("/sessions")
def list_my_simulation_sessions(
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """List only the authenticated student's sessions; never return case_data."""
    user_id = str(user.get("id", ""))
    if not user_id:
        raise HTTPException(401, "Authenticated user ID is missing.")

    if (pg := _pg_service()) is not None:
        from sqlalchemy import select

        from app.models.case import CaseVersion, ClinicalCase
        from app.models.simulation_session import SimulationSessionModel

        try:
            uid = UUID(user_id)
        except (ValueError, TypeError) as exc:
            raise HTTPException(401, "Invalid authenticated user ID.") from exc

        with pg.session_factory() as db:
            rows = db.execute(
                select(SimulationSessionModel, ClinicalCase.case_code)
                .outerjoin(
                    CaseVersion,
                    SimulationSessionModel.case_version_id == CaseVersion.id,
                )
                .outerjoin(ClinicalCase, CaseVersion.case_id == ClinicalCase.id)
                .where(SimulationSessionModel.user_id == uid)
                .order_by(
                    SimulationSessionModel.created_at.desc(),
                    SimulationSessionModel.id.desc(),
                )
                .limit(limit)
            ).all()

            return {"items": [
                {
                    "session_id": str(row.id),
                    "case_code": code or (row.state_json or {}).get("case_code"),
                    "mode": (row.state_json or {}).get("mode", "training"),
                    "current_phase": row.current_phase,
                    "is_completed": row.is_completed,
                    "is_paused": row.is_paused,
                    "diagnosis": row.diagnosis,
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                }
                for row, code in rows
            ]}

    # In-memory development fallback. Real persistent history uses PostgreSQL.
    owned = [
        session for session_id, session in sessions.items()
        if session_owners.get(session_id) == user_id
    ]
    owned.reverse()
    return {"items": [
        {
            "session_id": session.session_id,
            "case_code": getattr(session, "case_code", None),
            "mode": getattr(session, "mode", "training"),
            "current_phase": session.current_phase.value,
            "is_completed": session.is_completed,
            "is_paused": session.is_paused,
            "diagnosis": session.diagnosis,
            "created_at": session.events[0].timestamp.isoformat() if session.events else None,
            "updated_at": session.events[-1].timestamp.isoformat() if session.events else None,
        }
        for session in owned[:limit]
    ]}


@router.get("/sessions/{session_id}")
def get_simulation(
    session_id: str,
    user: CurrentUser,
):
    """Get a session only if it belongs to the authenticated user."""

    if (pg := _pg_service()) is not None:
        try:
            loaded = pg.load(str(user["id"]), session_id)
            return {
                **loaded.to_dict(),
                "mode": getattr(loaded, "mode", "training"),
                "case_code": getattr(loaded, "case_code", None),
                "case_version_id": getattr(loaded, "case_version_id", None),
                "version_number": getattr(loaded, "version_number", None),
                "duration_minutes": getattr(loaded, "duration_minutes", None),
            }
        except (SessionNotFound, ValueError, TypeError) as exc:
            raise HTTPException(
                404, "Simulation session not found."
            ) from exc
    session = get_owned_session(session_id, user)
    return session.to_dict()


@router.post("/sessions/{session_id}/phase")
def change_phase(
    session_id: str,
    payload: PhaseRequest,
    user: CurrentUser,
    request: Request,
):
    """Advance the simulation to the next valid phase."""

    if _pg_service() is not None:
        return _pg_action(
            user, session_id, request, "phase",
            {"phase": payload.phase.value},
            lambda s: _pg_change_phase(s, payload.phase),
        )
    session = get_owned_session(session_id, user)

    try:
        advance_phase(session, payload.phase)
    except (InvalidPhaseTransition, SimulationError) as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return session.to_dict()


@router.post("/sessions/{session_id}/pause")
def pause_simulation(
    session_id: str,
    user: CurrentUser,
    request: Request,
):
    """Pause a simulation owned by the authenticated user."""

    if _pg_service() is not None:
        return _pg_action(
            user, session_id, request, "pause", {},
            pause_session,
        )
    session = get_owned_session(session_id, user)

    try:
        result = pause_session(session)
    except SimulationError as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return result


@router.post("/sessions/{session_id}/resume")
def resume_simulation(
    session_id: str,
    user: CurrentUser,
    request: Request,
):
    """Resume a paused simulation owned by the authenticated user."""

    if _pg_service() is not None:
        return _pg_action(
            user, session_id, request, "resume", {},
            resume_session,
        )
    session = get_owned_session(session_id, user)

    try:
        result = resume_session(session)
    except SimulationError as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return result


@router.post("/sessions/{session_id}/patient-question")
async def ask_patient(
    session_id: str,
    payload: PatientQuestionRequest,
    user: CurrentUser,
):
    """Ask the simulated patient a question."""

    if _pg_service() is not None:
        raise HTTPException(
            501,
            "Patient Agent PostgreSQL integration belongs to F04.",
        )
    session = get_owned_session(session_id, user)

    try:
        agent = PatientAgent(llm_service=OpenRouterProvider())

        response = await ask_patient_async(
            session=session,
            question=payload.question,
            patient_agent=agent,
        )

    except (InvalidPhaseTransition, SimulationError) as exc:
        handle_simulation_error(exc)

    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a patient response.",
        ) from exc

    persist_session(session, user)

    return {
        "session_id": session.session_id,
        "response": response,
        "session": session.to_dict(),
    }


@router.post("/sessions/{session_id}/examinations")
def get_examination(
    session_id: str,
    payload: ExaminationRequest,
    user: CurrentUser,
    request: Request,
):
    """Request examination findings from the supplied case."""

    if _pg_service() is not None:
        return _pg_action(
            user, session_id, request, "examination",
            {"examination_name": payload.examination_name},
            lambda s: _pg_examination(s, payload.examination_name),
        )
    session = get_owned_session(session_id, user)

    try:
        result = request_examination(
            session,
            payload.examination_name,
        )
    except SimulationError as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return {"session_id": session_id, **result}


@router.post("/sessions/{session_id}/investigations")
def get_investigation(
    session_id: str,
    payload: InvestigationRequest,
    user: CurrentUser,
    request: Request,
):
    """Request investigation results from the supplied case."""

    if _pg_service() is not None:
        return _pg_action(
            user, session_id, request, "investigation",
            {"investigation_name": payload.investigation_name},
            lambda s: _pg_investigation(s, payload.investigation_name),
        )
    session = get_owned_session(session_id, user)

    try:
        result = request_investigation(
            session,
            payload.investigation_name,
        )
    except SimulationError as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return {"session_id": session_id, **result}


@router.post("/sessions/{session_id}/diagnosis")
def submit_diagnosis(
    session_id: str,
    payload: DiagnosisRequest,
    user: CurrentUser,
    request: Request,
):
    """Submit the student's diagnosis and treatment plan."""

    if _pg_service() is not None:
        return _pg_action(
            user, session_id, request, "diagnosis",
            {
                "diagnosis": payload.diagnosis,
                "treatment_plan": payload.treatment_plan,
            },
            lambda s: _pg_diagnosis(
                s, payload.diagnosis, payload.treatment_plan
            ),
        )
    session = get_owned_session(session_id, user)

    try:
        result = submit_diagnosis_and_plan(
            session,
            payload.diagnosis,
            payload.treatment_plan,
        )
    except SimulationError as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return {"session_id": session_id, **result}


@router.post("/sessions/{session_id}/complete")
def finish_simulation(
    session_id: str,
    user: CurrentUser,
    request: Request,
):
    """Complete the simulation after diagnosis and treatment plan."""

    if _pg_service() is not None:
        return _pg_action(
            user, session_id, request, "complete", {},
            complete_session,
        )
    session = get_owned_session(session_id, user)

    try:
        result = complete_session(session)
    except SimulationError as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return result
