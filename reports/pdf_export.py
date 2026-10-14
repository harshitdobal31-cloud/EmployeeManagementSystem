from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

REPORTS_DIR = BASE_DIR / "reports"

PDF_DIR = REPORTS_DIR / "pdf_exports"

PDF_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


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
    Generate professional landscape PDF report.

    Returns:
        Path object.
    """

    try:

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        file_path = PDF_DIR / filename

        document = SimpleDocTemplate(
            str(file_path),
            pagesize=landscape(A4),
            rightMargin=10 * mm,
            leftMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "EMSReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#0F172A"
            ),
            spaceAfter=5,
        )

        subtitle_style = ParagraphStyle(
            "EMSReportSubtitle",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#64748B"
            ),
            spaceAfter=10,
        )

        body_style = ParagraphStyle(
            "EMSReportBody",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor(
                "#1E293B"
            ),
        )

        header_style = ParagraphStyle(
            "EMSReportHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            textColor=colors.white,
        )

        story = []

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        story.append(
            Paragraph(
                title,
                title_style,
            )
        )

        generated_time = datetime.now().strftime(
            "%d-%m-%Y %I:%M %p"
        )

        story.append(
            Paragraph(
                f"Employee Management System | "
                f"Generated on {generated_time}",
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
                    body_style,
                )
            )

            if isinstance(
                summary,
                (list, tuple),
            ):

                for item in summary:

                    story.append(
                        Paragraph(
                            f"• {item}",
                            body_style,
                        )
                    )

            else:

                story.append(
                    Paragraph(
                        str(summary),
                        body_style,
                    )
                )

            story.append(
                Spacer(
                    1,
                    7,
                )
            )

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        table_data = []

        header_cells = []

        for header in headers:

            header_cells.append(
                Paragraph(
                    str(header),
                    header_style,
                )
            )

        table_data.append(
            header_cells
        )

        for row in rows:

            body_cells = []

            for value in row:

                text = (
                    ""
                    if value is None
                    else str(value)
                )

                body_cells.append(
                    Paragraph(
                        text,
                        body_style,
                    )
                )

            table_data.append(
                body_cells
            )

        if not table_data:

            table_data = [
                [
                    Paragraph(
                        "No data available",
                        body_style,
                    )
                ]
            ]

        table = Table(
            table_data,
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
                        colors.HexColor(
                            "#2563EB"
                        ),
                    ),

                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),

                    (
                        "ALIGN",
                        (0, 0),
                        (-1, 0),
                        "CENTER",
                    ),

                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor(
                            "#CBD5E1"
                        ),
                    ),

                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor(
                                "#F8FAFC"
                            ),
                        ],
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

        story.append(table)

        story.append(
            Spacer(
                1,
                10,
            )
        )

        story.append(
            Paragraph(
                "Employee Management System • Reports & Analytics",
                subtitle_style,
            )
        )

        # ----------------------------------------------------
        # BUILD
        # ----------------------------------------------------

        document.build(story)

        return file_path

    except Exception as error:

        raise Exception(
            f"Unable to generate PDF report: {error}"
        )