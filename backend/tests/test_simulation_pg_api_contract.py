from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.routes import simulation
from app.core.security import get_current_user
from app.main import app
from app.simulation.action_request import (
    classify_request,
    create_action_identity,
)
from app.simulation.engine import create_session

USER_ID = str(uuid4())
OTHER_USER_ID = str(uuid4())


class FakePostgresService:
    """API contract fake; not a PostgreSQL integration test."""

    def __init__(self):
        self.session = create_session({"patient": "synthetic"})
        self.owner = USER_ID
        self.saved = {}

    def load(self, user_id, session_id):
        from app.services.simulation_pg_service import SessionNotFound

        if user_id != self.owner or session_id != self.session.session_id:
            raise SessionNotFound()

        return self.session

    def apply_action(
        self, user_id, session_id, request_id,
        action, payload, handler
    ):
        session = self.load(user_id, session_id)
        identity = create_action_identity(
            session_id, request_id, action, payload
        )
        key = (session_id, request_id)

        if key in self.saved:
            fingerprint, response = self.saved[key]
            classify_request(fingerprint, identity.fingerprint)
            return response

        response = handler(session)
        self.saved[key] = (identity.fingerprint, response)
        return response


@pytest.fixture
def client_and_store(monkeypatch):
    store = FakePostgresService()
    original = app.dependency_overrides.copy()

    async def authenticated():
        return {"id": USER_ID}

    app.dependency_overrides[get_current_user] = authenticated
    monkeypatch.setattr(simulation, "_pg_service", lambda: store)

    try:
        with TestClient(app) as client:
            yield client, store
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


def test_pg_mode_rejects_missing_isolated_url(monkeypatch):
    monkeypatch.setenv("YA_DOK_F03_STORAGE", "postgres")
    monkeypatch.delenv("F03_TEST_DATABASE_URL", raising=False)
    simulation._isolated_pg_factory.cache_clear()

    with pytest.raises(HTTPException) as error:
        simulation._pg_service()

    assert error.value.status_code == 503


def test_pg_mode_rejects_shared_cloud_url(monkeypatch):
    monkeypatch.setenv("YA_DOK_F03_STORAGE", "postgres")
    monkeypatch.setenv(
        "F03_TEST_DATABASE_URL",
        "postgresql+psycopg://user:pass@pooler.supabase.com/postgres",
    )
    simulation._isolated_pg_factory.cache_clear()

    with pytest.raises(HTTPException) as error:
        simulation._pg_service()

    assert error.value.status_code == 503


def test_pg_api_requires_idempotency_key(client_and_store):
    client, store = client_and_store

    response = client.post(
        f"/api/v1/simulation/sessions/{store.session.session_id}/phase",
        json={"phase": "history_taking"},
    )

    assert response.status_code == 400
    assert store.session.current_phase.value == "introduction"


def test_pg_api_identical_retry_and_conflict(client_and_store):
    client, store = client_and_store
    url = (
        f"/api/v1/simulation/sessions/"
        f"{store.session.session_id}/phase"
    )
    headers = {"Idempotency-Key": str(uuid4())}

    first = client.post(
        url,
        json={"phase": "history_taking"},
        headers=headers,
    )
    assert first.status_code == 200, first.text

    event_count = len(store.session.events)

    replay = client.post(
        url,
        json={"phase": "history_taking"},
        headers=headers,
    )

    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert len(store.session.events) == event_count

    conflict = client.post(
        url,
        json={"phase": "examination"},
        headers=headers,
    )

    assert conflict.status_code == 409
    assert len(store.session.events) == event_count


def test_pg_api_denies_other_user(client_and_store):
    client, store = client_and_store
    original = app.dependency_overrides.copy()

    async def other_user():
        return {"id": OTHER_USER_ID}

    app.dependency_overrides[get_current_user] = other_user

    try:
        response = client.get(
            f"/api/v1/simulation/sessions/{store.session.session_id}"
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)
