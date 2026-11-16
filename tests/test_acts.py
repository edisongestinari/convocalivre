"""Reproducible, fully synthetic evaluation of the act classifier."""

import json
from pathlib import Path
import unittest

from convocalivre.acts import EVENT_TYPES, classify_mention
from convocalivre.benchmark import LABELS, evaluate_cases, predict_case
from convocalivre.core import analyze


FIXTURE = Path(__file__).parent / "fixtures" / "act_cases.json"


class ActClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
        cls.by_id = {item["id"]: item for item in cls.cases}

    def test_all_cases_are_synthetic_and_unique(self):
        self.assertEqual(len(self.cases), 39)
        self.assertEqual(len(self.by_id), len(self.cases))
        self.assertEqual(set(LABELS), set(EVENT_TYPES) | {"no_name_match"})

    def test_core_examples_and_negation(self):
        for case_id in ("C01", "C04", "N01", "N04", "D01", "D04",
                        "R01", "R04", "I01", "I02", "I03", "I04",
                        "I06", "I07", "M01", "M02"):
            case = self.by_id[case_id]
            with self.subTest(case_id=case_id):
                self.assertEqual(
                    predict_case(case["text"], case["name"]),
                    case["expected"],
                )

    def test_ambiguity_abstains_instead_of_guessing(self):
        # Two different names with conflicting actions in one clause.
        for case_id in ("H01", "H02"):
            case = self.by_id[case_id]
            with self.subTest(case_id=case_id):
                report = analyze(case["text"], case["name"])
                self.assertEqual(report["matches"][0]["act_type"], "indeterminado")
                self.assertEqual(
                    report["matches"][0]["act_basis"],
                    "conflicting_indicators",
                )
                self.assertTrue(report["matches"][0]["requires_manual_review"])

    def test_evidence_fields_and_counts(self):
        report = analyze("Maria de Sousa foi convocada.", "Maria de Sousa")
        self.assertEqual(report["matches"][0]["act_type"], "convocacao")
        self.assertEqual(report["matches"][0]["act_indicator"], "convocada")
        self.assertEqual(report["act_type_counts"]["convocacao"], 1)
        self.assertTrue(report["matches"][0]["requires_manual_review"])

    def test_source_independent_context(self):
        text = "Convocado outro candidato.\nMaria de Sousa apresentou recurso."
        report = analyze(text, "Maria de Sousa")
        self.assertEqual(report["matches"][0]["act_type"], "indeterminado")
        self.assertEqual(report["match_count"], 1)

    def test_invalid_offsets_are_rejected(self):
        with self.assertRaises(ValueError):
            classify_mention("abc", 3, 1)

    def test_confusion_accounting_and_no_leakage(self):
        metrics = evaluate_cases(self.cases)
        self.assertEqual(metrics["number_of_cases"], 39)
        self.assertEqual(
            metrics["exact_label_correct"] + metrics["exact_label_errors"], 39
        )
        self.assertEqual(
            sum(sum(row.values()) for row in metrics["confusion_matrix"].values()), 39
        )
        detection = metrics["event_detection"]
        self.assertEqual(
            sum(detection[key] for key in ("tp", "fp", "fn", "tn")), 39
        )
        # Adversarial cases remain visible as measured errors, not hidden.
        mismatch_ids = {item["id"] for item in metrics["mismatches"]}
        self.assertIn("H01", mismatch_ids)
        self.assertIn("H02", mismatch_ids)

    def test_duplicate_identifiers_cannot_inflate_metrics(self):
        with self.assertRaises(ValueError):
            evaluate_cases([self.cases[0], self.cases[0]])


if __name__ == "__main__":
    unittest.main()
