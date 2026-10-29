
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import simulation
from app.core.security import get_current_user
from app.simulation.engine import SimulationPhase


TEST_USER = {
    "id": "test-user-1",
    "email": "student@example.com",
}


async def override_get_current_user():
    return TEST_USER


app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


CASE_DATA = {
    "patient_name": "Ahmed",
    "age": 25,
    "gender": "male",
    "chief_complaint": "Headache",
    "symptoms": ["Headache for two days"],
    "medical_history": [],
    "medications": [],
    "examination": {},
    "investigations": {},
}


@pytest.fixture(autouse=True)
def clear_sessions():
    """Keep every API test independent."""
    simulation.sessions.clear()
    simulation.session_owners.clear()
    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )

    yield

    simulation.sessions.clear()
    simulation.session_owners.clear()
    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )


def create_test_session():
    response = client.post(
        "/api/v1/simulation/sessions",
        json={"case_data": CASE_DATA},
    )
    assert response.status_code == 201
    return response.json()["session_id"]


def advance_to(session_id, phase):
    return client.post(
        f"/api/v1/simulation/sessions/{session_id}/phase",
        json={"phase": phase},
    )


def test_create_simulation_session():
    response = client.post(
        "/api/v1/simulation/sessions",
        json={"case_data": CASE_DATA},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["session_id"]
    assert data["current_phase"] == SimulationPhase.INTRODUCTION.value
    assert data["is_completed"] is False
    assert data["events"][0]["event_type"] == "session_created"


def test_create_session_rejects_empty_case():
    response = client.post(
        "/api/v1/simulation/sessions",
        json={"case_data": {}},
    )

    assert response.status_code == 400


def test_get_existing_session():
    session_id = create_test_session()

    response = client.get(
        f"/api/v1/simulation/sessions/{session_id}"
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id


def test_get_missing_session_returns_404():
    response = client.get(
        "/api/v1/simulation/sessions/not-a-real-session"
    )

    assert response.status_code == 404


def test_user_cannot_access_another_users_session():
    session_id = create_test_session()

    async def override_other_user():
        return {
            "id": "different-user-2",
            "email": "other@example.com",
        }

    app.dependency_overrides[get_current_user] = (
        override_other_user
    )

    try:
        response = client.get(
            f"/api/v1/simulation/sessions/{session_id}"
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = (
            override_get_current_user
        )


def test_user_cannot_change_another_users_session():
    session_id = create_test_session()

    async def override_other_user():
        return {
            "id": "different-user-2",
            "email": "other@example.com",
        }

    app.dependency_overrides[get_current_user] = (
        override_other_user
    )

    try:
        response = client.post(
            f"/api/v1/simulation/sessions/{session_id}/phase",
            json={"phase": "history_taking"},
        )
        assert response.status_code == 404
        assert (
            simulation.sessions[session_id].current_phase
            == SimulationPhase.INTRODUCTION
        )
    finally:
        app.dependency_overrides[get_current_user] = (
            override_get_current_user
        )


def test_advance_to_history_taking():
    session_id = create_test_session()

    response = advance_to(session_id, "history_taking")

    assert response.status_code == 200
    assert response.json()["current_phase"] == "history_taking"


def test_cannot_skip_simulation_phase():
    session_id = create_test_session()

    response = advance_to(session_id, "examination")

    assert response.status_code == 409


def test_phase_request_rejects_invalid_phase():
    session_id = create_test_session()

    response = advance_to(session_id, "not_a_real_phase")

    assert response.status_code == 422


def test_examination_returns_unavailable_when_result_missing():
    session_id = create_test_session()
    assert advance_to(session_id, "history_taking").status_code == 200
    assert advance_to(session_id, "examination").status_code == 200

    response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/examinations",
        json={"examination_name": "General examination"},
    )

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["result"] is None


def test_examination_rejected_in_wrong_phase():
    session_id = create_test_session()

    response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/examinations",
        json={"examination_name": "General examination"},
    )

    assert response.status_code == 400


def test_investigation_returns_unavailable_when_result_missing():
    session_id = create_test_session()
    assert advance_to(session_id, "history_taking").status_code == 200
    assert advance_to(session_id, "examination").status_code == 200
    assert advance_to(session_id, "investigations").status_code == 200

    response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/investigations",
        json={"investigation_name": "Complete Blood Count"},
    )

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["result"] is None


def test_diagnosis_and_completion():
    session_id = create_test_session()
    assert advance_to(session_id, "history_taking").status_code == 200
    assert advance_to(session_id, "examination").status_code == 200
    assert advance_to(session_id, "investigations").status_code == 200
    assert advance_to(session_id, "diagnosis_and_plan").status_code == 200

    diagnosis_response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/diagnosis",
        json={
            "diagnosis": "Provisional headache diagnosis",
            "treatment_plan": (
                "Complete assessment before deciding on treatment."
            ),
        },
    )

    assert diagnosis_response.status_code == 200

    completion_response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/complete"
    )

    assert completion_response.status_code == 200
    assert completion_response.json()["current_phase"] == "completed"
    assert completion_response.json()["is_completed"] is True


def test_cannot_complete_without_diagnosis():
    session_id = create_test_session()
    assert advance_to(session_id, "history_taking").status_code == 200
    assert advance_to(session_id, "examination").status_code == 200
    assert advance_to(session_id, "investigations").status_code == 200
    assert advance_to(session_id, "diagnosis_and_plan").status_code == 200

    response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/complete"
    )

    assert response.status_code == 400


def test_patient_question_uses_mocked_agent(monkeypatch):
    session_id = create_test_session()
    assert advance_to(session_id, "history_taking").status_code == 200

    class FakePatientAgent:
        def __init__(self, llm_service):
            pass

        async def respond(self, case_data, messages, question):
            assert question == "What brought you here?"
            return "I have had a headache for two days."

    monkeypatch.setattr(
        simulation,
        "PatientAgent",
        FakePatientAgent,
    )

    response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/patient-question",
        json={"question": "What brought you here?"},
    )

    assert response.status_code == 200
    assert response.json()["response"] == (
        "I have had a headache for two days."
    )


def test_patient_question_rejects_empty_question():
    session_id = create_test_session()
    assert advance_to(session_id, "history_taking").status_code == 200

    response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/patient-question",
        json={"question": ""},
    )

    assert response.status_code == 422



def test_pause_and_resume_simulation():
    session_id = create_test_session()

    pause_response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/pause"
    )

    assert pause_response.status_code == 200
    assert pause_response.json()["is_paused"] is True

    resume_response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/resume"
    )

    assert resume_response.status_code == 200
    assert resume_response.json()["is_paused"] is False


def test_paused_simulation_cannot_advance_phase():
    session_id = create_test_session()

    pause_response = client.post(
        f"/api/v1/simulation/sessions/{session_id}/pause"
    )
    assert pause_response.status_code == 200

    phase_response = advance_to(
        session_id,
        "history_taking",
    )

    assert phase_response.status_code == 400
    assert (
        simulation.sessions[session_id].current_phase
        == SimulationPhase.INTRODUCTION
    )


def test_user_cannot_pause_another_users_simulation():
    session_id = create_test_session()

    async def override_other_user():
        return {
            "id": "different-user-2",
            "email": "other@example.com",
        }

    app.dependency_overrides[get_current_user] = (
        override_other_user
    )

    try:
        response = client.post(
            f"/api/v1/simulation/sessions/{session_id}/pause"
        )

        assert response.status_code == 404
        assert simulation.sessions[session_id].is_paused is False
    finally:
        app.dependency_overrides[get_current_user] = (
            override_get_current_user
        )
