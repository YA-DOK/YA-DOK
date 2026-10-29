import unittest
from dataclasses import replace
from backend.app.services.session_hint_engine import SessionSnapshot, get_session_hint

HINTS = {"history": ["Ask about onset.", "Clarify the timeline.", "Compare the symptom pattern."]}
BASE = SessionSnapshot(
    session_id="s1", student_id="student1", mode="training",
    stage="history", status="active", total_hints_used=0, stage_hints_used=0,
)

class TestSessionHintEngine(unittest.TestCase):
    def test_first_hint(self):
        result = get_session_hint(BASE, "student1", HINTS)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["hint_level"], 1)
        self.assertEqual(result["remaining_hints"], 2)

    def test_progressive_hint(self):
        session = replace(BASE, total_hints_used=1, stage_hints_used=1)
        self.assertEqual(get_session_hint(session, "student1", HINTS)["hint_level"], 2)

    def test_assessment_blocked(self):
        session = replace(BASE, mode="assessment")
        self.assertFalse(get_session_hint(session, "student1", HINTS)["allowed"])

    def test_inactive_blocked(self):
        session = replace(BASE, status="completed")
        self.assertFalse(get_session_hint(session, "student1", HINTS)["allowed"])

    def test_limit_blocked(self):
        session = replace(BASE, total_hints_used=3, stage_hints_used=2)
        self.assertFalse(get_session_hint(session, "student1", HINTS)["allowed"])

    def test_wrong_owner_rejected(self):
        with self.assertRaises(PermissionError):
            get_session_hint(BASE, "another_student", HINTS)

    def test_missing_stage_blocked(self):
        session = replace(BASE, stage="imaging")
        self.assertFalse(get_session_hint(session, "student1", HINTS)["allowed"])

    def test_invalid_counters_rejected(self):
        session = replace(BASE, total_hints_used=0, stage_hints_used=1)
        with self.assertRaises(ValueError):
            get_session_hint(session, "student1", HINTS)

if __name__ == "__main__":
    unittest.main()
