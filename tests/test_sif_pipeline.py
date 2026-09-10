"""Regression coverage for explainable energy + direct-control SIF decisions."""
import unittest
from unittest.mock import patch

from sentinelsif.classifier import SentinelClassifier


class SIFPipelineRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Rule regression tests are deterministic and do not require model downloads.
        with patch("sentinelsif.classifier.SentenceTransformer", side_effect=RuntimeError("test offline")):
            cls.engine = SentinelClassifier()

    def analyse(self, narrative):
        return self.engine.analyze_report({
            "report_id": "REGRESSION", "timestamp": "2026-09-01T00:00:00Z",
            "site": "Test site", "activity": "Test activity", "narrative": narrative,
            "filer_severity": "Low",
        })

    def assert_sif(self, narrative, energy=None, control=None):
        result = self.analyse(narrative)
        self.assertTrue(result["sif_potential"], result)
        if energy: self.assertEqual(result["energy_source"], energy, result)
        if control: self.assertIn(result["control_status"], control, result)
        self.assertIn("SIF-Potential", result["decision_rationale"])

    def test_suspended_load_with_failed_exclusion_zone_is_sif(self):
        self.assert_sif("A suspended load moved over the work area while workers were standing below. Exclusion zone was not maintained.", "Gravity", ("not_followed", "absent"))

    def test_defective_lifting_equipment_and_plan_failure_is_sif(self):
        self.assert_sif("Defective lifting equipment was used to lift a heavy component. The lifting plan was not followed.", "Gravity", ("not_followed", "absent"))

    def test_permit_violation_without_energy_is_not_sif(self):
        result = self.analyse("Work continued outside the approved permit scope and the permit extension was not obtained.")
        self.assertFalse(result["sif_potential"], result)
        self.assertEqual(result["energy_source"], "None", result)

    def test_verified_routine_controls_are_not_sif(self):
        result = self.analyse("During routine inspection, the required permit, isolation and PPE controls were verified before work started.")
        self.assertFalse(result["sif_potential"], result)

    def test_loto_failure_with_pressure_energy_is_sif(self):
        self.assert_sif("A flange was opened at 450 PSI without verifying energy isolation.", "Pressure", ("absent", "not_followed"))

    def test_height_work_without_fall_protection_is_sif(self):
        self.assert_sif("Worker was performing maintenance at height without wearing fall arrest equipment. Edge protection was missing.", "Gravity", ("absent", "not_followed"))

    def test_confined_space_without_monitoring_or_standby_is_sif(self):
        self.assert_sif("Worker entered a tank without gas monitoring and no standby attendant was present.", "Chemical/Thermal", ("absent", "not_followed"))

    def test_hot_work_near_hydrocarbon_without_controls_is_sif(self):
        self.assert_sif("Welding was carried out near hydrocarbon equipment without a valid permit and without a gas test.", "Chemical/Thermal", ("absent", "not_followed"))


if __name__ == "__main__":
    unittest.main()
