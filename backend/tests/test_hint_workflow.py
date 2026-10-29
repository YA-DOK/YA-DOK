import unittest
from contextlib import contextmanager
from dataclasses import replace
from threading import RLock

from backend.app.services.hint_workflow import HintWorkflow
from backend.app.services.session_hint_engine import SessionSnapshot


BASE = SessionSnapshot(
    session_id="session1", student_id="student1", mode="training",
    stage="history", status="active",
    total_hints_used=0, stage_hints_used=0,
)


class FakeLockedSession:
    def __init__(self, snapshot=BASE, hints=None):
        self.snapshot = snapshot
        self.approved_hints = hints or {"history": [
            "Ask about onset.", "Check progression.", "Review context."
        ]}
        self.events = []

    def record_hint_used(self, *, stage, hint_level, reason):
        self.events.append((stage, hint_level, reason))
        self.snapshot = replace(
            self.snapshot,
            total_hints_used=self.snapshot.total_hints_used + 1,
            stage_hints_used=self.snapshot.stage_hints_used + 1,
        )


class FakeStore:
    def __init__(self, record):
        self.record = record
        self.guard = RLock()

    @contextmanager
    def lock_session(self, session_id):
        with self.guard:
            if self.record is None or session_id != "session1":
                yield None
            else:
                yield self.record


class TestHintWorkflow(unittest.TestCase):
    def test_first_request_records_event(self):
        record = FakeLockedSession()
        result = HintWorkflow(FakeStore(record)).request_hint(
            session_id="session1", authenticated_user_id="student1")
        self.assertTrue(result["allowed"])
        self.assertEqual(result["hint_level"], 1)
        self.assertEqual(len(record.events), 1)
        self.assertEqual(record.snapshot.total_hints_used, 1)

    def test_second_request_progresses(self):
        record = FakeLockedSession()
        workflow = HintWorkflow(FakeStore(record))
        workflow.request_hint(session_id="session1", authenticated_user_id="student1")
        second = workflow.request_hint(session_id="session1", authenticated_user_id="student1")
        self.assertEqual(second["hint_level"], 2)
        self.assertEqual(len(record.events), 2)

    def test_assessment_does_not_record_event(self):
        record = FakeLockedSession(replace(BASE, mode="assessment"))
        result = HintWorkflow(FakeStore(record)).request_hint(
            session_id="session1", authenticated_user_id="student1")
        self.assertFalse(result["allowed"])
        self.assertEqual(record.events, [])

    def test_wrong_owner_does_not_record_event(self):
        record = FakeLockedSession()
        with self.assertRaises(PermissionError):
            HintWorkflow(FakeStore(record)).request_hint(
                session_id="session1", authenticated_user_id="other")
        self.assertEqual(record.events, [])

    def test_completed_session_does_not_record_event(self):
        record = FakeLockedSession(replace(BASE, status="completed"))
        result = HintWorkflow(FakeStore(record)).request_hint(
            session_id="session1", authenticated_user_id="student1")
        self.assertFalse(result["allowed"])
        self.assertEqual(record.events, [])

    def test_limit_is_enforced_across_requests(self):
        record = FakeLockedSession()
        workflow = HintWorkflow(FakeStore(record))
        results = [workflow.request_hint(
            session_id="session1", authenticated_user_id="student1")
            for _ in range(4)]
        self.assertEqual([r["allowed"] for r in results],
                         [True, True, True, False])
        self.assertEqual(len(record.events), 3)

    def test_session_not_found(self):
        with self.assertRaises(LookupError):
            HintWorkflow(FakeStore(None)).request_hint(
                session_id="session1", authenticated_user_id="student1")

    def test_reason_stored_by_server(self):
        record = FakeLockedSession()
        HintWorkflow(FakeStore(record)).request_hint(
            session_id="session1", authenticated_user_id="student1",
            reason="requested_during_history")
        self.assertEqual(record.events[0][2], "requested_during_history")

    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):
            HintWorkflow(FakeStore(FakeLockedSession())).request_hint(
                session_id="session1", authenticated_user_id="")


if __name__ == "__main__":
    unittest.main()
