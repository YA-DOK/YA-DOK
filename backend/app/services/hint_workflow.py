"""Feature 06 application workflow; database adapter will be supplied later.

This module never trusts hint level, mode, stage, or counters from a client.
"""
from contextlib import AbstractContextManager
from typing import Mapping, Protocol, Sequence

from .session_hint_engine import (
    SessionSnapshot,
    get_session_hint,
)


class LockedHintSession(Protocol):
    """Data loaded from the database inside a per-session transaction."""

    @property
    def snapshot(self) -> SessionSnapshot: ...

    @property
    def approved_hints(self) -> Mapping[str, Sequence[str]]: ...

    def record_hint_used(
        self, *, stage: str, hint_level: int, 
        reason: str
    ) -> None:
        """Persist a hint_used event and update counters in same transaction."""
        ...


class HintStore(Protocol):
    def lock_session(
        self, session_id: str
    ) -> AbstractContextManager[LockedHintSession | None]:
        """Lock and load; commit on success, roll back on failure."""
        ...


class HintWorkflow:
    def __init__(self, store: HintStore):
        self.store = store

    def request_hint(
        self, *, session_id: str, authenticated_user_id: str,
        reason: str = "student_requested_help"
    ) -> dict:
        """Run policy and record usage; user ID MUST come from verified auth."""
        if not session_id or not authenticated_user_id:
            raise ValueError("session_id and authenticated_user_id are required")
        with self.store.lock_session(session_id) as locked:
            if locked is None:
                raise LookupError("Session not found")

            result = get_session_hint(
                locked.snapshot, authenticated_user_id, locked.approved_hints
            )
            if result["allowed"]:
                locked.record_hint_used(
                    stage=locked.snapshot.stage,
                    hint_level=result["hint_level"],
                    reason=reason,
                )
            return result
