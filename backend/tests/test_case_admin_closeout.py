"""Structural/security regression tests for F02 closeout; no network or real DB."""
from copy import deepcopy
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.admin_case_library import router as admin_router
from app.api.routes.case_approval import router as approval_router
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.case import CaseVersion, ClinicalCase
from app.models.case_review import CaseReviewApproval
from app.models.profile import Profile
from app.schemas.case_blueprint import CaseBlueprintV32
from app.services.case_lifecycle import PublicationBlocked, publish_case_version
from app.services.case_review import blueprint_hash, clinician_is_allowed

UID=str(uuid4())

class MinimalDB:
    def __init__(self, role="admin"):
        self.role=role
        self.read_calls=0
        self.commit_calls=0
        self.case=ClinicalCase(case_code="FAKE-001")
        self.case.id=uuid4()
        self.case.created_at=None
        self.case.archived_at=None
        self.case.published_version_number=None
    def get(self, model, key):
        assert model is Profile
        return type("P", (), {"role": self.role})()
    def scalars(self, statement):
        self.read_calls+=1
        return type("Rows", (), {"all":lambda self: []})()
    def scalar(self, statement):
        self.read_calls+=1
        return self.case if statement.column_descriptions[0]["entity"] is ClinicalCase else None
    def commit(self): self.commit_calls+=1
    def rollback(self): pass


def client(db, routers, signed_in=True):
    app=FastAPI()
    for router in routers: app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db]=lambda: db
    if signed_in: app.dependency_overrides[get_current_user]=lambda:{"id":UID,"email":"fixture@example.invalid"}
    return TestClient(app)


def test_reviewer_allowlist_fails_closed():
    assert not clinician_is_allowed(UID, "")
    assert not clinician_is_allowed(UID, "invalid-uuid")
    assert clinician_is_allowed(UID, UID)
    assert clinician_is_allowed(UID, f"{uuid4()}, {UID}")


def test_admin_list_denied_to_anonymous_and_student():
    anonymous=MinimalDB()
    assert client(anonymous,[admin_router],signed_in=False).get("/api/v1/admin/cases").status_code==401
    assert anonymous.read_calls==0
    student=MinimalDB(role="student")
    assert client(student,[admin_router]).get("/api/v1/admin/cases").status_code==403
    assert student.read_calls==0


def test_admin_empty_list_safe_response():
    db=MinimalDB()
    r=client(db,[admin_router]).get("/api/v1/admin/cases")
    assert r.status_code==200
    assert r.json()=={"items":[],"limit":20,"offset":0,"has_more":False}
    assert "ground_truth" not in r.text


def test_approval_endpoint_denied_when_no_verified_reviewer(monkeypatch):
    from app.api.routes import case_approval
    # Must reject before service/DB writes even if payload supplied.
    monkeypatch.setattr(case_approval.settings, "clinical_reviewer_user_ids", "")
    fake_body={"blueprint": {"schema_version":"3.2","case_id":"FAKE-001","meta":{},"patient":{},
        "persona":{"respondent_role":"patient","speech_language":"ar"},"history_items":[],
        "exam_items":[],"investigations":[],"imaging":[],
        "ground_truth":{"final_diagnosis":{},"difficulty_factors":{},"debrief":{}}},
        "evidence_reference":"review-doc-123","medical_accuracy_confirmed":True,
        "privacy_review_confirmed":True,"source_review_confirmed":True}
    db=MinimalDB()
    r=client(db,[approval_router]).post("/api/v1/admin/cases/FAKE-001/approve",json=fake_body)
    assert r.status_code==403
    assert db.commit_calls==0


def test_blueprint_hash_stable_and_mutation_detected():
    value={"meta":{"title":"X","review_status":"approved"},"history_items":[]}
    assert blueprint_hash(value)==blueprint_hash(deepcopy(value))
    assert blueprint_hash(value)!=blueprint_hash({**value,"meta":{"title":"Y"}})


def test_model_snapshot_review_is_version_scoped():
    columns=CaseReviewApproval.__table__.columns
    assert "case_version_id" in columns
    assert "blueprint_sha256" in columns
    assert "reviewer_user_id" in columns


def test_approved_snapshot_creates_immutable_new_version_and_audit():
    from app.models.case_review import CaseReviewApproval
    from app.services.case_review import approve_new_snapshot
    from tests.test_case_lifecycle_api import approved_blueprint
    old = approved_blueprint()
    old["meta"]["review_status"] = "draft"
    class ReviewDB:
        def __init__(self):
            self.case = ClinicalCase(case_code="SYNTHETIC-CASE-01")
            self.case.id = uuid4()
            self.case.archived_at = None
            self.old = CaseVersion(case_id=self.case.id, version_number=1, blueprint=deepcopy(old))
            self.old.id = uuid4()
            self.pending = []
            self.new_versions = []
            self.audits = []
        def scalar(self, stmt):
            entity=stmt.column_descriptions[0]["entity"]
            if entity is ClinicalCase: return self.case
            if entity is CaseVersion: return self.new_versions[-1] if self.new_versions else self.old
            if entity is CaseReviewApproval: return None
            raise AssertionError(entity)
        def add(self, obj): self.pending.append(obj)
        def flush(self):
            for obj in self.pending:
                if isinstance(obj,CaseVersion):
                    obj.id=uuid4()
                    self.new_versions.append(obj)
                if isinstance(obj,CaseReviewApproval): self.audits.append(obj)
            self.pending.clear()
    db=ReviewDB()
    approved=CaseBlueprintV32.model_validate(approved_blueprint())
    result=approve_new_snapshot(db,"SYNTHETIC-CASE-01",approved,uuid4(),"signed-review-document-123")
    assert result.version_number==2
    assert result.status=="approved_pending_publication"
    assert db.old.blueprint==old
    assert db.old.published_at is None
    assert len(db.new_versions)==1 and len(db.audits)==1
    assert db.audits[0].blueprint_sha256==blueprint_hash(db.new_versions[0].blueprint)
    assert db.audits[0].case_version_id==db.new_versions[0].id
    assert db.case.published_version_number is None


def test_approval_refuses_medically_incomplete_snapshot_before_db_writes():
    from app.services.case_review import approve_new_snapshot
    from tests.test_case_lifecycle_api import approved_blueprint
    bp=approved_blueprint()
    bp["meta"]["anonymized"]=False
    class NoWriteDB:
        def scalar(self, stmt): raise AssertionError("should fail checks before querying")
        def add(self, obj): raise AssertionError("no DB writes allowed")
    import pytest
    with pytest.raises(PublicationBlocked):
        approve_new_snapshot(NoWriteDB(),"SYNTHETIC-CASE-01",CaseBlueprintV32.model_validate(bp),uuid4(),"signed-review-document-123")


def test_publish_refuses_missing_clinician_audit():
    from tests.test_case_lifecycle_api import FakeDB, approved_blueprint
    db=FakeDB(blueprint=approved_blueprint())
    db.audit_present=False
    import pytest
    with pytest.raises(PublicationBlocked):
        publish_case_version(db,"SYNTHETIC-CASE-01",1)
    assert db.case.published_version_number is None
