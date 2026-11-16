"""Reproducible evaluation on labeled *synthetic* cases only.

Usage from the repository root:
    python -m convocalivre.benchmark tests/fixtures/act_cases.json

These numbers MUST NOT be advertised as measured real-world accuracy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acts import EVENT_TYPES
from .core import analyze

LABELS = (*EVENT_TYPES, "no_name_match")
EVENT_LABELS = set(EVENT_TYPES) - {"indeterminado"}


def predict_case(text: str, name: str) -> str:
    report = analyze(text, name)
    matches = report["matches"]
    if not matches:
        return "no_name_match"
    kinds = {match["act_type"] for match in matches}
    return kinds.pop() if len(kinds) == 1 else "indeterminado"


def evaluate_cases(cases: list[dict]) -> dict:
    """Compute class-level FP/FN and event-vs-non-event confusion."""
    matrix = {a: {p: 0 for p in LABELS} for a in LABELS}
    mismatches = []
    seen = set()
    for case in cases:
        case_id = case["id"]
        if case_id in seen:
            raise ValueError(f"Repeated case id: {case_id}")
        seen.add(case_id)
        expected = case["expected"]
        if expected not in LABELS:
            raise ValueError(f"Unknown expected label: {expected}")
        predicted = predict_case(case["text"], case["name"])
        matrix[expected][predicted] += 1
        if predicted != expected:
            mismatches.append({
                "id": case_id, "expected": expected, "predicted": predicted,
            })

    total = len(cases)
    correct = sum(matrix[label][label] for label in LABELS)
    classes = {}
    for label in LABELS:
        tp = matrix[label][label]
        fp = sum(matrix[actual][label] for actual in LABELS if actual != label)
        fn = sum(matrix[label][prediction] for prediction in LABELS if prediction != label)
        precision = (tp / (tp + fp)) if (tp + fp) else None
        recall = (tp / (tp + fn)) if (tp + fn) else None
        classes[label] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall,
        }

    event_tp = event_fp = event_fn = event_tn = event_type_errors = 0
    for actual in LABELS:
        for predicted in LABELS:
            quantity = matrix[actual][predicted]
            actual_event = actual in EVENT_LABELS
            predicted_event = predicted in EVENT_LABELS
            if actual_event and predicted_event:
                event_tp += quantity
                if actual != predicted:
                    event_type_errors += quantity
            elif not actual_event and predicted_event:
                event_fp += quantity
            elif actual_event and not predicted_event:
                event_fn += quantity
            else:
                event_tn += quantity

    return {
        "dataset_type": "synthetic_only",
        "number_of_cases": total,
        "exact_label_correct": correct,
        "exact_label_errors": total - correct,
        "accuracy": (correct / total) if total else None,
        "event_detection": {
            "tp": event_tp, "fp": event_fp, "fn": event_fn, "tn": event_tn,
            "wrong_event_type": event_type_errors,
            "precision": (event_tp / (event_tp + event_fp))
            if (event_tp + event_fp) else None,
            "recall": (event_tp / (event_tp + event_fn))
            if (event_tp + event_fn) else None,
        },
        "per_class": classes,
        "confusion_matrix": matrix,
        "mismatches": mismatches,
        "caution": (
            "Dataset inteiramente sintetico: metricas NAO representam "
            "confiabilidade em diários oficiais reais. Erros de extracao de PDF "
            "e contexto legal não foram medidos."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="JSON sintético rotulado")
    parser.add_argument("--output", type=Path, help="Salvar relatório JSON (opcional)")
    args = parser.parse_args(argv)
    raw = json.loads(args.dataset.read_text(encoding="utf-8"))
    if raw.get("dataset_type") != "synthetic_only":
        parser.error("Este comando so aceita corpus explicitamente sintetico.")
    report = evaluate_cases(raw["cases"])
    report["dataset"] = raw.get("dataset")
    report_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(report_json, encoding="utf-8")
    else:
        print(report_json, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
