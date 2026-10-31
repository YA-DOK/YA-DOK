from datetime import datetime, timezone


# Temporary storage for development only
SESSION_EVENTS = []


def record_investigation_event(
    session_id: str,
    case_id: str,
    investigation_id: str,
    status: str,
    relevance: str | None = None,
    penalty: int = 0,
):
    event = {
        "session_id": session_id,
        "case_id": case_id,
        "investigation_id": investigation_id,
        "status": status,
        "relevance": relevance,
        "penalty": penalty,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    SESSION_EVENTS.append(event)

    return event


def get_session_events(session_id: str):
    return [
        event
        for event in SESSION_EVENTS
        if event["session_id"] == session_id
    ]