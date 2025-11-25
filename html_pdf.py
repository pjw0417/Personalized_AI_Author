"""PDF rendering via ReportLab (pure Python) with justification and bold headings."""
from __future__ import annotations

import html
import os
from pathlib import Path
import re
from typing import Iterable, List, Tuple

from reportlab.lib import pagesizes
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _int_to_roman(num: int) -> str:
    if num <= 0:
        return str(num)
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    remaining = num
    for value, numeral in vals:
        while remaining >= value:
            result += numeral
            remaining -= value
    return result


def _romanize_inline_numbers(text: str, max_value: int = 50) -> str:
    def repl(match: re.Match[str]) -> str:
        number = int(match.group(1))
        suffix = match.group(2)
        if number <= 0 or number > max_value:
            return match.group(0)
        return f"{_int_to_roman(number)}{suffix}"

    return re.sub(r"\b(\d+)([).])", repl, text)


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return bool(re.match(r"^(title|working title|chapter|section)\b", stripped, re.IGNORECASE))


def _lines_to_flowables(
    lines: Iterable[str],
    body_style: ParagraphStyle,
    heading_style: ParagraphStyle,
    title_style: ParagraphStyle,
) -> List[object]:
    flow: List[object] = []
    is_first_line = True
    for raw in lines:
        line = raw.strip("\r")
        if not line:
            flow.append(Spacer(1, 4))
            continue

        safe_text = html.escape(_romanize_inline_numbers(line))
        if is_first_line:
            flow.append(Paragraph(f"<b>{safe_text}</b>", title_style))
            is_first_line = False
        elif _is_heading(line):
            flow.append(Paragraph(f"<b>{safe_text}</b>", heading_style))
        else:
            flow.append(Paragraph(safe_text, body_style))

    return flow


def html_text_to_pdf(text: str, output_path: str) -> None:
    """Render plain text to PDF with justification, bold headings, and Romanized markers."""
    regular_font, bold_font, italic_font = _register_font_family()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=pagesizes.A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=12,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        wordWrap="CJK",
    )
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading3"],
        fontName=italic_font,
        fontSize=13,
        leading=17,
        alignment=TA_LEFT,
        spaceAfter=8,
        wordWrap="CJK",
    )

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=16,
        leading=20,
        alignment=TA_LEFT,
        spaceAfter=10,
        wordWrap="CJK",
    )

    lines = text.splitlines()
    story = _lines_to_flowables(lines, body, heading, title_style)
    doc.build(story)
    print(f"📄 PDF saved to: {output_path}")
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
ENV_FONT = os.getenv("PDF_FONT_PATH")
FONT_CANDIDATES: Tuple[Path | None, ...] = (
    Path(ENV_FONT) if ENV_FONT else None,
    FONTS_DIR / "NotoSans-Bold.ttf",
    FONTS_DIR / "NotoSans-Italic.ttf",
    FONTS_DIR / "NotoSansKR-Regular.ttf",
    FONTS_DIR / "NotoSans-Regular.ttf",
) 


def _resolve_font_path() -> Path | None:
    for candidate in FONT_CANDIDATES:
        if candidate and candidate.exists():
            return candidate
    return None


def _register_font_family() -> Tuple[str, str, str]:
    """Register a Unicode font if available; return (regular, bold, italic)."""
    regular_path = None
    bold_path = None
    italic_path = None

    kr_candidate = FONTS_DIR / "NotoSansKR-Regular.ttf"
    if kr_candidate.exists():
        regular_path = kr_candidate

    for name in ["NotoSans-Regular.ttf"]:
        candidate = FONTS_DIR / name
        if candidate.exists():
            regular_path = candidate
            break

    for name in ["NotoSans-Bold.ttf"]:
        candidate = FONTS_DIR / name
        if candidate.exists():
            bold_path = candidate
            break

    for name in ["NotoSans-Italic.ttf", "NotoSans-Regular.ttf"]:
        candidate = FONTS_DIR / name
        if candidate.exists():
            italic_path = candidate
            break

    if not regular_path:
        regular_path = _resolve_font_path()

    if not regular_path:
        return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"

    try:
        pdfmetrics.registerFont(TTFont("CustomUnicode", str(regular_path)))
        pdfmetrics.registerFont(TTFont("CustomUnicode-Bold", str(bold_path or regular_path)))
        pdfmetrics.registerFont(TTFont("CustomUnicode-Italic", str(italic_path or regular_path)))
        return "CustomUnicode", "CustomUnicode-Bold", "CustomUnicode-Italic"
    except Exception:
        return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
