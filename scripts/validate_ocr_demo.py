"""Validate deterministic parsing against the small labeled OCR demo set."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.report_scanner import FEATURE_ORDER, parse_text_pages


ARTIFACTS = ROOT / "artifacts/ocr_demo"


def main() -> None:
    samples = json.loads((ARTIFACTS / "validation_samples.json").read_text())
    expected_total = 0
    exact_total = 0
    false_extractions = 0
    unit_matches = 0
    unit_expected = 0
    details = []
    for sample in samples:
        result = parse_text_pages(sample["pages"], "Labeled demo text")
        expected = sample["expected"]
        observed = {feature: result.safe_candidate(feature).normalized_value for feature in FEATURE_ORDER if result.safe_candidate(feature)}
        correct = 0
        for feature, value in expected.items():
            expected_total += 1
            observed_value = observed.get(feature)
            matches = observed_value == value or (
                isinstance(value, float) and isinstance(observed_value, float) and abs(observed_value - value) < 1e-9
            )
            correct += int(matches)
            exact_total += int(matches)
            candidate = result.safe_candidate(feature)
            if candidate and feature in {"hemo", "pcv", "sc"}:
                unit_expected += 1
                unit_matches += int(bool(candidate.original_unit))
        false_extractions += len(set(observed) - set(expected))
        details.append({"sample": sample["id"], "correct": correct, "expected": len(expected)})
    output = {
        "samples": len(samples),
        "expected_fields": expected_total,
        "correctly_extracted": exact_total,
        "unit_checks": unit_expected,
        "unit_matches": unit_matches,
        "false_extraction_count": false_extractions,
        "details": details,
        "reporting_boundary": "Small fictional demo set; this is not a clinical OCR accuracy estimate.",
    }
    (ARTIFACTS / "validation_results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"Demo extraction validation: {exact_total}/{expected_total} expected fields correctly extracted.")
    print(f"Unit match: {unit_matches}/{unit_expected}; false extractions: {false_extractions}.")
    if exact_total != expected_total or false_extractions:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
