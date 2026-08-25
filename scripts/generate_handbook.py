from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "submission/handbook/qcare_layman_handbook.md"
OUTPUT = ROOT / "output/pdf/qcare_layman_handbook.pdf"

INK = colors.HexColor("#191B20")
SECONDARY = colors.HexColor("#5C626C")
ACCENT = colors.HexColor("#315AD8")
PAPER = colors.HexColor("#F7F5EF")
SURFACE = colors.HexColor("#EEECE6")
BORDER = colors.HexColor("#D9DAD5")


def inline_markup(text: str) -> str:
    value = html.escape(text.strip())
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<a href="\2" color="#315AD8">\1</a>', value)
    return value


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=34,
            leading=36,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Heading2"],
            fontName="Helvetica",
            fontSize=18,
            leading=24,
            textColor=ACCENT,
            spaceAfter=18,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=12,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=15.2,
            textColor=INK,
            spaceAfter=8,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            leftIndent=12,
            rightIndent=12,
            borderColor=ACCENT,
            borderWidth=0,
            borderPadding=10,
            backColor=SURFACE,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=12,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=12,
            textColor=SECONDARY,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "table": ParagraphStyle(
            "Table",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.5,
            textColor=INK,
        ),
    }


def add_page(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setStrokeColor(BORDER)
    canvas.line(22 * mm, 16 * mm, width - 22 * mm, 16 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SECONDARY)
    canvas.drawString(22 * mm, 10.5 * mm, "Q-CARE - Phase 3D evidence handbook")
    canvas.drawRightString(width - 22 * mm, 10.5 * mm, str(document.page))
    canvas.restoreState()


def markdown_table(lines: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    rows: list[list[Paragraph]] = []
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if index == 1 and all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append([Paragraph(inline_markup(cell), styles["table"]) for cell in cells])
    column_count = len(rows[0])
    available = A4[0] - 44 * mm
    widths = [available / column_count] * column_count
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SURFACE),
        ("TEXTCOLOR", (0, 0), (-1, 0), INK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def parse_markdown(source: str, styles: dict[str, ParagraphStyle]) -> list[object]:
    story: list[object] = []
    lines = source.splitlines()
    index = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(paragraph)), styles["body"]))
            paragraph.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        if not line.strip():
            flush_paragraph()
            index += 1
            continue
        if line.strip() == "<!-- PAGEBREAK -->":
            flush_paragraph()
            story.append(PageBreak())
            index += 1
            continue
        image_match = re.match(r"!\[([^]]+)\]\(([^)]+)\)", line.strip())
        if image_match:
            flush_paragraph()
            image_path = (SOURCE.parent / image_match.group(2)).resolve()
            image = Image(str(image_path))
            max_width = A4[0] - 44 * mm
            max_height = 105 * mm
            scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
            image.drawWidth = image.imageWidth * scale
            image.drawHeight = image.imageHeight * scale
            image.hAlign = "CENTER"
            story.extend([Spacer(1, 5), image, Paragraph(inline_markup(image_match.group(1)), styles["caption"])])
            index += 1
            continue
        if line.startswith("|-") or line.startswith("|:"):
            index += 1
            continue
        if line.startswith("|"):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.extend([markdown_table(table_lines, styles), Spacer(1, 10)])
            continue
        if line.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), styles["title"]))
            index += 1
            continue
        if line.startswith("## "):
            flush_paragraph()
            style = styles["subtitle"] if not any(isinstance(item, PageBreak) for item in story) and len(story) < 3 else styles["h2"]
            story.append(Paragraph(inline_markup(line[3:]), style))
            index += 1
            continue
        if line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[4:]), styles["h3"]))
            index += 1
            continue
        if line.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:]), styles["quote"]))
            index += 1
            continue
        if re.match(r"^[-*] ", line):
            flush_paragraph()
            bullets: list[ListItem] = []
            while index < len(lines) and re.match(r"^[-*] ", lines[index]):
                bullets.append(ListItem(Paragraph(inline_markup(lines[index][2:]), styles["body"]), leftIndent=14))
                index += 1
            story.append(ListFlowable(bullets, bulletType="bullet", leftIndent=18, bulletFontName="Helvetica", bulletFontSize=7))
            story.append(Spacer(1, 5))
            continue
        if re.match(r"^\d+\. ", line):
            flush_paragraph()
            items: list[ListItem] = []
            while index < len(lines) and re.match(r"^\d+\. ", lines[index]):
                text = re.sub(r"^\d+\. ", "", lines[index])
                items.append(ListItem(Paragraph(inline_markup(text), styles["body"]), leftIndent=16))
                index += 1
            story.append(ListFlowable(items, bulletType="1", start="1", leftIndent=20))
            story.append(Spacer(1, 5))
            continue
        paragraph.append(line.strip())
        index += 1

    flush_paragraph()
    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=22 * mm,
        title="Q-CARE Layman's Handbook",
        author="Q-CARE",
        subject="Phase 3D external transportability interpretation",
    )
    document.build(parse_markdown(SOURCE.read_text(), styles), onFirstPage=add_page, onLaterPages=add_page)
    print(OUTPUT)


if __name__ == "__main__":
    main()
