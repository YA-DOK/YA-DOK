"""What the STUDENT is allowed to see.

Everything returned to the frontend goes through these functions, so
internal case data (diagnosis, treatment, outcome, source notes, file
paths, hospital name) never leaves the server.
"""

from urllib.parse import quote

from .security import create_signed_params


# True  = student sees relevance + penalty immediately (current frontend).
# False = hidden until the final evaluation (exam mode).
SHOW_EVALUATION_TO_STUDENT = True

RESULT_FIELDS = (
    "findings",
    "result_type",
    "reference_range_note",
    "note",
    "modality",
    "body_part",
    "simulated_normal",
)

MEASUREMENT_FIELDS = ("name", "value", "unit", "reference_range")


def _pick(data: dict, keys) -> dict:
    return {
        key: data[key]
        for key in keys
        if key in data and data[key] is not None
    }


def public_case(case_data: dict) -> dict:
    patient = case_data.get("patient") or {}

    return {
        "id": case_data.get("id"),
        "title": case_data.get("title"),
        "patient": _pick(patient, ("age", "sex", "weight_kg")),
        "chief_complaint": (
            case_data.get("chief_complaint")
            or case_data.get("description")
        ),
        "present_history": case_data.get("present_history"),
        "medical_history": case_data.get("medical_history"),
    }


def clean_result(result: dict) -> dict:
    cleaned = _pick(result, RESULT_FIELDS)

    cleaned["measurements"] = [
        _pick(measurement, MEASUREMENT_FIELDS)
        for measurement in result.get("measurements", [])
        if isinstance(measurement, dict)
    ]

    return cleaned


def public_result(
    session_id: str,
    investigation_id: str,
    result: dict,
) -> dict:
    cleaned = clean_result(result)

    if result.get("image_path"):
        params = create_signed_params(session_id, investigation_id)
        cleaned["image_url"] = (
            f"/simulations/{quote(session_id, safe='')}"
            f"/investigations/{quote(investigation_id, safe='')}/image"
            f"?exp={params['exp']}&sig={params['sig']}"
        )

    return cleaned


def public_evaluation(evaluation: dict | None) -> dict:
    evaluation = evaluation or {}

    if SHOW_EVALUATION_TO_STUDENT:
        return _pick(
            evaluation,
            (
                "investigation_id",
                "investigation_name",
                "relevance",
                "is_relevant",
                "penalty",
            ),
        )

    return {
        "investigation_id": evaluation.get("investigation_id"),
        "relevance": None,
        "penalty": 0,
    }


def public_event(event: dict) -> dict:
    if SHOW_EVALUATION_TO_STUDENT:
        return event

    return {**event, "relevance": None, "penalty": 0}

