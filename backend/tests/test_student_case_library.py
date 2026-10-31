"""Student case library tests: no real user tokens, clinical records or DB writes."""
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from app.api.routes.student_cases import router
from app.core.database import get_db
from app.core.security import get_current_user


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeDB:
    def __init__(self, rows=()):
        self.rows = list(rows)
        self.queries = []

    def execute(self, stmt):
        self.queries.append(stmt)
        return FakeResult(self.rows)


def client_for(db, *, signed_in=True):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    def _db_override():
        yield db

    app.dependency_overrides[get_db] = _db_override
    if signed_in:
        app.dependency_overrides[get_current_user] = lambda: {"id": str(uuid4())}
    return TestClient(app)


SAFE_ROW = {
    "case_id": "DEMO-01", "version_number": 2, "title": "A fictional case",
    "subtitle": "For teaching", "short_brief": "Initial presentation",
    "specialty": "Pediatrics", "setting": "OPD", "difficulty": "beginner",
    "estimated_duration_minutes": 15,
}


def sql_of(stmt):
    return str(stmt.compile(dialect=postgresql.dialect()))


def test_no_login_cannot_list():
    db = FakeDB([SAFE_ROW])
    response = client_for(db, signed_in=False).get("/api/v1/cases")
    assert response.status_code == 401
    assert db.queries == []


def test_no_login_cannot_preview():
    db = FakeDB([SAFE_ROW])
    response = client_for(db, signed_in=False).get("/api/v1/cases/DEMO-01")
    assert response.status_code == 401
    assert db.queries == []


def test_empty_list_before_publication():
    db = FakeDB([])
    response = client_for(db).get("/api/v1/cases")
    assert response.status_code == 200
    assert response.json() == {"items": [], "limit": 20, "offset": 0, "has_more": False}


def test_only_explicit_public_fields_are_returned():
    db = FakeDB([{**SAFE_ROW, "ground_truth": {"final_diagnosis": "SECRET"}, "blueprint": {"private": "SECRET"}}])
    response = client_for(db).get("/api/v1/cases")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["case_id"] == "DEMO-01"
    assert "ground_truth" not in item and "blueprint" not in item
    assert "SECRET" not in response.text


def test_query_enforces_published_unarchived_pointer():
    db = FakeDB([])
    client_for(db).get("/api/v1/cases")
    query = sql_of(db.queries[0]).lower()
    assert "archived_at is null" in query
    assert "published_at is not null" in query
    assert "published_version_number is not null" in query
    assert "version_number = cases.published_version_number" in query
    assert "ground_truth" not in query


def test_specialty_difficulty_pagination_filters():
    db = FakeDB([SAFE_ROW, {**SAFE_ROW, "case_id": "DEMO-02"}])
    response = client_for(db).get(
        "/api/v1/cases?specialty=Pediatrics&difficulty=beginner&limit=1&offset=0"
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["has_more"] is True
    sql = sql_of(db.queries[0]).lower()
    assert 'jsonb_extract_path_text' in sql
    assert "lower(" in sql
    assert "limit" in sql


def test_pagination_validation():
    db = FakeDB([])
    response = client_for(db).get("/api/v1/cases?limit=500")
    assert response.status_code == 422
    assert not db.queries


def test_case_preview_not_found():
    response = client_for(FakeDB([])).get("/api/v1/cases/DOES-NOT-EXIST")
    assert response.status_code == 404


def test_case_preview_is_safe():
    response = client_for(FakeDB([SAFE_ROW])).get("/api/v1/cases/DEMO-01")
    assert response.status_code == 200
    assert response.json()["version_number"] == 2
    assert "ground_truth" not in response.json()
