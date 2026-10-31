"""Explicit integration boundary. Implement repository against existing F02/F03.

No user-controlled identity or blueprint is accepted by the public API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

Intent = Literal[
    "history_question", "examination_request", "investigation_request",
    "diagnosis_attempt", "management_attempt", "other",
]
Answerability = Literal["answered", "unknown", "partial", "not_applicable"]


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_message_id: UUID
    content: str = Field(min_length=1, max_length=1000)


class PatientReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_message_id: UUID
    session_id: UUID
    intent: Intent
    answerability: Answerability
    reply: str = Field(min_length=1, max_length=650)
    fact_ids: list[str] = Field(default_factory=list)
    request_id: str = Field(min_length=1)
    model: str | None = None


class StoredMessage(BaseModel):
    role: Literal["student", "patient"]
    content: str


class QuestionPart(BaseModel):
    """Model-supplied evidence for one literal subquestion."""
    model_config = ConfigDict(extra="forbid")
    span: str = Field(min_length=1, max_length=1000)
    answerability: Literal["answered", "unknown"]
    fact_ids: list[str]
    reply: str


class PatientChatResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Intent
    answerability: Answerability
    fact_ids: list[str]
    reply: str
    # Empty only for legacy single-question fake models; strict provider always returns parts.
    parts: list[QuestionPart] = Field(default_factory=list)


@dataclass(frozen=True)
class SessionSnapshot:
    session_id: UUID
    owner_user_id: UUID
    phase: str
    is_completed: bool
    is_paused: bool
    # Must be F02's persisted *immutable* version, NOT latest version.
    blueprint: dict[str, Any]
    case_version_id: str
    is_approved_version: bool


@dataclass(frozen=True)
class Reservation:
    # state == existing means response is final and must be reused verbatim.
    state: Literal["reserved", "existing", "in_progress"]
    existing: PatientReply | None = None
    lease_token: str | None = None


class ChatRepository(Protocol):
    async def get_session(self, session_id: UUID) -> SessionSnapshot | None:
        """Fetch session and correct *pinned* F02 blueprint; never return raw case supplied by client."""
        ...

    async def find_completed_reply(
        self, *, session_id: UUID, client_message_id: UUID, content: str
    ) -> PatientReply | None:
        """Return existing completed reply for same content even if session has since finished.

        A reused key with different content must raise HTTP 409. Called only for
        non-chat-allowed phases to avoid an extra normal-path DB round trip.
        """
        ...

    async def recent_messages(self, session_id: UUID, *, limit: int) -> list[StoredMessage]:
        """Return ordered last N messages for this session. Must be owner-authorized upstream."""
        ...

    async def reserve_message(
        self, *, session_id: UUID, client_message_id: UUID, content: str
    ) -> Reservation:
        """Atomically reserve (session_id, client_message_id).

        REQUIRED in shared PostgreSQL transaction, with UNIQUE(session_id, client_message_id).
        Store message content/hash; same ID with different content must error (409).
        Only one worker can hold a pending reservation. Previously completed returns existing.
        Rate limits/concurrent in-flight/daily token budgets must be enforced ATOMICALLY
        for *new reservations only*; completed duplicate requests bypass quota checks.
        Use lease expiry to recover if a worker crashes before finalizing/releasing.
        """
        ...

    async def finish_message(
        self, *, session_id: UUID, client_message_id: UUID, reply: PatientReply, lease_token: str,
    ) -> None:
        """Commit response and canonical F03 event(s) in one DB transaction.

        Re-check locked F03 phase/ownership before commit; if a concurrent phase
        transition invalidates the message, fail rather than append out-of-phase events.
        """
        ...

    async def release_reservation(
        self, *, session_id: UUID, client_message_id: UUID, lease_token: str
    ) -> None:
        """Release a *failed* reservation safely for retry; never delete a completed response."""
        ...

    async def list_messages(self, *, session_id: UUID, limit: int) -> list[StoredMessage]:
        """Messages ordered chronologically. Capped to limit for student UI."""
        ...


class TextModel(Protocol):
    async def generate(
        self, *, messages: list[dict[str, str]], allowed_fact_ids: list[str], session_key: str
    ) -> tuple[PatientChatResult, str | None]:
        ...
