from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Literal
from uuid import UUID
import json


class IdempotencyConflict(ValueError):
    pass


@dataclass(frozen=True)
class ActionRequestIdentity:
    session_id: UUID
    request_id: UUID
    fingerprint: str


def create_action_identity(
    session_id: str | UUID,
    request_id: str | UUID,
    action: str,
    payload: dict[str, Any],
) -> ActionRequestIdentity:
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Action is required.")
    if not isinstance(payload, dict):
        raise TypeError("Payload must be an object.")

    canonical = json.dumps(
        {"action": action.strip(), "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )

    return ActionRequestIdentity(
        session_id=UUID(str(session_id)),
        request_id=UUID(str(request_id)),
        fingerprint=sha256(canonical.encode("utf-8")).hexdigest(),
    )


def classify_request(
    stored_fingerprint: str | None,
    incoming_fingerprint: str,
) -> Literal["execute", "replay"]:
    if stored_fingerprint is None:
        return "execute"
    if stored_fingerprint == incoming_fingerprint:
        return "replay"
    raise IdempotencyConflict(
        "Request ID was already used with different action data."
    )
