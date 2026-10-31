from uuid import uuid4

import pytest

from app.simulation.action_request import (
    IdempotencyConflict,
    classify_request,
    create_action_identity,
)


def test_payload_key_order_does_not_change_fingerprint():
    session_id, request_id = uuid4(), uuid4()
    first = create_action_identity(
        session_id, request_id, "diagnosis",
        {"diagnosis": "A", "plan": {"a": 1, "b": 2}},
    )
    second = create_action_identity(
        session_id, request_id, "diagnosis",
        {"plan": {"b": 2, "a": 1}, "diagnosis": "A"},
    )
    assert first.fingerprint == second.fingerprint


def test_first_request_executes():
    identity = create_action_identity(
        uuid4(), uuid4(), "pause", {}
    )
    assert classify_request(None, identity.fingerprint) == "execute"


def test_identical_retry_is_replayed():
    identity = create_action_identity(
        uuid4(), uuid4(), "pause", {}
    )
    assert classify_request(
        identity.fingerprint, identity.fingerprint
    ) == "replay"


def test_changed_payload_with_same_id_is_rejected():
    session_id, request_id = uuid4(), uuid4()
    first = create_action_identity(
        session_id, request_id, "diagnosis", {"value": "A"}
    )
    changed = create_action_identity(
        session_id, request_id, "diagnosis", {"value": "B"}
    )
    with pytest.raises(IdempotencyConflict):
        classify_request(first.fingerprint, changed.fingerprint)


def test_changed_action_with_same_id_is_rejected():
    session_id, request_id = uuid4(), uuid4()
    first = create_action_identity(
        session_id, request_id, "pause", {}
    )
    changed = create_action_identity(
        session_id, request_id, "resume", {}
    )
    with pytest.raises(IdempotencyConflict):
        classify_request(first.fingerprint, changed.fingerprint)


def test_request_identity_is_scoped_to_session():
    request_id = uuid4()
    first = create_action_identity(
        uuid4(), request_id, "pause", {}
    )
    second = create_action_identity(
        uuid4(), request_id, "pause", {}
    )
    assert first.session_id != second.session_id


def test_invalid_request_id_is_rejected():
    with pytest.raises(ValueError):
        create_action_identity(uuid4(), "not-a-uuid", "pause", {})
