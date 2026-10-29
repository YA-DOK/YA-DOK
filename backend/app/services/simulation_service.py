
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.simulation.engine import (
    SimulationEvent,
    SimulationMessage,
    SimulationPhase,
    SimulationSession,
)
from app.simulation.local_store import LocalSimulationStore


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    return str(value)


def _phase_value(phase: Any) -> str:
    return str(getattr(phase, "value", phase))


class SimulationService:
    """Persistence service for local Simulation Engine development."""

    def __init__(self, store: LocalSimulationStore | None = None):
        self.store = store or LocalSimulationStore()

    @staticmethod
    def _session_state(session: SimulationSession) -> dict[str, Any]:
        return _json_safe(
            {
                "current_phase": _phase_value(session.current_phase),
                "messages": [
                    {
                        "role": message.role,
                        "content": message.content,
                        "action": message.action,
                    }
                    for message in session.messages
                ],
                "requested_investigations": session.requested_investigations,
                "requested_examinations": session.requested_examinations,
                "diagnosis": session.diagnosis,
                "treatment_plan": session.treatment_plan,
                "is_paused": session.is_paused,
                "is_completed": session.is_completed,
            }
        )

    def persist_new_session(
        self,
        user_id: str,
        session: SimulationSession,
    ) -> str:
        session_id = str(session.session_id)

        self.store.create_session(
            user_id=str(user_id),
            case_data=_json_safe(session.case_data),
            state=self._session_state(session),
            session_id=session_id,
        )
        self.sync_session(user_id, session)
        return session_id

    def save_session_state(
        self,
        user_id: str,
        session: SimulationSession,
    ) -> bool:
        return self.store.save_state(
            session_id=str(session.session_id),
            user_id=str(user_id),
            state=self._session_state(session),
        )

    def persist_new_events(
        self,
        user_id: str,
        session: SimulationSession,
        start_index: int,
    ) -> int:
        if start_index < 0 or start_index > len(session.events):
            raise ValueError("Invalid event start index.")

        for index in range(start_index, len(session.events)):
            event_data = _json_safe(session.events[index].to_dict())
            self.store.append_event(
                session_id=str(session.session_id),
                user_id=str(user_id),
                event=event_data,
                sequence_number=index + 1,
            )

        return len(session.events)

    def sync_session(
        self,
        user_id: str,
        session: SimulationSession,
    ) -> None:
        """Save current state and append only events not already stored."""
        session_id = str(session.session_id)
        user_id = str(user_id)

        existing = self.store.get_session(session_id, user_id)
        if existing is None:
            self.persist_new_session(user_id, session)
            return

        if not self.save_session_state(user_id, session):
            raise ValueError("Simulation session not found.")

        stored_events = self.store.list_events(session_id, user_id)
        if stored_events is None:
            raise ValueError("Simulation session not found.")

        self.persist_new_events(
            user_id=user_id,
            session=session,
            start_index=len(stored_events),
        )

    def get_session(self, session_id: str, user_id: str):
        return self.store.get_session(
            session_id=str(session_id),
            user_id=str(user_id),
        )

    def list_events(self, session_id: str, user_id: str):
        return self.store.list_events(
            session_id=str(session_id),
            user_id=str(user_id),
        )

    def restore_session(
        self,
        session_id: str,
        user_id: str,
    ) -> SimulationSession | None:
        """Rebuild an engine session from SQLite for its verified owner."""
        row = self.get_session(session_id, user_id)
        if row is None:
            return None

        state = row["state"]
        session = SimulationSession(
            case_data=row["case_data"],
            session_id=row["id"],
            current_phase=SimulationPhase(
                state.get("current_phase", row["current_phase"])
            ),
            messages=[
                SimulationMessage(
                    role=message["role"],
                    content=message["content"],
                    action=message.get("action", "chat"),
                )
                for message in state.get("messages", [])
            ],
            requested_investigations=list(
                state.get("requested_investigations", [])
            ),
            requested_examinations=list(
                state.get("requested_examinations", [])
            ),
            diagnosis=state.get("diagnosis"),
            treatment_plan=state.get("treatment_plan"),
            is_completed=bool(
                state.get("is_completed", row["is_completed"])
            ),
            is_paused=bool(
                state.get("is_paused", row["is_paused"])
            ),
        )

        stored_events = self.list_events(session_id, user_id) or []
        for item in stored_events:
            timestamp_text = item.get("created_at")
            timestamp = (
                datetime.fromisoformat(
                    timestamp_text.replace("Z", "+00:00")
                )
                if timestamp_text
                else datetime.now().astimezone()
            )

            session.events.append(
                SimulationEvent(
                    event_id=item["id"],
                    event_type=item["event_type"],
                    phase=SimulationPhase(item["phase"]),
                    details=item.get("details", {}),
                    timestamp=timestamp,
                )
            )

        return session
