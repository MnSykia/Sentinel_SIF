import json
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from app import normalise, report_from_row, validate_date_filters, validate_training_dataset


class AppRobustnessTests(unittest.TestCase):
    def test_normalise_rejects_non_objects(self):
        for value in (None, "text", [], 42):
            record, errors = normalise(value, "test")
            self.assertIsNone(record)
            self.assertIn("record must be an object", errors)

    def test_normalise_timestamp_validation(self):
        valid, errors = normalise({"id": "R-1", "date": "2026-09-10T12:00:00Z", "location": "Site", "work_type": "Activity", "description": "Valid narrative"}, "test")
        self.assertEqual(errors, [])
        self.assertEqual(valid["report_id"], "R-1")
        invalid, errors = normalise({"id": "R-2", "date": "not-a-date", "location": "Site", "work_type": "Activity", "description": "Valid narrative"}, "test")
        self.assertIsNone(invalid)
        self.assertTrue(any("ISO-8601" in error for error in errors))

    def test_dashboard_date_validation(self):
        self.assertEqual(validate_date_filters("2026-09-01", "2026-09-10"), ("2026-09-01", "2026-09-10"))
        for values in (("bad", None), ("2026-09-11", "2026-09-10")):
            with self.assertRaises(HTTPException): validate_date_filters(*values)

    def test_training_validation_rejects_missing_or_malformed_data(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "train.json"
            with self.assertRaises(RuntimeError): validate_training_dataset(path)
            path.write_text(json.dumps(["bad"]), encoding="utf-8")
            with self.assertRaises(RuntimeError): validate_training_dataset(path)

    def test_malformed_persisted_model_output_is_controlled(self):
        with self.assertRaises(HTTPException) as raised:
            report_from_row({"report_id": "BROKEN", "model_output": "not-json"})
        self.assertEqual(raised.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
