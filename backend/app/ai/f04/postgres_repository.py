"""F04 adapter for the existing F03 tables. No extra database tables required.

Reservations occupy simulation_action_requests.response_json with an F04-only marker.
The session row lock serializes reservation/commit against F03 actions without
holding a transaction open during the external LLM request.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from starlette.concurrency import run_in_threadpool

from app.ai.f04.contracts import (
    PatientReply,
    Reservation,
    SessionSnapshot,
    StoredMessage,
)
from app.ai.f04.errors import failure
from app.models.case import CaseVersion
from app.models.simulation_action_request import SimulationActionRequestModel
from app.models.simulation_session import SimulationSessionModel
from app.services.simulation_pg_service import PostgresSimulationService, _hydrate
from app.simulation.action_request import create_action_identity
from app.simulation.engine import SimulationMessage

LEASE_SECONDS = 60  # Larger than model timeout. Expired claims are recoverable.
MAX_QUESTIONS_PER_SESSION = 80


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _id(session_id: UUID, message_id: UUID, content: str):
    return create_action_identity(session_id, message_id, "f04_chat", {"content": content})


def _payload(row):
    return row.response_json if isinstance(row.response_json, dict) else {}


def _stored(row) -> PatientReply | None:
    data = _payload(row)
    if data.get("_f04_status") == "complete":
        return PatientReply.model_validate(data["reply"])
    return None


def _expiry(data: dict) -> datetime:
    try:
        return datetime.fromisoformat(data["expires_at"])
    except (ValueError, TypeError, KeyError):
        return datetime.min.replace(tzinfo=UTC)


def _locked_session(db, session_id: UUID):
    return db.scalar(
        select(SimulationSessionModel)
        .where(SimulationSessionModel.id == session_id)
        .with_for_update()
    )


def _validate_open(row) -> None:
    if row is None:
        raise failure(404, "SESSION_NOT_FOUND", "Simulation session not found.")
    if row.case_version_id is None:
        raise failure(409, "CASE_NOT_PINNED", "Start the simulation from a published case.")
    if row.is_completed or row.is_paused:
        raise failure(409, "CHAT_NOT_ALLOWED", "Patient chat requires an active, unpaused session.")
    # F04 uses its own reservation path: reject late chats here, too.
    state = row.state_json or {}
    minutes = state.get("duration_minutes")
    if state.get("mode") == "test" and isinstance(minutes, (int, float)) and not isinstance(minutes, bool) and minutes > 0:
        started = row.created_at
        if started is not None:
            if started.tzinfo is None:
                started = started.replace(tzinfo=UTC)
            if _utc_now() >= started + timedelta(minutes=minutes):
                raise failure(409, "TIME_LIMIT_REACHED", "Assessment time limit reached. Open the session to view its final status.")


class PostgresChatRepository:
    def __init__(self, factory: sessionmaker):
        self.factory = factory
        self.pg = PostgresSimulationService(factory)

    async def get_session(self, session_id: UUID) -> SessionSnapshot | None:
        return await run_in_threadpool(self._get_session, session_id)

    def _get_session(self, session_id: UUID) -> SessionSnapshot | None:
        with self.factory() as db:
            row = db.get(SimulationSessionModel, session_id)
            if row is None:
                return None
            version = db.get(CaseVersion, row.case_version_id) if row.case_version_id else None
            # A session is pinned at creation; don't switch to current published version.
            blueprint = deepcopy(row.case_data)
            if version is not None:
                truth = (version.blueprint or {}).get("ground_truth")
                if isinstance(truth, dict):
                    # ONLY used for answer leak screening. Projector never sends it to LLM.
                    blueprint["ground_truth"] = {
                        "final_diagnosis": truth.get("final_diagnosis", {})
                    }
            return SessionSnapshot(
                session_id=session_id,
                owner_user_id=row.user_id,
                phase=row.current_phase,
                is_completed=row.is_completed,
                is_paused=row.is_paused,
                blueprint=blueprint,
                case_version_id=str(row.case_version_id or ""),
                is_approved_version=bool(version and version.published_at is not None),
            )

    async def find_completed_reply(self, *, session_id: UUID, client_message_id: UUID, content: str) -> PatientReply | None:
        return await run_in_threadpool(self._find_completed_reply, session_id, client_message_id, content)

    def _find_completed_reply(self, sid: UUID, mid: UUID, content: str) -> PatientReply | None:
        identity = _id(sid, mid, content)
        with self.factory() as db:
            row = db.get(SimulationActionRequestModel, (sid, mid))
            if not row:
                return None
            if row.fingerprint != identity.fingerprint:
                raise failure(409, "IDEMPOTENCY_CONFLICT", "Message ID was already used with different content.")
            return _stored(row)

    async def reserve_message(self, *, session_id: UUID, client_message_id: UUID, content: str) -> Reservation:
        return await run_in_threadpool(self._reserve, session_id, client_message_id, content)

    def _reserve(self, sid: UUID, mid: UUID, content: str) -> Reservation:
        identity = _id(sid, mid, content)
        with self.factory.begin() as db:
            row = _locked_session(db, sid)
            if row is None:
                raise failure(404, "SESSION_NOT_FOUND", "Simulation session not found.")

            previous = db.get(SimulationActionRequestModel, (sid, mid))
            if previous is not None:
                if previous.fingerprint != identity.fingerprint:
                    raise failure(409, "IDEMPOTENCY_CONFLICT", "Message ID was already used with different content.")
                reply = _stored(previous)
                if reply is not None:
                    return Reservation(state="existing", existing=reply)
            _validate_open(row)
            now = _utc_now()
            other = list(db.scalars(select(SimulationActionRequestModel).where(
                SimulationActionRequestModel.session_id == sid,
                SimulationActionRequestModel.response_json["_f04_status"].astext == "pending",
            )))
            for active in other:
                if active.request_id != mid and _expiry(_payload(active)) > now:
                    raise failure(409, "MESSAGE_IN_PROGRESS", "Another patient question is being processed.")
            completed_count = db.scalar(select(func.count()).select_from(SimulationActionRequestModel).where(
                SimulationActionRequestModel.session_id == sid,
                SimulationActionRequestModel.response_json["_f04_status"].astext == "complete",
            )) or 0
            if completed_count >= MAX_QUESTIONS_PER_SESSION:
                raise failure(429, "CHAT_LIMIT_REACHED", "Question limit reached for this case.")
            if previous is not None and _expiry(_payload(previous)) > now:
                return Reservation(state="in_progress")
            token = str(uuid4())
            pending = {
                "_f04_status": "pending", "lease_token": token,
                "expires_at": (now + timedelta(seconds=LEASE_SECONDS)).isoformat(),
                "content": content,
            }
            if previous is None:
                db.add(SimulationActionRequestModel(
                    session_id=sid, request_id=mid,
                    fingerprint=identity.fingerprint, response_json=pending,
                ))
            else:
                previous.response_json = pending
            return Reservation(state="reserved", lease_token=token)

    async def recent_messages(self, session_id: UUID, *, limit: int) -> list[StoredMessage]:
        return await run_in_threadpool(self._messages, session_id, limit)

    async def list_messages(self, *, session_id: UUID, limit: int) -> list[StoredMessage]:
        return await run_in_threadpool(self._messages, session_id, limit)

    def _messages(self, sid: UUID, limit: int) -> list[StoredMessage]:
        with self.factory() as db:
            row = db.get(SimulationSessionModel, sid)
            if row is None:
                raise failure(404, "SESSION_NOT_FOUND", "Simulation session not found.")
            messages = (row.state_json or {}).get("messages", [])
            return [StoredMessage(
                role="student" if m["action"] == "patient_question" else "patient",
                content=m["content"][:1000],
            ) for m in messages if isinstance(m, dict)
                and m.get("action") in {"patient_question", "patient_response"}
                and isinstance(m.get("content"), str)][-limit:]

    async def finish_message(self, *, session_id: UUID, client_message_id: UUID, reply: PatientReply, lease_token: str) -> None:
        await run_in_threadpool(self._finish, session_id, client_message_id, reply, lease_token)

    def _finish(self, sid: UUID, mid: UUID, reply: PatientReply, token: str) -> None:
        with self.factory.begin() as db:
            session_row = _locked_session(db, sid)
            _validate_open(session_row)
            request_row = db.get(SimulationActionRequestModel, (sid, mid))
            data = _payload(request_row) if request_row else {}
            if data.get("_f04_status") != "pending" or data.get("lease_token") != token:
                raise failure(409, "MESSAGE_LEASE_LOST", "This message is no longer pending. Please retry.")
            if _expiry(data) <= _utc_now():
                raise failure(409, "MESSAGE_LEASE_EXPIRED", "The message request timed out. Please retry.")
            question = data["content"]
            all_events = self.pg._events(db, sid)
            simulation = _hydrate(session_row, all_events)
            old_count = len(simulation.events)
            simulation.messages.append(SimulationMessage(role="user", content=question, action="patient_question"))
            simulation.record_event("patient_question", {"question": question, "client_message_id": str(mid)})
            simulation.messages.append(SimulationMessage(role="assistant", content=reply.reply, action="patient_response"))
            simulation.record_event("patient_response", {
                "response": reply.reply,
                "client_message_id": str(mid),
                "intent": reply.intent,
                "answerability": reply.answerability,
                "fact_ids": reply.fact_ids,
                "model": reply.model,
            })
            self.pg._save_state(session_row, simulation)
            self.pg._append_events(db, simulation, old_count)
            request_row.response_json = {
                "_f04_status": "complete",
                "reply": reply.model_dump(mode="json"),
            }

    async def release_reservation(self, *, session_id: UUID, client_message_id: UUID, lease_token: str) -> None:
        await run_in_threadpool(self._release, session_id, client_message_id, lease_token)

    def _release(self, sid: UUID, mid: UUID, token: str) -> None:
        with self.factory.begin() as db:
            row = _locked_session(db, sid)
            if row is None:
                return
            request_row = db.get(SimulationActionRequestModel, (sid, mid))
            data = _payload(request_row) if request_row else {}
            if data.get("_f04_status") == "pending" and data.get("lease_token") == token:
                db.delete(request_row)
