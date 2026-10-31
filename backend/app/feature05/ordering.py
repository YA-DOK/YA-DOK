
from datetime import datetime, timedelta, timezone
from copy import deepcopy

from .json_loader import get_case_by_id
from .catalog import get_investigation_by_id
from .schemas import InvestigationCategory
from .evaluation import evaluate_investigation
from .events import record_investigation_event
from .normal_results import build_normal_training_result


# Temporary in-memory storage.
# Database persistence will be handled during integration.
ORDERS = {}
SESSION_CASES = {}


def order_investigation(
    session_id: str,
    case_id: str,
    investigation_id: str,
):

    if not all(
        isinstance(value, str) and value.strip()
        for value in (session_id, case_id, investigation_id)
    ):
        return {
            "status": "error",
            "message": "Invalid input",
        }

    # Prevent changing cases within the same session.
    if session_id in SESSION_CASES:
        if SESSION_CASES[session_id] != case_id:
            return {
                "status": "error",
                "message": "Session belongs to another case",
            }

    case_data = get_case_by_id(case_id)

    if case_data is None:
        return {
            "status": "error",
            "message": "Case not found",
        }

    investigation = get_investigation_by_id(
        investigation_id
    )

    if investigation is None:
        return {
            "status": "error",
            "message": "Investigation not found",
        }

    # Physical examinations use a different service.
    if investigation.category in (
        InvestigationCategory.GENERAL,
        InvestigationCategory.SYSTEM,
    ):
        return {
            "status": "error",
            "message": "Use clinical examination service",
        }

    order_key = (session_id, investigation_id)

    # Handle duplicate requests.
    if order_key in ORDERS:

        record_investigation_event(
            session_id=session_id,
            case_id=case_id,
            investigation_id=investigation_id,
            status="already_ordered",
            relevance=None,
            penalty=0,
        )

        return {
            "status": "already_ordered",
            "message": "Investigation already ordered",
        }

    # Get educational relevance and penalty.
    evaluation = evaluate_investigation(
        case_id,
        investigation_id,
    )

    if evaluation.get("status") != "success":
        return {
            "status": "error",
            "message": "Educational evaluation failed",
        }

    # Rule 1:
    # Always prefer the actual case-defined result.
    configured_result = case_data.get(
        "investigation_results", {}
    ).get(investigation_id)

    result = deepcopy(configured_result)

    # Rule 2:
    # If no case result exists, allow a synthetic normal
    # result only for non-indicated investigations.
    if result is None:

        if evaluation["relevance"] in (
            "unnecessary",
            "not_indicated",
        ):
            result = build_normal_training_result(
                investigation_id=investigation.id,
                category=investigation.category.value,
            )

    # Rule 3:
    # Never invent a result for an essential/relevant
    # investigation or an unsupported test category.
    if result is None:

        SESSION_CASES[session_id] = case_id

        record_investigation_event(
            session_id=session_id,
            case_id=case_id,
            investigation_id=investigation_id,
            status="unavailable",
            relevance=evaluation["relevance"],
            penalty=evaluation["penalty"],
        )

        return {
            "status": "unavailable",
            "investigation_id": investigation_id,
            "message": (
                "No authorized result/template "
                "for this investigation"
            ),
        }

    # Preserve case-defined release delays.
    delay = result.get(
        "release_delay_seconds",
        0,
    )

    if (
        isinstance(delay, bool)
        or not isinstance(delay, (int, float))
        or delay < 0
    ):
        return {
            "status": "error",
            "message": "Invalid result release delay",
        }

    now = datetime.now(timezone.utc)

    ready_at = now + timedelta(
        seconds=delay
    )

    status = (
        "pending"
        if delay > 0
        else "completed"
    )

    # Store the request and its result.
    ORDERS[order_key] = {
        "case_id": case_id,
        "ordered_at": now,
        "ready_at": ready_at,
        "result": result,
        "evaluation": evaluation,
    }

    SESSION_CASES[session_id] = case_id

    # Record the event for educational evaluation.
    record_investigation_event(
        session_id=session_id,
        case_id=case_id,
        investigation_id=investigation_id,
        status=status,
        relevance=evaluation["relevance"],
        penalty=evaluation["penalty"],
    )

    return {
        "status": status,
        "investigation_id": investigation_id,
        "investigation_name": investigation.name,
        "release_delay_seconds": delay,
        "ready_at": ready_at.isoformat(),
        "evaluation": evaluation,
    }


def get_investigation_status(
    session_id: str,
    investigation_id: str,
):

    order = ORDERS.get(
        (session_id, investigation_id)
    )

    if order is None:
        return {
            "investigation_id": investigation_id,
            "status": "not_ordered",
        }

    now = datetime.now(timezone.utc)

    return {
        "investigation_id": investigation_id,
        "status": (
            "completed"
            if now >= order["ready_at"]
            else "pending"
        ),
        "ordered_at": order["ordered_at"].isoformat(),
        "ready_at": order["ready_at"].isoformat(),
    }


def get_investigation_result(
    session_id: str,
    investigation_id: str,
):

    order = ORDERS.get(
        (session_id, investigation_id)
    )

    if order is None:
        return {
            "status": "not_ordered",
            "message": "Investigation not ordered",
        }

    now = datetime.now(timezone.utc)

    if now < order["ready_at"]:
        return {
            "status": "pending",
            "message": "Result is not ready yet",
            "ready_at": order["ready_at"].isoformat(),
        }

    return {
        "status": "completed",
        "investigation_id": investigation_id,
        "result": order["result"],
        "evaluation": order["evaluation"],
    }
