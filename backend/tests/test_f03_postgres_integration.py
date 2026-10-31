import os
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.services.simulation_pg_service import (
    PostgresSimulationService,
    SessionNotFound,
)
from app.simulation.action_request import IdempotencyConflict
from app.simulation.engine import (
    SimulationPhase,
    advance_phase,
)


@pytest.fixture
def pg():
    raw = os.environ.get("F03_TEST_DATABASE_URL")
    if not raw:
        pytest.skip("Isolated PostgreSQL URL not configured")

    url = make_url(raw)
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or url.database != "yadok_f03_test"
    ):
        pytest.fail("Unsafe database target: local F03 test DB required")

    engine = create_engine(raw, pool_pre_ping=True)

    with engine.connect() as conn:
        existing = set(inspect(conn).get_table_names())
        required = {
            "profiles",
            "simulation_sessions",
            "simulation_events",
            "simulation_action_requests",
        }
        assert required.issubset(existing)

    factory = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    owner, stranger = uuid4(), uuid4()

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO profiles (id) VALUES (:a), (:b)"),
            {"a": owner, "b": stranger},
        )

    try:
        yield (
            PostgresSimulationService(factory),
            str(owner),
            str(stranger),
            engine,
        )
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM profiles WHERE id IN (:a, :b)"),
                {"a": owner, "b": stranger},
            )
        engine.dispose()


def move_to_history(session):
    advance_phase(session, SimulationPhase.HISTORY_TAKING)
    return session.to_dict()


def test_pg_restores_complete_session_and_protects_owner(pg):
    service, owner, stranger, _ = pg
    case = {"patient": {"age_months": 18}}

    original = service.create(owner, case)
    restored = PostgresSimulationService(
        service.session_factory
    ).load(owner, original.session_id)

    assert restored.case_data == case
    assert restored.to_dict() == original.to_dict()

    with pytest.raises(SessionNotFound):
        service.load(stranger, original.session_id)


def test_pg_idempotency_and_conflict(pg):
    service, owner, _, _ = pg
    session = service.create(owner, {"patient": "synthetic"})
    key = str(uuid4())

    first = service.apply_action(
        owner, session.session_id, key,
        "phase", {"phase": "history_taking"}, move_to_history,
    )
    count = len(service.load(owner, session.session_id).events)

    replay = PostgresSimulationService(
        service.session_factory
    ).apply_action(
        owner, session.session_id, key,
        "phase", {"phase": "history_taking"}, move_to_history,
    )

    assert replay == first
    assert len(service.load(owner, session.session_id).events) == count

    with pytest.raises(IdempotencyConflict):
        service.apply_action(
            owner, session.session_id, key,
            "phase", {"phase": "examination"}, move_to_history,
        )


def test_pg_database_failure_rolls_back_everything(pg):
    service, owner, _, engine = pg
    session = service.create(owner, {"patient": "synthetic"})
    before = service.load(owner, session.session_id).to_dict()
    key = str(uuid4())

    def bad_event(s):
        advance_phase(s, SimulationPhase.HISTORY_TAKING)
        s.events[-1].event_id = s.events[0].event_id
        return s.to_dict()

    with pytest.raises(IntegrityError):
        service.apply_action(
            owner, session.session_id, key,
            "rollback_probe", {}, bad_event,
        )

    assert service.load(owner, session.session_id).to_dict() == before

    with engine.connect() as conn:
        count = conn.scalar(
            text(
                "SELECT COUNT(*) FROM simulation_action_requests "
                "WHERE session_id = :sid AND request_id = :rid"
            ),
            {"sid": UUID(session.session_id), "rid": UUID(key)},
        )
    assert count == 0


def test_pg_concurrent_duplicate_request(pg):
    service, owner, _, _ = pg
    session = service.create(owner, {"patient": "synthetic"})
    key = str(uuid4())

    def worker(_):
        return PostgresSimulationService(
            service.session_factory
        ).apply_action(
            owner, session.session_id, key,
            "phase", {"phase": "history_taking"}, move_to_history,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(worker, range(2)))

    assert results[0] == results[1]

    restored = service.load(owner, session.session_id)
    assert restored.current_phase == SimulationPhase.HISTORY_TAKING
    assert len(restored.events) == 2


def test_pg_real_http_session_lifecycle(pg, monkeypatch):
    from fastapi.testclient import TestClient

    from app.api.routes import simulation as routes
    from app.core.security import get_current_user
    from app.main import app

    service, owner, stranger, _ = pg
    old_overrides = app.dependency_overrides.copy()

    monkeypatch.setattr(routes.settings, "app_env", "development")
    monkeypatch.setenv("F03_ALLOW_SYNTHETIC", "1")
    monkeypatch.setenv("YA_DOK_F03_STORAGE", "postgres")

    # Each request gets a fresh service using the real PostgreSQL pool.
    monkeypatch.setattr(
        routes,
        "_pg_service",
        lambda: PostgresSimulationService(service.session_factory),
    )

    app.dependency_overrides[get_current_user] = lambda: {"id": owner}

    def check(response, expected=200):
        assert response.status_code == expected, (
            f"HTTP {response.status_code}: {response.text}"
        )
        return response.json()

    def send(client, url, payload=None, key=None):
        kwargs = {
            "headers": {"Idempotency-Key": key or str(uuid4())}
        }
        if payload is not None:
            kwargs["json"] = payload
        return client.post(url, **kwargs)

    try:
        with TestClient(app) as client:
            created = check(
                client.post(
                    "/api/v1/simulation/sessions",
                    json={"case_data": {
                        "patient": {"age_months": 18}
                    }},
                ),
                201,
            )
            sid = created["session_id"]
            base = f"/api/v1/simulation/sessions/{sid}"

            check(client.get(base))
            assert len(service.load(owner, sid).events) == 1

            phase_url = base + "/phase"
            key = str(uuid4())

            first = check(send(
                client, phase_url,
                {"phase": "history_taking"}, key,
            ))
            event_count = len(service.load(owner, sid).events)

            replay = check(send(
                client, phase_url,
                {"phase": "history_taking"}, key,
            ))
            assert replay == first
            assert len(service.load(owner, sid).events) == event_count

            check(send(
                client, phase_url,
                {"phase": "examination"}, key,
            ), 409)

            check(send(
                client, phase_url,
                {"phase": "investigations"},
            ), 409)

            # Real DB ownership, not fake-service ownership.
            app.dependency_overrides[get_current_user] = (
                lambda: {"id": stranger}
            )
            check(client.get(base), 404)
            check(send(client, base + "/pause"), 404)

            app.dependency_overrides[get_current_user] = (
                lambda: {"id": owner}
            )

            check(send(client, base + "/pause"))
            assert service.load(owner, sid).is_paused is True

            check(send(client, base + "/resume"))
            assert service.load(owner, sid).is_paused is False

            for phase in (
                "examination",
                "investigations",
                "diagnosis_and_plan",
            ):
                check(send(
                    client, phase_url, {"phase": phase}
                ))

            check(send(client, base + "/complete"), 400)

            check(send(
                client,
                base + "/diagnosis",
                {
                    "diagnosis": "Synthetic diagnosis",
                    "treatment_plan": "Synthetic treatment plan",
                },
            ))

            completion_key = str(uuid4())
            completed = check(send(
                client, base + "/complete", key=completion_key
            ))
            assert service.load(owner, sid).is_completed is True

            final_events = len(service.load(owner, sid).events)
            assert check(send(
                client, base + "/complete", key=completion_key
            )) == completed
            assert len(service.load(owner, sid).events) == final_events

            final = check(client.get(base))
            assert final["is_completed"] is True

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(old_overrides)


def test_pg_test_mode_deadline_survives_reload(pg):
    service, owner, _, engine = pg
    session = service.create(owner, {"patient": "synthetic"}, mode="test")

    # Only the isolated yadok_f03_test database is accepted by the pg fixture.
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE simulation_sessions SET "
            "state_json = jsonb_set(state_json, '{duration_minutes}', '20'::jsonb) "
            "WHERE id = :sid"
        ), {"sid": UUID(session.session_id)})
        conn.execute(text(
            "UPDATE simulation_events SET created_at = now() - interval '21 minutes' "
            "WHERE session_id = :sid AND event_type = 'session_created'"
        ), {"sid": UUID(session.session_id)})

    expired = service.load(owner, session.session_id)
    assert expired.is_completed is True
    assert expired.current_phase == SimulationPhase.COMPLETED
    assert expired.diagnosis is None
    assert expired.events[-1].details["reason"] == "time_limit"
    assert [e.event_type for e in expired.events].count("session_timed_out") == 1
    restored = service.load(owner, session.session_id)
    assert len(restored.events) == len(expired.events)
