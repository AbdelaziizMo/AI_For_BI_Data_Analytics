import re
from pathlib import Path
from html import unescape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

REPORT_FILE = OUTPUT_DIR / "ai_business_report.md"
PDF_FILE = OUTPUT_DIR / "ai_business_report_final.pdf"
VISUALIZATIONS_DIR = OUTPUT_DIR / "visualizations"


# ============================================================
# PAGE CONFIG
# ============================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 20 * mm
BOTTOM_MARGIN = 18 * mm


# ============================================================
# FONT
# ============================================================

def register_fonts():

    candidates = [
        (
            "Arial",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ),
        (
            "Calibri",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ),
    ]

    for name, regular, bold in candidates:

        regular_path = Path(regular)
        bold_path = Path(bold)

        if regular_path.exists() and bold_path.exists():

            pdfmetrics.registerFont(
                TTFont(name, str(regular_path))
            )

            pdfmetrics.registerFont(
                TTFont(
                    f"{name}-Bold",
                    str(bold_path),
                )
            )

            return name, f"{name}-Bold"

    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontName=FONT_BOLD,
    fontSize=20,
    leading=24,
    alignment=TA_CENTER,
    spaceAfter=14,
)

h1_style = ParagraphStyle(
    "H1Custom",
    parent=styles["Heading1"],
    fontName=FONT_BOLD,
    fontSize=16,
    leading=20,
    spaceBefore=12,
    spaceAfter=8,
)

h2_style = ParagraphStyle(
    "H2Custom",
    parent=styles["Heading2"],
    fontName=FONT_BOLD,
    fontSize=12.5,
    leading=16,
    spaceBefore=10,
    spaceAfter=6,
)

body_style = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontName=FONT,
    fontSize=9.5,
    leading=14,
    spaceAfter=6,
)

bullet_style = ParagraphStyle(
    "BulletCustom",
    parent=body_style,
    leftIndent=13,
    firstLineIndent=-8,
    spaceAfter=4,
)

number_style = ParagraphStyle(
    "NumberCustom",
    parent=body_style,
    leftIndent=16,
    firstLineIndent=-12,
    spaceAfter=4,
)

caption_style = ParagraphStyle(
    "CaptionCustom",
    parent=body_style,
    fontName=FONT,
    fontSize=8,
    leading=10,
    alignment=TA_CENTER,
    textColor=colors.grey,
    spaceBefore=4,
    spaceAfter=10,
)


# ============================================================
# PAGE HEADER / FOOTER
# ============================================================

def add_header_footer(canvas, doc):

    canvas.saveState()

    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(colors.grey)

    canvas.drawString(
        LEFT_MARGIN,
        PAGE_HEIGHT - 10 * mm,
        "AI Business Intelligence Report",
    )

    canvas.drawCentredString(
        PAGE_WIDTH / 2,
        8 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# MARKDOWN CLEANING
# ============================================================

def clean_markdown(text):

    text = unescape(text)

    # Remove escaped markdown characters
    text = text.replace(r"\*", "*")
    text = text.replace(r"\_", "_")
    text = text.replace(r"\-", "-")

    # Horizontal rule
    text = re.sub(
        r"^\s*\\?[-*_]{3,}\s*$",
        "",
        text,
    )

    # --------------------------------------------------------
    # Protect inline code BEFORE processing markdown
    # --------------------------------------------------------

    code_tokens = {}

    def protect_code(match):

        token = f"CODETOKEN{len(code_tokens)}"

        code_tokens[token] = (
            f"<font name='Courier'>{match.group(1)}</font>"
        )

        return token

    text = re.sub(
        r"`([^`]+)`",
        protect_code,
        text,
    )

    # Bold
    text = re.sub(
        r"\*\*(.*?)\*\*",
        r"<b>\1</b>",
        text,
    )

    # Remove remaining single asterisks
    text = re.sub(
        r"(?<!\*)\*(?!\*)",
        "",
        text,
    )

    # Italic
    text = re.sub(
        r"_(.*?)_",
        r"<i>\1</i>",
        text,
    )

    # Restore inline code
    for token, replacement in code_tokens.items():

        text = text.replace(
            token,
            replacement,
        )

    # Markdown links
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text,
    )

    return text.strip()


# ============================================================
# IMAGE CREATION
# ============================================================

def add_visualization(filename, caption):

    image_path = VISUALIZATIONS_DIR / filename

    print(
        f"      Checking image: {filename}"
    )

    if not image_path.exists():

        print(
            f"      WARNING: Missing image: {image_path}"
        )

        return Paragraph(
            f"<b>[Missing visualization]</b><br/>{filename}",
            body_style,
        )

    print(
        f"      OK: {image_path}"
    )

    try:

        img = Image(
            str(image_path)
        )

        max_width = (
            PAGE_WIDTH
            - LEFT_MARGIN
            - RIGHT_MARGIN
        )

        max_height = 105 * mm

        width = img.imageWidth
        height = img.imageHeight

        scale = min(
            max_width / width,
            max_height / height,
            1.0,
        )

        img.drawWidth = width * scale
        img.drawHeight = height * scale

        img.hAlign = "CENTER"

        return KeepTogether(
            [
                Spacer(1, 7),
                img,
                Paragraph(
                    caption,
                    caption_style,
                ),
                Spacer(1, 8),
            ]
        )

    except Exception as e:

        print(
            f"      ERROR loading {filename}: {e}"
        )

        return Paragraph(
            f"<b>Unable to load visualization:</b> "
            f"{filename}",
            body_style,
        )


# ============================================================
# TABLE
# ============================================================

def build_table(table_lines):

    rows = []

    for line in table_lines:

        line = line.strip()

        if not line:
            continue

        # Skip markdown separator
        if re.match(
            r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$",
            line,
        ):
            continue

        cells = [
            cell.strip()
            for cell in line.strip("|").split("|")
        ]

        rows.append(
            [
                Paragraph(
                    clean_markdown(cell),
                    body_style,
                )
                for cell in cells
            ]
        )

    if not rows:
        return None

    table = Table(
        rows,
        repeatRows=1,
        hAlign="CENTER",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#E8EEF5"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    FONT_BOLD,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


# ============================================================
# PARSE REPORT
# ============================================================

def build_story(markdown):

    lines = markdown.splitlines()

    story = []

    i = 0

    while i < len(lines):

        raw = lines[i].strip()

        if not raw:

            story.append(
                Spacer(1, 4)
            )

            i += 1
            continue

        # ----------------------------------------------------
        # HEADINGS
        # ----------------------------------------------------

        heading = re.match(
            r"^\*{0,2}#{1,3}\s+(.+?)\*{0,2}$",
            raw,
        )

        if heading:

            title = clean_markdown(
                heading.group(1)
            )

            # ------------------------------------------------
            # MAIN TITLE
            # ------------------------------------------------

            if title == "Executive Summary":

                story.append(
                    Paragraph(
                        title,
                        title_style,
                    )
                )

            else:

                story.append(
                    Paragraph(
                        title,
                        h1_style,
                    )
                )

                # ==================================================
                # CURRENT VISUALIZATION
                # ==================================================

                # --------------------------------------------------
                # TIME TREND ANALYSIS
                # --------------------------------------------------

                if title == "Time Trend Analysis":

                    story.append(
                        add_visualization(
                            "01_peak_daily_revenue_on_largest_spike_date.png",
                            "Peak daily revenue on the largest revenue spike date",
                        )
                    )

            i += 1
            continue

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        if "|" in raw and i + 1 < len(lines):

            if "|" in lines[i + 1]:

                table_lines = []

                while (
                    i < len(lines)
                    and "|" in lines[i]
                ):

                    table_lines.append(
                        lines[i]
                    )

                    i += 1

                table = build_table(
                    table_lines
                )

                if table:

                    story.append(table)

                    story.append(
                        Spacer(1, 8)
                    )

                continue

        # ----------------------------------------------------
        # BULLET
        # ----------------------------------------------------

        bullet = re.match(
            r"^\\?\*\s+(.+)",
            raw,
        )

        if bullet:

            text = clean_markdown(
                bullet.group(1)
            )

            story.append(
                Paragraph(
                    f"• {text}",
                    bullet_style,
                )
            )

            i += 1
            continue

        # ----------------------------------------------------
        # NESTED BULLET
        # ----------------------------------------------------

        nested = re.match(
            r"^\\?\*\s+(.+)",
            raw,
        )

        if nested:

            text = clean_markdown(
                nested.group(1)
            )

            story.append(
                Paragraph(
                    f"• {text}",
                    bullet_style,
                )
            )

            i += 1
            continue

        # ----------------------------------------------------
        # NUMBERED LIST
        # ----------------------------------------------------

        numbered = re.match(
            r"^(?:\\)?(\d+)\.\s+(.+)",
            raw,
        )

        if numbered:

            number = numbered.group(1)

            text = clean_markdown(
                numbered.group(2)
            )

            story.append(
                Paragraph(
                    f"{number}. {text}",
                    number_style,
                )
            )

            i += 1
            continue

        # ----------------------------------------------------
        # NORMAL TEXT
        # ----------------------------------------------------

        text = clean_markdown(raw)

        if text:

            story.append(
                Paragraph(
                    text,
                    body_style,
                )
            )

        i += 1

    return story


# ============================================================
# VALIDATION
# ============================================================

def validate_files():

    print()
    print("=" * 65)
    print("AI BUSINESS REPORT → PDF")
    print("=" * 65)
    print()

    # --------------------------------------------------------
    # 1. Markdown report
    # --------------------------------------------------------

    print(
        "[1/3] Checking Markdown report..."
    )

    if not REPORT_FILE.exists():

        raise FileNotFoundError(
            f"Report not found:\n{REPORT_FILE}"
        )

    print(
        f"      OK: {REPORT_FILE}"
    )

    # --------------------------------------------------------
    # 2. Current visualization
    # --------------------------------------------------------

    print()
    print(
        "[2/3] Checking visualization..."
    )

    expected = (
        "01_peak_daily_revenue_on_largest_spike_date.png"
    )

    path = VISUALIZATIONS_DIR / expected

    if path.exists():

        print(
            f"      OK: {expected}"
        )

    else:

        raise FileNotFoundError(
            f"Visualization not found:\n{path}"
        )

    # --------------------------------------------------------
    # 3. Validation complete
    # --------------------------------------------------------

    print()
    print(
        "[3/3] Inputs validated successfully."
    )


# ============================================================
# BUILD PDF
# ============================================================

def build_pdf():

    markdown = REPORT_FILE.read_text(
        encoding="utf-8"
    )

    print()
    print(
        "Building PDF..."
    )
    print()

    story = build_story(
        markdown
    )

    doc = SimpleDocTemplate(
        str(PDF_FILE),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="AI Business Intelligence Report",
        author="Abdelaziz Mostafa",
    )

    doc.build(
        story,
        onFirstPage=add_header_footer,
        onLaterPages=add_header_footer,
    )

    print()
    print("=" * 65)
    print(
        "PDF GENERATED SUCCESSFULLY"
    )
    print("=" * 65)

    print(
        f"Output: {PDF_FILE}"
    )

    print(
        f"Size:   {PDF_FILE.stat().st_size:,} bytes"
    )

    print("=" * 65)
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    validate_files()

    build_pdf()


if __name__ == "__main__":
    main()