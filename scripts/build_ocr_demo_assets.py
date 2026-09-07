"""Build fictional, offline Q-CARE OCR demo documents and labeled samples."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/ocr_demo"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/Arial.ttf")


def digital_pdf(path: Path) -> None:
    if FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont("QCareSans", str(FONT_PATH)))
        font = "QCareSans"
    else:
        font = "Helvetica"
    document = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    width, height = A4
    document.setFillColor(HexColor("#17191F"))
    document.setFont(font, 23)
    document.drawString(54, height - 66, "Q-CARE DEMO LABORATORY")
    document.setFillColor(HexColor("#315AD8"))
    document.setFont(font, 11)
    document.drawString(54, height - 91, "SAMPLE RESEARCH REPORT - NOT A REAL PATIENT")
    document.setStrokeColor(HexColor("#D8D9DE"))
    document.line(54, height - 110, width - 54, height - 110)
    document.setFillColor(HexColor("#17191F"))
    document.setFont(font, 13)
    rows = [
        ("Haemoglobin", "10.4 g/dL"),
        ("Packed Cell Volume", "31 %"),
        ("Serum Creatinine", "2.4 mg/dL"),
        ("Urine Specific Gravity", "1.010"),
        ("Serum Albumin", "3.7 g/dL"),
    ]
    y = height - 155
    for label, value in rows:
        document.drawString(62, y, label)
        document.drawRightString(width - 62, y, value)
        document.setStrokeColor(HexColor("#E5E5E8"))
        document.line(62, y - 10, width - 62, y - 10)
        y -= 47
    document.setFillColor(HexColor("#5D6270"))
    document.setFont(font, 10)
    document.drawString(54, 64, "Fictional values for deterministic extraction and researcher-verification demonstrations only.")
    document.save()


def photo_report(path: Path) -> None:
    width, height = 1500, 2050
    image = Image.new("RGB", (width, height), "#F7F4EC")
    draw = ImageDraw.Draw(image)
    font_file = str(FONT_PATH) if FONT_PATH.exists() else None
    title = ImageFont.truetype(font_file, 58) if font_file else ImageFont.load_default()
    subtitle = ImageFont.truetype(font_file, 31) if font_file else ImageFont.load_default()
    body = ImageFont.truetype(font_file, 39) if font_file else ImageFont.load_default()
    small = ImageFont.truetype(font_file, 25) if font_file else ImageFont.load_default()
    draw.text((110, 105), "Q-CARE DEMO REPORT", font=title, fill="#16191F")
    draw.text((110, 185), "SAMPLE RESEARCH REPORT - NOT A REAL PATIENT", font=subtitle, fill="#315AD8")
    draw.line((110, 255, width - 110, 255), fill="#BFC2CA", width=3)
    rows = [
        "Hb: 12.6 g/dL",
        "HCT: 38 %",
        "Creat.: 1.4 mg/dL",
        "Urine Albumin: 1 +",
        "Sp Gr: 1.020",
        "Diabetes Mellitus: No",
        "Hypertension: Yes",
        "Appetite: Good",
    ]
    y = 335
    for row in rows:
        draw.text((145, y), row, font=body, fill="#25272D")
        draw.line((135, y + 62, width - 135, y + 62), fill="#D6D4CE", width=2)
        y += 155
    draw.text((110, height - 145), "Fictional values for offline OCR validation only.", font=small, fill="#626773")
    rng = np.random.default_rng(20260825)
    array = np.asarray(image, dtype=np.int16)
    noise = rng.normal(0, 2.2, array.shape[:2])[:, :, None]
    array = np.clip(array + noise, 0, 255).astype(np.uint8)
    noisy = Image.fromarray(array, "RGB")
    skewed = noisy.rotate(1.1, resample=Image.Resampling.BICUBIC, expand=True, fillcolor="#EEEAE0")
    skewed.save(path, format="PNG", optimize=True)


def labeled_samples(path: Path) -> None:
    samples = [
        {"id": "core_names", "pages": ["Haemoglobin: 10.4 g/dL\nPCV: 31 %\nSerum Creatinine: 2.4 mg/dL\nSpecific Gravity: 1.010"], "expected": {"hemo": 10.4, "pcv": 31.0, "sc": 2.4, "sg": 1.01}},
        {"id": "us_aliases", "pages": ["Hemoglobin = 13.2 g/dL\nHematocrit = 40 %\nCREA = 1.1 mg/dL\nSp Gr = 1.020"], "expected": {"hemo": 13.2, "pcv": 40.0, "sc": 1.1, "sg": 1.02}},
        {"id": "safe_units", "pages": ["HGB 126 g/L\nHCT 38 %\nCreatinine 176.8 umol/L"], "expected": {"hemo": 12.6, "pcv": 38.0, "sc": 2.0}},
        {"id": "history", "pages": ["Known diabetic: Yes\nHTN: No\nAppetite: Poor"], "expected": {"dm": "yes", "htn": "no", "appet": "poor"}},
        {"id": "urine_albumin", "pages": ["Urine Albumin: 2 +\nUrine Specific Gravity: 1.015"], "expected": {"al": 2.0, "sg": 1.015}},
        {"id": "multipage", "pages": ["Hb: 11.8 g/dL\nPCV: 35 %", "S. Creatinine: 1.8 mg/dL\nDM: No\nKnown hypertensive"], "expected": {"hemo": 11.8, "pcv": 35.0, "sc": 1.8, "dm": "no", "htn": "yes"}},
    ]
    path.write_text(json.dumps(samples, indent=2) + "\n")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    digital_pdf(OUTPUT / "sample_digital_report.pdf")
    photo_report(OUTPUT / "sample_photo_report.png")
    labeled_samples(OUTPUT / "validation_samples.json")
    print(f"Built OCR demo assets in {OUTPUT}")


if __name__ == "__main__":
    main()
