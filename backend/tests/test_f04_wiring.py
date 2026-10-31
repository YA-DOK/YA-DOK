"""Run in the REAL repository with all F02/F03 modules installed."""
from app.main import app


def test_f04_message_routes_registered():
    paths = {(route.path, method)
             for route in app.routes
             for method in getattr(route, "methods", set())}
    path = "/api/v1/simulation/sessions/{session_id}/messages"
    assert (path, "POST") in paths
    assert (path, "GET") in paths


def test_existing_f03_routes_remain_registered():
    paths = {route.path for route in app.routes}
    assert "/api/v1/simulation/sessions/{session_id}/phase" in paths
    assert "/api/v1/simulation/sessions/{session_id}/patient-question" in paths
