"""F03/F04 route contract tests using FastAPI OpenAPI."""

from app.main import app


def test_f04_message_routes_registered():
    paths = app.openapi()["paths"]
    path = "/api/v1/simulation/sessions/{session_id}/messages"

    assert path in paths
    assert "post" in paths[path]
    assert "get" in paths[path]


def test_existing_f03_routes_remain_registered():
    paths = app.openapi()["paths"]

    phase = "/api/v1/simulation/sessions/{session_id}/phase"
    patient = "/api/v1/simulation/sessions/{session_id}/patient-question"

    assert "post" in paths[phase]
    assert "post" in paths[patient]
