"""Deterministic, human-confirmed report extraction for Q-CARE.

The scanner extracts only the eight frozen model inputs. It never calls a
predictive model and never treats OCR output as confirmed data.
"""

from __future__ import annotations

import csv
import io
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError


FEATURE_ORDER = ("hemo", "pcv", "sc", "al", "sg", "dm", "htn", "appet")
FEATURE_NAMES = {
    "hemo": "Haemoglobin",
    "pcv": "Packed cell volume",
    "sc": "Serum creatinine",
    "al": "Albumin (dataset ordinal grade)",
    "sg": "Specific gravity",
    "dm": "Diabetes mellitus",
    "htn": "Hypertension",
    "appet": "Appetite",
}
NORMALIZED_UNITS = {
    "hemo": "g/dL",
    "pcv": "%",
    "sc": "mg/dL",
    "al": "ordinal grade (0-5)",
    "sg": "unitless",
    "dm": "dataset category",
    "htn": "dataset category",
    "appet": "dataset category",
}
SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 8


class ReportValidationError(ValueError):
    """A friendly validation error for unsupported or malformed uploads."""


class ProfileConfirmationError(ValueError):
    """Raised when a researcher-confirmed profile is incomplete or invalid."""


@dataclass(frozen=True)
class SourceLine:
    page: int
    text: str
    engine_confidence: float | None = None


@dataclass(frozen=True)
class FieldCandidate:
    feature: str
    canonical_name: str
    detected_label: str
    raw_value: str
    normalized_value: float | str | None
    original_unit: str
    normalized_unit: str
    page: int
    source: str
    confidence: str
    method: str
    status: str
    reason: str = ""


@dataclass
class ExtractionResult:
    filename: str
    input_type: str
    method: str
    page_count: int
    candidates: dict[str, list[FieldCandidate]] = field(default_factory=dict)
    text_by_page: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def detected_count(self) -> int:
        return sum(1 for feature in FEATURE_ORDER if self.safe_candidate(feature) is not None)

    def safe_candidate(self, feature: str) -> FieldCandidate | None:
        options = self.candidates.get(feature, [])
        ready = [item for item in options if item.status == "READY" and item.normalized_value is not None]
        values = {str(item.normalized_value) for item in ready}
        return ready[0] if len(ready) == 1 and len(values) == 1 and len(options) == 1 else None

    def field_status(self, feature: str) -> str:
        options = self.candidates.get(feature, [])
        if not options:
            return "MANUAL" if feature in {"dm", "htn", "appet"} else "MISSING"
        normalized = {str(item.normalized_value) for item in options if item.normalized_value is not None}
        raw = {item.raw_value for item in options}
        if len(normalized) > 1 or (not normalized and len(raw) > 1):
            return "MULTIPLE VALUES DETECTED"
        if self.safe_candidate(feature):
            return "READY"
        return "REVIEW REQUIRED"


ALIASES: dict[str, tuple[str, ...]] = {
    "hemo": ("haemoglobin", "hemoglobin", "hgb", "hb"),
    "pcv": ("packed cell volume", "haematocrit", "hematocrit", "pcv", "hct"),
    "sc": ("serum creatinine", "s. creatinine", "s creatinine", "creatinine", "creat.", "crea"),
    "al": ("urinary albumin", "urine albumin", "serum albumin", "albumin"),
    "sg": ("urine specific gravity", "specific gravity", "sp. gravity", "sp gravity", "sp gr", "sg"),
    "dm": ("diabetes mellitus", "known diabetic", "diabetes", "dm"),
    "htn": ("known hypertensive", "hypertension", "htn"),
    "appet": ("poor appetite", "normal appetite", "good appetite", "appetite"),
}

BROAD_BOUNDS = {
    "hemo": (1.0, 30.0),
    "pcv": (5.0, 75.0),
    "sc": (0.1, 100.0),
    "al": (0.0, 5.0),
    "sg": (1.0, 1.05),
}


def validate_upload(filename: str, data: bytes) -> str:
    """Validate size, suffix, and basic file signature without executing content."""

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ReportValidationError("Unsupported report format. Use PDF, PNG, JPG/JPEG, or WEBP.")
    if not data:
        raise ReportValidationError("The uploaded report is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ReportValidationError("The report exceeds the 10 MB demo limit.")
    signatures = {
        ".pdf": data.startswith(b"%PDF"),
        ".png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": data.startswith(b"\xff\xd8"),
        ".jpeg": data.startswith(b"\xff\xd8"),
        ".webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
    }
    if not signatures[suffix]:
        raise ReportValidationError("The file content does not match its extension or is malformed.")
    return suffix


def _label_pattern(alias: str) -> str:
    pieces = [re.escape(part) for part in re.split(r"\s+", alias.strip())]
    return r"\s+".join(pieces)


def _find_alias(line: str, feature: str) -> tuple[str, re.Match[str]] | None:
    for alias in sorted(ALIASES[feature], key=len, reverse=True):
        pattern = rf"(?<![A-Za-z0-9]){_label_pattern(alias)}(?![A-Za-z0-9])"
        match = re.search(pattern, line, flags=re.IGNORECASE)
        if match:
            return match.group(0), match
    return None


def _confidence(valid: bool, unit_present: bool, engine_confidence: float | None) -> str:
    if not valid:
        return "LOW"
    if engine_confidence is not None and engine_confidence < 60:
        return "LOW"
    if not unit_present or (engine_confidence is not None and engine_confidence < 80):
        return "MEDIUM"
    return "HIGH"


def _numeric_tail(text: str) -> tuple[str, str] | None:
    match = re.search(
        r"(?:[:=]|\.{2,}|\s|-)+\s*([<>]?\s*\d+(?:\.\d+)?)\s*(g\s*/\s*d[l1]|gm\s*/\s*d[l1]|g\s*/\s*l|g%|%|mg\s*/\s*d[l1]|(?:u|µ|μ)mol\s*/\s*l|\+)?",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return re.sub(r"\s+", "", match.group(1)), re.sub(r"\s+", "", match.group(2) or "")


def _normalise_numeric(feature: str, raw_value: str, raw_unit: str) -> tuple[float | None, str, str]:
    try:
        value = float(raw_value.replace("<", "").replace(">", ""))
    except ValueError:
        return None, "REVIEW REQUIRED", "Value could not be parsed deterministically."
    unit = raw_unit.lower().replace("1", "l").replace("μ", "µ")
    reason = ""
    if feature == "hemo":
        if unit in {"g/dl", "gm/dl", "g%"}:
            pass
        elif unit == "g/l":
            value /= 10.0
            reason = "Converted deterministically from g/L to g/dL."
        else:
            return value, "REVIEW REQUIRED", "Haemoglobin unit is missing or unsupported."
    elif feature == "pcv":
        if unit != "%":
            return value, "REVIEW REQUIRED", "Packed cell volume requires an explicit percent unit."
    elif feature == "sc":
        if unit == "mg/dl":
            pass
        elif unit in {"umol/l", "µmol/l"}:
            value /= 88.4
            reason = "Converted deterministically from µmol/L to mg/dL using 88.4 µmol/L per mg/dL."
        else:
            return value, "REVIEW REQUIRED", "Creatinine unit is missing or unsupported."
    elif feature == "sg":
        if unit:
            return value, "REVIEW REQUIRED", "Specific gravity is expected as a unitless value."
    low, high = BROAD_BOUNDS[feature]
    if not low <= value <= high:
        return value, "REVIEW REQUIRED", "Value falls outside broad data-validation bounds."
    return value, "READY", reason


def _categorical_value(feature: str, line: str, alias: str) -> str | None:
    lowered = line.lower()
    if feature in {"dm", "htn"}:
        if alias.lower() in {"known diabetic", "known hypertensive"} and not re.search(r"\b(no|not|absent|negative)\b", lowered):
            return "yes"
        if re.search(r"\b(yes|present|positive)\b", lowered):
            return "yes"
        if re.search(r"\b(no|absent|negative)\b", lowered):
            return "no"
    if feature == "appet":
        if "poor appetite" in lowered or re.search(r"\bappetite\b.*\bpoor\b", lowered):
            return "poor"
        if any(term in lowered for term in ("normal appetite", "good appetite")) or re.search(r"\bappetite\b.*\b(normal|good)\b", lowered):
            return "good"
    return None


def _parse_line(source: SourceLine, method: str) -> list[FieldCandidate]:
    line = " ".join(source.text.strip().split())
    if not line:
        return []
    found: list[FieldCandidate] = []
    for feature in FEATURE_ORDER:
        alias_match = _find_alias(line, feature)
        if not alias_match:
            continue
        label, match = alias_match
        tail = line[match.end():]
        if feature in {"dm", "htn", "appet"}:
            value = _categorical_value(feature, line, label)
            status = "READY" if value else "REVIEW REQUIRED"
            found.append(FieldCandidate(
                feature, FEATURE_NAMES[feature], label, value or "—", value, "", NORMALIZED_UNITS[feature],
                source.page, line, _confidence(value is not None, True, source.engine_confidence), method, status,
                "Categorical value was not explicit." if value is None else "",
            ))
            continue
        numeric = _numeric_tail(tail)
        if not numeric:
            continue
        raw_value, raw_unit = numeric
        if feature == "al":
            lower_line = line.lower()
            explicit_urine = "urine albumin" in lower_line or "urinary albumin" in lower_line
            explicit_serum = "serum albumin" in lower_line or raw_unit.lower().replace(" ", "") in {"g/dl", "gm/dl", "g/l"}
            numeric_value = float(raw_value.replace("<", "").replace(">", ""))
            if explicit_urine and 0 <= numeric_value <= 5 and raw_unit in {"", "+"}:
                normalized: float | None = numeric_value
                status = "READY"
                reason = "Explicit urinary albumin ordinal representation."
            else:
                normalized = None
                status = "REVIEW REQUIRED"
                reason = (
                    "Current model expects the dataset-compatible albumin representation; serum albumin cannot automatically be assumed equivalent."
                    if explicit_serum else
                    "Albumin context is insufficient to establish the dataset-compatible urinary ordinal representation."
                )
            found.append(FieldCandidate(
                feature, FEATURE_NAMES[feature], label, raw_value, normalized, raw_unit, NORMALIZED_UNITS[feature],
                source.page, line, _confidence(normalized is not None, explicit_urine, source.engine_confidence), method, status, reason,
            ))
            continue
        value, status, reason = _normalise_numeric(feature, raw_value, raw_unit)
        unit_expected = feature == "sg" or bool(raw_unit)
        found.append(FieldCandidate(
            feature, FEATURE_NAMES[feature], label, raw_value, value, raw_unit, NORMALIZED_UNITS[feature],
            source.page, line, _confidence(status == "READY", unit_expected, source.engine_confidence), method, status, reason,
        ))
    return found


def parse_source_lines(lines: Iterable[SourceLine], method: str = "Deterministic text parsing") -> dict[str, list[FieldCandidate]]:
    """Parse source lines with label dictionaries and field-specific rules."""

    grouped: dict[str, list[FieldCandidate]] = {feature: [] for feature in FEATURE_ORDER}
    for line in lines:
        for candidate in _parse_line(line, method):
            key = (candidate.normalized_value, candidate.raw_value, candidate.page, candidate.source)
            existing = {(item.normalized_value, item.raw_value, item.page, item.source) for item in grouped[candidate.feature]}
            if key not in existing:
                grouped[candidate.feature].append(candidate)
    return grouped


def _page_source_lines(pages: Iterable[str]) -> list[SourceLine]:
    """Preserve lines while reconstructing common PDF label/value splits."""

    sources: list[SourceLine] = []
    for page_number, text in enumerate(pages, start=1):
        lines = [" ".join(line.split()) for line in str(text).splitlines() if line.strip()]
        for index, line in enumerate(lines):
            sources.append(SourceLine(page_number, line))
            contains_numeric_alias = any(_find_alias(line, feature) for feature in ("hemo", "pcv", "sc", "al", "sg"))
            next_is_value = index + 1 < len(lines) and bool(re.search(r"\d", lines[index + 1]))
            if contains_numeric_alias and not re.search(r"\d", line) and next_is_value:
                sources.append(SourceLine(page_number, f"{line} {lines[index + 1]}"))
    return sources


def parse_text_pages(pages: Iterable[str], method: str = "Deterministic text parsing") -> ExtractionResult:
    page_list = tuple(str(page) for page in pages)
    lines = _page_source_lines(page_list)
    return ExtractionResult("text-input", "text", method, len(page_list), parse_source_lines(lines, method), page_list)


def _embedded_pdf_pages(data: bytes) -> tuple[tuple[str, ...], str]:
    try:
        import pymupdf  # type: ignore

        document = pymupdf.open(stream=data, filetype="pdf")
        if document.page_count > MAX_PDF_PAGES:
            raise ReportValidationError(f"PDF has {document.page_count} pages; the demo limit is {MAX_PDF_PAGES}.")
        pages = tuple(document.load_page(index).get_text("text") for index in range(document.page_count))
        document.close()
        return pages, "Embedded PDF text · PyMuPDF"
    except ImportError:
        executable = shutil.which("pdftotext")
        if not executable:
            raise ReportValidationError("PDF text extraction is unavailable. Install PyMuPDF or Poppler.")
        with tempfile.TemporaryDirectory(prefix="qcare-pdf-") as directory:
            source = Path(directory) / "report.pdf"
            source.write_bytes(data)
            completed = subprocess.run(
                [executable, "-layout", str(source), "-"], capture_output=True, text=True, timeout=30, check=False
            )
        if completed.returncode != 0:
            raise ReportValidationError("The PDF could not be read. It may be malformed or password protected.")
        pages = tuple(completed.stdout.split("\f"))
        if len(pages) > MAX_PDF_PAGES:
            raise ReportValidationError(f"PDF has more than the {MAX_PDF_PAGES}-page demo limit.")
        return pages, "Embedded PDF text · Poppler fallback"
    except ReportValidationError:
        raise
    except Exception as error:
        raise ReportValidationError(f"The PDF could not be read safely: {error}") from error


def _otsu_threshold(array: np.ndarray) -> int:
    histogram = np.bincount(array.ravel(), minlength=256).astype(float)
    total = array.size
    cumulative = np.cumsum(histogram)
    cumulative_mean = np.cumsum(histogram * np.arange(256))
    global_mean = cumulative_mean[-1]
    denominator = cumulative * (total - cumulative)
    denominator[denominator == 0] = 1
    variance = (global_mean * cumulative - cumulative_mean) ** 2 / denominator
    return int(np.argmax(variance))


def _projection_score(image: Image.Image) -> float:
    array = np.asarray(image, dtype=np.uint8)
    threshold = _otsu_threshold(array)
    ink = array < threshold
    return float(np.var(ink.sum(axis=1)))


def _deskew(image: Image.Image) -> Image.Image:
    preview = image.copy()
    preview.thumbnail((1400, 1400))
    base_score = _projection_score(preview)
    best_angle, best_score = 0.0, base_score
    for angle in (-2.0, -1.0, 1.0, 2.0):
        rotated = preview.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)
        score = _projection_score(rotated)
        if score > best_score:
            best_angle, best_score = angle, score
    if best_angle and best_score > base_score * 1.04:
        return image.rotate(best_angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)
    return image


def preprocess_image(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Return a restrained grayscale variant and an adaptive-threshold variant."""

    oriented = ImageOps.exif_transpose(image).convert("L")
    if min(oriented.size) < 1200:
        scale = min(2.5, 1200 / max(min(oriented.size), 1))
        oriented = oriented.resize((int(oriented.width * scale), int(oriented.height * scale)), Image.Resampling.LANCZOS)
    enhanced = ImageOps.autocontrast(oriented, cutoff=1)
    enhanced = _deskew(enhanced)
    denoised = enhanced.filter(ImageFilter.MedianFilter(size=3))
    local_mean = np.asarray(denoised.filter(ImageFilter.BoxBlur(radius=18)), dtype=np.int16)
    pixels = np.asarray(denoised, dtype=np.int16)
    thresholded = Image.fromarray(np.where(pixels < local_mean - 7, 0, 255).astype(np.uint8), mode="L")
    return enhanced, thresholded


def _ocr_lines(image: Image.Image, page: int) -> tuple[list[SourceLine], str]:
    executable = shutil.which("tesseract")
    if not executable:
        raise RuntimeError("Local Tesseract OCR is not installed.")
    with tempfile.TemporaryDirectory(prefix="qcare-ocr-") as directory:
        source = Path(directory) / "page.png"
        image.save(source, format="PNG")
        completed = subprocess.run(
            [executable, str(source), "stdout", "--psm", "6", "tsv"],
            capture_output=True, text=True, timeout=45, check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Tesseract OCR failed.")
    groups: dict[tuple[str, str, str], list[tuple[str, float]]] = {}
    reader = csv.DictReader(io.StringIO(completed.stdout), delimiter="\t")
    for row in reader:
        word = (row.get("text") or "").strip()
        if not word:
            continue
        try:
            confidence = float(row.get("conf") or -1)
        except ValueError:
            confidence = -1
        key = (row.get("block_num", "0"), row.get("par_num", "0"), row.get("line_num", "0"))
        groups.setdefault(key, []).append((word, confidence))
    lines = []
    for words in groups.values():
        valid_conf = [confidence for _, confidence in words if confidence >= 0]
        lines.append(SourceLine(page, " ".join(word for word, _ in words), float(np.mean(valid_conf)) if valid_conf else None))
    return lines, "Local Tesseract OCR"


def _score_candidates(candidates: Mapping[str, list[FieldCandidate]]) -> tuple[int, int, int]:
    ready = sum(1 for values in candidates.values() if len(values) == 1 and values[0].status == "READY")
    total = sum(bool(values) for values in candidates.values())
    high = sum(item.confidence == "HIGH" for values in candidates.values() for item in values)
    return ready, total, high


def _ocr_image(image: Image.Image, page: int) -> tuple[list[SourceLine], dict[str, list[FieldCandidate]]]:
    enhanced, thresholded = preprocess_image(image)
    attempts: list[tuple[list[SourceLine], dict[str, list[FieldCandidate]]]] = []
    for variant in (enhanced, thresholded):
        lines, method = _ocr_lines(variant, page)
        attempts.append((lines, parse_source_lines(lines, method)))
    return max(attempts, key=lambda attempt: _score_candidates(attempt[1]))


def _pdf_page_images(data: bytes) -> list[Image.Image]:
    try:
        import pymupdf  # type: ignore

        document = pymupdf.open(stream=data, filetype="pdf")
        if document.page_count > MAX_PDF_PAGES:
            raise ReportValidationError(f"PDF has {document.page_count} pages; the demo limit is {MAX_PDF_PAGES}.")
        images = []
        for index in range(document.page_count):
            pixmap = document.load_page(index).get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
            images.append(Image.open(io.BytesIO(pixmap.tobytes("png"))).copy())
        document.close()
        return images
    except ImportError:
        executable = shutil.which("pdftoppm")
        if not executable:
            raise RuntimeError("Scanned-PDF rendering is unavailable.")
        with tempfile.TemporaryDirectory(prefix="qcare-render-") as directory:
            source = Path(directory) / "report.pdf"
            source.write_bytes(data)
            prefix = Path(directory) / "page"
            completed = subprocess.run(
                [executable, "-png", "-r", "180", "-f", "1", "-l", str(MAX_PDF_PAGES), str(source), str(prefix)],
                capture_output=True, text=True, timeout=60, check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or "Scanned-PDF rendering failed.")
            return [Image.open(path).copy() for path in sorted(Path(directory).glob("page-*.png"))]


def extract_report(data: bytes, filename: str) -> ExtractionResult:
    """Extract report fields without ever running a predictive model."""

    suffix = validate_upload(filename, data)
    if suffix == ".pdf":
        pages, method = _embedded_pdf_pages(data)
        usable_characters = sum(len(re.sub(r"\s+", "", page)) for page in pages)
        if usable_characters >= 40:
            lines = _page_source_lines(pages)
            return ExtractionResult(filename, "PDF", method, len(pages), parse_source_lines(lines, method), pages)
        try:
            images = _pdf_page_images(data)
            all_lines: list[SourceLine] = []
            for page_number, image in enumerate(images, start=1):
                lines, _ = _ocr_image(image, page_number)
                all_lines.extend(lines)
            text_pages = tuple("\n".join(line.text for line in all_lines if line.page == page) for page in range(1, len(images) + 1))
            return ExtractionResult(filename, "Scanned PDF", "Local Tesseract OCR", len(images), parse_source_lines(all_lines, "Local Tesseract OCR"), text_pages)
        except Exception as error:
            return ExtractionResult(
                filename, "Scanned PDF", "Manual fallback", len(pages), {feature: [] for feature in FEATURE_ORDER}, pages,
                ("Automatic extraction could not confidently read this report. Please review the extracted text or enter the values manually.", str(error)),
            )
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise ReportValidationError("The image could not be decoded. It may be malformed.") from error
    try:
        lines, candidates = _ocr_image(image, 1)
        text = "\n".join(line.text for line in lines)
        return ExtractionResult(filename, "Image", "Local Tesseract OCR", 1, candidates, (text,))
    except Exception as error:
        return ExtractionResult(
            filename, "Image", "Manual fallback", 1, {feature: [] for feature in FEATURE_ORDER}, (),
            ("Automatic extraction could not confidently read this report. Please review the extracted text or enter the values manually.", str(error)),
        )


def review_defaults(result: ExtractionResult) -> dict[str, Any | None]:
    return {
        feature: result.safe_candidate(feature).normalized_value if result.safe_candidate(feature) else None
        for feature in FEATURE_ORDER
    }


def confirm_profile(values: Mapping[str, Any]) -> dict[str, Any]:
    """Validate explicit researcher choices and return the frozen eight-feature profile."""

    missing = [FEATURE_NAMES[feature] for feature in FEATURE_ORDER if values.get(feature) in {None, "", "Select…"}]
    if missing:
        raise ProfileConfirmationError("Complete all eight fields before confirmation: " + ", ".join(missing))
    profile: dict[str, Any] = {}
    for feature in FEATURE_ORDER:
        value = values[feature]
        if feature in {"dm", "htn"}:
            normalized = str(value).strip().lower()
            if normalized not in {"yes", "no"}:
                raise ProfileConfirmationError(f"{FEATURE_NAMES[feature]} must be yes or no.")
            profile[feature] = normalized
        elif feature == "appet":
            normalized = str(value).strip().lower()
            if normalized not in {"good", "poor"}:
                raise ProfileConfirmationError("Appetite must use the dataset-compatible good or poor category.")
            profile[feature] = normalized
        else:
            try:
                numeric = float(value)
            except (TypeError, ValueError) as error:
                raise ProfileConfirmationError(f"{FEATURE_NAMES[feature]} must be numeric.") from error
            if not np.isfinite(numeric):
                raise ProfileConfirmationError(f"{FEATURE_NAMES[feature]} must be finite.")
            low, high = BROAD_BOUNDS[feature]
            if not low <= numeric <= high:
                raise ProfileConfirmationError(f"{FEATURE_NAMES[feature]} falls outside broad data-validation bounds ({low:g}-{high:g}).")
            profile[feature] = numeric
    return profile


def profile_health(profile: Mapping[str, Any], observed_ranges: Mapping[str, Any]) -> dict[str, str]:
    """Describe profile readiness against frozen model structure and development ranges."""

    complete = all(feature in profile and profile[feature] not in {None, ""} for feature in FEATURE_ORDER)
    outside = []
    if complete:
        for feature in FEATURE_ORDER:
            observed = observed_ranges[feature]
            value = profile[feature]
            if feature in {"dm", "htn", "appet"}:
                if str(value).lower() not in {str(item).lower() for item in observed}:
                    outside.append(feature)
            else:
                low, high = observed
                if not float(low) <= float(value) <= float(high):
                    outside.append(feature)
    return {
        "FEATURE COMPLETENESS": f"{sum(feature in profile and profile[feature] not in {None, ''} for feature in FEATURE_ORDER)} / 8",
        "UNIT REVIEW": "PASSED" if complete else "REVIEW",
        "DEVELOPMENT-RANGE CHECK": "WARNING" if outside else "PASSED" if complete else "REVIEW",
        "MODEL INPUT STATUS": "READY" if complete else "REVIEW REQUIRED",
        "outside_features": ", ".join(outside),
    }


def review_table(result: ExtractionResult, observed_ranges: Mapping[str, Any] | None = None) -> list[dict[str, str]]:
    rows = []
    for feature in FEATURE_ORDER:
        options = result.candidates.get(feature, [])
        candidate = options[0] if len(options) == 1 else None
        development_status = "REVIEW REQUIRED"
        if candidate and candidate.normalized_value is not None and observed_ranges and feature in observed_ranges:
            observed = observed_ranges[feature]
            if feature in {"dm", "htn", "appet"}:
                within = str(candidate.normalized_value).lower() in {str(value).lower() for value in observed}
            else:
                low, high = observed
                within = float(low) <= float(candidate.normalized_value) <= float(high)
            development_status = "WITHIN DEVELOPMENT RANGE" if within else "OUTSIDE DEVELOPMENT RANGE"
        normalized = "—"
        if candidate and candidate.normalized_value is not None:
            value = candidate.normalized_value
            displayed = f"{value:g}" if isinstance(value, float) else str(value)
            normalized = f"{displayed} {candidate.normalized_unit}".strip()
        rows.append({
            "Q-CARE Feature": FEATURE_NAMES[feature],
            "Extracted": candidate.raw_value if candidate else "—" if not options else f"{len(options)} candidates",
            "Unit": (candidate.original_unit or "—") if candidate else "—",
            "Normalized": normalized,
            "Confidence": candidate.confidence.title() if candidate else "—",
            "Source": f"Page {candidate.page}" if candidate else "—",
            "Status": result.field_status(feature).title(),
            "Development range": development_status.title(),
        })
    return rows
