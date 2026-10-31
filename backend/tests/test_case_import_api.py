"""FastAPI contract tests: no external auth requests, real clinical data, or DB writes."""
from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.cases import router
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.case import CaseVersion, ClinicalCase
from app.models.profile import Profile

USER_ID = str(uuid4())


class FakeDB:
    """Minimal test double, simulates the two SELECTs, insert, flush and commit."""

    def __init__(self, role="admin"):
        self.role = role
        self.case = None
        self.versions = []
        self.pending = []
        self.commits = 0
        self.rollbacks = 0

    def get(self, model, key):
        assert model is Profile
        return type("ProfileRow", (), {"role": self.role})() if self.role is not None else None

    def scalar(self, stmt):
        entity = stmt.column_descriptions[0]["entity"]
        if entity is ClinicalCase:
            # The only imported case in these tests.
            return self.case
        if entity is CaseVersion:
            return self.versions[-1] if self.versions else None
        raise AssertionError(f"Unexpected query: {stmt}")

    def add(self, obj):
        self.pending.append(obj)

    def flush(self):
        for obj in self.pending:
            if isinstance(obj, ClinicalCase):
                obj.id = uuid4()
                self.case = obj
            elif isinstance(obj, CaseVersion):
                obj.id = uuid4()
                self.versions.append(obj)
        self.pending.clear()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1
        self.pending.clear()


@pytest.fixture
def blueprint():
    return {
        "schema_version": "3.2",
        "case_id": "SYNTHETIC_TEST_001",
        "meta": {"title": "Fictional test case", "review_status": "draft", "anonymized": False},
        "patient": {"display_name": "Fictional patient", "age_months": 120},
        "persona": {"respondent_role": "patient", "speech_language": "ar-EG"},
        "history_items": [], "exam_items": [], "investigations": [], "imaging": [],
        "ground_truth": {"final_diagnosis": {}, "difficulty_factors": {}, "debrief": {}},
    }


def make_client(db, *, signed_in=True):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    if signed_in:
        app.dependency_overrides[get_current_user] = lambda: {"id": USER_ID, "email": "test@example.invalid"}
    return TestClient(app, raise_server_exceptions=True)


def test_no_token_is_401(blueprint):
    db = FakeDB()
    client = make_client(db, signed_in=False)
    r = client.post("/api/v1/admin/cases/import", json=blueprint)
    assert r.status_code == 401
    assert not db.versions


def test_student_cannot_import(blueprint):
    db = FakeDB(role="student")
    r = make_client(db).post("/api/v1/admin/cases/import", json=blueprint)
    assert r.status_code == 403
    assert not db.versions


def test_draft_import_creates_private_v1(blueprint):
    db = FakeDB()
    r = make_client(db).post("/api/v1/admin/cases/import", json=blueprint)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["case_id"] == "SYNTHETIC_TEST_001"
    assert data["version_number"] == 1
    assert data["status"] == "draft"
    assert data["unchanged"] is False
    assert data["publication_blocker_count"] > 0
    assert "blueprint" not in data and "ground_truth" not in data
    assert db.commits == 1
    assert db.case.published_version_number is None
    assert db.versions[0].published_at is None
    assert db.versions[0].blueprint["schema_version"] == "3.2"


def test_import_identical_json_is_idempotent(blueprint):
    db = FakeDB()
    client = make_client(db)
    a = client.post("/api/v1/admin/cases/import", json=blueprint)
    b = client.post("/api/v1/admin/cases/import", json=blueprint)
    assert a.status_code == 201 and b.status_code == 201
    assert b.json()["version_number"] == 1
    assert b.json()["unchanged"] is True
    assert len(db.versions) == 1


def test_changed_json_creates_new_version_without_overwrite(blueprint):
    db = FakeDB()
    client = make_client(db)
    assert client.post("/api/v1/admin/cases/import", json=blueprint).status_code == 201
    first = deepcopy(db.versions[0].blueprint)
    updated = deepcopy(blueprint)
    updated["meta"]["title"] = "Updated fictional test case"
    r = client.post("/api/v1/admin/cases/import", json=updated)
    assert r.status_code == 201
    assert r.json()["version_number"] == 2
    assert len(db.versions) == 2
    assert db.versions[0].blueprint == first
    assert db.versions[1].blueprint["meta"]["title"] == updated["meta"]["title"]


def test_wrong_schema_is_422_and_no_writes(blueprint):
    db = FakeDB()
    blueprint["schema_version"] = "3.0"
    r = make_client(db).post("/api/v1/admin/cases/import", json=blueprint)
    assert r.status_code == 422
    assert not db.versions


def test_self_declared_approved_is_rejected(blueprint):
    db = FakeDB()
    blueprint["meta"]["review_status"] = "approved"
    r = make_client(db).post("/api/v1/admin/cases/import", json=blueprint)
    assert r.status_code == 422
    assert not db.versions
