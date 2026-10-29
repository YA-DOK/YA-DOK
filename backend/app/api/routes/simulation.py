
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.ai.llm.openrouter import OpenRouterProvider
from app.core.security import get_current_user
from app.services.simulation_service import SimulationService
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

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]


class CreateSessionRequest(BaseModel):
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
    treatment_plan: str = Field(..., min_length=1, max_length=5000)


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


@router.post("/sessions", status_code=201)
def start_simulation(
    payload: CreateSessionRequest,
    user: CurrentUser,
):
    """Create a simulation owned by the authenticated user."""
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


@router.get("/sessions/{session_id}")
def get_simulation(
    session_id: str,
    user: CurrentUser,
):
    """Get a session only if it belongs to the authenticated user."""
    session = get_owned_session(session_id, user)
    return session.to_dict()


@router.post("/sessions/{session_id}/phase")
def change_phase(
    session_id: str,
    payload: PhaseRequest,
    user: CurrentUser,
):
    """Advance the simulation to the next valid phase."""
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
):
    """Pause a simulation owned by the authenticated user."""
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
):
    """Resume a paused simulation owned by the authenticated user."""
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
):
    """Request examination findings from the supplied case."""
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
):
    """Request investigation results from the supplied case."""
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
):
    """Submit the student's diagnosis and treatment plan."""
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
):
    """Complete the simulation after diagnosis and treatment plan."""
    session = get_owned_session(session_id, user)

    try:
        result = complete_session(session)
    except SimulationError as exc:
        handle_simulation_error(exc)

    persist_session(session, user)
    return result
