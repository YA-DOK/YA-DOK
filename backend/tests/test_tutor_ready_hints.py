
import pytest

from backend.app.services.blueprint_adapter import (
    get_tutor_ready_hints,
)


BLUEPRINT = {
    "schema_version": "3.2",
    "meta": {"review_status": "approved"},
    "history_items": [],
    "answer_key": {"diagnosis": "SECRET_DIAGNOSIS"},
}

HINTS = {
    "history": [
        "Start by taking the patient history.",
        "Ask about the onset of symptoms.",
        "Review the relevant history findings.",
    ]
}


def test_approved_hints():
    result = get_tutor_ready_hints(
        BLUEPRINT, "history", HINTS
    )
    assert result == HINTS["history"]


def test_no_answer_key_leak():
    result = get_tutor_ready_hints(
        BLUEPRINT, "history", HINTS
    )
    assert "SECRET_DIAGNOSIS" not in str(result)


def test_draft_case_blocked():
    draft = {
        **BLUEPRINT,
        "meta": {"review_status": "draft"},
    }
    assert get_tutor_ready_hints(
        draft, "history", HINTS
    ) == []


def test_invalid_stage():
    with pytest.raises(ValueError):
        get_tutor_ready_hints(
            BLUEPRINT, "invalid", HINTS
        )


def test_missing_hints():
    assert get_tutor_ready_hints(
        BLUEPRINT, "history", {}
    ) == []

@pytest.mark.parametrize(
    "leaked_term",
    ["Secret Disease", "Hidden Diagnosis"],
)
def test_diagnosis_leak_is_blocked(leaked_term):
    blueprint = {
        "schema_version": "3.2",
        "meta": {"review_status": "approved"},
        "history_items": [],
        "ground_truth": {
            "final_diagnosis": {
                "label": "Secret Disease",
                "leak_terms": ["Hidden Diagnosis"],
            }
        },
    }

    hints = {
        "history": [
            "Review the patient history.",
            f"Consider {leaked_term}.",
            "Compare the relevant findings.",
        ]
    }

    result = get_tutor_ready_hints(
        blueprint,
        "history",
        hints,
    )

    assert result == []
