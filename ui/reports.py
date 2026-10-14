from __future__ import annotations

import sys
from datetime import datetime, date, time

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from services.report_service import (
    get_employee_report,
    get_attendance_report,
    get_payroll_report,
    get_performance_report,
    get_department_report,
    get_quality_report,
    get_audit_report,
    get_report_counts,
)

from database.database import SessionLocal
from database.models import Employee, User

from reports.excel_export import export_to_excel
from reports.pdf_export import export_to_pdf
from utils.export import export_to_csv


# ============================================================
# THEME
# ============================================================

BG = "#07111F"
BG2 = "#0D1A2D"
CARD = "#14243D"
CARD_HOVER = "#192D4B"
BORDER = "#294463"

BLUE = "#2F80FF"
BLUE_LIGHT = "#58A6FF"
BLUE_DARK = "#1859B8"

GREEN = "#22C55E"
GREEN_DARK = "#0B3D25"

PURPLE = "#A855F7"
ORANGE = "#F59E0B"
RED = "#EF4444"
PINK = "#EC4899"
CYAN = "#22D3EE"

TEXT = "#F7FAFF"
TEXT2 = "#D6E1F0"
MUTED = "#8EA3BD"

TABLE_BG = "#0A1728"
TABLE_ALT = "#0E1D31"


# ============================================================
# REPORT TYPES
# ============================================================

REPORTS = [
    ("Employee", "👥", "Employee records & employment", BLUE),
    ("Attendance", "◷", "Attendance & working hours", CYAN),
    ("Payroll", "₹", "Salary & payroll history", GREEN),
    ("Performance", "★", "Reviews & employee scores", ORANGE),
    ("Department", "▦", "Department-wise distribution", PURPLE),
    ("Quality", "⚠", "Quality issues & resolution", RED),
    ("Audit", "⌕", "System activity & audit history", PINK),
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_text(value):
    """
    Convert database values into safe display text.
    """

    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y %I:%M %p")

    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")

    if isinstance(value, float):
        return f"{value:,.2f}"

    return str(value)


def money(value):
    """
    Format salary/money values.
    """

    try:
        return f"₹ {float(value or 0):,.2f}"
    except Exception:
        return "₹ 0.00"


def clean_filename(value):
    """
    Make a safe filename.
    """

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_-"
    )

    return "".join(
        char if char in allowed else "_"
        for char in value
    )


# ============================================================
# DATE HELPERS
# ============================================================

def normalize_date(value):
    """
    Convert different date formats into Python date.

    Supports:
    - datetime
    - date
    - YYYY-MM-DD
    - DD-MM-YYYY
    - YYYY/MM/DD
    - DD/MM/YYYY
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):

        value = value.strip()

        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
        ]

        for fmt in formats:

            try:
                parsed = datetime.strptime(
                    value,
                    fmt
                )

                return parsed.date()

            except ValueError:
                continue

    return None


def normalize_datetime(value):
    """
    Convert database value into datetime.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(
            value,
            time.min
        )

    if isinstance(value, str):

        value = value.strip()

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %I:%M %p",
            "%Y-%m-%d",
            "%d-%m-%Y",
        ]

        for fmt in formats:

            try:
                return datetime.strptime(
                    value,
                    fmt
                )

            except ValueError:
                continue

    return None


# ============================================================
# REPORT CARD
# ============================================================

class ReportCard(QFrame):

    clicked = Signal(str)

    def __init__(
        self,
        report_name,
        icon,
        description,
        accent,
        parent=None,
    ):

        super().__init__(parent)

        self.report_name = report_name
        self.accent = accent

        self.setObjectName("ReportCard")

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setMinimumHeight(126)
        self.setMaximumHeight(140)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.normal_style = f"""
            QFrame#ReportCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """

        self.hover_style = f"""
            QFrame#ReportCard {{
                background: {CARD_HOVER};
                border: 2px solid {accent};
                border-radius: 14px;
            }}
        """

        self.setStyleSheet(
            self.normal_style
        )

        self.build_ui(
            icon,
            description
        )

    # --------------------------------------------------------

    def build_ui(
        self,
        icon,
        description
    ):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            12,
            10,
            12,
            10
        )

        layout.setSpacing(5)

        # Top row

        top = QHBoxLayout()

        icon_label = QLabel(icon)

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setFixedSize(
            34,
            34
        )

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                background: {self.accent}22;
                color: {self.accent};
                border: 1px solid {self.accent}55;
                border-radius: 9px;
                font-size: 17px;
                font-weight: 800;
            }}
            """
        )

        top.addWidget(
            icon_label
        )

        top.addStretch()

        dot = QLabel("●")

        dot.setStyleSheet(
            f"""
            color: {self.accent};
            font-size: 8px;
            background: transparent;
            """
        )

        top.addWidget(dot)

        layout.addLayout(top)

        # Title

        title = QLabel(
            self.report_name
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                font-size: 13px;
                font-weight: 800;
            }}
            """
        )

        layout.addWidget(title)

        # Description

        description_label = QLabel(
            description
        )

        description_label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                background: transparent;
                font-size: 9px;
            }}
            """
        )

        description_label.setWordWrap(True)

        layout.addWidget(
            description_label
        )

        # Open

        open_label = QLabel(
            "Open report  →"
        )

        open_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.accent};
                background: transparent;
                font-size: 9px;
                font-weight: 700;
            }}
            """
        )

        layout.addWidget(
            open_label
        )

    # --------------------------------------------------------

    def enterEvent(self, event):

        self.setStyleSheet(
            self.hover_style
        )

        super().enterEvent(event)

    # --------------------------------------------------------

    def leaveEvent(self, event):

        self.setStyleSheet(
            self.normal_style
        )

        super().leaveEvent(event)

    # --------------------------------------------------------

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.clicked.emit(
                self.report_name
            )

        super().mousePressEvent(event)


# ============================================================
# REPORTS WINDOW
# ============================================================

class ReportsWindow(QWidget):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)

        self.current_report = "Employee"

        self.current_rows = []

        self.current_headers = []

        self.current_title = ""

        self.current_subtitle = ""

        # IMPORTANT
        # Stores only currently active filter widgets.
        self._active_filter_widgets = []

        self.build_ui()

        self.load_report(
            "Employee"
        )

    # ========================================================
    # MAIN UI
    # ========================================================

    def build_ui(self):

        self.setWindowTitle(
            "Employee Management System | Reports & Analytics"
        )

        self.resize(
            1500,
            920
        )

        self.setMinimumSize(
            1200,
            760
        )

        self.setStyleSheet(
            f"""
            QWidget {{
                font-family: Segoe UI, Arial;
            }}

            QWidget#Root {{
                background: {BG};
            }}

            QScrollArea {{
                border: none;
                background: {BG};
            }}

            QScrollBar:vertical {{
                background: {BG2};
                width: 10px;
            }}

            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 5px;
                min-height: 50px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {BLUE};
            }}
            """
        )

        root = QWidget()

        root.setObjectName(
            "Root"
        )

        main = QVBoxLayout(root)

        main.setContentsMargins(
            12,
            12,
            12,
            18
        )

        main.setSpacing(12)

        main.addWidget(
            self.build_header()
        )

        main.addWidget(
            self.build_report_types()
        )

        self.filter_card = self.build_filter_card()

        main.addWidget(
            self.filter_card
        )

        main.addWidget(
            self.build_stats()
        )

        main.addWidget(
            self.build_preview_header()
        )

        main.addWidget(
            self.build_table(),
            1
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setWidget(
            root
        )

        outer = QVBoxLayout(self)

        outer.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer.addWidget(
            scroll
        )

    # ========================================================
    # HEADER
    # ========================================================

    def build_header(self):

        card = QFrame()

        card.setFixedHeight(
            88
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

        layout = QHBoxLayout(card)

        layout.setContentsMargins(
            18,
            12,
            18,
            12
        )

        # Icon

        icon = QLabel("▥")

        icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon.setFixedSize(
            48,
            48
        )

        icon.setStyleSheet(
            f"""
            QLabel {{
                background: #16345C;
                color: {BLUE_LIGHT};
                border-radius: 13px;
                font-size: 23px;
                font-weight: 800;
            }}
            """
        )

        layout.addWidget(
            icon
        )

        # Text

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            2
        )

        title = QLabel(
            "Reports & Analytics"
        )

        title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 24px;
            font-weight: 900;
            background: transparent;
            """
        )

        text_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Generate, analyze and export organizational reports"
        )

        subtitle.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 10px;
            background: transparent;
            """
        )

        text_layout.addWidget(
            subtitle
        )

        layout.addLayout(
            text_layout
        )

        layout.addStretch()

        # Status

        self.data_status = QLabel(
            "●  Data Ready"
        )

        self.data_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.data_status.setFixedSize(
            120,
            44
        )

        self.data_status.setStyleSheet(
            f"""
            QLabel {{
                background: {GREEN_DARK};
                color: {GREEN};
                border: 1px solid #17683D;
                border-radius: 10px;
                font-size: 10px;
                font-weight: 800;
            }}
            """
        )

        layout.addWidget(
            self.data_status
        )

        # Refresh

        refresh_button = QPushButton(
            "↻  Refresh"
        )

        refresh_button.setFixedSize(
            105,
            44
        )

        refresh_button.clicked.connect(
            self.refresh_all
        )

        refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        refresh_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 10px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {BLUE_LIGHT};
            }}

            QPushButton:pressed {{
                background: {BLUE_DARK};
            }}
            """
        )

        layout.addWidget(
            refresh_button
        )

        return card

    # ========================================================
    # REPORT TYPES
    # ========================================================

    def build_report_types(self):

        box = QWidget()

        layout = QVBoxLayout(box)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        title_row = QHBoxLayout()

        title = QLabel(
            "Report Types"
        )

        title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 16px;
            font-weight: 900;
            background: transparent;
            """
        )

        title_row.addWidget(
            title
        )

        title_row.addStretch()

        hint = QLabel(
            "Select a report to view and export data"
        )

        hint.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 9px;
            background: transparent;
            """
        )

        title_row.addWidget(
            hint
        )

        layout.addLayout(
            title_row
        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(
            8
        )

        grid.setVerticalSpacing(
            8
        )

        self.report_cards = {}

        for index, data in enumerate(
            REPORTS
        ):

            card = ReportCard(
                *data,
                parent=box
            )

            card.clicked.connect(
                self.report_selected
            )

            self.report_cards[
                data[0]
            ] = card

            grid.addWidget(
                card,
                0,
                index
            )

            grid.setColumnStretch(
                index,
                1
            )

        layout.addLayout(
            grid
        )

        return box

    # ========================================================
    # FILTER CARD
    # ========================================================

    def build_filter_card(self):

        card = QFrame()

        card.setObjectName(
            "FilterCard"
        )

        card.setStyleSheet(
            f"""
            QFrame#FilterCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

        self.filter_layout = QVBoxLayout(card)

        self.filter_layout.setContentsMargins(
            15,
            12,
            15,
            12
        )

        self.filter_layout.setSpacing(
            7
        )

        return card

    # ========================================================
    # STATS
    # ========================================================

    def build_stats(self):

        box = QWidget()

        layout = QGridLayout(box)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setHorizontalSpacing(
            10
        )

        self.total_value = self.create_stat_card(
            layout,
            0,
            "▦",
            "TOTAL RECORDS",
            "0",
            BLUE_LIGHT
        )

        self.filtered_value = self.create_stat_card(
            layout,
            1,
            "✓",
            "FILTERED RECORDS",
            "0",
            GREEN
        )

        self.report_value = self.create_stat_card(
            layout,
            2,
            "□",
            "CURRENT REPORT",
            "Employee",
            ORANGE
        )

        self.export_value = self.create_stat_card(
            layout,
            3,
            "↗",
            "EXPORT OPTIONS",
            "3",
            PURPLE
        )

        for index in range(4):

            layout.setColumnStretch(
                index,
                1
            )

        return box

    # --------------------------------------------------------

    def create_stat_card(
        self,
        layout,
        column,
        icon,
        title,
        value,
        accent
    ):

        card = QFrame()

        card.setMinimumHeight(
            72
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """
        )

        row = QHBoxLayout(card)

        row.setContentsMargins(
            11,
            8,
            11,
            8
        )

        icon_label = QLabel(
            icon
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setFixedSize(
            36,
            36
        )

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                background: {accent}22;
                color: {accent};
                border-radius: 9px;
                font-size: 16px;
                font-weight: 900;
            }}
            """
        )

        row.addWidget(
            icon_label
        )

        text = QVBoxLayout()

        text.setSpacing(
            1
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 8px;
            font-weight: 800;
            background: transparent;
            """
        )

        text.addWidget(
            title_label
        )

        value_label = QLabel(
            value
        )

        value_label.setStyleSheet(
            f"""
            color: {accent};
            font-size: 16px;
            font-weight: 900;
            background: transparent;
            """
        )

        text.addWidget(
            value_label
        )

        row.addLayout(
            text
        )

        layout.addWidget(
            card,
            0,
            column
        )

        return value_label

    # ========================================================
    # PREVIEW HEADER
    # ========================================================

    def build_preview_header(self):

        box = QWidget()

        layout = QHBoxLayout(box)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        text = QVBoxLayout()

        text.setSpacing(
            1
        )

        self.preview_title = QLabel(
            "Employee Report Preview"
        )

        self.preview_title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 16px;
            font-weight: 900;
            background: transparent;
            """
        )

        text.addWidget(
            self.preview_title
        )

        self.preview_subtitle = QLabel(
            "Employee records • 0 records"
        )

        self.preview_subtitle.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 9px;
            background: transparent;
            """
        )

        text.addWidget(
            self.preview_subtitle
        )

        layout.addLayout(
            text
        )

        layout.addStretch()

        excel = self.create_export_button(
            "▦  Excel",
            GREEN,
            self.export_excel
        )

        csv = self.create_export_button(
            "▤  CSV",
            CYAN,
            self.export_csv
        )

        pdf = self.create_export_button(
            "▣  PDF",
            ORANGE,
            self.export_pdf
        )

        layout.addWidget(
            excel
        )

        layout.addWidget(
            csv
        )

        layout.addWidget(
            pdf
        )

        return box

    # --------------------------------------------------------

    def create_export_button(
        self,
        text,
        color,
        function
    ):

        button = QPushButton(
            text
        )

        button.setFixedSize(
            100,
            36
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.clicked.connect(
            function
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                background: {color}18;
                color: {color};
                border: 1px solid {color}44;
                border-radius: 8px;
                font-size: 9px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {color}30;
                border-color: {color};
            }}
            """
        )

        return button

    # ========================================================
    # TABLE
    # ========================================================

    def build_table(self):

        frame = QFrame()

        frame.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

        layout = QVBoxLayout(frame)

        layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        self.table = QTableWidget()

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setShowGrid(
            False
        )

        self.table.setWordWrap(
            False
        )

        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {TABLE_BG};
                color: {TEXT2};
                border: none;
                border-radius: 10px;
                font-size: 10px;
                alternate-background-color: {TABLE_ALT};
                selection-background-color: #173B67;
                selection-color: white;
            }}

            QHeaderView::section {{
                background: #1A3961;
                color: white;
                border: none;
                border-bottom: 2px solid {BLUE};
                padding: 8px;
                font-size: 9px;
                font-weight: 800;
            }}

            QTableWidget::item {{
                border-bottom: 1px solid #1C3048;
                padding: 7px;
            }}
            """
        )

        self.table.verticalHeader().setDefaultSectionSize(
            34
        )

        layout.addWidget(
            self.table
        )

        return frame

    # ========================================================
    # SAFE FILTER WIDGET CLEANUP
    # ========================================================

    def invalidate_filter_references(self):

        """
        IMPORTANT FIX

        Old QComboBox/QDateEdit objects were being deleted
        but Python attributes were still pointing to them.

        That caused:

        RuntimeError:
        Internal C++ object already deleted

        We reset all references before deleting widgets.
        """

        filter_names = [
            "employee_status",
            "employee_department",
            "employee_type",

            "att_employee",
            "att_status",
            "att_date_mode",
            "att_from",
            "att_to",

            "pay_employee",
            "pay_month",
            "pay_status",

            "perf_employee",
            "perf_category",
            "perf_date_mode",
            "perf_from",
            "perf_to",

            "quality_status",
            "quality_priority",

            "audit_user",
            "audit_date_mode",
            "audit_from",
            "audit_to",
        ]

        for name in filter_names:

            setattr(
                self,
                name,
                None
            )

        self._active_filter_widgets = []

    # --------------------------------------------------------

    def clear_layout(
        self,
        layout
    ):

        if layout is None:
            return

        while layout.count():

            item = layout.takeAt(0)

            widget = item.widget()

            child_layout = item.layout()

            if widget is not None:

                widget.hide()

                widget.setParent(
                    None
                )

                widget.deleteLater()

            elif child_layout is not None:

                self.clear_layout(
                    child_layout
                )

    # ========================================================
    # REPORT SELECTION
    # ========================================================

    def report_selected(
        self,
        report_name
    ):

        self.load_report(
            report_name
        )

    # --------------------------------------------------------

    def load_report(
        self,
        report_name
    ):

        self.current_report = report_name

        self.current_rows = []

        self.current_headers = []

        # VERY IMPORTANT
        # Reset old Qt references before deleting widgets.
        self.invalidate_filter_references()

        self.clear_layout(
            self.filter_layout
        )

        self.create_filters(
            report_name
        )

        self.highlight_report_card(
            report_name
        )

        self.refresh_report_data()

    # --------------------------------------------------------

    def highlight_report_card(
        self,
        report_name
    ):

        for name, card in self.report_cards.items():

            if name == report_name:

                card.setStyleSheet(
                    card.hover_style
                )

            else:

                card.setStyleSheet(
                    card.normal_style
                )

    # ========================================================
    # FILTER CREATION
    # ========================================================

    def create_filters(
        self,
        report_name
    ):

        # ----------------------------------------------------
        # FILTER HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title = QLabel(
            f"{report_name} Report Filters"
        )

        title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 13px;
            font-weight: 900;
            background: transparent;
            """
        )

        header.addWidget(
            title
        )

        header.addStretch()

        self.result_count_label = QLabel(
            "0 records found"
        )

        self.result_count_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 9px;
            background: transparent;
            """
        )

        header.addWidget(
            self.result_count_label
        )

        clear_button = QPushButton(
            "✕  Clear"
        )

        clear_button.setFixedHeight(
            30
        )

        clear_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        clear_button.clicked.connect(
            self.clear_filters
        )

        clear_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {BG2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 9px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: {BLUE};
                color: white;
                border-color: {BLUE};
            }}
            """
        )

        header.addWidget(
            clear_button
        )

        self.filter_layout.addLayout(
            header
        )

        # ----------------------------------------------------
        # FILTER ROW
        # ----------------------------------------------------

        row = QHBoxLayout()

        row.setSpacing(
            9
        )

        # ====================================================
        # EMPLOYEE
        # ====================================================

        if report_name == "Employee":

            self.employee_status = self.create_combo(
                [
                    "All",
                    "Active",
                    "Inactive"
                ]
            )

            self.employee_department = self.create_combo(
                [
                    "All"
                ] + self.get_departments()
            )

            self.employee_type = self.create_combo(
                [
                    "All",
                    "Full Time",
                    "Part Time",
                    "Contract",
                    "Intern",
                ]
            )

            row.addWidget(
                self.filter_field(
                    "Employee Status",
                    self.employee_status
                )
            )

            row.addWidget(
                self.filter_field(
                    "Department",
                    self.employee_department
                )
            )

            row.addWidget(
                self.filter_field(
                    "Employment Type",
                    self.employee_type
                )
            )

            self.employee_status.currentIndexChanged.connect(
                self.apply_filters
            )

            self.employee_department.currentIndexChanged.connect(
                self.apply_filters
            )

            self.employee_type.currentIndexChanged.connect(
                self.apply_filters
            )

        # ====================================================
        # ATTENDANCE
        # ====================================================

        elif report_name == "Attendance":

            self.att_employee = (
                self.create_employee_combo()
            )

            self.att_status = self.create_combo(
                [
                    "All",
                    "Present",
                    "Absent",
                    "Late",
                    "Leave",
                    "Half Day",
                ]
            )

            # ------------------------------------------------
            # THIS IS THE IMPORTANT DATE FILTER
            # ------------------------------------------------

            self.att_date_mode = self.create_combo(
                [
                    "All Dates",
                    "Custom Range",
                ]
            )

            self.att_from = self.date_edit()

            self.att_to = self.date_edit()

            # Default dates
            self.set_broad_date_range(
                self.att_from,
                self.att_to
            )

            row.addWidget(
                self.filter_field(
                    "Employee",
                    self.att_employee
                )
            )

            row.addWidget(
                self.filter_field(
                    "Status",
                    self.att_status
                )
            )

            row.addWidget(
                self.filter_field(
                    "Date Filter",
                    self.att_date_mode
                )
            )

            row.addWidget(
                self.filter_field(
                    "From Date",
                    self.att_from
                )
            )

            row.addWidget(
                self.filter_field(
                    "To Date",
                    self.att_to
                )
            )

            self.att_employee.currentIndexChanged.connect(
                self.apply_filters
            )

            self.att_status.currentIndexChanged.connect(
                self.apply_filters
            )

            self.att_date_mode.currentIndexChanged.connect(
                self.attendance_date_mode_changed
            )

            self.att_from.dateChanged.connect(
                self.apply_filters
            )

            self.att_to.dateChanged.connect(
                self.apply_filters
            )

            self.update_date_controls(
                self.att_date_mode,
                self.att_from,
                self.att_to
            )

        # ====================================================
        # PAYROLL
        # ====================================================

        elif report_name == "Payroll":

            self.pay_employee = (
                self.create_employee_combo()
            )

            self.pay_month = self.create_combo(
                ["All"] +
                self.get_payroll_months()
            )

            self.pay_status = self.create_combo(
                [
                    "All",
                    "Processed",
                    "Locked",
                ]
            )

            row.addWidget(
                self.filter_field(
                    "Employee",
                    self.pay_employee
                )
            )

            row.addWidget(
                self.filter_field(
                    "Payroll Month",
                    self.pay_month
                )
            )

            row.addWidget(
                self.filter_field(
                    "Status",
                    self.pay_status
                )
            )

            self.pay_employee.currentIndexChanged.connect(
                self.apply_filters
            )

            self.pay_month.currentIndexChanged.connect(
                self.apply_filters
            )

            self.pay_status.currentIndexChanged.connect(
                self.apply_filters
            )

        # ====================================================
        # PERFORMANCE
        # ====================================================

        elif report_name == "Performance":

            self.perf_employee = (
                self.create_employee_combo()
            )

            self.perf_category = self.create_combo(
                [
                    "All",
                    "Excellent",
                    "Very Good",
                    "Good",
                    "Average",
                    "Poor",
                ]
            )

            self.perf_date_mode = self.create_combo(
                [
                    "All Dates",
                    "Custom Range",
                ]
            )

            self.perf_from = self.date_edit()

            self.perf_to = self.date_edit()

            self.set_broad_date_range(
                self.perf_from,
                self.perf_to
            )

            row.addWidget(
                self.filter_field(
                    "Employee",
                    self.perf_employee
                )
            )

            row.addWidget(
                self.filter_field(
                    "Category",
                    self.perf_category
                )
            )

            row.addWidget(
                self.filter_field(
                    "Date Filter",
                    self.perf_date_mode
                )
            )

            row.addWidget(
                self.filter_field(
                    "From Date",
                    self.perf_from
                )
            )

            row.addWidget(
                self.filter_field(
                    "To Date",
                    self.perf_to
                )
            )

            self.perf_employee.currentIndexChanged.connect(
                self.apply_filters
            )

            self.perf_category.currentIndexChanged.connect(
                self.apply_filters
            )

            self.perf_date_mode.currentIndexChanged.connect(
                self.performance_date_mode_changed
            )

            self.perf_from.dateChanged.connect(
                self.apply_filters
            )

            self.perf_to.dateChanged.connect(
                self.apply_filters
            )

            self.update_date_controls(
                self.perf_date_mode,
                self.perf_from,
                self.perf_to
            )

        # ====================================================
        # DEPARTMENT
        # ====================================================

        elif report_name == "Department":

            label = QLabel(
                "Department-wise employee distribution"
            )

            label.setStyleSheet(
                f"""
                color: {MUTED};
                font-size: 10px;
                background: transparent;
                padding: 5px;
                """
            )

            row.addWidget(
                label
            )

            row.addStretch()

        # ====================================================
        # QUALITY
        # ====================================================

        elif report_name == "Quality":

            self.quality_status = self.create_combo(
                [
                    "All",
                    "Open",
                    "In Progress",
                    "Resolved",
                    "Closed",
                ]
            )

            self.quality_priority = self.create_combo(
                [
                    "All",
                    "Low",
                    "Medium",
                    "High",
                    "Critical",
                ]
            )

            row.addWidget(
                self.filter_field(
                    "Status",
                    self.quality_status
                )
            )

            row.addWidget(
                self.filter_field(
                    "Priority",
                    self.quality_priority
                )
            )

            self.quality_status.currentIndexChanged.connect(
                self.apply_filters
            )

            self.quality_priority.currentIndexChanged.connect(
                self.apply_filters
            )

        # ====================================================
        # AUDIT
        # ====================================================

        elif report_name == "Audit":

            self.audit_user = (
                self.create_user_combo()
            )

            self.audit_date_mode = self.create_combo(
                [
                    "All Dates",
                    "Custom Range",
                ]
            )

            self.audit_from = self.date_edit()

            self.audit_to = self.date_edit()

            self.set_broad_date_range(
                self.audit_from,
                self.audit_to
            )

            row.addWidget(
                self.filter_field(
                    "User",
                    self.audit_user
                )
            )

            row.addWidget(
                self.filter_field(
                    "Date Filter",
                    self.audit_date_mode
                )
            )

            row.addWidget(
                self.filter_field(
                    "From Date",
                    self.audit_from
                )
            )

            row.addWidget(
                self.filter_field(
                    "To Date",
                    self.audit_to
                )
            )

            self.audit_user.currentIndexChanged.connect(
                self.apply_filters
            )

            self.audit_date_mode.currentIndexChanged.connect(
                self.audit_date_mode_changed
            )

            self.audit_from.dateChanged.connect(
                self.apply_filters
            )

            self.audit_to.dateChanged.connect(
                self.apply_filters
            )

            self.update_date_controls(
                self.audit_date_mode,
                self.audit_from,
                self.audit_to
            )

        row.addStretch()

        self.filter_layout.addLayout(
            row
        )

        self._active_filter_widgets = (
            self.collect_current_filter_widgets()
        )

    # ========================================================
    # FILTER WIDGETS
    # ========================================================

    def create_combo(
        self,
        values
    ):

        combo = QComboBox()

        combo.addItems(
            [
                str(value)
                for value in values
            ]
        )

        combo.setFixedHeight(
            34
        )

        combo.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {BG2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0 9px;
                font-size: 9px;
            }}

            QComboBox:hover {{
                border-color: {BLUE};
            }}

            QComboBox:focus {{
                border: 1px solid {BLUE};
            }}

            QComboBox QAbstractItemView {{
                background: {BG2};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {BLUE};
            }}
            """
        )

        return combo

    # --------------------------------------------------------

    def date_edit(self):

        widget = QDateEdit()

        widget.setCalendarPopup(
            True
        )

        widget.setDate(
            QDate.currentDate()
        )

        widget.setDisplayFormat(
            "dd-MM-yyyy"
        )

        widget.setFixedHeight(
            34
        )

        widget.setStyleSheet(
            f"""
            QDateEdit {{
                background: {BG2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0 7px;
                font-size: 9px;
            }}

            QDateEdit:hover {{
                border-color: {BLUE};
            }}

            QDateEdit:focus {{
                border: 1px solid {BLUE};
            }}

            QCalendarWidget {{
                background: {BG2};
                color: {TEXT};
            }}
            """
        )

        return widget

    # --------------------------------------------------------

    def filter_field(
        self,
        title,
        widget
    ):

        box = QWidget()

        box.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout(box)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            3
        )

        label = QLabel(
            title
        )

        label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 8px;
            font-weight: 700;
            background: transparent;
            """
        )

        layout.addWidget(
            label
        )

        layout.addWidget(
            widget
        )

        return box

    # --------------------------------------------------------

    def create_employee_combo(self):

        combo = self.create_combo(
            []
        )

        combo.addItem(
            "All",
            None
        )

        db = SessionLocal()

        try:

            employees = (
                db.query(Employee)
                .order_by(Employee.full_name.asc())
                .all()
            )

            for employee in employees:

                combo.addItem(
                    f"{employee.employee_id} — "
                    f"{employee.full_name}",
                    employee.id
                )

        finally:

            db.close()

        return combo

    # --------------------------------------------------------

    def create_user_combo(self):

        combo = self.create_combo(
            []
        )

        combo.addItem(
            "All",
            None
        )

        db = SessionLocal()

        try:

            users = (
                db.query(User)
                .order_by(User.username.asc())
                .all()
            )

            for user in users:

                combo.addItem(
                    user.username,
                    user.id
                )

        finally:

            db.close()

        return combo

    # ========================================================
    # DATABASE HELPERS
    # ========================================================

    def get_departments(self):

        db = SessionLocal()

        try:

            values = (
                db.query(Employee.department)
                .filter(
                    Employee.department.isnot(None)
                )
                .distinct()
                .all()
            )

            return sorted(
                {
                    str(row[0])
                    for row in values
                    if row[0]
                }
            )

        finally:

            db.close()

    # --------------------------------------------------------

    def get_payroll_months(self):

        from database.models import Payroll

        db = SessionLocal()

        try:

            values = (
                db.query(
                    Payroll.payroll_month
                )
                .distinct()
                .all()
            )

            return sorted(
                {
                    str(row[0])
                    for row in values
                    if row[0]
                },
                reverse=True
            )

        finally:

            db.close()

    # ========================================================
    # DATE FILTER HELPERS
    # ========================================================

    def set_broad_date_range(
        self,
        from_widget,
        to_widget
    ):

        """
        Give date filters a broad default range.

        This avoids the problem where both dates start
        at today's date and old records disappear.
        """

        from_widget.blockSignals(
            True
        )

        to_widget.blockSignals(
            True
        )

        from_widget.setDate(
            QDate(2000, 1, 1)
        )

        to_widget.setDate(
            QDate.currentDate()
        )

        from_widget.blockSignals(
            False
        )

        to_widget.blockSignals(
            False
        )

    # --------------------------------------------------------

    def update_date_controls(
        self,
        mode_widget,
        from_widget,
        to_widget
    ):

        custom = (
            mode_widget.currentText()
            == "Custom Range"
        )

        from_widget.setEnabled(
            custom
        )

        to_widget.setEnabled(
            custom
        )

    # --------------------------------------------------------

    def attendance_date_mode_changed(
        self,
        index
    ):

        self.update_date_controls(
            self.att_date_mode,
            self.att_from,
            self.att_to
        )

        self.refresh_report_data()

    # --------------------------------------------------------

    def performance_date_mode_changed(
        self,
        index
    ):

        self.update_date_controls(
            self.perf_date_mode,
            self.perf_from,
            self.perf_to
        )

        self.refresh_report_data()

    # --------------------------------------------------------

    def audit_date_mode_changed(
        self,
        index
    ):

        self.update_date_controls(
            self.audit_date_mode,
            self.audit_from,
            self.audit_to
        )

        self.refresh_report_data()

    # --------------------------------------------------------

    def qdate_to_date(
        self,
        widget
    ):

        return widget.date().toPython()

    # ========================================================
    # CURRENT FILTER WIDGETS
    # ========================================================

    def collect_current_filter_widgets(self):

        names = [
            "employee_status",
            "employee_department",
            "employee_type",

            "att_employee",
            "att_status",
            "att_date_mode",
            "att_from",
            "att_to",

            "pay_employee",
            "pay_month",
            "pay_status",

            "perf_employee",
            "perf_category",
            "perf_date_mode",
            "perf_from",
            "perf_to",

            "quality_status",
            "quality_priority",

            "audit_user",
            "audit_date_mode",
            "audit_from",
            "audit_to",
        ]

        widgets = []

        for name in names:

            widget = getattr(
                self,
                name,
                None
            )

            if widget is not None:

                widgets.append(
                    widget
                )

        return widgets

    # ========================================================
    # CLEAR FILTERS
    # ========================================================

    def clear_filters(self):

        widgets = list(
            self._active_filter_widgets
        )

        for widget in widgets:

            try:

                widget.blockSignals(
                    True
                )

                if isinstance(
                    widget,
                    QComboBox
                ):

                    widget.setCurrentIndex(
                        0
                    )

                elif isinstance(
                    widget,
                    QDateEdit
                ):

                    widget.setDate(
                        QDate.currentDate()
                    )

                widget.blockSignals(
                    False
                )

            except RuntimeError:
                # Old/deleted Qt object.
                # Ignore safely.
                continue

        # Restore date controls
        if getattr(
            self,
            "att_date_mode",
            None
        ) is not None:

            self.update_date_controls(
                self.att_date_mode,
                self.att_from,
                self.att_to
            )

        if getattr(
            self,
            "perf_date_mode",
            None
        ) is not None:

            self.update_date_controls(
                self.perf_date_mode,
                self.perf_from,
                self.perf_to
            )

        if getattr(
            self,
            "audit_date_mode",
            None
        ) is not None:

            self.update_date_controls(
                self.audit_date_mode,
                self.audit_from,
                self.audit_to
            )

        self.refresh_report_data()

    # ========================================================
    # APPLY FILTERS
    # ========================================================

    def apply_filters(
        self,
        *_args
    ):

        self.refresh_report_data()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_all(self):

        self.data_status.setText(
            "●  Refreshing..."
        )

        self.data_status.setStyleSheet(
            f"""
            QLabel {{
                background: #33250E;
                color: {ORANGE};
                border: 1px solid #6B4C12;
                border-radius: 10px;
                font-size: 10px;
                font-weight: 800;
            }}
            """
        )

        QApplication.processEvents()

        self.load_report(
            self.current_report
        )

        self.data_status.setText(
            "●  Data Ready"
        )

        self.data_status.setStyleSheet(
            f"""
            QLabel {{
                background: {GREEN_DARK};
                color: {GREEN};
                border: 1px solid #17683D;
                border-radius: 10px;
                font-size: 10px;
                font-weight: 800;
            }}
            """
        )

    # ========================================================
    # REPORT DATA
    # ========================================================

    def refresh_report_data(self):

        try:

            report = self.current_report

            # ==================================================
            # EMPLOYEE
            # ==================================================

            if report == "Employee":

                data = get_employee_report(
                    department=self.employee_department.currentText(),
                    status=self.employee_status.currentText(),
                    employment_type=self.employee_type.currentText(),
                )

                headers = [
                    "Employee ID",
                    "Full Name",
                    "Email",
                    "Phone",
                    "Department",
                    "Designation",
                    "Employment Type",
                    "Salary",
                    "Status",
                ]

                rows = []

                for employee in data:

                    rows.append(
                        [
                            employee.employee_id,
                            employee.full_name,
                            employee.email,
                            employee.phone,
                            employee.department,
                            employee.designation,
                            employee.employment_type,
                            money(employee.salary),
                            employee.status,
                        ]
                    )

                title = "Employee Report"

                subtitle = (
                    "Employee records & employment information"
                )

            # ==================================================
            # ATTENDANCE
            # ==================================================

            elif report == "Attendance":

                employee_id = (
                    self.att_employee.currentData()
                )

                status = (
                    self.att_status.currentText()
                )

                # ----------------------------------------------
                # IMPORTANT:
                #
                # Do NOT send From/To dates to service here.
                #
                # We fetch employee + status data first.
                # Then Python filters attendance date.
                #
                # This fixes the Custom Date Range problem.
                # ----------------------------------------------

                data = get_attendance_report(
                    employee_id=employee_id,
                    status=status,
                    from_date=None,
                    to_date=None,
                )

                # ----------------------------------------------
                # CUSTOM DATE RANGE
                # ----------------------------------------------

                if (
                    self.att_date_mode.currentText()
                    == "Custom Range"
                ):

                    from_date = (
                        self.qdate_to_date(
                            self.att_from
                        )
                    )

                    to_date = (
                        self.qdate_to_date(
                            self.att_to
                        )
                    )

                    if from_date > to_date:

                        self.show_error(
                            "Invalid Date Range",
                            "From Date cannot be greater than To Date."
                        )

                        return

                    filtered_data = []

                    for attendance, employee in data:

                        attendance_date = normalize_date(
                            attendance.attendance_date
                        )

                        if attendance_date is None:
                            continue

                        if (
                            from_date
                            <= attendance_date
                            <= to_date
                        ):

                            filtered_data.append(
                                (
                                    attendance,
                                    employee
                                )
                            )

                    data = filtered_data

                headers = [
                    "Employee ID",
                    "Employee Name",
                    "Date",
                    "Check In",
                    "Check Out",
                    "Working Hours",
                    "Status",
                ]

                rows = []

                for attendance, employee in data:

                    rows.append(
                        [
                            employee.employee_id,
                            employee.full_name,
                            attendance.attendance_date,
                            attendance.check_in,
                            attendance.check_out,
                            attendance.working_hours,
                            attendance.status,
                        ]
                    )

                title = "Attendance Report"

                if (
                    self.att_date_mode.currentText()
                    == "Custom Range"
                ):

                    subtitle = (
                        "Attendance & working hours  •  "
                        f"{self.qdate_to_date(self.att_from).strftime('%d-%m-%Y')}"
                        " to "
                        f"{self.qdate_to_date(self.att_to).strftime('%d-%m-%Y')}"
                    )

                else:

                    subtitle = (
                        "Attendance & working hours  •  All Dates"
                    )

            # ==================================================
            # PAYROLL
            # ==================================================

            elif report == "Payroll":

                employee_id = (
                    self.pay_employee.currentData()
                )

                month = (
                    self.pay_month.currentText()
                )

                data = get_payroll_report(
                    employee_id=employee_id,
                    payroll_month=(
                        None
                        if month == "All"
                        else month
                    ),
                    status=self.pay_status.currentText(),
                )

                headers = [
                    "Employee ID",
                    "Employee Name",
                    "Month",
                    "Basic Salary",
                    "Allowances",
                    "Deductions",
                    "Net Salary",
                    "Status",
                ]

                rows = []

                for payroll, employee in data:

                    rows.append(
                        [
                            employee.employee_id,
                            employee.full_name,
                            payroll.payroll_month,
                            money(payroll.basic_salary),
                            money(payroll.allowances),
                            money(payroll.deductions),
                            money(payroll.net_salary),
                            payroll.status,
                        ]
                    )

                title = "Payroll Report"

                subtitle = (
                    "Salary, allowances, deductions and payroll history"
                )

            # ==================================================
            # PERFORMANCE
            # ==================================================

            elif report == "Performance":

                employee_id = (
                    self.perf_employee.currentData()
                )

                category = (
                    self.perf_category.currentText()
                )

                # ----------------------------------------------
                # Load without date restriction first.
                # Python date filter gives consistent behaviour.
                # ----------------------------------------------

                data = get_performance_report(
                    employee_id=employee_id,
                    category=category,
                    from_date=None,
                    to_date=None,
                )

                # ----------------------------------------------
                # CUSTOM DATE RANGE
                # ----------------------------------------------

                if (
                    self.perf_date_mode.currentText()
                    == "Custom Range"
                ):

                    from_date = (
                        self.qdate_to_date(
                            self.perf_from
                        )
                    )

                    to_date = (
                        self.qdate_to_date(
                            self.perf_to
                        )
                    )

                    if from_date > to_date:

                        self.show_error(
                            "Invalid Date Range",
                            "From Date cannot be greater than To Date."
                        )

                        return

                    filtered_data = []

                    for performance, employee in data:

                        review_date = normalize_date(
                            performance.review_date
                        )

                        if review_date is None:
                            continue

                        if (
                            from_date
                            <= review_date
                            <= to_date
                        ):

                            filtered_data.append(
                                (
                                    performance,
                                    employee
                                )
                            )

                    data = filtered_data

                headers = [
                    "Employee ID",
                    "Employee Name",
                    "Review Date",
                    "Score",
                    "Percentage",
                    "Category",
                    "Comments",
                ]

                rows = []

                for performance, employee in data:

                    rows.append(
                        [
                            employee.employee_id,
                            employee.full_name,
                            performance.review_date,
                            performance.score,
                            performance.percentage,
                            performance.category,
                            performance.comments,
                        ]
                    )

                title = "Performance Report"

                if (
                    self.perf_date_mode.currentText()
                    == "Custom Range"
                ):

                    subtitle = (
                        "Performance reviews  •  "
                        f"{self.qdate_to_date(self.perf_from).strftime('%d-%m-%Y')}"
                        " to "
                        f"{self.qdate_to_date(self.perf_to).strftime('%d-%m-%Y')}"
                    )

                else:

                    subtitle = (
                        "Performance reviews & employee evaluation  •  All Dates"
                    )

            # ==================================================
            # DEPARTMENT
            # ==================================================

            elif report == "Department":

                data = get_department_report()

                headers = [
                    "Department",
                    "Total Employees",
                    "Active Employees",
                    "Inactive Employees",
                ]

                rows = []

                for item in data:

                    rows.append(
                        [
                            item["department"],
                            item["total_employees"],
                            item["active_employees"],
                            item["inactive_employees"],
                        ]
                    )

                title = "Department Report"

                subtitle = (
                    "Department-wise employee distribution"
                )

            # ==================================================
            # QUALITY
            # ==================================================

            elif report == "Quality":

                data = get_quality_report(
                    status=self.quality_status.currentText(),
                    priority=self.quality_priority.currentText(),
                )

                headers = [
                    "Issue ID",
                    "Title",
                    "Category",
                    "Priority",
                    "Status",
                    "Issue Date",
                    "Root Cause",
                    "Corrective Action",
                ]

                rows = []

                for item in data:

                    rows.append(
                        [
                            item.issue_id,
                            item.title,
                            item.category,
                            item.priority,
                            item.status,
                            item.issue_date,
                            item.root_cause,
                            item.corrective_action,
                        ]
                    )

                title = "Quality Report"

                subtitle = (
                    "Quality issues, priorities and resolution tracking"
                )

            # ==================================================
            # AUDIT
            # ==================================================

            elif report == "Audit":

                user_id = (
                    self.audit_user.currentData()
                )

                # ----------------------------------------------
                # First get all audit records for selected user.
                # Then Python filters the date.
                # ----------------------------------------------

                data = get_audit_report(
                    user_id=user_id,
                    from_date=None,
                    to_date=None,
                )

                if (
                    self.audit_date_mode.currentText()
                    == "Custom Range"
                ):

                    from_date = (
                        self.qdate_to_date(
                            self.audit_from
                        )
                    )

                    to_date = (
                        self.qdate_to_date(
                            self.audit_to
                        )
                    )

                    if from_date > to_date:

                        self.show_error(
                            "Invalid Date Range",
                            "From Date cannot be greater than To Date."
                        )

                        return

                    filtered_data = []

                    start_datetime = datetime.combine(
                        from_date,
                        time.min
                    )

                    end_datetime = datetime.combine(
                        to_date,
                        time.max
                    )

                    for item in data:

                        created_at = normalize_datetime(
                            item.created_at
                        )

                        if created_at is None:
                            continue

                        if (
                            start_datetime
                            <= created_at
                            <= end_datetime
                        ):

                            filtered_data.append(
                                item
                            )

                    data = filtered_data

                headers = [
                    "User ID",
                    "Action",
                    "Description",
                    "Created At",
                ]

                rows = []

                for item in data:

                    rows.append(
                        [
                            item.user_id,
                            item.action,
                            item.description,
                            item.created_at,
                        ]
                    )

                title = "Audit Report"

                if (
                    self.audit_date_mode.currentText()
                    == "Custom Range"
                ):

                    subtitle = (
                        "Audit history  •  "
                        f"{self.qdate_to_date(self.audit_from).strftime('%d-%m-%Y')}"
                        " to "
                        f"{self.qdate_to_date(self.audit_to).strftime('%d-%m-%Y')}"
                    )

                else:

                    subtitle = (
                        "System activity & audit history  •  All Dates"
                    )

            else:

                headers = []

                rows = []

                title = "Report"

                subtitle = ""

            # ==================================================
            # SAVE RESULT
            # ==================================================

            self.current_headers = headers

            self.current_rows = rows

            self.current_title = title

            self.current_subtitle = subtitle

            # ==================================================
            # UPDATE UI
            # ==================================================

            self.update_table(
                headers,
                rows
            )

            self.update_summary(
                rows,
                title,
                subtitle
            )

            self.data_status.setText(
                "●  Data Ready"
            )

        except Exception as error:

            self.current_rows = []

            self.current_headers = []

            self.update_table(
                [],
                []
            )

            self.data_status.setText(
                "●  Error"
            )

            self.show_error(
                "Unable to Load Report",
                str(error)
            )

    # ========================================================
    # TABLE UPDATE
    # ========================================================

    def update_table(
        self,
        headers,
        rows
    ):

        self.table.clear()

        self.table.setColumnCount(
            len(headers)
        )

        self.table.setHorizontalHeaderLabels(
            headers
        )

        self.table.setRowCount(
            len(rows)
        )

        for row_index, row_data in enumerate(
            rows
        ):

            for column_index, value in enumerate(
                row_data
            ):

                item = QTableWidgetItem(
                    safe_text(value)
                )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter
                    |
                    Qt.AlignmentFlag.AlignLeft
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item
                )

        if headers:

            header = (
                self.table.horizontalHeader()
            )

            header.setSectionResizeMode(
                QHeaderView.ResizeMode.Interactive
            )

            for index, header_name in enumerate(
                headers
            ):

                width = max(
                    95,
                    min(
                        210,
                        len(header_name) * 11
                    )
                )

                header.resizeSection(
                    index,
                    width
                )

            header.setStretchLastSection(
                True
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    def update_summary(
        self,
        rows,
        title,
        subtitle
    ):

        count = len(rows)

        # Filtered count
        self.filtered_value.setText(
            str(count)
        )

        # Current report
        self.report_value.setText(
            self.current_report
        )

        self.preview_title.setText(
            f"{title} Preview"
        )

        self.preview_subtitle.setText(
            f"{subtitle}  •  "
            f"{count} record"
            + (
                "s"
                if count != 1
                else ""
            )
        )

        self.result_count_label.setText(
            f"{count} record"
            + (
                "s"
                if count != 1
                else ""
            )
            + " found"
        )

        # Total count
        self.update_total_count()

    # ========================================================
    # TOTAL COUNT
    # ========================================================

    def update_total_count(self):

        try:

            counts = get_report_counts()

            mapping = {
                "Employee": "employees",
                "Attendance": "attendance",
                "Payroll": "payroll",
                "Performance": "performance",
                "Department": "departments",
                "Quality": "quality_issues",
                "Audit": "audit_logs",
            }

            key = mapping.get(
                self.current_report
            )

            total = counts.get(
                key,
                len(self.current_rows)
            )

            self.total_value.setText(
                str(total)
            )

        except Exception:

            self.total_value.setText(
                str(
                    len(
                        self.current_rows
                    )
                )
            )

    # ========================================================
    # EXPORT - EXCEL
    # ========================================================

    def export_excel(self):

        if not self.current_headers:

            self.show_info(
                "No Data",
                "There is no report data to export."
            )

            return

        try:

            filename = (
                f"{clean_filename(self.current_report)}_Report.xlsx"
            )

            path = export_to_excel(
                filename=filename,
                title=self.current_title,
                headers=self.current_headers,
                rows=[
                    [
                        safe_text(value)
                        for value in row
                    ]
                    for row in self.current_rows
                ],
            )

            self.show_success(
                "Excel Export Successful",
                f"Report created successfully.\n\n{path}"
            )

        except Exception as error:

            self.show_error(
                "Excel Export Failed",
                str(error)
            )

    # ========================================================
    # EXPORT - CSV
    # ========================================================

    def export_csv(self):

        if not self.current_headers:

            self.show_info(
                "No Data",
                "There is no report data to export."
            )

            return

        try:

            filename = (
                f"{clean_filename(self.current_report)}_Report.csv"
            )

            path = export_to_csv(
                filename,
                self.current_headers,
                [
                    [
                        safe_text(value)
                        for value in row
                    ]
                    for row in self.current_rows
                ],
            )

            self.show_success(
                "CSV Export Successful",
                f"Report created successfully.\n\n{path}"
            )

        except Exception as error:

            self.show_error(
                "CSV Export Failed",
                str(error)
            )

    # ========================================================
    # EXPORT - PDF
    # ========================================================

    def export_pdf(self):

        if not self.current_headers:

            self.show_info(
                "No Data",
                "There is no report data to export."
            )

            return

        try:

            filename = (
                f"{clean_filename(self.current_report)}_Report.pdf"
            )

            summary = [
                f"Report Type: {self.current_report}",
                f"Total Records: {len(self.current_rows)}",
            ]

            path = export_to_pdf(
                filename=filename,
                title=self.current_title,
                headers=self.current_headers,
                rows=[
                    [
                        safe_text(value)
                        for value in row
                    ]
                    for row in self.current_rows
                ],
                summary=summary,
            )

            self.show_success(
                "PDF Export Successful",
                f"Report created successfully.\n\n{path}"
            )

        except Exception as error:

            self.show_error(
                "PDF Export Failed",
                str(error)
            )

    # ========================================================
    # MESSAGE BOXES
    # ========================================================

    def show_success(
        self,
        title,
        message
    ):

        QMessageBox.information(
            self,
            title,
            message
        )

    # --------------------------------------------------------

    def show_info(
        self,
        title,
        message
    ):

        QMessageBox.information(
            self,
            title,
            message
        )

    # --------------------------------------------------------

    def show_error(
        self,
        title,
        message
    ):

        QMessageBox.critical(
            self,
            title,
            message
        )


# ============================================================
# STANDALONE RUNNER
# ============================================================

def run_reports_window():

    app = QApplication.instance()

    owns_app = (
        app is None
    )

    if owns_app:

        app = QApplication(
            sys.argv
        )

    # Fix Qt font warning:
    # QFont::setPointSize: Point size <= 0
    current_font = app.font()

    if current_font.pointSize() <= 0:

        current_font = QFont(
            "Segoe UI",
            10
        )

        app.setFont(
            current_font
        )

    window = ReportsWindow()

    window.show()

    window.raise_()

    window.activateWindow()

    if owns_app:

        return app.exec()

    return 0


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        run_reports_window()
    )