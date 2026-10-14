from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
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

PAYSLIP_DIR = BASE_DIR / "reports" / "payslips"

PAYSLIP_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# GENERATE PAYSLIP PDF
# ============================================================

def generate_payslip_pdf(
    payroll,
    employee,
    file_path=None
):
    """
    Generate a professional employee payslip PDF.

    Parameters:
        payroll:
            Payroll database object.

        employee:
            Employee database object.

        file_path:
            Optional custom PDF path.

    Returns:
        Path of generated PDF.
    """

    # --------------------------------------------------------
    # Create default PDF file path
    # --------------------------------------------------------

    if file_path is None:

        employee_id = (
            str(employee.employee_id)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        payroll_month = (
            str(payroll.payroll_month)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        file_path = (
            PAYSLIP_DIR
            / f"Payslip_{employee_id}_{payroll_month}.pdf"
        )

    else:

        file_path = Path(file_path)

    # --------------------------------------------------------
    # Salary values
    # --------------------------------------------------------

    basic_salary = float(
        payroll.basic_salary or 0
    )

    allowances = float(
        payroll.allowances or 0
    )

    deductions = float(
        payroll.deductions or 0
    )

    net_salary = float(
        payroll.net_salary or 0
    )

    gross_salary = (
        basic_salary + allowances
    )

    # --------------------------------------------------------
    # Create PDF
    # --------------------------------------------------------

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    # --------------------------------------------------------
    # Styles
    # --------------------------------------------------------

    company_style = ParagraphStyle(
        "CompanyStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F2747"),
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=15,
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#0F2747"),
        spaceBefore=8,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )

    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
    )

    # --------------------------------------------------------
    # PDF Content
    # --------------------------------------------------------

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    story.append(
        Paragraph(
            "EMPLOYEE MANAGEMENT SYSTEM",
            company_style
        )
    )

    story.append(
        Paragraph(
            "Monthly Salary Payslip",
            subtitle_style
        )
    )

    # ========================================================
    # EMPLOYEE INFORMATION
    # ========================================================

    employee_data = [
        [
            Paragraph(
                "<b>Employee ID</b>",
                normal_style
            ),
            Paragraph(
                str(employee.employee_id),
                normal_style
            ),
            Paragraph(
                "<b>Payroll Month</b>",
                normal_style
            ),
            Paragraph(
                str(payroll.payroll_month),
                normal_style
            ),
        ],
        [
            Paragraph(
                "<b>Employee Name</b>",
                normal_style
            ),
            Paragraph(
                str(employee.full_name),
                normal_style
            ),
            Paragraph(
                "<b>Status</b>",
                normal_style
            ),
            Paragraph(
                str(payroll.status),
                normal_style
            ),
        ],
        [
            Paragraph(
                "<b>Department</b>",
                normal_style
            ),
            Paragraph(
                str(employee.department or "-"),
                normal_style
            ),
            Paragraph(
                "<b>Designation</b>",
                normal_style
            ),
            Paragraph(
                str(employee.designation or "-"),
                normal_style
            ),
        ],
    ]

    employee_table = Table(
        employee_data,
        colWidths=[
            32 * mm,
            55 * mm,
            32 * mm,
            55 * mm,
        ],
    )

    employee_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#EEF4FF"),
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    colors.HexColor("#EEF4FF"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E2E8F0"),
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
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(
        employee_table
    )

    story.append(
        Spacer(1, 15)
    )

    # ========================================================
    # SALARY BREAKDOWN
    # ========================================================

    story.append(
        Paragraph(
            "Salary Breakdown",
            section_style
        )
    )

    salary_data = [
        [
            Paragraph(
                "<b>Salary Component</b>",
                normal_style
            ),
            Paragraph(
                "<b>Amount</b>",
                normal_style
            ),
        ],
        [
            Paragraph(
                "Basic Salary",
                normal_style
            ),
            Paragraph(
                f"₹ {basic_salary:,.2f}",
                normal_style
            ),
        ],
        [
            Paragraph(
                "Allowances",
                normal_style
            ),
            Paragraph(
                f"₹ {allowances:,.2f}",
                normal_style
            ),
        ],
        [
            Paragraph(
                "<b>Gross Salary</b>",
                normal_style
            ),
            Paragraph(
                f"<b>₹ {gross_salary:,.2f}</b>",
                normal_style
            ),
        ],
        [
            Paragraph(
                "Deductions",
                normal_style
            ),
            Paragraph(
                f"₹ {deductions:,.2f}",
                normal_style
            ),
        ],
    ]

    salary_table = Table(
        salary_data,
        colWidths=[
            130 * mm,
            44 * mm,
        ],
    )

    salary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0F2747"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "BACKGROUND",
                    (0, 3),
                    (-1, 3),
                    colors.HexColor("#F1F5F9"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E2E8F0"),
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
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
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    story.append(
        salary_table
    )

    story.append(
        Spacer(1, 15)
    )

    # ========================================================
    # NET SALARY
    # ========================================================

    net_salary_data = [
        [
            Paragraph(
                "<b>NET SALARY</b>",
                normal_style
            ),
            Paragraph(
                f"<b>₹ {net_salary:,.2f}</b>",
                normal_style
            ),
        ]
    ]

    net_table = Table(
        net_salary_data,
        colWidths=[
            130 * mm,
            44 * mm,
        ],
    )

    net_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#E8F1FF"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#93C5FD"),
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT",
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
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
            ]
        )
    )

    story.append(
        net_table
    )

    story.append(
        Spacer(1, 30)
    )

    # ========================================================
    # FOOTER
    # ========================================================

    story.append(
        Paragraph(
            "This is a system-generated payslip.",
            footer_style
        )
    )

    story.append(
        Spacer(1, 5)
    )

    story.append(
        Paragraph(
            "Employee Management System | Payroll Module",
            footer_style
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story
    )

    return file_path