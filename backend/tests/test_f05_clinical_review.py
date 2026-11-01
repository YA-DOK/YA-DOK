from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.routes import simulation
from app.core.security import get_current_user
from app.feature05.clinical_review import build_clinical_review
from app.main import app
from app.simulation.engine import (
    SimulationPhase,
    advance_phase,
    create_session,
    request_examination,
    request_investigation,
)

CASE = {
    "case_id": "SYN-F05-REVIEW",
    "exam_items": [
        {"id": "temperature", "label": "Body Temperature", "value": 38.7, "unit": "C", "relevance": "essential"},
        {"id": "lung_exam", "label": "Chest Auscultation", "finding": "SECRET CRACKLES", "relevance": "essential"},
    ],
    "case_investigation_items": [
        {"id": "cbc", "label": "Complete Blood Count", "relevance": "helpful",
         "results": [{"label": "WBC", "value": 18000, "unit": "/uL"}]},
        {"id": "crp", "label": "CRP", "relevance": "not_indicated", "results": []},
    ],
    "imaging": [{"id": "cxr", "label": "Chest X-ray", "report_text": "SECRET INFILTRATE", "relevance": "essential"}],
}


def make_session():
    s = create_session(CASE)
    advance_phase(s, SimulationPhase.HISTORY_TAKING)
    advance_phase(s, SimulationPhase.EXAMINATION)
    assert request_examination(s, "Body Temperature")["status"] == "completed"
    assert request_examination(s, "Body Temperature")["status"] == "already_requested"
    advance_phase(s, SimulationPhase.INVESTIGATIONS)
    assert request_investigation(s, "Complete Blood Count")["status"] == "completed"
    assert request_investigation(s, "CRP")["status"] == "unavailable"
    advance_phase(s, SimulationPhase.DIAGNOSIS_AND_PLAN)
    s.is_completed = True
    s.current_phase = SimulationPhase.COMPLETED
    return s


def test_summary_counts_and_essential_gap():
    result = build_clinical_review(make_session())
    assert result["request_counts"] == {
        "examination": 2, "investigation_or_imaging": 2, "repeated": 1,
        "unavailable": 1, "not_indicated": 1, "unrated": 0,
    }
    assert result["essential_actions"] == {"total": 3, "attempted": 1, "not_requested": 2}
    assert result["penalty_points"] is None


def test_timing_from_saved_events_not_result_release_delay():
    s = make_session()
    first = s.events[0].timestamp
    requests = [ev for ev in s.events if ev.event_type in ("examination_requested", "investigation_requested")]
    for index, ev in enumerate(requests, 1):
        ev.timestamp = first + timedelta(seconds=index * 3)
    timing = build_clinical_review(s)["request_timing"]
    assert timing["first_request_seconds"] == 3
    assert timing["last_request_seconds"] == 12
    assert timing["recorded_request_count"] == 4
    assert build_clinical_review(s)["result_release_delay"] == "not_configured_in_blueprint_v3_2"


def test_no_case_results_or_medical_secrets_in_review():
    s = make_session()
    result = str(build_clinical_review(s))
    assert "SECRET" not in result
    assert "18000" not in result
    assert "38.7" not in result


def test_live_session_is_not_reviewable():
    s = make_session()
    s.is_completed = False
    with pytest.raises(ValueError):
        build_clinical_review(s)


def test_legacy_session_empty_rubric_is_not_scored():
    s = create_session({"examination": {"abc": "normal"}})
    s.is_completed = True
    review = build_clinical_review(s)
    assert review["essential_actions"]["total"] == 0
    assert review["penalty_status"] == "requires_clinician_approved_rubric"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(simulation, "_pg_service", lambda: None)
    app.dependency_overrides[get_current_user] = lambda: {"id": "f05-owner"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_user, None)
    simulation.sessions.clear()
    simulation.session_owners.clear()


def test_endpoint_requires_completion(client):
    s = make_session()
    s.is_completed = False
    simulation.sessions[s.session_id] = s
    simulation.session_owners[s.session_id] = "f05-owner"
    res = client.get(f"/api/v1/simulation/sessions/{s.session_id}/clinical-review")
    assert res.status_code == 409


def test_endpoint_requires_owner(client):
    s = make_session()
    simulation.sessions[s.session_id] = s
    simulation.session_owners[s.session_id] = "someone-else"
    res = client.get(f"/api/v1/simulation/sessions/{s.session_id}/clinical-review")
    assert res.status_code == 404


def test_endpoint_returns_review_for_completed_owner(client):
    s = make_session()
    simulation.sessions[s.session_id] = s
    simulation.session_owners[s.session_id] = "f05-owner"
    res = client.get(f"/api/v1/simulation/sessions/{s.session_id}/clinical-review")
    assert res.status_code == 200
    assert res.json()["request_counts"]["repeated"] == 1
    assert "SECRET" not in res.text
