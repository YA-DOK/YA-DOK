
import pytest

from backend.app.services.blueprint_adapter import (
    build_session_hint_map,
)

from backend.app.services.session_hint_engine import (
    SessionSnapshot,
    get_session_hint,
)


# Synthetic test data - not a real medical case
BLUEPRINT = {
    "schema_version": "3.2",
    "meta": {"review_status": "approved"},
    "history_items": [],
    "answer_key": {
        "diagnosis": "SECRET_DIAGNOSIS"
    },
}

REVIEWED_HINTS = {
    "history": [
        "Start by taking the patient history.",
        "Ask about the onset of symptoms.",
        "Review the relevant history findings.",
    ]
}


def make_session(
    mode="training",
    total_used=0,
    stage_used=0,
):
    return SessionSnapshot(
        session_id="session-001",
        student_id="student-001",
        mode=mode,
        stage="history",
        status="active",
        total_hints_used=total_used,
        stage_hints_used=stage_used,
    )


def test_blueprint_to_session_hint():
    hint_map = build_session_hint_map(
        BLUEPRINT,
        REVIEWED_HINTS,
    )

    result = get_session_hint(
        make_session(),
        "student-001",
        hint_map,
    )

    assert result["allowed"] is True
    assert result["hint_level"] == 1
    assert result["remaining_hints"] == 2
    assert result["hint"] == REVIEWED_HINTS["history"][0]

    assert "SECRET_DIAGNOSIS" not in str(result)


def test_progressive_hint():
    hint_map = build_session_hint_map(
        BLUEPRINT,
        REVIEWED_HINTS,
    )

    result = get_session_hint(
        make_session(total_used=1, stage_used=1),
        "student-001",
        hint_map,
    )

    assert result["allowed"] is True
    assert result["hint_level"] == 2


def test_test_mode_blocks_hints():
    hint_map = build_session_hint_map(
        BLUEPRINT,
        REVIEWED_HINTS,
    )

    result = get_session_hint(
        make_session(mode="assessment"),
        "student-001",
        hint_map,
    )

    assert result["allowed"] is False


def test_wrong_student_blocked():
    hint_map = build_session_hint_map(
        BLUEPRINT,
        REVIEWED_HINTS,
    )

    with pytest.raises(PermissionError):
        get_session_hint(
            make_session(),
            "another-student",
            hint_map,
        )


def test_draft_blueprint_blocked():
    draft = {
        **BLUEPRINT,
        "meta": {"review_status": "draft"},
    }

    hint_map = build_session_hint_map(
        draft,
        REVIEWED_HINTS,
    )

    result = get_session_hint(
        make_session(),
        "student-001",
        hint_map,
    )

    assert result["allowed"] is False

def test_third_hint_is_last_allowed():
    hint_map = build_session_hint_map(
        BLUEPRINT,
        REVIEWED_HINTS,
    )

    result = get_session_hint(
        make_session(total_used=2, stage_used=2),
        "student-001",
        hint_map,
    )

    assert result["allowed"] is True
    assert result["hint_level"] == 3
    assert result["remaining_hints"] == 0


def test_fourth_hint_is_blocked():
    hint_map = build_session_hint_map(
        BLUEPRINT,
        REVIEWED_HINTS,
    )

    result = get_session_hint(
        make_session(total_used=3, stage_used=3),
        "student-001",
        hint_map,
    )

    assert result["allowed"] is False
    assert "hint" not in result


def test_completed_session_blocks_hints():
    hint_map = build_session_hint_map(
        BLUEPRINT,
        REVIEWED_HINTS,
    )

    session = SessionSnapshot(
        session_id="session-001",
        student_id="student-001",
        mode="training",
        stage="history",
        status="completed",
        total_hints_used=0,
        stage_hints_used=0,
    )

    result = get_session_hint(
        session,
        "student-001",
        hint_map,
    )

    assert result["allowed"] is False
    assert "hint" not in result
