from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# REPORT DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
PDF_DIR = REPORTS_DIR / "pdf_exports"

PDF_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PDF EXPORT
# ============================================================

def export_to_pdf(
    filename,
    title,
    headers,
    rows,
    summary=None,
):
    """
    Generate a professional PDF report.

    Parameters:
        filename : PDF filename
        title    : Report title
        headers  : List of table headers
        rows     : List of table rows
        summary  : Optional summary text/list

    Returns:
        Path of generated PDF
    """

    try:

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        file_path = PDF_DIR / filename

        # ----------------------------------------------------
        # DOCUMENT
        # ----------------------------------------------------

        document = SimpleDocTemplate(
            str(file_path),
            pagesize=landscape(A4),
            rightMargin=12 * mm,
            leftMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )

        # ----------------------------------------------------
        # STYLES
        # ----------------------------------------------------

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=8,
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=12,
        )

        summary_style = ParagraphStyle(
            "ReportSummary",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            spaceAfter=6,
        )

        # ----------------------------------------------------
        # STORY
        # ----------------------------------------------------

        story = []

        # Title
        story.append(
            Paragraph(
                title,
                title_style,
            )
        )

        # Generated date/time
        generated_time = datetime.now().strftime(
            "%d-%m-%Y %I:%M %p"
        )

        story.append(
            Paragraph(
                f"Generated on: {generated_time}",
                subtitle_style,
            )
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        if summary:

            story.append(
                Paragraph(
                    "<b>Report Summary</b>",
                    summary_style,
                )
            )

            if isinstance(summary, (list, tuple)):

                for item in summary:

                    story.append(
                        Paragraph(
                            f"• {item}",
                            summary_style,
                        )
                    )

            else:

                story.append(
                    Paragraph(
                        str(summary),
                        summary_style,
                    )
                )

            story.append(
                Spacer(1, 6)
            )

        # ----------------------------------------------------
        # TABLE DATA
        # ----------------------------------------------------

        table_data = []

        # Header
        table_data.append(
            [
                Paragraph(
                    f"<b>{header}</b>",
                    styles["Normal"],
                )
                for header in headers
            ]
        )

        # Rows
        for row in rows:

            table_data.append(
                [
                    Paragraph(
                        str(value)
                        if value is not None
                        else "",
                        styles["Normal"],
                    )
                    for value in row
                ]
            )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        table = Table(
            table_data,
            repeatRows=1,
            hAlign="CENTER",
        )

        table.setStyle(
            TableStyle(
                [
                    # Header
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1F4E78"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, 0),
                        "CENTER",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),

                    # Body
                    (
                        "ALIGN",
                        (0, 1),
                        (-1, -1),
                        "LEFT",
                    ),

                    # Borders
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),

                    # Padding
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(table)

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        story.append(
            Spacer(1, 12)
        )

        story.append(
            Paragraph(
                "Employee Management System",
                subtitle_style,
            )
        )

        # ----------------------------------------------------
        # BUILD PDF
        # ----------------------------------------------------

        document.build(story)

        return file_path

    except Exception as error:

        raise Exception(
            f"Unable to generate PDF report: {error}"
        )