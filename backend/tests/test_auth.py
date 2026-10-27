
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import auth
from app.core.config import settings

# Test the real auth router without connecting to the database
app = FastAPI()
app.include_router(auth.router, prefix="/api/v1")

client = TestClient(app)


def mock_supabase_response(monkeypatch, status_code, data):
    """Replace Supabase HTTP calls with fake responses."""

    monkeypatch.setattr(
        settings,
        "supabase_url",
        "https://example.supabase.co",
    )
    monkeypatch.setattr(
        settings,
        "supabase_key",
        "test-publishable-key",
    )

    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code,
            json=data,
        )
    )

    original_client = httpx.AsyncClient

    def mocked_client(*args, **kwargs):
        return original_client(
            *args,
            transport=transport,
            **kwargs,
        )

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        mocked_client,
    )


def test_missing_token():
    """Requests without tokens must be rejected."""

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_valid_token(monkeypatch):
    """Valid Supabase tokens must be accepted."""

    mock_supabase_response(
        monkeypatch,
        200,
        {
            "id": "test-user-123",
            "email": "student@example.com",
        },
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer valid-test-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "test-user-123",
        "email": "student@example.com",
    }


def test_invalid_token(monkeypatch):
    """Invalid tokens must be rejected."""

    mock_supabase_response(
        monkeypatch,
        401,
        {"message": "Invalid token"},
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-test-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
