
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.hints import (
    router,
    get_current_student_id,
    get_hint_workflow,
)


class FakeWorkflow:
    def request_hint(self, session_id, authenticated_user_id):
        if session_id == "missing":
            raise LookupError("Session not found")

        if session_id == "other":
            raise PermissionError("Access denied")

        return {
            "allowed": True,
            "hint_level": 1,
            "hint": "Review the available information.",
            "remaining_hints": 2,
        }


class TestHintsAPI(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router, prefix="/api/v1")

        self.app.dependency_overrides[get_current_student_id] = (
            lambda: "student-1"
        )
        self.app.dependency_overrides[get_hint_workflow] = (
            lambda: FakeWorkflow()
        )

        self.client = TestClient(self.app)
        self.url = "/api/v1/simulations/session-1/hints"

    def test_valid_hint(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["allowed"])
        self.assertEqual(response.json()["hint_level"], 1)

    def test_missing_session(self):
        response = self.client.post(
            "/api/v1/simulations/missing/hints"
        )
        self.assertEqual(response.status_code, 404)

    def test_wrong_student(self):
        response = self.client.post(
            "/api/v1/simulations/other/hints"
        )
        self.assertEqual(response.status_code, 403)

    def test_unconfigured_authentication(self):
        self.app.dependency_overrides.clear()

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
