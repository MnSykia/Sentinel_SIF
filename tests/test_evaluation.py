import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import cast
from unittest.mock import patch

from evaluation import evaluate_classifier, run_evaluation
from sentinelsif.classifier import SentinelClassifier


class _StubClassifier:
    def __init__(self, results, is_trained=True):
        self.results = iter(results)
        self.is_trained = is_trained

    def analyze_report(self, record):
        return next(self.results)

    def train_on_data(self, dataset_path):
        self.is_trained = True


def StubClassifier(results, is_trained=True) -> SentinelClassifier:
    return cast(SentinelClassifier, _StubClassifier(results, is_trained))


def formal_record(report_id="EXPERT-1", sif=True, rules=None, **overrides):
    record = {
        "report_id": report_id,
        "timestamp": "2026-01-01T00:00:00Z",
        "report_type": "Near-Miss",
        "site": "Reviewed site",
        "activity": "Reviewed activity",
        "narrative": "Independently reviewed safety narrative.",
        "ground_truth_sif": sif,
        "ground_truth_lsr": rules or ["Energy Isolation"],
        "annotation_status": "expert_reviewed",
        "annotator_count": 2,
        "source": "independent review",
        "source_reference": "REVIEW-001",
        "reviewed_at": "2026-01-02T00:00:00Z",
    }
    record.update(overrides)
    return record


class EvaluationTests(unittest.TestCase):
    def synthetic_record(self, report_id, sif=False, rules=None):
        return {"report_id": report_id, "narrative": "Synthetic benchmark narrative.", "ground_truth": {"sif_potential": sif, "life_saving_rules": rules or []}}

    def write_synthetic(self, root, master, training):
        data_dir = Path(root) / "data"
        data_dir.mkdir(exist_ok=True)
        (data_dir / "dataset.json").write_text(json.dumps(master), encoding="utf-8")
        (data_dir / "train_split.json").write_text(json.dumps(training), encoding="utf-8")

    def write_expert(self, root, records):
        (Path(root) / "data" / "expert_reviewed_test.json").write_text(json.dumps(records), encoding="utf-8")

    def test_synthetic_benchmark_metrics_use_held_out_records(self):
        training = [self.synthetic_record("TRAIN")]
        held_out = [
            self.synthetic_record("A", True, ["Energy Isolation"]),
            self.synthetic_record("B", True, ["Hot Work"]),
            self.synthetic_record("C"),
            self.synthetic_record("D"),
        ]
        results = [
            {"sif_potential": True, "life_saving_rules": [{"rule": "Energy Isolation"}, {"rule": "Hot Work"}]},
            {"sif_potential": False, "life_saving_rules": [{"rule": "Energy Isolation"}]},
            {"sif_potential": True, "life_saving_rules": []},
            {"sif_potential": False, "life_saving_rules": []},
        ]
        with tempfile.TemporaryDirectory() as temp:
            self.write_synthetic(temp, training + held_out, training)
            result = evaluate_classifier(Path(temp), StubClassifier(results))
        self.assertEqual(result["status"], "synthetic_benchmark")
        self.assertEqual(result["test_set_size"], 4)
        self.assertAlmostEqual(result["measured"]["sif_recall"], 0.5)
        self.assertAlmostEqual(result["measured"]["sif_precision"], 0.5)
        self.assertAlmostEqual(result["measured"]["lsr_top1"], 0.5)
        self.assertAlmostEqual(result["measured"]["lsr_top2"], 0.5)
        self.assertEqual(result["formal_evaluation"]["status"], "not_evaluated")

    def test_valid_formal_evaluation_is_primary(self):
        records = [formal_record("A", True, ["Energy Isolation"]), formal_record("B", False, [])]
        with tempfile.TemporaryDirectory() as temp:
            self.write_synthetic(temp, [self.synthetic_record("SYNTH")], [self.synthetic_record("TRAIN")])
            self.write_expert(temp, records)
            result = evaluate_classifier(Path(temp), StubClassifier([
                {"sif_potential": False, "life_saving_rules": []},
                {"sif_potential": True, "life_saving_rules": [{"rule": "Energy Isolation"}]},
                {"sif_potential": False, "life_saving_rules": [{"rule": "Hot Work"}]},
            ]))
        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["evaluation_type"], "expert_reviewed")
        self.assertEqual(result["formal_evaluation"]["dataset_size"], 2)

    def test_valid_formal_evaluation_does_not_require_synthetic_files(self):
        records = [formal_record("A", True, ["Energy Isolation"])]
        with tempfile.TemporaryDirectory() as temp:
            data_dir = Path(temp) / "data"
            data_dir.mkdir()
            (data_dir / "train_split.json").write_text(json.dumps([]), encoding="utf-8")
            self.write_expert(temp, records)
            result = evaluate_classifier(Path(temp), StubClassifier([{"sif_potential": True, "life_saving_rules": [{"rule": "Energy Isolation"}]}]))
        self.assertEqual(result["status"], "evaluated")
        self.assertEqual(result["evaluation_type"], "expert_reviewed")

    def test_missing_or_empty_formal_dataset_is_not_evaluated(self):
        with tempfile.TemporaryDirectory() as temp:
            self.write_synthetic(temp, [{"report_id": "A", "ground_truth": {"sif_potential": True, "life_saving_rules": []}}], [])
            result = evaluate_classifier(Path(temp), StubClassifier([{"sif_potential": True, "life_saving_rules": []}]))
            self.assertEqual(result["formal_evaluation"]["status"], "not_evaluated")
            self.write_expert(temp, [])
            result = evaluate_classifier(Path(temp), StubClassifier([{"sif_potential": True, "life_saving_rules": []}]))
        self.assertEqual(result["formal_evaluation"]["status"], "not_evaluated")
        self.assertIsNone(result["formal_evaluation"]["measured"]["sif_recall"])

    def test_missing_synthetic_dataset_is_not_evaluated(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "data").mkdir()
            result = evaluate_classifier(Path(temp), StubClassifier([]))
        self.assertEqual(result["status"], "not_evaluated")
        self.assertEqual(result["synthetic_benchmark"]["status"], "not_evaluated")

    def test_malformed_or_non_array_synthetic_files_are_invalid(self):
        cases = [("{not-json", "invalid JSON"), ("{}", "top-level JSON value must be an array")]
        for payload, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                data_dir = Path(temp) / "data"
                data_dir.mkdir()
                (data_dir / "dataset.json").write_text(payload, encoding="utf-8")
                (data_dir / "train_split.json").write_text("[]", encoding="utf-8")
                result = evaluate_classifier(Path(temp), StubClassifier([]))
                self.assertEqual(result["status"], "invalid_test_set")
                self.assertTrue(any(expected in error for error in result["validation"]["errors"]))

    def test_malformed_duplicate_invalid_and_overlap_formal_data(self):
        cases = [
            ([formal_record("A", ground_truth_sif="yes")], "ground_truth_sif"),
            ([formal_record("A"), formal_record("A")], "duplicate"),
            ([formal_record("TRAIN")], "overlaps"),
            ([formal_record("A", rules=["Not a Life-Saving Rule"])], "invalid ground_truth_lsr"),
        ]
        for records, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                self.write_synthetic(temp, [self.synthetic_record("S")], [self.synthetic_record("TRAIN")])
                self.write_expert(temp, records)
                result = evaluate_classifier(Path(temp), StubClassifier([{"sif_potential": False, "life_saving_rules": []}]))
                self.assertEqual(result["formal_evaluation"]["status"], "invalid_test_set")
                self.assertEqual(result["status"], "invalid_test_set")
                self.assertTrue(any(expected in error or (expected == "invalid ground_truth_lsr" and "invalid Life-Saving Rule" in error) for error in result["formal_evaluation"]["validation"]["errors"]))

    def test_synthetic_schema_and_id_validation(self):
        cases = [
            ([self.synthetic_record("A"), {"report_id": "A", "narrative": "x", "ground_truth": {"sif_potential": False, "life_saving_rules": []}}], [self.synthetic_record("TRAIN")], "dataset: duplicate report_id"),
            ([self.synthetic_record("A")], [self.synthetic_record("TRAIN"), self.synthetic_record("TRAIN")], "training: duplicate report_id"),
            ([self.synthetic_record("A")], [self.synthetic_record("MISSING")], "not present in dataset"),
            ([{"report_id": "A", "narrative": "x", "ground_truth": {"sif_potential": "yes", "life_saving_rules": ["Energy Isolation"]}}], [], "sif_potential must be boolean"),
            ([{"report_id": "A", "narrative": "x", "ground_truth": {"sif_potential": False, "life_saving_rules": ["Bad Rule"]}}], [], "invalid Life-Saving Rule"),
            (["not an object"], [], "record must be an object"),
        ]
        for master, training, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                self.write_synthetic(temp, master, training)
                result = evaluate_classifier(Path(temp), StubClassifier([]))
                self.assertEqual(result["status"], "invalid_test_set")
                self.assertTrue(any(expected in error for error in result["validation"]["errors"]))

    def test_formal_provenance_edge_cases(self):
        cases = [
            (formal_record("A", rules=["Energy Isolation", "Energy Isolation"]), "duplicate labels"),
            (formal_record("A", annotator_count=True), "annotator_count"),
            (formal_record("A", annotator_count=0), "annotator_count"),
            (formal_record("A", timestamp="2026-01-01T00:00:00"), "timestamp"),
            (formal_record("A", source_reference=""), "source_reference"),
        ]
        for record, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp:
                self.write_synthetic(temp, [self.synthetic_record("S")], [self.synthetic_record("TRAIN")])
                self.write_expert(temp, [record])
                result = evaluate_classifier(Path(temp), StubClassifier([{"sif_potential": False, "life_saving_rules": []}]))
                self.assertEqual(result["formal_evaluation"]["status"], "invalid_test_set")
                self.assertTrue(any(expected in error for error in result["formal_evaluation"]["validation"]["errors"]))

    def test_supplied_classifier_training_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            self.write_synthetic(temp, [self.synthetic_record("S")], [])
            classifier = StubClassifier([{"sif_potential": False, "life_saving_rules": []}])
            result = evaluate_classifier(Path(temp), classifier)
            self.assertEqual(result["status"], "synthetic_benchmark")

    def test_untrained_supplied_classifier_requires_explicit_training(self):
        with tempfile.TemporaryDirectory() as temp:
            self.write_synthetic(temp, [self.synthetic_record("S")], [])
            with self.assertRaisesRegex(ValueError, "untrained"):
                evaluate_classifier(Path(temp), StubClassifier([], is_trained=False))

    def test_run_evaluation_prints_cli_summary(self):
        result = {
            "status": "synthetic_benchmark",
            "evaluation_dataset": "data/dataset.json",
            "test_set_size": 4,
            "measured": {"sif_recall": 0.5, "sif_precision": None},
        }
        output = StringIO()
        with patch("evaluation.evaluate_classifier", return_value=result), redirect_stdout(output):
            self.assertIs(run_evaluation(), result)
        self.assertIn("SentinelSIF held-out evaluation", output.getvalue())
        self.assertIn("sif_recall: 50.0%", output.getvalue())
        self.assertIn("sif_precision: Not evaluated", output.getvalue())

    def test_api_evaluation_preserves_provenance_fields(self):
        from app import evaluation as api_evaluation
        with patch("app.evaluate_classifier") as mocked:
            mocked.return_value = {"status": "synthetic_benchmark", "evaluation_type": "synthetic_benchmark"}
            self.assertEqual(api_evaluation()["evaluation_type"], "synthetic_benchmark")
            mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
