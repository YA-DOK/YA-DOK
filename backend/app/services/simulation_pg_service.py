from datetime import timezone
from copy import deepcopy
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

import app.models.profile  # Register profiles FK target
from app.models.simulation_session import SimulationSessionModel
from app.models.simulation_event import SimulationEventModel
from app.models.simulation_action_request import SimulationActionRequestModel
from app.services.simulation_service import SimulationService, _json_safe
from app.simulation.action_request import (
    classify_request,
    create_action_identity,
)
from app.simulation.engine import (
    SimulationEvent,
    SimulationMessage,
    SimulationPhase,
    SimulationSession,
    create_session,
)


class SessionNotFound(Exception):
    pass


def _state(session: SimulationSession) -> dict[str, Any]:
    state = SimulationService._session_state(session)
    state["mode"] = getattr(session, "mode", "training")
    for key in (
        "case_code",
        "case_version_id",
        "version_number",
        "duration_minutes",
    ):
        state[key] = getattr(session, key, None)
    return state


def _hydrate(row, events) -> SimulationSession:
    state = row.state_json or {}

    session = SimulationSession(
        case_data=deepcopy(row.case_data),
        session_id=str(row.id),
        current_phase=SimulationPhase(
            state.get("current_phase", row.current_phase)
        ),
        messages=[
            SimulationMessage(
                role=item["role"],
                content=item["content"],
                action=item.get("action", "chat"),
            )
            for item in state.get("messages", [])
        ],
        requested_examinations=list(
            state.get("requested_examinations", [])
        ),
        requested_investigations=list(
            state.get("requested_investigations", [])
        ),
        diagnosis=state.get("diagnosis"),
        treatment_plan=state.get("treatment_plan"),
        is_paused=bool(state.get("is_paused", row.is_paused)),
        is_completed=bool(
            state.get("is_completed", row.is_completed)
        ),
    )

    for event in events:
        session.events.append(
            SimulationEvent(
                event_id=str(event.id),
                event_type=event.event_type,
                phase=SimulationPhase(event.phase),
                details=deepcopy(event.details),
                timestamp=event.created_at.astimezone(timezone.utc),
            )
        )

    session.mode = state.get("mode", "training")
    for key in (
        "case_code",
        "case_version_id",
        "version_number",
        "duration_minutes",
    ):
        setattr(session, key, state.get(key))
    return session


class PostgresSimulationService:
    """Atomic PostgreSQL session and action persistence."""

    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    @staticmethod
    def _events(db, session_id: UUID):
        return list(
            db.scalars(
                select(SimulationEventModel)
                .where(SimulationEventModel.session_id == session_id)
                .order_by(SimulationEventModel.sequence_number)
            )
        )

    @staticmethod
    def _append_events(db, session, start_index):
        session_uuid = UUID(str(session.session_id))

        for index in range(start_index, len(session.events)):
            event = session.events[index]
            db.add(
                SimulationEventModel(
                    id=UUID(str(event.event_id)),
                    session_id=session_uuid,
                    sequence_number=index + 1,
                    event_type=event.event_type,
                    phase=event.phase.value,
                    details=_json_safe(event.details),
                    created_at=event.timestamp,
                )
            )

    @staticmethod
    def _save_state(row, session):
        row.state_json = _state(session)
        row.current_phase = session.current_phase.value
        row.is_paused = session.is_paused
        row.is_completed = session.is_completed
        row.diagnosis = session.diagnosis
        row.treatment_plan = session.treatment_plan

    def create(
        self,
        user_id: str,
        case_data: dict,
        case_version_id: str | None = None,
        mode: str = "training",
    ) -> SimulationSession:
        if mode not in ("training", "test"):
            raise ValueError("Invalid simulation mode.")
        session = create_session(deepcopy(case_data))
        session.mode = mode

        with self.session_factory.begin() as db:
            row = SimulationSessionModel(
                id=UUID(session.session_id),
                user_id=UUID(str(user_id)),
                case_version_id=(
                    UUID(str(case_version_id))
                    if case_version_id else None
                ),
                case_data=_json_safe(session.case_data),
                state_json=_state(session),
                current_phase=session.current_phase.value,
                is_paused=False,
                is_completed=False,
            )
            db.add(row)
            db.flush()
            self._append_events(db, session, 0)

        return session

    def load(
        self,
        user_id: str,
        session_id: str,
    ) -> SimulationSession:
        sid = UUID(str(session_id))
        uid = UUID(str(user_id))

        with self.session_factory() as db:
            row = db.scalar(
                select(SimulationSessionModel).where(
                    SimulationSessionModel.id == sid,
                    SimulationSessionModel.user_id == uid,
                )
            )

            if row is None:
                raise SessionNotFound()

            return _hydrate(row, self._events(db, sid))

    def apply_action(
        self,
        user_id: str,
        session_id: str,
        request_id: str,
        action: str,
        payload: dict,
        handler: Callable[[SimulationSession], Any],
    ) -> Any:
        identity = create_action_identity(
            session_id, request_id, action, payload
        )
        uid = UUID(str(user_id))

        with self.session_factory.begin() as db:
            row = db.scalar(
                select(SimulationSessionModel)
                .where(
                    SimulationSessionModel.id == identity.session_id,
                    SimulationSessionModel.user_id == uid,
                )
                .with_for_update()
            )

            if row is None:
                raise SessionNotFound()

            previous = db.get(
                SimulationActionRequestModel,
                (identity.session_id, identity.request_id),
            )

            if previous is not None:
                classify_request(
                    previous.fingerprint,
                    identity.fingerprint,
                )
                return deepcopy(previous.response_json)

            events = self._events(db, identity.session_id)
            session = _hydrate(row, events)
            old_count = len(session.events)

            response = _json_safe(handler(session))

            self._save_state(row, session)
            self._append_events(db, session, old_count)

            db.add(
                SimulationActionRequestModel(
                    session_id=identity.session_id,
                    request_id=identity.request_id,
                    fingerprint=identity.fingerprint,
                    response_json=response,
                )
            )

        return response
