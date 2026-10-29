
import json
import tempfile
import unittest
from pathlib import Path

from backend.app.services.blueprint_adapter import (
    load_blueprint,
    get_stage_items,
    get_priority_items,
)


class TestBlueprintAdapter(unittest.TestCase):

    def setUp(self):
        self.blueprint = {
            "schema_version": "3.2",
            "meta": {
                "review_status": "draft"
            },
            "history_items": [
                {
                    "id": "onset",
                    "known": True,
                    "facts": ["Symptoms began yesterday."],
                    "relevance": "essential"
                },
                {
                    "id": "other",
                    "known": True,
                    "facts": ["No additional information."],
                    "relevance": "optional"
                }
            ],
            "exam_items": [],
            "investigations": [],
            "imaging": []
        }

    def test_stage_mapping(self):
        items = get_stage_items(
            self.blueprint, "history"
        )
        self.assertEqual(len(items), 2)

    def test_draft_blocks_priority_items(self):
        items = get_priority_items(
            self.blueprint, "history"
        )
        self.assertEqual(items, [])

    def test_approved_priority_items(self):
        self.blueprint["meta"]["review_status"] = "approved"

        items = get_priority_items(
            self.blueprint, "history"
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "onset")

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            get_stage_items(
                self.blueprint, "invalid"
            )

    def test_load_blueprint(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "case.json"

            path.write_text(
                json.dumps(self.blueprint),
                encoding="utf-8"
            )

            result = load_blueprint(str(path))

            self.assertEqual(
                result["schema_version"], "3.2"
            )


if __name__ == "__main__":
    unittest.main()
