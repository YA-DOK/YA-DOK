
from .json_loader import get_case_by_id
from .catalog import get_investigation_by_id


# Used when the case does not define its own penalty.
DEFAULT_UNNECESSARY_PENALTY = 3


def evaluate_investigation(
    case_id: str,
    investigation_id: str,
):

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
            "message": "Investigation not found in catalog",
        }

    relevance_data = case_data.get(
        "educational_relevance", {}
    ).get(investigation_id)

    configured_result = case_data.get(
        "investigation_results", {}
    ).get(investigation_id)

    if relevance_data is not None:

        relevance = relevance_data.get("relevance", "relevant")
        penalty = relevance_data.get("penalty", 0)

    elif configured_result is not None:

        relevance = "relevant"
        penalty = 0

    else:
        # Not part of this case: result is a simulated normal.
        relevance = "unnecessary"
        penalty = case_data.get(
            "default_unnecessary_penalty"
        ) or DEFAULT_UNNECESSARY_PENALTY

    return {
        "status": "success",
        "investigation_id": investigation_id,
        "investigation_name": investigation.name,
        "relevance": relevance,
        "is_relevant": relevance in ("essential", "relevant"),
        "has_case_specific_result": configured_result is not None,
        "penalty": penalty,
    }
