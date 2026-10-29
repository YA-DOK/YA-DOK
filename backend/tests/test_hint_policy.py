
import unittest

from backend.app.services.hint_policy import get_hint


class TestHintPolicy(unittest.TestCase):

    def test_training_first_hint(self):
        result = get_hint("training", "history", 0)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["hint_level"], 1)

    def test_training_third_hint(self):
        result = get_hint("training", "history", 2)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["remaining_hints"], 0)

    def test_hint_limit(self):
        result = get_hint("training", "history", 3)
        self.assertFalse(result["allowed"])

    def test_assessment_blocks_hints(self):
        result = get_hint("assessment", "history", 0)
        self.assertFalse(result["allowed"])

    def test_invalid_mode(self):
        with self.assertRaises(ValueError):
            get_hint("invalid", "history", 0)


if __name__ == "__main__":
    unittest.main()
