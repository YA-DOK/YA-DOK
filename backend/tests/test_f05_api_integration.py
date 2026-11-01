"""Verify new F05 endpoints use F01 ownership and existing F03 sessions."""
from fastapi.testclient import TestClient

from app.api.routes import simulation
from app.core.security import get_current_user
from app.main import app
from app.simulation.engine import create_session

USER = "test-clinical-user"

async def current():
    return {"id": USER}


def test_authenticated_catalogue_does_not_leak_results(monkeypatch):
    monkeypatch.setattr(simulation, "_pg_service", lambda: None)
    session = create_session({
        "exam_items": [{"id": "chest", "label": "Chest", "system": "chest",
                        "finding": "PRIVATE FINDING", "relevance": "essential"}],
        "investigations": {}, "imaging": [],
    })
    simulation.sessions[session.session_id] = session
    simulation.session_owners[session.session_id] = USER
    app.dependency_overrides[get_current_user] = current
    try:
        res = TestClient(app).get(f"/api/v1/simulation/sessions/{session.session_id}/clinical-options")
        assert res.status_code == 200
        assert res.json()["examinations"][0]["id"] == "chest"
        assert "PRIVATE FINDING" not in res.text
        assert "essential" not in res.text
    finally:
        simulation.sessions.pop(session.session_id, None)
        simulation.session_owners.pop(session.session_id, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_other_student_cannot_discover_exam_catalogue(monkeypatch):
    monkeypatch.setattr(simulation, "_pg_service", lambda: None)
    session = create_session({"exam_items": [{"id": "secret", "label": "Hidden", "system": "exam"}]})
    simulation.sessions[session.session_id] = session
    simulation.session_owners[session.session_id] = "another-user"
    app.dependency_overrides[get_current_user] = current
    try:
        res = TestClient(app).get(f"/api/v1/simulation/sessions/{session.session_id}/clinical-options")
        assert res.status_code == 404
    finally:
        simulation.sessions.pop(session.session_id, None)
        simulation.session_owners.pop(session.session_id, None)
        app.dependency_overrides.pop(get_current_user, None)
