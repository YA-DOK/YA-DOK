
from .json_loader import get_case_by_id
from .catalog import get_investigation_by_id
from .schemas import InvestigationCategory
from .evaluation import evaluate_investigation
from .events import record_investigation_event
from .ordering import SESSION_CASES


# Temporary storage for completed examinations
PERFORMED_EXAMINATIONS = {}


def perform_examination(
    case_id: str,
    examination_id: str,
    session_id: str,
):
    # Validate input
    if not all(
        isinstance(value, str) and value.strip()
        for value in (case_id, examination_id, session_id)
    ):
        return {
            "status": "error",
            "message": "Invalid input",
        }

    # Prevent using one session with different cases
    if (
        session_id in SESSION_CASES
        and SESSION_CASES[session_id] != case_id
    ):
        return {
            "status": "error",
            "message": "Session belongs to another case",
        }

    # Load case
    case_data = get_case_by_id(case_id)

    if case_data is None:
        return {
            "status": "error",
            "message": "Case not found",
        }

    # Check catalog
    examination = get_investigation_by_id(examination_id)

    if examination is None:
        return {
            "status": "error",
            "message": "Examination not found",
        }

    # Only general and system examinations
    if examination.category not in (
        InvestigationCategory.GENERAL,
        InvestigationCategory.SYSTEM,
    ):
        return {
            "status": "error",
            "message": "Use investigation ordering service",
        }

    # Check availability
    if examination_id not in case_data.get(
        "available_investigations", []
    ):
        SESSION_CASES[session_id] = case_id

        record_investigation_event(
            session_id=session_id,
            case_id=case_id,
            investigation_id=examination_id,
            status="unavailable",
            relevance=None,
            penalty=0,
        )

        return {
            "status": "unavailable",
            "message": "Examination not available for this case",
        }

    # Prevent duplicate examinations
    examination_key = (session_id, examination_id)

    if examination_key in PERFORMED_EXAMINATIONS:
        record_investigation_event(
            session_id=session_id,
            case_id=case_id,
            investigation_id=examination_id,
            status="already_performed",
            relevance=None,
            penalty=0,
        )

        return {
            "status": "already_performed",
            "message": "Examination already performed",
        }

    # Load configured findings
    result = case_data.get(
        "investigation_results", {}
    ).get(examination_id)

    if result is None:
        return {
            "status": "error",
            "message": "Examination result not configured",
        }

    # Educational evaluation
    evaluation = evaluate_investigation(
        case_id,
        examination_id,
    )

    if evaluation.get("status") != "success":
        return {
            "status": "error",
            "message": "Educational evaluation not configured",
        }

    # Save completed examination
    SESSION_CASES[session_id] = case_id

    PERFORMED_EXAMINATIONS[examination_key] = {
        "case_id": case_id,
        "result": result,
        "evaluation": evaluation,
    }

    # Record the examination event
    record_investigation_event(
        session_id=session_id,
        case_id=case_id,
        investigation_id=examination_id,
        status="completed",
        relevance=evaluation["relevance"],
        penalty=evaluation["penalty"],
    )

    return {
        "status": "completed",
        "examination_id": examination_id,
        "examination_name": examination.name,
        "result": result,
        "evaluation": evaluation,
    }
