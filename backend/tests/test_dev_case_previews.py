"""Security tests for the local draft-preview endpoint. Never leak source metadata."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.routes import dev_case_previews as preview


def test_anonymized_synthetic_metadata_is_allowlisted():
    row = dict(case_id="SYN-PED-001", version_number=1, anonymized="true",
               title="Child With Cough", subtitle="Synthetic", short_brief="A fictional child.",
               specialty="Pediatrics", setting="Clinic", difficulty="beginner",
               duration_text="12", ground_truth={"diagnosis": "PRIVATE"})
    result = preview._safe_preview(row)
    assert result["title"] == "Child With Cough"
    assert result["demo"] is True
    assert result["restricted"] is False
    assert "ground_truth" not in result
    assert "blueprint" not in result


def test_non_anonymized_cases_have_all_source_metadata_masked():
    row = dict(case_id="PED-RT-0002", version_number=1, anonymized="false",
               title="Private clinical story", subtitle="private subtitle",
               short_brief="PATIENT DETAILS", specialty="Pediatrics",
               setting="Patient Hospital", difficulty="intermediate", duration_text="20")
    result = preview._safe_preview(row)
    assert result["restricted"] is True
    assert result["title"] != row["title"]
    assert result["short_brief"] != row["short_brief"]
    assert result["specialty"] is None
    assert result["setting"] is None
    assert result["estimated_duration_minutes"] is None


def test_no_access_outside_local_app():
    with patch.object(preview.settings, "app_env", "production"):
        with pytest.raises(HTTPException) as exc:
            preview._only_local_db()
        assert exc.value.status_code == 404


def test_no_access_when_db_is_cloud_even_if_app_local():
    with patch.object(preview.settings, "app_env", "local"), patch.object(
        preview.settings, "database_url", "postgresql+psycopg://user:password@db.example.com/postgres"
    ):
        with pytest.raises(HTTPException) as exc:
            preview._only_local_db()
        assert exc.value.status_code == 404
