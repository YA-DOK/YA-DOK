"""No real database/health data touched. API and lifecycle contract tests."""
from copy import deepcopy
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.case_lifecycle import router
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.case import CaseVersion, ClinicalCase
from app.models.case_review import CaseReviewApproval
from app.models.profile import Profile
from app.services.case_review import blueprint_hash

USER_ID = str(uuid4())


def approved_blueprint():
    return {
        "schema_version": "3.2",
        "case_id": "SYNTHETIC-CASE-01",
        "meta": {
            "title": "Fictional respiratory presentation",
            "short_brief": "An adult with an unspecified symptom",
            "specialty": "Demo",
            "setting": "OPD",
            "anonymized": True,
            "review_status": "approved",
            "reviewed_by": "Synthetic reviewer fixture - not a real clinical approval",
        },
        "patient": {"display_name": "Fictional", "age_months": 240},
        "persona": {"respondent_role": "patient", "speech_language": "ar-EG", "opening_line": "عندي شكوى."},
        "history_items": [{
            "id": "chief_complaint", "category": "chief_complaint", "known": True,
            "facts": ["Fictional symptom"], "relevance": "essential",
            "origin": "authored", "authored_by": "Synthetic fixture author",
        }],
        "exam_items": [],
        "investigations": [],
        "imaging": [],
        "ground_truth": {
            "final_diagnosis": {"id": "fixture_dx", "label": "Fixture Diagnosis", "leak_terms": ["Fixture Diagnosis"]},
            "distractors": [
                {"id": "alt_one", "label": "Alternative One", "why_not": "Synthetic test reason"},
                {"id": "alt_two", "label": "Alternative Two", "why_not": "Synthetic test reason"},
                {"id": "alt_three", "label": "Alternative Three", "why_not": "Synthetic test reason"},
            ],
            "distractors_approved_by": "Synthetic reviewer fixture",
            "difficulty_factors": {"presentation_typicality": "typical", "distractor_similarity": "low"},
            "debrief": {},
        },
    }


class FakeDB:
    def __init__(self, *, role="admin", case_exists=True, version_exists=True, blueprint=None):
        self.role = role
        self.case = None
        if case_exists:
            self.case = ClinicalCase(case_code="SYNTHETIC-CASE-01")
            self.case.id = uuid4()
            self.case.published_version_number = None
            self.case.archived_at = None
        self.version = None
        if version_exists and self.case is not None:
            self.version = CaseVersion(
                case_id=self.case.id,
                version_number=1,
                blueprint=deepcopy(blueprint if blueprint is not None else approved_blueprint()),
            )
            self.version.id = uuid4()
            self.version.published_at = None
        self.commits = 0
        self.rollbacks = 0
        self.statements = []
        self.audit_present = True

    def get(self, model, key):
        assert model is Profile
        return type("FakeProfile", (), {"role": self.role})() if self.role else None

    def scalar(self, stmt):
        self.statements.append(stmt)
        entity = stmt.column_descriptions[0]["entity"]
        if entity is ClinicalCase:
            return self.case
        if entity is CaseVersion:
            return self.version
        if entity is CaseReviewApproval:
            if self.version and self.audit_present:
                return type("Audit", (), {"blueprint_sha256": blueprint_hash(self.version.blueprint)})()
            return None
        raise AssertionError("unexpected query")

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def client_for(db, *, signed_in=True):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    if signed_in:
        app.dependency_overrides[get_current_user] = lambda: {"id": USER_ID}
    return TestClient(app)


def uri(endpoint):
    return "/api/v1/admin/cases/SYNTHETIC-CASE-01" + endpoint


def test_unauthenticated_cannot_archive():
    db = FakeDB()
    assert client_for(db, signed_in=False).post(uri("/archive")).status_code == 401
    assert db.commits == 0


def test_student_cannot_publish_or_archive_or_restore():
    db = FakeDB(role="student")
    client = client_for(db)
    for p in ("/versions/1/publish", "/archive", "/restore"):
        assert client.post(uri(p)).status_code == 403
    assert db.commits == 0


def test_archive_retains_pointer_and_version_and_is_idempotent():
    db = FakeDB()
    db.case.published_version_number = 1
    db.version.published_at = db.case.created_at
    client = client_for(db)
    one = client.post(uri("/archive"))
    two = client.post(uri("/archive"))
    assert one.status_code == 200
    assert one.json()["status"] == "archived"
    assert one.json()["unchanged"] is False
    assert two.json()["unchanged"] is True
    assert db.case.published_version_number == 1
    assert db.version.blueprint["ground_truth"]["final_diagnosis"]["id"] == "fixture_dx"


def test_restore_reexposes_previous_published_pointer_without_rewriting():
    db = FakeDB()
    db.case.published_version_number = 1
    db.version.published_at = db.case.created_at
    client = client_for(db)
    assert client.post(uri("/archive")).status_code == 200
    r = client.post(uri("/restore"))
    assert r.status_code == 200
    assert r.json()["status"] == "published"
    assert r.json()["published_version_number"] == 1
    assert db.case.archived_at is None
    assert client.post(uri("/restore")).json()["unchanged"] is True


def test_restore_draft_remains_draft():
    db = FakeDB()
    client = client_for(db)
    client.post(uri("/archive"))
    assert client.post(uri("/restore")).json()["status"] == "draft"


def test_missing_case_is_404():
    db = FakeDB(case_exists=False)
    assert client_for(db).post(uri("/archive")).status_code == 404
    assert db.commits == 0


def test_missing_version_is_404():
    db = FakeDB(version_exists=False)
    assert client_for(db).post(uri("/versions/1/publish")).status_code == 404
    assert db.case.published_version_number is None


def test_no_publish_on_draft():
    bp = approved_blueprint()
    bp["meta"]["review_status"] = "draft"
    db = FakeDB(blueprint=bp)
    r = client_for(db).post(uri("/versions/1/publish"))
    assert r.status_code == 409
    assert r.json()["detail"]["blocker_count"] >= 1
    assert db.case.published_version_number is None
    assert db.version.published_at is None
    assert db.commits == 0


def test_publish_anonymization_required():
    bp = approved_blueprint()
    bp["meta"]["anonymized"] = False
    db = FakeDB(blueprint=bp)
    assert client_for(db).post(uri("/versions/1/publish")).status_code == 409
    assert db.case.published_version_number is None


def test_metadata_leak_is_blocked():
    bp = approved_blueprint()
    bp["meta"]["short_brief"] = "The answer is Fixture Diagnosis"
    db = FakeDB(blueprint=bp)
    r = client_for(db).post(uri("/versions/1/publish"))
    assert r.status_code == 409
    assert db.case.published_version_number is None


def test_approved_synthetic_fixture_can_publish_without_changing_blueprint():
    db = FakeDB()
    original = deepcopy(db.version.blueprint)
    client = client_for(db)
    r = client.post(uri("/versions/1/publish"))
    assert r.status_code == 200, r.text
    assert r.json() == {
        "case_id": "SYNTHETIC-CASE-01", "status": "published",
        "published_version_number": 1, "unchanged": False,
    }
    assert db.version.published_at is not None
    assert db.version.blueprint == original
    assert client.post(uri("/versions/1/publish")).json()["unchanged"] is True


def test_publish_archived_case_rejected_until_restored():
    db = FakeDB()
    client = client_for(db)
    assert client.post(uri("/archive")).status_code == 200
    assert client.post(uri("/versions/1/publish")).status_code == 409
    assert db.case.published_version_number is None


def test_invalid_version_number_rejected():
    db = FakeDB()
    r = client_for(db).post(uri("/versions/0/publish"))
    assert r.status_code == 422
    assert db.case.published_version_number is None


def test_blueprint_id_mismatch_blocks_publishing():
    bp = approved_blueprint()
    bp["case_id"] = "DIFFERENT"
    db = FakeDB(blueprint=bp)
    assert client_for(db).post(uri("/versions/1/publish")).status_code == 409


def test_no_private_content_in_response():
    db = FakeDB()
    response = client_for(db).post(uri("/versions/1/publish"))
    assert response.status_code == 200
    assert "ground_truth" not in response.text
    assert "Fixture Diagnosis" not in response.text
