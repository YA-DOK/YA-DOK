from dataclasses import dataclass
from typing import Mapping, Sequence

MAX_HINTS_PER_SESSION = 3


@dataclass(frozen=True)
class SessionSnapshot:
    session_id: str
    student_id: str
    mode: str
    stage: str
    status: str
    total_hints_used: int
    stage_hints_used: int


def get_session_hint(
    session: SessionSnapshot,
    requester_id: str,
    approved_hints: Mapping[str, Sequence[str]],
) -> dict:
    """Decide whether to reveal a pre-approved hint. Does not save usage."""
    if requester_id != session.student_id:
        raise PermissionError("You cannot access this session")

    if session.mode not in {"training", "assessment"}:
        raise ValueError("Invalid session mode")

    if (session.total_hints_used < 0 or session.stage_hints_used < 0
            or session.stage_hints_used > session.total_hints_used):
        raise ValueError("Invalid hint counters")

    if session.status != "active":
        return {"allowed": False, "reason": "Session is not active"}

    if session.mode == "assessment":
        return {"allowed": False, "reason": "Hints are disabled in Assessment Mode"}

    if session.total_hints_used >= MAX_HINTS_PER_SESSION:
        return {"allowed": False, "reason": "Maximum session hints reached"}

    stage_hints = approved_hints.get(session.stage)
    if not stage_hints or session.stage_hints_used >= len(stage_hints):
        return {"allowed": False, "reason": "No hint available for this stage"}

    hint_level = session.stage_hints_used + 1
    return {
        "allowed": True,
        "hint_level": hint_level,
        "hint": stage_hints[session.stage_hints_used],
        "remaining_hints": MAX_HINTS_PER_SESSION - session.total_hints_used - 1,
    }
