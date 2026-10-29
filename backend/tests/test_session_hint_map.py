
from backend.app.services.blueprint_adapter import (
    build_session_hint_map,
)


def test_build_session_hint_map():
    blueprint = {
        "schema_version": "3.2",
        "meta": {"review_status": "approved"},
        "history_items": [],
        "exam_items": [],
        "answer_key": {
            "diagnosis": "SECRET_DIAGNOSIS"
        },
    }

    reviewed_hints = {
        "history": [
            "Start with the patient's history.",
            "Ask about symptom onset.",
            "Explore relevant symptoms.",
        ],
        "physical_exam": [
            "Review the examination.",
            "Check the main findings.",
            "Consider relevant signs.",
        ],
    }

    result = build_session_hint_map(
        blueprint,
        reviewed_hints,
    )

    assert len(result) == 2
    assert len(result["history"]) == 3
    assert len(result["physical_exam"]) == 3

    assert "SECRET_DIAGNOSIS" not in str(result)


def test_draft_case_has_no_hints():
    blueprint = {
        "schema_version": "3.2",
        "meta": {"review_status": "draft"},
        "history_items": [],
    }

    reviewed_hints = {
        "history": ["Hint 1", "Hint 2", "Hint 3"]
    }

    result = build_session_hint_map(
        blueprint,
        reviewed_hints,
    )

    assert result == {}
