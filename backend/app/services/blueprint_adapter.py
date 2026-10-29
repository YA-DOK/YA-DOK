import re
import json
from pathlib import Path


STAGE_MAPPING = {
    "history": "history_items",
    "physical_exam": "exam_items",
    "investigations": "investigations",
    "imaging": "imaging",
}


def load_blueprint(file_path: str) -> dict:
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        blueprint = json.load(file)

    if blueprint.get("schema_version") != "3.2":
        raise ValueError("Unsupported blueprint version")

    return blueprint


def get_stage_items(
    blueprint: dict,
    stage: str
) -> list:

    if stage not in STAGE_MAPPING:
        raise ValueError("Invalid blueprint stage")

    section = STAGE_MAPPING[stage]

    return blueprint.get(section, [])


def get_priority_items(
    blueprint: dict,
    stage: str
) -> list:

    items = get_stage_items(blueprint, stage)

    if blueprint.get("meta", {}).get(
        "review_status"
    ) != "approved":
        return []

    return [
        item for item in items
        if item.get("relevance") in (
            "essential", "helpful"
        )
    ]

def get_tutor_ready_hints(
    blueprint: dict,
    stage: str,
    approved_hints: dict[str, list[str]],
) -> list[str]:
    """
    Return only reviewed hints for the current stage.
    Do not expose raw Blueprint data to the Tutor.
    """

    # Validate the stage
    get_stage_items(blueprint, stage)

    # Only approved Blueprint versions
    if blueprint.get("schema_version") != "3.2":
        return []

    if blueprint.get("meta", {}).get("review_status") != "approved":
        return []

    # Get reviewed hints for this stage
    hints = approved_hints.get(stage)

    if not isinstance(hints, list) or len(hints) != 3:
        return []

    if any(
        not isinstance(hint, str)
        or not hint.strip()
        or len(hint) > 500
        for hint in hints
    ):
        return []

 
    # Check for direct diagnosis leakage
    ground_truth = blueprint.get("ground_truth") or {}
    diagnosis = ground_truth.get("final_diagnosis") or {}

    forbidden_terms = [
        diagnosis.get("label"),
        *(diagnosis.get("leak_terms") or []),
    ]

    safe_hints = [hint.strip() for hint in hints]

    for term in forbidden_terms:
        if not isinstance(term, str) or not term.strip():
            continue

        pattern = (
            r"(?<!\w)"
            + re.escape(term.strip())
            + r"(?!\w)"
        )

        for hint in safe_hints:
            if re.search(pattern, hint, flags=re.IGNORECASE):
                return []

    return safe_hints




def build_session_hint_map(
    blueprint: dict,
    approved_hints: dict[str, list[str]],
) -> dict[str, list[str]]:
    """
    Prepare reviewed hints for the session engine.

    Only supported stages with valid reviewed hints
    are included in the result.
    """

    session_hints = {}

    for stage in STAGE_MAPPING:
        hints = get_tutor_ready_hints(
            blueprint,
            stage,
            approved_hints,
        )

        if hints:
            session_hints[stage] = hints

    return session_hints
