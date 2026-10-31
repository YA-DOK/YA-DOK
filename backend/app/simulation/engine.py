
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    return datetime.now(timezone.utc)


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
    """Advance the session by exactly one phase and log it."""
    _ensure_active(session)

    previous_phase = session.current_phase
    next_phase = transition_phase(
        previous_phase,
        requested_phase,
    )

    if next_phase == SimulationPhase.COMPLETED and (
        not session.diagnosis or not session.treatment_plan
    ):
        raise SimulationError(
            "Submit a diagnosis and treatment plan before completion."
        )

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
    _ensure_phase(
        session,
        SimulationPhase.HISTORY_TAKING,
    )

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
    _ensure_phase(
        session,
        SimulationPhase.HISTORY_TAKING,
    )

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


def request_examination(
    session: SimulationSession,
    examination_name: str,
) -> dict[str, Any]:
    """Return examination findings only when they exist in the case."""
    _ensure_phase(
        session,
        SimulationPhase.EXAMINATION,
    )

    examination_name = examination_name.strip()

    if not examination_name:
        raise SimulationError("Examination name cannot be empty.")

    session.requested_examinations.append(examination_name)

    # Support both keys used by different case-data formats.
    findings = session.case_data.get("physical_examination")

    if not isinstance(findings, dict) or not findings:
        findings = session.case_data.get("examination", {})

    if not isinstance(findings, dict):
        findings = {}

    result = _find_case_result(findings, examination_name)

    # Match equivalent labels such as "Abdominal" and
    # "Abdominal examination".
    if result is None:
        requested_normalized = _normalize_examination_name(
            examination_name
        )

        for finding_name, finding_value in findings.items():
            if (
                _normalize_examination_name(str(finding_name))
                == requested_normalized
            ):
                result = finding_value
                break

    if result is None:
        response = {
            "available": False,
            "name": examination_name,
            "result": None,
            "message": (
                "مفيش نتيجة للفحص ده في بيانات الحالة. "
                "ضيفي نتيجة الفحص تحت physical_examination "
                "علشان تظهر في المحاكاة."
            ),
        }
    else:
        response = {
            "available": True,
            "name": examination_name,
            "result": result,
            "message": "تم استرجاع نتيجة الفحص من بيانات الحالة.",
        }

    session.messages.append(
        SimulationMessage(
            role="user",
            content=f"Examination requested: {examination_name}",
            action="request_examination",
        )
    )

    session.messages.append(
        SimulationMessage(
            role="system",
            content=json.dumps(response, ensure_ascii=False),
            action="examination_result",
        )
    )

    session.record_event(
        "examination_requested",
        {
            "name": examination_name,
            "available": response["available"],
            "result": response["result"],
        },
    )

    return response


def request_investigation(
    session: SimulationSession,
    investigation_name: str,
) -> dict[str, Any]:
    """Return a test result only if it exists in the supplied case."""
    _ensure_phase(
        session,
        SimulationPhase.INVESTIGATIONS,
    )

    investigation_name = investigation_name.strip()

    if not investigation_name:
        raise SimulationError(
            "Investigation name cannot be empty."
        )

    session.requested_investigations.append(investigation_name)

    investigations = session.case_data.get(
        "investigations",
        {},
    )

    result = _find_case_result(
        investigations,
        investigation_name,
    )

    if result is None:
        response = {
            "available": False,
            "name": investigation_name,
            "result": None,
            "message": (
                "مفيش نتيجة للتحليل ده في بيانات الحالة."
            ),
        }
    else:
        response = {
            "available": True,
            "name": investigation_name,
            "result": result,
            "message": "تم استرجاع نتيجة التحليل من بيانات الحالة.",
        }

    session.messages.append(
        SimulationMessage(
            role="user",
            content=f"Investigation requested: {investigation_name}",
            action="request_investigation",
        )
    )

    session.messages.append(
        SimulationMessage(
            role="system",
            content=json.dumps(response, ensure_ascii=False),
            action="investigation_result",
        )
    )

    session.record_event(
        "investigation_requested",
        {
            "name": investigation_name,
            "available": response["available"],
            "result": response["result"],
        },
    )

    return response


def submit_diagnosis_and_plan(
    session: SimulationSession,
    diagnosis: str,
    treatment_plan: str,
) -> dict[str, str]:
    """Record the student's proposed diagnosis and plan."""
    _ensure_phase(
        session,
        SimulationPhase.DIAGNOSIS_AND_PLAN,
    )

    diagnosis = diagnosis.strip()
    treatment_plan = treatment_plan.strip()

    if not diagnosis:
        raise SimulationError("Diagnosis cannot be empty.")

    if not treatment_plan:
        raise SimulationError("Treatment plan cannot be empty.")

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
    """Complete the session after the diagnosis and plan phase."""
    _ensure_phase(
        session,
        SimulationPhase.DIAGNOSIS_AND_PLAN,
    )

    if not session.diagnosis or not session.treatment_plan:
        raise SimulationError(
            "Submit a diagnosis and treatment plan before completion."
        )

    advance_phase(
        session,
        SimulationPhase.COMPLETED,
    )

    return session.to_dict()
