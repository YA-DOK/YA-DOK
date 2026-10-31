"""Run from backend/: python -m pytest tests/test_case_blueprint_contract.py -q"""
from copy import deepcopy
from pathlib import Path
import json

import pytest
from pydantic import ValidationError

from app.schemas.case_blueprint import CaseBlueprintV32, publication_issues, student_case_summary


@pytest.fixture
def draft() -> dict:
    # Entirely fictional test fixture: no clinical or patient records.
    return {
        "schema_version": "3.2",
        "case_id": "TEST_CASE_001",
        "meta": {"title": "Test case", "specialty": "Test", "review_status": "draft"},
        "patient": {"display_name": "Test Patient", "age_months": 120},
        "persona": {"respondent_role": "patient", "speech_language": "ar-EG"},
        "history_items": [{"id": "chief_complaint", "category": "chief_complaint", "known": False,
                           "facts": [], "origin": "authored"}],
        "exam_items": [],
        "investigations": [],
        "imaging": [],
        "ground_truth": {"final_diagnosis": {}, "difficulty_factors": {}, "debrief": {}},
    }


def test_valid_draft_structure(draft):
    assert CaseBlueprintV32.model_validate(draft).schema_version == "3.2"


def test_legacy_versions_rejected(draft):
    draft["schema_version"] = "3.1"
    with pytest.raises(ValidationError):
        CaseBlueprintV32.model_validate(draft)


def test_duplicate_history_ids_rejected(draft):
    draft["history_items"].append(deepcopy(draft["history_items"][0]))
    with pytest.raises(ValidationError, match="duplicate IDs"):
        CaseBlueprintV32.model_validate(draft)


def test_missing_history_cannot_have_facts(draft):
    draft["history_items"][0]["facts"] = ["Unsupported fictional observation"]
    with pytest.raises(ValidationError, match="unknown history"):
        CaseBlueprintV32.model_validate(draft)


def test_draft_is_not_publishable(draft):
    issues = publication_issues(CaseBlueprintV32.model_validate(draft))
    assert any("approved" in issue for issue in issues)
    assert any("anonymized" in issue for issue in issues)


def test_student_summary_never_includes_answer_key(draft):
    draft["ground_truth"]["final_diagnosis"] = {"id": "private_code", "label": "SECRET_DIAGNOSIS"}
    result = student_case_summary(CaseBlueprintV32.model_validate(draft))
    assert "ground_truth" not in result
    assert "SECRET_DIAGNOSIS" not in str(result)


def test_unknown_root_fields_rejected(draft):
    draft["surprise_field"] = "accidental typo"
    with pytest.raises(ValidationError):
        CaseBlueprintV32.model_validate(draft)
