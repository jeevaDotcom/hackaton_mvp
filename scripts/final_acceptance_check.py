"""Read-only final Q-CARE component manifest and dependency check."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def readable(relative: str) -> bool:
    path = ROOT / relative
    return path.is_file() and path.stat().st_size > 0 and bool(path.read_bytes()[:32])


def source_contains(relative: str, *needles: str) -> bool:
    if not readable(relative):
        return False
    source = (ROOT / relative).read_text(errors="replace")
    return all(needle in source for needle in needles)


def check_group(name: str, checks: list[tuple[str, bool]]) -> list[bool]:
    print(name)
    outcomes: list[bool] = []
    for label, passed in checks:
        outcomes.append(passed)
        print(f"  {'PASS' if passed else 'FAIL'}  {label}")
    return outcomes


def main() -> int:
    outcomes: list[bool] = []
    outcomes += check_group("APPLICATION", [
        ("app.py", readable("app.py")),
        ("workstation UI", readable("src/workstation_page.py")),
        ("shared theme", readable("src/ui_theme.py")),
    ])
    outcomes += check_group("MODELS", [
        ("frozen RBF-SVM artifact", readable("artifacts/models/final_classical_8.joblib")),
        ("frozen QSVC artifact", readable("artifacts/models/final_qsvc_8.joblib")),
        ("frozen VQC weights", readable("artifacts/live_vqc/model/weights.npy")),
        ("frozen VQC metadata", readable("artifacts/live_vqc/metadata.json")),
        ("frozen preprocessors", readable("artifacts/live_vqc/preprocessor/preprocessor.joblib") and readable("artifacts/models/final_classical_8.joblib")),
    ])
    outcomes += check_group("EVIDENCE", [
        ("ResultsRepository", readable("src/results_repository.py")),
        ("Phase 1 artifacts", readable("artifacts/development_cv_results.csv") and readable("artifacts/development_decision.json")),
        ("Phase 2 quantum artifacts", readable("artifacts/quantum_cv_summary.csv") and readable("artifacts/qsvc_z_reps1_8_circuit.txt")),
        ("Phase 3 robustness artifacts", readable("artifacts/quantum_noise_results.csv") and readable("artifacts/quantum_training_size_results.csv")),
        ("Phase 3C transportability evidence", readable("artifacts/phase3/external_ckd_metrics.csv") and readable("reports/root_cause/phase3c_summary.json")),
    ])
    outcomes += check_group("OCR", [
        ("report_scanner module", readable("src/report_scanner.py")),
        ("digital demo report", readable("artifacts/ocr_demo/sample_digital_report.pdf")),
        ("image demo report", readable("artifacts/ocr_demo/sample_photo_report.png")),
        ("OCR validation data", readable("artifacts/ocr_demo/validation_results.json") and readable("artifacts/ocr_demo/validation_samples.json")),
    ])
    outcomes += check_group("CSV BATCH", [
        ("batch module", readable("src/csv_batch.py")),
        ("sample batch CSV", readable("artifacts/batch_demo/qcare_batch_demo.csv")),
        ("mapping and validation logic", source_contains("src/csv_batch.py", "suggest_column_mapping", "validate_mapping", "normalize_row")),
        ("batch tests", readable("tests/test_csv_batch.py")),
    ])
    outcomes += check_group("STAGE", [
        ("stage decision documentation", readable("research/stage_module_decision.md")),
        ("stage view anchor", source_contains("src/workstation_page.py", "CKD STAGE RESEARCH VIEW", "NOT VALIDATED IN CURRENT Q-CARE MODEL")),
    ])
    outcomes += check_group("REPORT", [
        ("research report module", readable("src/research_report.py")),
        ("single demo PDF", readable("artifacts/report_demo/qcare_single_demo_report.pdf")),
        ("scan demo PDF", readable("artifacts/report_demo/qcare_scan_demo_report.pdf")),
        ("batch demo PDF", readable("artifacts/report_demo/qcare_batch_demo_report.pdf")),
    ])
    outcomes += check_group("TESTS", [
        ("single/workstation tests", readable("tests/test_single_page_workstation.py")),
        ("OCR tests", readable("tests/test_report_scanner.py")),
        ("stage tests", readable("tests/test_stage_scope.py")),
        ("PDF tests", readable("tests/test_research_report.py")),
    ])

    streamlit_available = importlib.util.find_spec("streamlit") is not None
    outcomes += check_group("EXTERNAL EXECUTABLES / DEPS", [
        (f"Python {sys.version.split()[0]}", sys.version_info >= (3, 11)),
        ("Streamlit import", streamlit_available),
        ("Tesseract executable", shutil.which("tesseract") is not None),
    ])
    passed = sum(outcomes)
    failed = len(outcomes) - passed
    print(f"\nFINAL ACCEPTANCE MANIFEST: {'PASS' if failed == 0 else 'FAIL'} ({passed} passed, {failed} failed)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
