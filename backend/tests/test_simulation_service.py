
from uuid import uuid4

from app.simulation.local_store import LocalSimulationStore
from app.services.simulation_service import SimulationService
from app.simulation.engine import SimulationSession


def test_persist_and_retrieve_engine_session(tmp_path):
    store = LocalSimulationStore(tmp_path / "service.db")
    service = SimulationService(store)
    user_id = str(uuid4())

    session = SimulationSession(
        case_data={"case_id": "service-test", "symptoms": ["fever"]}
    )

    session_id = service.persist_new_session(user_id, session)

    saved = service.get_session(session_id, user_id)

    assert saved is not None
    assert saved["id"] == session_id
    assert saved["case_data"]["case_id"] == "service-test"
    assert saved["state"]["current_phase"] == "introduction"


def test_persist_session_events(tmp_path):
    store = LocalSimulationStore(tmp_path / "events.db")
    service = SimulationService(store)
    user_id = str(uuid4())

    session = SimulationSession(
        case_data={"case_id": "events-test"}
    )

    session_id = service.persist_new_session(user_id, session)
    events = service.list_events(session_id, user_id)

    assert events is not None
    assert len(events) == len(session.events)
    assert [
        event["sequence_number"] for event in events
    ] == list(range(1, len(events) + 1))


def test_service_does_not_return_another_users_session(tmp_path):
    store = LocalSimulationStore(tmp_path / "ownership.db")
    service = SimulationService(store)
    owner_id = str(uuid4())
    other_user_id = str(uuid4())

    session = SimulationSession(
        case_data={"case_id": "ownership-test"}
    )

    session_id = service.persist_new_session(owner_id, session)

    assert service.get_session(session_id, other_user_id) is None
    assert service.list_events(session_id, other_user_id) is None
