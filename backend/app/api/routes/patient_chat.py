"""F04 patient messages using existing F03 session IDs and verified Supabase auth."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.ai.f04.contracts import PatientReply, SendMessageRequest, StoredMessage
from app.ai.f04.errors import failure
from app.ai.f04.postgres_repository import PostgresChatRepository
from app.ai.f04.provider import ModelSettings, OpenRouterTextModel
from app.ai.f04.service import ChatService
from app.api.routes.simulation import _pg_service
from app.core.config import settings
from app.core.security import get_current_user

router = APIRouter(prefix="/simulation/sessions", tags=["F04 Patient Chat"])


def _repository() -> PostgresChatRepository:
    pg = _pg_service()
    if pg is None:
        raise failure(503, "POSTGRES_REQUIRED", "F04 requires PostgreSQL simulation storage.")
    return PostgresChatRepository(pg.session_factory)


def _user_id(user: dict) -> UUID:
    try:
        return UUID(str(user["id"]))
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(401, "Invalid authenticated user") from exc


@router.post("/{session_id}/messages", response_model=PatientReply)
async def send_patient_message(
    session_id: UUID,
    payload: SendMessageRequest,
    request: Request,
    user: dict = Depends(get_current_user),  # noqa: B008
):
    client = getattr(request.app.state, "f04_http_client", None)
    if client is None:
        raise failure(503, "F04_NOT_READY", "The AI connection is not initialized.")
    repo = _repository()
    model = OpenRouterTextModel(
        ModelSettings(
            api_key=settings.openrouter_api_key,
            model=settings.llm_model or "openai/gpt-6-luna",
        ),
        client,
    )
    return await ChatService(repo, model).send(
        session_id=session_id,
        user_id=_user_id(user),
        request=payload,
    )


@router.get("/{session_id}/messages", response_model=list[StoredMessage])
async def list_patient_messages(
    session_id: UUID,
    limit: int = Query(default=100, ge=1, le=100),
    user: dict = Depends(get_current_user),  # noqa: B008
):
    repo = _repository()
    snapshot = await repo.get_session(session_id)
    if snapshot is None or snapshot.owner_user_id != _user_id(user):
        raise failure(404, "SESSION_NOT_FOUND", "Simulation session not found.")
    return await repo.list_messages(session_id=session_id, limit=limit)
