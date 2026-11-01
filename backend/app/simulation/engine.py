
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4


class SimulationPhase(str, Enum):
    INTRODUCTION = "introduction"
    HISTORY_TAKING = "history_taking"
    EXAMINATION = "examination"
    INVESTIGATIONS = "investigations"
    DIAGNOSIS_AND_PLAN = "diagnosis_and_plan"
    COMPLETED = "completed"


class InvalidPhaseTransition(ValueError):
    """Raised when a simulation attempts an invalid phase transition."""


class SimulationError(ValueError):
    """Raised when a simulation action is invalid."""


PHASE_ORDER = [
    SimulationPhase.INTRODUCTION,
    SimulationPhase.HISTORY_TAKING,
    SimulationPhase.EXAMINATION,
    SimulationPhase.INVESTIGATIONS,
    SimulationPhase.DIAGNOSIS_AND_PLAN,
    SimulationPhase.COMPLETED,
]


def get_next_phase(
    current_phase: SimulationPhase,
) -> SimulationPhase | None:
    """Return the next phase, or None when completed."""
    current_index = PHASE_ORDER.index(current_phase)

    if current_index == len(PHASE_ORDER) - 1:
        return None

    return PHASE_ORDER[current_index + 1]


def transition_phase(
    current_phase: SimulationPhase,
    requested_phase: SimulationPhase,
) -> SimulationPhase:
    """Allow only one forward transition at a time."""
    expected_phase = get_next_phase(current_phase)

    if expected_phase is None or requested_phase != expected_phase:
        raise InvalidPhaseTransition(
            f"Cannot transition from '{current_phase.value}' "
            f"to '{requested_phase.value}'."
        )

    return requested_phase


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(UTC)


@dataclass
class SimulationMessage:
    role: str
    content: str
    action: str = "chat"


@dataclass
class SimulationEvent:
    """A timestamped event recorded during a simulation."""

    event_type: str
    phase: SimulationPhase
    details: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly event representation."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "phase": self.phase.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


@dataclass
class SimulationSession:
    """An in-memory medical simulation session."""

    case_data: dict[str, Any]
    session_id: str = field(default_factory=lambda: str(uuid4()))
    current_phase: SimulationPhase = SimulationPhase.INTRODUCTION
    messages: list[SimulationMessage] = field(default_factory=list)
    events: list[SimulationEvent] = field(default_factory=list)
    requested_investigations: list[str] = field(default_factory=list)
    requested_examinations: list[str] = field(default_factory=list)
    diagnosis: str | None = None
    treatment_plan: str | None = None
    is_completed: bool = False
    is_paused: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.case_data, dict) or not self.case_data:
            raise SimulationError(
                "case_data must be a non-empty dictionary."
            )

    def record_event(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
        phase: SimulationPhase | None = None,
    ) -> SimulationEvent:
        """Append an event in the order it occurs."""
        event = SimulationEvent(
            event_type=event_type,
            phase=phase or self.current_phase,
            details=details or {},
        )
        self.events.append(event)
        return event

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation of the session."""
        return {
            "session_id": self.session_id,
            "current_phase": self.current_phase.value,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "action": message.action,
                }
                for message in self.messages
            ],
            "events": [event.to_dict() for event in self.events],
            "requested_investigations": list(
                self.requested_investigations
            ),
            "requested_examinations": list(
                self.requested_examinations
            ),
            "diagnosis": self.diagnosis,
            "treatment_plan": self.treatment_plan,
            "is_completed": self.is_completed,
            "is_paused": self.is_paused,
        }


def create_session(
    case_data: dict[str, Any],
) -> SimulationSession:
    """Start a new simulation for a supplied medical case."""
    session = SimulationSession(case_data=case_data)

    session.messages.append(
        SimulationMessage(
            role="system",
            content=(
                "You are running a medical training simulation. "
                "Use only the supplied case information. "
                "Do not invent symptoms, examination findings, "
                "or investigation results."
            ),
        )
    )

    session.record_event(
        "session_created",
        {"initial_phase": session.current_phase.value},
    )

    return session


def test_time_limit_reached(
    session: SimulationSession,
    *,
    now: datetime | None = None,
) -> bool:
    """Only published, timed TEST attempts have a wall-clock deadline."""
    if session.is_completed or getattr(session, "mode", "training") != "test":
        return False
    minutes = getattr(session, "duration_minutes", None)
    if not isinstance(minutes, (int, float)) or isinstance(minutes, bool) or minutes <= 0:
        return False
    created = next((event for event in session.events if event.event_type == "session_created"), None)
    if created is None:
        return False
    start = created.timestamp
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    current = now or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current >= start + timedelta(minutes=minutes)


def expire_test_session_if_due(
    session: SimulationSession,
    *,
    now: datetime | None = None,
) -> bool:
    """Persistable, idempotent timeout without forcing a diagnosis."""
    if not test_time_limit_reached(session, now=now):
        return False
    old_phase = session.current_phase
    session.current_phase = SimulationPhase.COMPLETED
    session.is_completed = True
    session.is_paused = False
    session.record_event(
        "phase_changed",
        {"from_phase": old_phase.value, "to_phase": "completed", "reason": "time_limit"},
        phase=SimulationPhase.COMPLETED,
    )
    session.record_event(
        "session_timed_out",
        {"duration_minutes": session.duration_minutes, "previous_phase": old_phase.value},
        phase=SimulationPhase.COMPLETED,
    )
    session.record_event(
        "session_completed",
        {"completed": True, "reason": "time_limit"},
        phase=SimulationPhase.COMPLETED,
    )
    return True


def _ensure_active(session: SimulationSession) -> None:
    """Reject actions when a session is completed or paused."""
    if session.is_completed:
        raise SimulationError(
            "This simulation has been completed."
        )

    if session.is_paused:
        raise SimulationError(
            "This simulation is paused."
        )


def pause_session(session: SimulationSession) -> dict[str, Any]:
    """Pause an active simulation session."""
    if session.is_completed:
        raise SimulationError(
            "A completed simulation cannot be paused."
        )

    if session.is_paused:
        raise SimulationError(
            "This simulation is already paused."
        )

    session.is_paused = True

    session.record_event(
        "session_paused",
        {"is_paused": True},
    )

    return {
        "session_id": session.session_id,
        "is_paused": session.is_paused,
        "current_phase": session.current_phase.value,
    }


def resume_session(session: SimulationSession) -> dict[str, Any]:
    """Resume a simulation session."""
    if session.is_completed:
        raise SimulationError(
            "A completed simulation cannot be resumed."
        )

    if not session.is_paused:
        raise SimulationError(
            "This simulation is not paused."
        )

    session.is_paused = False

    session.record_event(
        "session_resumed",
        {"is_paused": False},
    )

    return {
        "session_id": session.session_id,
        "is_paused": session.is_paused,
        "current_phase": session.current_phase.value,
    }


def _ensure_phase(
    session: SimulationSession,
    required_phase: SimulationPhase,
) -> None:
    """Ensure the session is active and in the required phase."""
    _ensure_active(session)

    if session.current_phase != required_phase:
        raise SimulationError(
            f"This action requires the "
            f"'{required_phase.value}' phase. "
            f"Current phase: '{session.current_phase.value}'."
        )


def advance_phase(
    session: SimulationSession,
    requested_phase: SimulationPhase,
) -> SimulationPhase:
    """Advance sequentially, except completion after a submitted diagnosis."""
    _ensure_active(session)

    previous_phase = session.current_phase
    if requested_phase == SimulationPhase.COMPLETED:
        if not session.diagnosis:
            raise SimulationError("Submit a diagnosis before completion.")
        next_phase = SimulationPhase.COMPLETED
    else:
        next_phase = transition_phase(previous_phase, requested_phase)

    session.current_phase = next_phase

    if requested_phase == SimulationPhase.COMPLETED:
        session.is_completed = True

    session.record_event(
        "phase_changed",
        {
            "from_phase": previous_phase.value,
            "to_phase": next_phase.value,
        },
        phase=next_phase,
    )

    if session.is_completed:
        session.record_event(
            "session_completed",
            {"completed": True},
            phase=next_phase,
        )

    return session.current_phase


def ask_patient(
    session: SimulationSession,
    question: str,
    responder: Callable[..., str] | None = None,
) -> str:
    """Record a student's question and obtain a patient response."""
    _ensure_active(session)

    question = question.strip()

    if not question:
        raise SimulationError("Question cannot be empty.")

    session.messages.append(
        SimulationMessage(
            role="user",
            content=question,
            action="patient_question",
        )
    )

    session.record_event(
        "patient_question",
        {"question": question},
    )

    if responder is None:
        response = (
            "Patient AI is not connected yet. "
            "Connect an AI responder to generate a patient answer."
        )
    else:
        history = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in session.messages
            if message.role in {"user", "assistant"}
        ]

        try:
            response = responder(
                case_data=session.case_data,
                messages=history,
                question=question,
            )
        except Exception as exc:
            session.record_event(
                "patient_response_failed",
                {"error_type": type(exc).__name__},
            )
            raise SimulationError(
                "Failed to generate a patient response."
            ) from exc

        if not isinstance(response, str) or not response.strip():
            session.record_event(
                "patient_response_failed",
                {"reason": "empty_response"},
            )
            raise SimulationError(
                "The patient responder returned an empty response."
            )

        response = response.strip()

    session.messages.append(
        SimulationMessage(
            role="assistant",
            content=response,
            action="patient_response",
        )
    )

    session.record_event(
        "patient_response",
        {"response": response},
    )

    return response


async def ask_patient_async(
    session: SimulationSession,
    question: str,
    patient_agent: Any,
) -> str:
    """Ask the patient using an async PatientAgent."""
    _ensure_active(session)

    question = question.strip()

    if not question:
        raise SimulationError("Question cannot be empty.")

    session.messages.append(
        SimulationMessage(
            role="user",
            content=question,
            action="patient_question",
        )
    )

    session.record_event(
        "patient_question",
        {"question": question},
    )

    history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in session.messages
        if message.role in {"user", "assistant"}
    ]

    try:
        response = await patient_agent.respond(
            case_data=session.case_data,
            messages=history,
            question=question,
        )
    except Exception as exc:
        session.record_event(
            "patient_response_failed",
            {"error_type": type(exc).__name__},
        )
        raise SimulationError(
            "Failed to generate a patient response."
        ) from exc

    if not isinstance(response, str) or not response.strip():
        session.record_event(
            "patient_response_failed",
            {"reason": "empty_response"},
        )
        raise SimulationError(
            "The patient responder returned an empty response."
        )

    response = response.strip()

    session.messages.append(
        SimulationMessage(
            role="assistant",
            content=response,
            action="patient_response",
        )
    )

    session.record_event(
        "patient_response",
        {"response": response},
    )

    return response


def _find_case_result(
    results: Any,
    requested_name: str,
) -> Any | None:
    """Find an explicitly available result without inventing data."""
    if not isinstance(results, dict):
        return None

    requested = requested_name.strip().casefold()

    for name, result in results.items():
        if str(name).strip().casefold() == requested:
            return result

    return None


def _normalize_examination_name(value: str) -> str:
    """Normalize common examination labels for matching."""
    normalized = value.strip().casefold().replace("_", " ")

    suffixes = (
        " physical examination",
        " examination",
        " physical exam",
        " exam",
    )

    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
            break

    return " ".join(normalized.split())


def request_examination(session: SimulationSession, examination_name: str) -> dict[str, Any]:
    """F05 case-defined, phase-independent examination in an active F03 session."""
    _ensure_active(session)
    from app.feature05.session_actions import perform_examination
    return perform_examination(session, examination_name, SimulationError)



def request_investigation(session: SimulationSession, investigation_name: str) -> dict[str, Any]:
    """F05 case-defined investigation (lab/imaging) available throughout active session."""
    _ensure_active(session)
    from app.feature05.session_actions import perform_investigation
    return perform_investigation(session, investigation_name, SimulationError)



def submit_diagnosis_and_plan(
    session: SimulationSession,
    diagnosis: str,
    treatment_plan: str,
) -> dict[str, str]:
    """Record a diagnosis in any active phase; treatment is optional."""
    _ensure_active(session)

    diagnosis = diagnosis.strip()
    treatment_plan = treatment_plan.strip()

    if not diagnosis:
        raise SimulationError("Diagnosis cannot be empty.")

    session.diagnosis = diagnosis
    session.treatment_plan = treatment_plan

    session.messages.append(
        SimulationMessage(
            role="user",
            content=(
                f"Diagnosis: {diagnosis}\n"
                f"Treatment plan: {treatment_plan}"
            ),
            action="submit_diagnosis",
        )
    )

    session.record_event(
        "diagnosis_submitted",
        {
            "diagnosis": diagnosis,
            "treatment_plan": treatment_plan,
        },
    )

    return {
        "diagnosis": diagnosis,
        "treatment_plan": treatment_plan,
    }


def complete_session(
    session: SimulationSession,
) -> dict[str, Any]:
    """Complete an active session after diagnosis, regardless of phase."""
    advance_phase(session, SimulationPhase.COMPLETED)

    return session.to_dict()


def patient_dialogue_history(messages: list[SimulationMessage]) -> list[dict[str, str]]:
    """Patient-only history: F05 clinical findings must never reach patient LLM context."""
    return [
        {"role": message.role, "content": message.content}
        for message in messages
        if (message.role == "user" and message.action == "patient_question")
        or (message.role == "assistant" and message.action == "patient_response")
    ]
