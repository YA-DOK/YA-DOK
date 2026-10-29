
from uuid import uuid4

from app.simulation.local_store import LocalSimulationStore


def test_create_and_retrieve_session(tmp_path):
    store = LocalSimulationStore(tmp_path / "test.db")
    user_id = str(uuid4())

    session_id = store.create_session(
        user_id=user_id,
        case_data={"case_id": "demo-001", "symptoms": ["fever"]},
        state={"current_phase": "introduction"},
    )

    session = store.get_session(session_id, user_id)

    assert session is not None
    assert session["id"] == session_id
    assert session["case_data"]["case_id"] == "demo-001"
    assert session["state"]["current_phase"] == "introduction"


def test_append_and_list_events(tmp_path):
    store = LocalSimulationStore(tmp_path / "test.db")
    user_id = str(uuid4())

    session_id = store.create_session(
        user_id=user_id,
        case_data={"case_id": "demo-002"},
    )

    store.append_event(
        session_id=session_id,
        user_id=user_id,
        event={
            "event_id": str(uuid4()),
            "event_type": "session_created",
            "phase": "introduction",
            "details": {"source": "test"},
        },
        sequence_number=1,
    )

    events = store.list_events(session_id, user_id)

    assert events is not None
    assert len(events) == 1
    assert events[0]["sequence_number"] == 1
    assert events[0]["details"]["source"] == "test"


def test_user_cannot_read_another_users_session(tmp_path):
    store = LocalSimulationStore(tmp_path / "test.db")
    owner_id = str(uuid4())
    other_user_id = str(uuid4())

    session_id = store.create_session(
        user_id=owner_id,
        case_data={"case_id": "demo-003"},
    )

    assert store.get_session(session_id, other_user_id) is None
    assert store.list_events(session_id, other_user_id) is None


def test_save_state_updates_session(tmp_path):
    store = LocalSimulationStore(tmp_path / "test.db")
    user_id = str(uuid4())

    session_id = store.create_session(
        user_id=user_id,
        case_data={"case_id": "demo-004"},
    )

    saved = store.save_state(
        session_id=session_id,
        user_id=user_id,
        state={
            "current_phase": "history_taking",
            "is_paused": True,
            "is_completed": False,
            "diagnosis": None,
            "treatment_plan": None,
        },
    )

    session = store.get_session(session_id, user_id)

    assert saved is True
    assert session is not None
    assert session["current_phase"] == "history_taking"
    assert session["is_paused"] is True


def test_save_state_rejects_wrong_owner(tmp_path):
    store = LocalSimulationStore(tmp_path / "test.db")
    owner_id = str(uuid4())
    other_user_id = str(uuid4())

    session_id = store.create_session(
        user_id=owner_id,
        case_data={"case_id": "demo-005"},
    )

    saved = store.save_state(
        session_id=session_id,
        user_id=other_user_id,
        state={"current_phase": "introduction"},
    )

    assert saved is False
