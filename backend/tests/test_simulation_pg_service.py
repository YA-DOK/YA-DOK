from types import SimpleNamespace
from uuid import UUID

from app.services.simulation_pg_service import _hydrate, _state
from app.simulation.engine import (
    create_session,
    pause_session,
)


def test_complete_session_snapshot_roundtrip():
    case_data = {"patient": {"age": 10}}
    original = create_session(case_data)
    pause_session(original)

    row = SimpleNamespace(
        id=UUID(original.session_id),
        case_data=case_data,
        state_json=_state(original),
        current_phase=original.current_phase.value,
        is_paused=original.is_paused,
        is_completed=original.is_completed,
    )

    events = [
        SimpleNamespace(
            id=UUID(event.event_id),
            event_type=event.event_type,
            phase=event.phase.value,
            details=event.details,
            created_at=event.timestamp,
        )
        for event in original.events
    ]

    restored = _hydrate(row, events)

    assert restored.to_dict() == original.to_dict()
    assert restored.case_data == case_data
    assert restored.is_paused is True
