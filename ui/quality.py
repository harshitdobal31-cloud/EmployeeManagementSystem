from __future__ import annotations

import sys
from datetime import datetime, date

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.database import SessionLocal
from database.models import (
    Employee,
    User,
    Payroll,
    Attendance,
)

from services.quality_service import (
    create_quality_issue,
    get_all_quality_issues,
    search_quality_issues,
    update_quality_issue,
    delete_quality_issue,
    get_quality_statistics,
    create_improvement_action,
    get_all_improvement_actions,
    update_improvement_action,
    delete_improvement_action,
    get_improvement_statistics,
)

try:
    from utils.session import Session
except ImportError:

    class Session:
        current_user = None

        @classmethod
        def get_user(cls):
            return cls.current_user


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
# HELPER FUNCTIONS
# ============================================================

def safe_text(value):

    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime(
            "%d-%m-%Y %I:%M %p"
        )

    if isinstance(value, date):
        return value.strftime(
            "%d-%m-%Y"
        )

    return str(value)


def normalize_date(value):

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):

        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
        ]

        for fmt in formats:

            try:
                return datetime.strptime(
                    value,
                    fmt
                ).date()

            except ValueError:
                pass

    return None


def money(value):

    try:
        return f"₹ {float(value or 0):,.2f}"
    except Exception:
        return "₹ 0.00"


# ============================================================
# KPI CARD
# ============================================================

class QualityKpiCard(QFrame):

    def __init__(
        self,
        icon,
        title,
        value,
        subtitle,
        accent,
        parent=None,
    ):

        super().__init__(parent)

        self.setMinimumHeight(118)

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 15px;
            }}

            QFrame:hover {{
                background: {CARD_HOVER};
                border: 1px solid {accent};
            }}
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            15,
            13,
            15,
            13
        )

        layout.setSpacing(4)

        top = QHBoxLayout()

        icon_label = QLabel(
            icon
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setFixedSize(
            40,
            40
        )

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                background: {accent}22;
                color: {accent};
                border: 1px solid {accent}44;
                border-radius: 11px;
                font-size: 18px;
                font-weight: 900;
            }}
            """
        )

        top.addWidget(
            icon_label
        )

        top.addStretch()

        indicator = QLabel(
            "●"
        )

        indicator.setStyleSheet(
            f"""
            color: {accent};
            font-size: 8px;
            background: transparent;
            """
        )

        top.addWidget(
            indicator
        )

        layout.addLayout(
            top
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 9px;
            font-weight: 800;
            background: transparent;
            """
        )

        layout.addWidget(
            title_label
        )

        self.value_label = QLabel(
            value
        )

        self.value_label.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 21px;
            font-weight: 900;
            background: transparent;
            """
        )

        layout.addWidget(
            self.value_label
        )

        self.subtitle_label = QLabel(
            subtitle
        )

        self.subtitle_label.setStyleSheet(
            f"""
            color: {accent};
            font-size: 8px;
            font-weight: 700;
            background: transparent;
            """
        )

        layout.addWidget(
            self.subtitle_label
        )

    def set_value(
        self,
        value,
        subtitle=None
    ):

        self.value_label.setText(
            str(value)
        )

        if subtitle is not None:

            self.subtitle_label.setText(
                subtitle
            )


# ============================================================
# QUALITY ISSUE DIALOG
# ============================================================

class QualityIssueDialog(QDialog):

    def __init__(
        self,
        issue=None,
        parent=None,
    ):

        super().__init__(parent)

        self.issue = issue

        self.setWindowTitle(
            "Edit Quality Issue"
            if issue
            else "Add Quality Issue"
        )

        self.setMinimumSize(
            700,
            650
        )

        self.setModal(
            True
        )

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {BG};
            }}

            QLabel {{
                color: {TEXT2};
                background: transparent;
                font-size: 10px;
            }}

            QLineEdit,
            QTextEdit,
            QComboBox,
            QDateEdit {{
                background: {BG2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 7px;
                font-size: 10px;
            }}

            QLineEdit:focus,
            QTextEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {{
                border: 1px solid {BLUE};
            }}

            QPushButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 10px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {BLUE_LIGHT};
            }}
            """
        )

        self.build_ui()

        if issue:

            self.load_issue(
                issue
            )

    # --------------------------------------------------------

    def build_ui(self):

        main = QVBoxLayout(self)

        main.setContentsMargins(
            22,
            20,
            22,
            20
        )

        main.setSpacing(
            12
        )

        title = QLabel(
            "Quality Issue"
        )

        title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 21px;
            font-weight: 900;
            """
        )

        main.addWidget(
            title
        )

        subtitle = QLabel(
            "Record, investigate and resolve a quality problem"
        )

        subtitle.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 9px;
            """
        )

        main.addWidget(
            subtitle
        )

        form = QGridLayout()

        form.setHorizontalSpacing(
            12
        )

        form.setVerticalSpacing(
            8
        )

        # Issue ID

        self.issue_id = QLineEdit()

        self.issue_id.setPlaceholderText(
            "Example: QI-001"
        )

        form.addWidget(
            QLabel("Issue ID *"),
            0,
            0
        )

        form.addWidget(
            self.issue_id,
            0,
            1
        )

        # Title

        self.title_input = QLineEdit()

        self.title_input.setPlaceholderText(
            "Enter quality issue title"
        )

        form.addWidget(
            QLabel("Title *"),
            1,
            0
        )

        form.addWidget(
            self.title_input,
            1,
            1
        )

        # Category

        self.category = QComboBox()

        self.category.addItems(
            [
                "Payroll",
                "Attendance",
                "Data Entry",
                "Employee Records",
                "Performance",
                "System",
                "Report",
                "Other",
            ]
        )

        form.addWidget(
            QLabel("Category"),
            2,
            0
        )

        form.addWidget(
            self.category,
            2,
            1
        )

        # Priority

        self.priority = QComboBox()

        self.priority.addItems(
            [
                "Low",
                "Medium",
                "High",
                "Critical",
            ]
        )

        self.priority.setCurrentText(
            "Medium"
        )

        form.addWidget(
            QLabel("Priority"),
            3,
            0
        )

        form.addWidget(
            self.priority,
            3,
            1
        )

        # Status

        self.status = QComboBox()

        self.status.addItems(
            [
                "Open",
                "In Progress",
                "Resolved",
                "Closed",
            ]
        )

        form.addWidget(
            QLabel("Status"),
            4,
            0
        )

        form.addWidget(
            self.status,
            4,
            1
        )

        # Assigned To

        self.assigned_to = QComboBox()

        self.assigned_to.addItem(
            "Unassigned",
            None
        )

        self.load_users()

        form.addWidget(
            QLabel("Assigned To"),
            5,
            0
        )

        form.addWidget(
            self.assigned_to,
            5,
            1
        )

        # Description

        self.description = QTextEdit()

        self.description.setPlaceholderText(
            "Describe the quality problem..."
        )

        self.description.setMinimumHeight(
            80
        )

        form.addWidget(
            QLabel("Description *"),
            6,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form.addWidget(
            self.description,
            6,
            1
        )

        # Root cause

        self.root_cause = QTextEdit()

        self.root_cause.setPlaceholderText(
            "Enter root cause identified during investigation..."
        )

        self.root_cause.setMinimumHeight(
            70
        )

        form.addWidget(
            QLabel("Root Cause"),
            7,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form.addWidget(
            self.root_cause,
            7,
            1
        )

        # Corrective Action

        self.corrective_action = QTextEdit()

        self.corrective_action.setPlaceholderText(
            "Enter corrective action taken..."
        )

        self.corrective_action.setMinimumHeight(
            70
        )

        form.addWidget(
            QLabel("Corrective Action"),
            8,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form.addWidget(
            self.corrective_action,
            8,
            1
        )

        main.addLayout(
            form
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            |
            QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.validate_and_accept
        )

        buttons.rejected.connect(
            self.reject
        )

        main.addWidget(
            buttons
        )

    # --------------------------------------------------------

    def load_users(self):

        db = SessionLocal()

        try:

            users = (
                db.query(User)
                .order_by(
                    User.username.asc()
                )
                .all()
            )

            for user in users:

                self.assigned_to.addItem(
                    f"{user.username} ({user.role})",
                    user.id
                )

        finally:

            db.close()

    # --------------------------------------------------------

    def load_issue(
        self,
        issue
    ):

        self.issue_id.setText(
            safe_text(
                issue.issue_id
            )
        )

        self.issue_id.setEnabled(
            False
        )

        self.title_input.setText(
            safe_text(
                issue.title
            )
        )

        self.category.setCurrentText(
            safe_text(
                issue.category
            )
        )

        self.priority.setCurrentText(
            safe_text(
                issue.priority
            )
        )

        self.status.setCurrentText(
            safe_text(
                issue.status
            )
        )

        self.description.setPlainText(
            safe_text(
                issue.description
            )
        )

        self.root_cause.setPlainText(
            safe_text(
                issue.root_cause
            )
        )

        self.corrective_action.setPlainText(
            safe_text(
                issue.corrective_action
            )
        )

        if issue.assigned_to:

            index = self.assigned_to.findData(
                issue.assigned_to
            )

            if index >= 0:

                self.assigned_to.setCurrentIndex(
                    index
                )

    # --------------------------------------------------------

    def validate_and_accept(self):

        issue_id = (
            self.issue_id.text()
            .strip()
        )

        title = (
            self.title_input.text()
            .strip()
        )

        description = (
            self.description.toPlainText()
            .strip()
        )

        if not issue_id:

            QMessageBox.warning(
                self,
                "Validation",
                "Please enter Issue ID."
            )

            return

        if not title:

            QMessageBox.warning(
                self,
                "Validation",
                "Please enter issue title."
            )

            return

        if not description:

            QMessageBox.warning(
                self,
                "Validation",
                "Please enter issue description."
            )

            return

        self.accept()

    # --------------------------------------------------------

    def get_data(self):

        return {
            "issue_id": self.issue_id.text().strip(),
            "title": self.title_input.text().strip(),
            "description": self.description.toPlainText().strip(),
            "category": self.category.currentText(),
            "priority": self.priority.currentText(),
            "status": self.status.currentText(),
            "assigned_to": self.assigned_to.currentData(),
            "root_cause": self.root_cause.toPlainText().strip(),
            "corrective_action": self.corrective_action.toPlainText().strip(),
        }


# ============================================================
# PDCA DIALOG
# ============================================================

class ImprovementDialog(QDialog):

    def __init__(
        self,
        action=None,
        parent=None,
    ):

        super().__init__(parent)

        self.action = action

        self.setWindowTitle(
            "Edit Improvement Action"
            if action
            else "Add PDCA Improvement Action"
        )

        self.setMinimumSize(
            700,
            650
        )

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {BG};
            }}

            QLabel {{
                color: {TEXT2};
                font-size: 10px;
                background: transparent;
            }}

            QLineEdit,
            QTextEdit,
            QComboBox,
            QDateEdit {{
                background: {BG2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 7px;
                font-size: 10px;
            }}

            QLineEdit:focus,
            QTextEdit:focus,
            QComboBox:focus,
            QDateEdit:focus {{
                border-color: {BLUE};
            }}

            QPushButton {{
                background: {PURPLE};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 10px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: #B96AF9;
            }}
            """
        )

        self.build_ui()

        if action:

            self.load_action(
                action
            )

    # --------------------------------------------------------

    def build_ui(self):

        main = QVBoxLayout(self)

        main.setContentsMargins(
            22,
            20,
            22,
            20
        )

        main.setSpacing(
            10
        )

        title = QLabel(
            "PDCA Continuous Improvement"
        )

        title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 21px;
            font-weight: 900;
            """
        )

        main.addWidget(
            title
        )

        subtitle = QLabel(
            "Plan → Do → Check → Act"
        )

        subtitle.setStyleSheet(
            f"""
            color: {PURPLE};
            font-size: 10px;
            font-weight: 800;
            """
        )

        main.addWidget(
            subtitle
        )

        form = QGridLayout()

        form.setHorizontalSpacing(
            12
        )

        form.setVerticalSpacing(
            8
        )

        # Problem

        self.problem = QTextEdit()

        self.problem.setPlaceholderText(
            "What problem are we trying to improve?"
        )

        self.problem.setMinimumHeight(
            65
        )

        form.addWidget(
            QLabel("Problem *"),
            0,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form.addWidget(
            self.problem,
            0,
            1
        )

        # Root Cause

        self.root_cause = QTextEdit()

        self.root_cause.setPlaceholderText(
            "What is the root cause?"
        )

        self.root_cause.setMinimumHeight(
            65
        )

        form.addWidget(
            QLabel("Root Cause"),
            1,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form.addWidget(
            self.root_cause,
            1,
            1
        )

        # Corrective

        self.corrective = QTextEdit()

        self.corrective.setPlaceholderText(
            "What corrective action will be taken?"
        )

        self.corrective.setMinimumHeight(
            65
        )

        form.addWidget(
            QLabel("Corrective Action"),
            2,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form.addWidget(
            self.corrective,
            2,
            1
        )

        # Preventive

        self.preventive = QTextEdit()

        self.preventive.setPlaceholderText(
            "What preventive action will stop recurrence?"
        )

        self.preventive.setMinimumHeight(
            65
        )

        form.addWidget(
            QLabel("Preventive Action"),
            3,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form.addWidget(
            self.preventive,
            3,
            1
        )

        # Responsible

        self.responsible = QComboBox()

        self.responsible.addItem(
            "Unassigned",
            None
        )

        self.load_users()

        form.addWidget(
            QLabel("Responsible Person"),
            4,
            0
        )

        form.addWidget(
            self.responsible,
            4,
            1
        )

        # Priority

        self.priority = QComboBox()

        self.priority.addItems(
            [
                "Low",
                "Medium",
                "High",
                "Critical",
            ]
        )

        self.priority.setCurrentText(
            "Medium"
        )

        form.addWidget(
            QLabel("Priority"),
            5,
            0
        )

        form.addWidget(
            self.priority,
            5,
            1
        )

        # Status

        self.status = QComboBox()

        self.status.addItems(
            [
                "Planned",
                "In Progress",
                "Completed",
                "Cancelled",
            ]
        )

        form.addWidget(
            QLabel("Status"),
            6,
            0
        )

        form.addWidget(
            self.status,
            6,
            1
        )

        # PDCA Stage

        self.stage = QComboBox()

        self.stage.addItems(
            [
                "Plan",
                "Do",
                "Check",
                "Act",
            ]
        )

        form.addWidget(
            QLabel("PDCA Stage"),
            7,
            0
        )

        form.addWidget(
            self.stage,
            7,
            1
        )

        # Due Date

        self.due_date = QDateEdit()

        self.due_date.setCalendarPopup(
            True
        )

        self.due_date.setDate(
            QDate.currentDate()
        )

        self.due_date.setDisplayFormat(
            "dd-MM-yyyy"
        )

        form.addWidget(
            QLabel("Due Date"),
            8,
            0
        )

        form.addWidget(
            self.due_date,
            8,
            1
        )

        main.addLayout(
            form
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            |
            QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.validate_and_accept
        )

        buttons.rejected.connect(
            self.reject
        )

        main.addWidget(
            buttons
        )

    # --------------------------------------------------------

    def load_users(self):

        db = SessionLocal()

        try:

            users = (
                db.query(User)
                .order_by(
                    User.username.asc()
                )
                .all()
            )

            for user in users:

                self.responsible.addItem(
                    f"{user.username} ({user.role})",
                    user.id
                )

        finally:

            db.close()

    # --------------------------------------------------------

    def load_action(
        self,
        action
    ):

        self.problem.setPlainText(
            safe_text(
                action.problem
            )
        )

        self.root_cause.setPlainText(
            safe_text(
                action.root_cause
            )
        )

        self.corrective.setPlainText(
            safe_text(
                action.corrective_action
            )
        )

        self.preventive.setPlainText(
            safe_text(
                action.preventive_action
            )
        )

        self.priority.setCurrentText(
            safe_text(
                action.priority
            )
        )

        self.status.setCurrentText(
            safe_text(
                action.status
            )
        )

        self.stage.setCurrentText(
            safe_text(
                action.pdca_stage
            )
        )

        if action.responsible_person:

            index = self.responsible.findData(
                action.responsible_person
            )

            if index >= 0:

                self.responsible.setCurrentIndex(
                    index
                )

        action_date = normalize_date(
            action.due_date
        )

        if action_date:

            self.due_date.setDate(
                QDate(
                    action_date.year,
                    action_date.month,
                    action_date.day
                )
            )

    # --------------------------------------------------------

    def validate_and_accept(self):

        problem = (
            self.problem.toPlainText()
            .strip()
        )

        if not problem:

            QMessageBox.warning(
                self,
                "Validation",
                "Please enter the improvement problem."
            )

            return

        self.accept()

    # --------------------------------------------------------

    def get_data(self):

        return {
            "problem": self.problem.toPlainText().strip(),
            "root_cause": self.root_cause.toPlainText().strip(),
            "corrective_action": self.corrective.toPlainText().strip(),
            "preventive_action": self.preventive.toPlainText().strip(),
            "responsible_person": self.responsible.currentData(),
            "priority": self.priority.currentText(),
            "status": self.status.currentText(),
            "pdca_stage": self.stage.currentText(),
            "due_date": self.due_date.date().toPython(),
        }


# ============================================================
# QUALITY WINDOW
# ============================================================

class QualityWindow(QWidget):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Employee Management System | TQM Quality Management"
        )

        self.resize(
            1500,
            930
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
                background: {BG};
                border: none;
            }}

            QTableWidget {{
                background: {TABLE_BG};
                alternate-background-color: {TABLE_ALT};
                color: {TEXT2};
                border: none;
                font-size: 10px;
                selection-background-color: #173B67;
                selection-color: white;
            }}

            QHeaderView::section {{
                background: #1A3961;
                color: white;
                padding: 8px;
                border: none;
                border-bottom: 2px solid {BLUE};
                font-size: 9px;
                font-weight: 800;
            }}

            QTableWidget::item {{
                padding: 7px;
                border-bottom: 1px solid #1C3048;
            }}
            """
        )

        self.build_ui()

        self.refresh_all()

    # ========================================================
    # MAIN UI
    # ========================================================

    def build_ui(self):

        root = QWidget()

        root.setObjectName(
            "Root"
        )

        main = QVBoxLayout(root)

        main.setContentsMargins(
            15,
            15,
            15,
            20
        )

        main.setSpacing(
            12
        )

        main.addWidget(
            self.build_header()
        )

        self.tabs = QTabWidget()

        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                background: {BG};
                border-radius: 10px;
            }}

            QTabBar::tab {{
                background: {CARD};
                color: {MUTED};
                padding: 11px 24px;
                margin-right: 3px;
                border-radius: 8px;
                font-size: 10px;
                font-weight: 800;
            }}

            QTabBar::tab:selected {{
                background: {BLUE};
                color: white;
            }}

            QTabBar::tab:hover {{
                color: white;
            }}
            """
        )

        self.tabs.addTab(
            self.build_overview_tab(),
            "▦  TQM Overview"
        )

        self.tabs.addTab(
            self.build_issues_tab(),
            "⚠  Quality Issues"
        )

        self.tabs.addTab(
            self.build_pdca_tab(),
            "↻  PDCA Improvement"
        )

        main.addWidget(
            self.tabs,
            1
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setWidget(
            root
        )

        outer = QVBoxLayout(
            self
        )

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
            92
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 15px;
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

        icon = QLabel(
            "✓"
        )

        icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon.setFixedSize(
            52,
            52
        )

        icon.setStyleSheet(
            f"""
            QLabel {{
                background: {GREEN_DARK};
                color: {GREEN};
                border: 1px solid #17683D;
                border-radius: 14px;
                font-size: 26px;
                font-weight: 900;
            }}
            """
        )

        layout.addWidget(
            icon
        )

        text = QVBoxLayout()

        text.setSpacing(
            2
        )

        title = QLabel(
            "TQM Quality Management"
        )

        title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 24px;
            font-weight: 900;
            background: transparent;
            """
        )

        text.addWidget(
            title
        )

        subtitle = QLabel(
            "Quality monitoring • Issue management • Continuous improvement"
        )

        subtitle.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 10px;
            background: transparent;
            """
        )

        text.addWidget(
            subtitle
        )

        layout.addLayout(
            text
        )

        layout.addStretch()

        self.health_label = QLabel(
            "●  Quality Monitoring"
        )

        self.health_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.health_label.setFixedSize(
            145,
            42
        )

        self.health_label.setStyleSheet(
            f"""
            QLabel {{
                background: #102D21;
                color: {GREEN};
                border: 1px solid #17683D;
                border-radius: 10px;
                font-size: 9px;
                font-weight: 800;
            }}
            """
        )

        layout.addWidget(
            self.health_label
        )

        refresh = QPushButton(
            "↻  Refresh"
        )

        refresh.setFixedSize(
            105,
            42
        )

        refresh.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        refresh.clicked.connect(
            self.refresh_all
        )

        refresh.setStyleSheet(
            f"""
            QPushButton {{
                background: {BLUE};
                color: white;
                border: none;
                border-radius: 9px;
                font-size: 10px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {BLUE_LIGHT};
            }}
            """
        )

        layout.addWidget(
            refresh
        )

        return card

    # ========================================================
    # OVERVIEW TAB
    # ========================================================

    def build_overview_tab(self):

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        layout.setSpacing(
            12
        )

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        grid = QGridLayout()

        grid.setHorizontalSpacing(
            10
        )

        grid.setVerticalSpacing(
            10
        )

        self.quality_score_card = QualityKpiCard(
            "✓",
            "QUALITY SCORE",
            "0%",
            "Overall quality indicator",
            GREEN
        )

        self.payroll_accuracy_card = QualityKpiCard(
            "₹",
            "PAYROLL ACCURACY",
            "0%",
            "Processed / locked records",
            BLUE
        )

        self.attendance_accuracy_card = QualityKpiCard(
            "◷",
            "ATTENDANCE ACCURACY",
            "0%",
            "Complete attendance records",
            CYAN
        )

        self.completeness_card = QualityKpiCard(
            "▣",
            "RECORD COMPLETENESS",
            "0%",
            "Required employee data",
            PURPLE
        )

        self.pending_card = QualityKpiCard(
            "!",
            "PENDING ISSUES",
            "0",
            "Open + in progress",
            ORANGE
        )

        self.resolved_card = QualityKpiCard(
            "✓",
            "RESOLVED ISSUES",
            "0",
            "Resolved + closed",
            GREEN
        )

        cards = [
            self.quality_score_card,
            self.payroll_accuracy_card,
            self.attendance_accuracy_card,
            self.completeness_card,
            self.pending_card,
            self.resolved_card,
        ]

        for index, card in enumerate(cards):

            row = index // 3
            column = index % 3

            grid.addWidget(
                card,
                row,
                column
            )

        for column in range(3):

            grid.setColumnStretch(
                column,
                1
            )

        layout.addLayout(
            grid
        )

        # ----------------------------------------------------
        # PRIMARY QUALITY GOAL
        # ----------------------------------------------------

        goal_card = QFrame()

        goal_card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """
        )

        goal_layout = QVBoxLayout(goal_card)

        goal_layout.setContentsMargins(
            16,
            13,
            16,
            13
        )

        goal_layout.setSpacing(7)

        # Header

        goal_header = QHBoxLayout()

        goal_title = QLabel(
            "🎯  PRIMARY QUALITY GOAL"
        )

        goal_title.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 11px;
            font-weight: 900;
            background: transparent;
            """
        )

        goal_header.addWidget(goal_title)
        goal_header.addStretch()

        self.goal_status_label = QLabel(
            "Improvement Required"
        )

        self.goal_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.goal_status_label.setStyleSheet(
            f"""
            QLabel {{
                background: #3A2810;
                color: {ORANGE};
                border: 1px solid #805B18;
                border-radius: 7px;
                padding: 5px 10px;
                font-size: 9px;
                font-weight: 800;
            }}
            """
        )

        goal_header.addWidget(self.goal_status_label)
        goal_layout.addLayout(goal_header)

        # Goal name

        self.goal_name_label = QLabel(
            "Improve Usability"
        )

        self.goal_name_label.setStyleSheet(
            f"""
            color: {BLUE_LIGHT};
            font-size: 19px;
            font-weight: 900;
            background: transparent;
            """
        )

        goal_layout.addWidget(self.goal_name_label)

        # Description

        goal_description = QLabel(
            "Improve the usability, accuracy and overall quality "
            "of the Employee Management System."
        )

        goal_description.setWordWrap(True)

        goal_description.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 9px;
            background: transparent;
            """
        )

        goal_layout.addWidget(goal_description)

        # Progress information

        progress_info = QHBoxLayout()

        self.goal_current_label = QLabel(
            "Current: 0.0%"
        )

        self.goal_current_label.setStyleSheet(
            f"""
            color: {TEXT2};
            font-size: 10px;
            font-weight: 700;
            background: transparent;
            """
        )

        progress_info.addWidget(self.goal_current_label)
        progress_info.addStretch()

        self.goal_target_label = QLabel(
            "Target: 90%"
        )

        self.goal_target_label.setStyleSheet(
            f"""
            color: {GREEN};
            font-size: 10px;
            font-weight: 800;
            background: transparent;
            """
        )

        progress_info.addWidget(self.goal_target_label)
        goal_layout.addLayout(progress_info)

        # Progress bar

        self.goal_progress = QProgressBar()

        self.goal_progress.setRange(0, 100)
        self.goal_progress.setValue(0)
        self.goal_progress.setTextVisible(False)
        self.goal_progress.setFixedHeight(10)

        self.goal_progress.setStyleSheet(
            f"""
            QProgressBar {{
                background: #0B1728;
                border: 1px solid #294463;
                border-radius: 5px;
            }}

            QProgressBar::chunk {{
                background: {BLUE};
                border-radius: 4px;
            }}
            """
        )

        goal_layout.addWidget(self.goal_progress)

        # Gap to target

        self.goal_gap_label = QLabel(
            "Gap to target: 90.0%"
        )

        self.goal_gap_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 9px;
            background: transparent;
            """
        )

        goal_layout.addWidget(self.goal_gap_label)

        layout.addWidget(goal_card)

        # ----------------------------------------------------
        # LOWER SECTION
        # ----------------------------------------------------

        lower = QHBoxLayout()

        lower.setSpacing(
            12
        )

        # Issue summary

        issue_panel = self.create_panel(
            "Quality Issue Summary",
            "Current quality issue distribution"
        )

        issue_layout = QVBoxLayout()

        issue_layout.setContentsMargins(
            15,
            5,
            15,
            15
        )

        self.issue_summary_labels = {}

        issue_items = [
            ("Open", ORANGE),
            ("In Progress", BLUE),
            ("Resolved", GREEN),
            ("Closed", PURPLE),
            ("Critical", RED),
        ]

        for name, accent in issue_items:

            row = QHBoxLayout()

            label = QLabel(
                name
            )

            label.setStyleSheet(
                f"""
                color: {TEXT2};
                font-size: 10px;
                font-weight: 700;
                """
            )

            row.addWidget(
                label
            )

            row.addStretch()

            value = QLabel(
                "0"
            )

            value.setStyleSheet(
                f"""
                color: {accent};
                font-size: 17px;
                font-weight: 900;
                """
            )

            row.addWidget(
                value
            )

            issue_layout.addLayout(
                row
            )

            self.issue_summary_labels[
                name
            ] = value

        issue_panel.layout().addLayout(
            issue_layout
        )

        lower.addWidget(
            issue_panel,
            1
        )

        # PDCA summary

        pdca_panel = self.create_panel(
            "PDCA Progress",
            "Continuous improvement cycle"
        )

        pdca_layout = QVBoxLayout()

        pdca_layout.setContentsMargins(
            15,
            5,
            15,
            15
        )

        self.pdca_labels = {}

        pdca_items = [
            ("Plan", BLUE),
            ("Do", ORANGE),
            ("Check", CYAN),
            ("Act", GREEN),
        ]

        for name, accent in pdca_items:

            row = QHBoxLayout()

            circle = QLabel(
                name[0]
            )

            circle.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            circle.setFixedSize(
                28,
                28
            )

            circle.setStyleSheet(
                f"""
                QLabel {{
                    background: {accent}22;
                    color: {accent};
                    border: 1px solid {accent}55;
                    border-radius: 14px;
                    font-weight: 900;
                }}
                """
            )

            row.addWidget(
                circle
            )

            label = QLabel(
                name
            )

            label.setStyleSheet(
                f"""
                color: {TEXT2};
                font-size: 10px;
                font-weight: 700;
                """
            )

            row.addWidget(
                label
            )

            row.addStretch()

            value = QLabel(
                "0"
            )

            value.setStyleSheet(
                f"""
                color: {accent};
                font-size: 16px;
                font-weight: 900;
                """
            )

            row.addWidget(
                value
            )

            pdca_layout.addLayout(
                row
            )

            self.pdca_labels[
                name
            ] = value

        pdca_panel.layout().addLayout(
            pdca_layout
        )

        lower.addWidget(
            pdca_panel,
            1
        )

        # Recent issues

        recent_panel = self.create_panel(
            "Recent Quality Issues",
            "Latest reported quality problems"
        )

        recent_layout = QVBoxLayout()

        recent_layout.setContentsMargins(
            15,
            5,
            15,
            15
        )

        self.recent_issues_label = QLabel(
            "No quality issues recorded."
        )

        self.recent_issues_label.setWordWrap(
            True
        )

        self.recent_issues_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 10px;
            line-height: 1.5;
            """
        )

        recent_layout.addWidget(
            self.recent_issues_label
        )

        recent_panel.layout().addLayout(
            recent_layout
        )

        lower.addWidget(
            recent_panel,
            2
        )

        layout.addLayout(
            lower
        )

        # Info panel

        info = QFrame()

        info.setStyleSheet(
            f"""
            QFrame {{
                background: #0C2038;
                border: 1px solid #1C4770;
                border-radius: 11px;
            }}
            """
        )

        info_layout = QHBoxLayout(info)

        info_layout.setContentsMargins(
            15,
            11,
            15,
            11
        )

        info_icon = QLabel(
            "ⓘ"
        )

        info_icon.setStyleSheet(
            f"""
            color: {BLUE_LIGHT};
            font-size: 18px;
            font-weight: 900;
            """
        )

        info_layout.addWidget(
            info_icon
        )

        info_text = QLabel(
            "TQM uses these indicators to identify quality problems, "
            "track corrective actions and support continuous improvement."
        )

        info_text.setStyleSheet(
            f"""
            color: {TEXT2};
            font-size: 9px;
            """
        )

        info_text.setWordWrap(
            True
        )

        info_layout.addWidget(
            info_text
        )

        layout.addWidget(
            info
        )

        return page

    # ========================================================
    # ISSUE TAB
    # ========================================================

    def build_issues_tab(self):

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        layout.setSpacing(
            10
        )

        # Toolbar

        toolbar = QHBoxLayout()

        self.issue_search = QLineEdit()

        self.issue_search.setPlaceholderText(
            "Search Issue ID, title or description..."
        )

        self.issue_search.setFixedHeight(
            38
        )

        self.issue_search.setStyleSheet(
            f"""
            QLineEdit {{
                background: {CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 9px;
                padding: 0 12px;
                font-size: 10px;
            }}

            QLineEdit:focus {{
                border-color: {BLUE};
            }}
            """
        )

        self.issue_search.textChanged.connect(
            self.refresh_issue_table
        )

        toolbar.addWidget(
            self.issue_search,
            2
        )

        self.issue_status_filter = self.create_combo(
            [
                "All",
                "Open",
                "In Progress",
                "Resolved",
                "Closed",
            ]
        )

        self.issue_status_filter.setFixedWidth(
            135
        )

        self.issue_status_filter.currentIndexChanged.connect(
            self.refresh_issue_table
        )

        toolbar.addWidget(
            self.issue_status_filter
        )

        self.issue_priority_filter = self.create_combo(
            [
                "All",
                "Low",
                "Medium",
                "High",
                "Critical",
            ]
        )

        self.issue_priority_filter.setFixedWidth(
            125
        )

        self.issue_priority_filter.currentIndexChanged.connect(
            self.refresh_issue_table
        )

        toolbar.addWidget(
            self.issue_priority_filter
        )

        add_button = self.create_button(
            "+  Add Issue",
            BLUE,
            self.add_quality_issue
        )

        toolbar.addWidget(
            add_button
        )

        layout.addLayout(
            toolbar
        )

        # Table

        table_card = QFrame()

        table_card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 13px;
            }}
            """
        )

        table_layout = QVBoxLayout(
            table_card
        )

        table_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        self.issue_table = QTableWidget()

        self.issue_table.setColumnCount(
            8
        )

        self.issue_table.setHorizontalHeaderLabels(
            [
                "Issue ID",
                "Title",
                "Category",
                "Priority",
                "Status",
                "Issue Date",
                "Assigned To",
                "Actions",
            ]
        )

        self.configure_table(
            self.issue_table
        )

        table_layout.addWidget(
            self.issue_table
        )

        layout.addWidget(
            table_card,
            1
        )

        return page

    # ========================================================
    # PDCA TAB
    # ========================================================

    def build_pdca_tab(self):

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        layout.setSpacing(
            10
        )

        # PDCA cards

        cards_layout = QHBoxLayout()

        self.plan_card = self.create_pdca_card(
            "PLAN",
            "Identify problem & plan",
            BLUE
        )

        self.do_card = self.create_pdca_card(
            "DO",
            "Implement solution",
            ORANGE
        )

        self.check_card = self.create_pdca_card(
            "CHECK",
            "Measure effectiveness",
            CYAN
        )

        self.act_card = self.create_pdca_card(
            "ACT",
            "Standardize improvement",
            GREEN
        )

        cards_layout.addWidget(
            self.plan_card
        )

        cards_layout.addWidget(
            self.do_card
        )

        cards_layout.addWidget(
            self.check_card
        )

        cards_layout.addWidget(
            self.act_card
        )

        layout.addLayout(
            cards_layout
        )

        # Toolbar

        toolbar = QHBoxLayout()

        heading = QLabel(
            "Continuous Improvement Actions"
        )

        heading.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 15px;
            font-weight: 900;
            """
        )

        toolbar.addWidget(
            heading
        )

        toolbar.addStretch()

        add_button = self.create_button(
            "+  Add Improvement",
            PURPLE,
            self.add_improvement_action
        )

        toolbar.addWidget(
            add_button
        )

        layout.addLayout(
            toolbar
        )

        # Table

        table_card = QFrame()

        table_card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 13px;
            }}
            """
        )

        table_layout = QVBoxLayout(
            table_card
        )

        table_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        self.pdca_table = QTableWidget()

        self.pdca_table.setColumnCount(
            8
        )

        self.pdca_table.setHorizontalHeaderLabels(
            [
                "Problem",
                "Priority",
                "Status",
                "PDCA Stage",
                "Responsible",
                "Due Date",
                "Created",
                "Actions",
            ]
        )

        self.configure_table(
            self.pdca_table
        )

        table_layout.addWidget(
            self.pdca_table
        )

        layout.addWidget(
            table_card,
            1
        )

        return page

    # ========================================================
    # GENERIC UI HELPERS
    # ========================================================

    def create_panel(
        self,
        title,
        subtitle
    ):

        panel = QFrame()

        panel.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 13px;
            }}
            """
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        header = QVBoxLayout()

        header.setContentsMargins(
            15,
            13,
            15,
            7
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 12px;
            font-weight: 900;
            """
        )

        header.addWidget(
            title_label
        )

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 8px;
            """
        )

        header.addWidget(
            subtitle_label
        )

        layout.addLayout(
            header
        )

        return panel

    # --------------------------------------------------------

    def create_combo(
        self,
        items
    ):

        combo = QComboBox()

        combo.addItems(
            items
        )

        combo.setFixedHeight(
            36
        )

        combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0 9px;
                font-size: 9px;
            }}

            QComboBox:hover {{
                border-color: {BLUE};
            }}

            QComboBox QAbstractItemView {{
                background: {BG2};
                color: {TEXT};
                selection-background-color: {BLUE};
            }}
            """
        )

        return combo

    # --------------------------------------------------------

    def create_button(
        self,
        text,
        color,
        function
    ):

        button = QPushButton(
            text
        )

        button.setFixedHeight(
            38
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
                background: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 9px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {color};
                border: 1px solid white;
            }}
            """
        )

        return button

    # --------------------------------------------------------

    def configure_table(
        self,
        table
    ):

        table.setAlternatingRowColors(
            True
        )

        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        table.verticalHeader().setVisible(
            False
        )

        table.setShowGrid(
            False
        )

        table.verticalHeader().setDefaultSectionSize(
            42
        )

        table.horizontalHeader().setStretchLastSection(
            True
        )

    # --------------------------------------------------------

    def create_pdca_card(
        self,
        title,
        subtitle,
        accent
    ):

        card = QFrame()

        card.setMinimumHeight(
            90
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}

            QFrame:hover {{
                border-color: {accent};
            }}
            """
        )

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            14,
            12,
            14,
            12
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            color: {accent};
            font-size: 16px;
            font-weight: 900;
            """
        )

        layout.addWidget(
            title_label
        )

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setStyleSheet(
            f"""
            color: {MUTED};
            font-size: 8px;
            """
        )

        layout.addWidget(
            subtitle_label
        )

        value = QLabel(
            "0"
        )

        value.setStyleSheet(
            f"""
            color: {TEXT};
            font-size: 19px;
            font-weight: 900;
            """
        )

        layout.addWidget(
            value
        )

        card.value_label = value

        return card

    # ========================================================
    # REFRESH ALL
    # ========================================================

    def refresh_all(self):

        try:

            self.refresh_overview()

            self.refresh_issue_table()

            self.refresh_pdca_table()

            self.health_label.setText(
                "●  Quality Monitoring"
            )

        except Exception as error:

            self.health_label.setText(
                "●  Error"
            )

            QMessageBox.critical(
                self,
                "Quality Dashboard Error",
                str(error)
            )

    # ========================================================
    # OVERVIEW REFRESH
    # ========================================================

    def refresh_overview(self):

        quality_stats = (
            get_quality_statistics()
        )

        pdca_stats = (
            get_improvement_statistics()
        )

        # ----------------------------------------------------
        # Issue numbers
        # ----------------------------------------------------

        open_count = quality_stats.get(
            "open",
            0
        )

        in_progress = quality_stats.get(
            "in_progress",
            0
        )

        resolved = quality_stats.get(
            "resolved",
            0
        )

        closed = quality_stats.get(
            "closed",
            0
        )

        critical = quality_stats.get(
            "critical",
            0
        )

        pending = (
            open_count
            +
            in_progress
        )

        resolved_total = (
            resolved
            +
            closed
        )

        # ----------------------------------------------------
        # KPI cards
        # ----------------------------------------------------

        payroll_accuracy = (
            self.calculate_payroll_accuracy()
        )

        attendance_accuracy = (
            self.calculate_attendance_accuracy()
        )

        record_completeness = (
            self.calculate_record_completeness()
        )

        quality_score = (
            self.calculate_quality_score(
                payroll_accuracy,
                attendance_accuracy,
                record_completeness,
                pending,
                quality_stats.get(
                    "total",
                    0
                )
            )
        )

        self.quality_score_card.set_value(
            f"{quality_score:.1f}%",
            "Overall TQM indicator"
        )

        # ----------------------------------------------------
        # PRIMARY QUALITY GOAL
        # ----------------------------------------------------

        quality_goal_target = 90.0

        goal_progress = (
            quality_score
            / quality_goal_target
            * 100
        )

        goal_progress = max(
            0,
            min(100, goal_progress)
        )

        goal_gap = max(
            0,
            quality_goal_target - quality_score
        )

        self.goal_current_label.setText(
            f"Current: {quality_score:.1f}%"
        )

        self.goal_target_label.setText(
            f"Target: {quality_goal_target:.0f}%"
        )

        self.goal_progress.setValue(
            int(goal_progress)
        )

        self.goal_gap_label.setText(
            f"Gap to target: {goal_gap:.1f}%"
        )

        if quality_score >= quality_goal_target:

            self.goal_status_label.setText(
                "Goal Achieved"
            )

            self.goal_status_label.setStyleSheet(
                f"""
                QLabel {{
                    background: #0F3D25;
                    color: {GREEN};
                    border: 1px solid #17683D;
                    border-radius: 7px;
                    padding: 5px 10px;
                    font-size: 9px;
                    font-weight: 800;
                }}
                """
            )

        elif quality_score >= 80:

            self.goal_status_label.setText(
                "On Track"
            )

            self.goal_status_label.setStyleSheet(
                f"""
                QLabel {{
                    background: #102D21;
                    color: {GREEN};
                    border: 1px solid #17683D;
                    border-radius: 7px;
                    padding: 5px 10px;
                    font-size: 9px;
                    font-weight: 800;
                }}
                """
            )

        else:

            self.goal_status_label.setText(
                "Improvement Required"
            )

            self.goal_status_label.setStyleSheet(
                f"""
                QLabel {{
                    background: #3A2810;
                    color: {ORANGE};
                    border: 1px solid #805B18;
                    border-radius: 7px;
                    padding: 5px 10px;
                    font-size: 9px;
                    font-weight: 800;
                }}
                """
            )

        self.payroll_accuracy_card.set_value(
            f"{payroll_accuracy:.1f}%",
            "Payroll processing quality"
        )

        self.attendance_accuracy_card.set_value(
            f"{attendance_accuracy:.1f}%",
            "Attendance record completeness"
        )

        self.completeness_card.set_value(
            f"{record_completeness:.1f}%",
            "Employee information completeness"
        )

        self.pending_card.set_value(
            pending,
            "Open + in progress"
        )

        self.resolved_card.set_value(
            resolved_total,
            "Resolved + closed"
        )

        # ----------------------------------------------------
        # Issue summary
        # ----------------------------------------------------

        self.issue_summary_labels[
            "Open"
        ].setText(
            str(open_count)
        )

        self.issue_summary_labels[
            "In Progress"
        ].setText(
            str(in_progress)
        )

        self.issue_summary_labels[
            "Resolved"
        ].setText(
            str(resolved)
        )

        self.issue_summary_labels[
            "Closed"
        ].setText(
            str(closed)
        )

        self.issue_summary_labels[
            "Critical"
        ].setText(
            str(critical)
        )

        # ----------------------------------------------------
        # PDCA
        # ----------------------------------------------------

        self.pdca_labels[
            "Plan"
        ].setText(
            str(
                pdca_stats.get(
                    "plan",
                    0
                )
            )
        )

        self.pdca_labels[
            "Do"
        ].setText(
            str(
                pdca_stats.get(
                    "do",
                    0
                )
            )
        )

        self.pdca_labels[
            "Check"
        ].setText(
            str(
                pdca_stats.get(
                    "check",
                    0
                )
            )
        )

        self.pdca_labels[
            "Act"
        ].setText(
            str(
                pdca_stats.get(
                    "act",
                    0
                )
            )
        )

        # ----------------------------------------------------
        # Recent issues
        # ----------------------------------------------------

        self.update_recent_issues()

        # PDCA cards

        self.plan_card.value_label.setText(
            str(
                pdca_stats.get(
                    "plan",
                    0
                )
            )
        )

        self.do_card.value_label.setText(
            str(
                pdca_stats.get(
                    "do",
                    0
                )
            )
        )

        self.check_card.value_label.setText(
            str(
                pdca_stats.get(
                    "check",
                    0
                )
            )
        )

        self.act_card.value_label.setText(
            str(
                pdca_stats.get(
                    "act",
                    0
                )
            )
        )

    # ========================================================
    # QUALITY METRICS
    # ========================================================

    def calculate_payroll_accuracy(self):

        db = SessionLocal()

        try:

            total = (
                db.query(Payroll)
                .count()
            )

            if total == 0:
                return 100.0

            valid = (
                db.query(Payroll)
                .filter(
                    Payroll.status.in_(
                        [
                            "Processed",
                            "Locked",
                        ]
                    )
                )
                .count()
            )

            return (
                valid
                /
                total
                *
                100
            )

        finally:

            db.close()

    # --------------------------------------------------------

    def calculate_attendance_accuracy(self):

        db = SessionLocal()

        try:

            total = (
                db.query(Attendance)
                .count()
            )

            if total == 0:
                return 100.0

            complete = (
                db.query(Attendance)
                .filter(
                    Attendance.status.isnot(None)
                )
                .filter(
                    Attendance.attendance_date.isnot(None)
                )
                .count()
            )

            return (
                complete
                /
                total
                *
                100
            )

        finally:

            db.close()

    # --------------------------------------------------------

    def calculate_record_completeness(self):

        db = SessionLocal()

        try:

            employees = (
                db.query(Employee)
                .all()
            )

            if not employees:
                return 100.0

            total_fields = (
                len(employees)
                *
                7
            )

            completed_fields = 0

            for employee in employees:

                fields = [
                    employee.employee_id,
                    employee.full_name,
                    employee.email,
                    employee.phone,
                    employee.department,
                    employee.designation,
                    employee.joining_date,
                ]

                completed_fields += sum(
                    1
                    for value in fields
                    if value not in (
                        None,
                        "",
                    )
                )

            return (
                completed_fields
                /
                total_fields
                *
                100
            )

        finally:

            db.close()

    # --------------------------------------------------------

    def calculate_quality_score(
        self,
        payroll,
        attendance,
        completeness,
        pending,
        total_issues
    ):

        base_score = (
            payroll
            +
            attendance
            +
            completeness
        ) / 3

        if total_issues > 0:

            issue_penalty = min(
                20,
                (
                    pending
                    /
                    total_issues
                )
                *
                20
            )

        else:

            issue_penalty = 0

        return max(
            0,
            min(
                100,
                base_score - issue_penalty
            )
        )

    # ========================================================
    # RECENT ISSUES
    # ========================================================

    def update_recent_issues(self):

        issues = (
            get_all_quality_issues()
        )

        if not issues:

            self.recent_issues_label.setText(
                "No quality issues recorded."
            )

            return

        lines = []

        for issue in issues[:5]:

            priority = safe_text(
                issue.priority
            )

            status = safe_text(
                issue.status
            )

            lines.append(
                f"• {safe_text(issue.issue_id)}  |  "
                f"{safe_text(issue.title)}  |  "
                f"{priority}  |  {status}"
            )

        self.recent_issues_label.setText(
            "\n".join(lines)
        )

    # ========================================================
    # ISSUE TABLE
    # ========================================================

    def refresh_issue_table(self):

        try:

            keyword = (
                self.issue_search.text().strip()
            )

            status = (
                self.issue_status_filter.currentText()
            )

            priority = (
                self.issue_priority_filter.currentText()
            )

            issues = search_quality_issues(
                keyword=keyword,
                status=status,
                priority=priority,
                category="All",
            )

            self.issue_table.setRowCount(
                len(issues)
            )

            for row, issue in enumerate(
                issues
            ):

                values = [
                    issue.issue_id,
                    issue.title,
                    issue.category,
                    issue.priority,
                    issue.status,
                    issue.issue_date,
                    self.get_user_name(
                        issue.assigned_to
                    ),
                ]

                for column, value in enumerate(
                    values
                ):

                    item = QTableWidgetItem(
                        safe_text(value)
                    )

                    item.setToolTip(
                        safe_text(value)
                    )

                    self.issue_table.setItem(
                        row,
                        column,
                        item
                    )

                self.add_issue_actions(
                    row,
                    issue
                )

            self.issue_table.resizeColumnsToContents()

            self.issue_table.setColumnWidth(
                0,
                90
            )

            self.issue_table.setColumnWidth(
                1,
                230
            )

            self.issue_table.setColumnWidth(
                2,
                120
            )

            self.issue_table.setColumnWidth(
                3,
                95
            )

            self.issue_table.setColumnWidth(
                4,
                110
            )

            self.issue_table.setColumnWidth(
                5,
                115
            )

            self.issue_table.setColumnWidth(
                6,
                130
            )

            self.issue_table.setColumnWidth(
                7,
                150
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Quality Issues Error",
                str(error)
            )

    # ========================================================
    # ISSUE ACTION BUTTONS
    # ========================================================

    def add_issue_actions(
        self,
        row,
        issue
    ):

        widget = QWidget()

        layout = QHBoxLayout(widget)

        layout.setContentsMargins(
            4,
            2,
            4,
            2
        )

        layout.setSpacing(
            4
        )

        edit = QPushButton(
            "Edit"
        )

        edit.setFixedHeight(
            28
        )

        edit.clicked.connect(
            lambda checked=False, x=issue:
            self.edit_quality_issue(x)
        )

        edit.setStyleSheet(
            f"""
            QPushButton {{
                background: {BLUE}22;
                color: {BLUE_LIGHT};
                border: 1px solid {BLUE}44;
                border-radius: 6px;
                font-size: 8px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {BLUE};
                color: white;
            }}
            """
        )

        delete = QPushButton(
            "Delete"
        )

        delete.setFixedHeight(
            28
        )

        delete.clicked.connect(
            lambda checked=False, x=issue:
            self.delete_quality_issue(x)
        )

        delete.setStyleSheet(
            f"""
            QPushButton {{
                background: {RED}22;
                color: {RED};
                border: 1px solid {RED}44;
                border-radius: 6px;
                font-size: 8px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {RED};
                color: white;
            }}
            """
        )

        layout.addWidget(
            edit
        )

        layout.addWidget(
            delete
        )

        self.issue_table.setCellWidget(
            row,
            7,
            widget
        )

    # ========================================================
    # ADD ISSUE
    # ========================================================

    def add_quality_issue(self):

        dialog = QualityIssueDialog(
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        user = self.get_current_user()

        if not user:

            QMessageBox.warning(
                self,
                "Login Required",
                "Please login before creating a quality issue."
            )

            return

        try:

            create_quality_issue(
                issue_id=data["issue_id"],
                title=data["title"],
                description=data["description"],
                category=data["category"],
                priority=data["priority"],
                reported_by=user.id,
                assigned_to=data["assigned_to"],
                issue_date=datetime.now(),
            )

            QMessageBox.information(
                self,
                "Success",
                "Quality issue created successfully."
            )

            self.refresh_all()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unable to Create Issue",
                str(error)
            )

    # ========================================================
    # EDIT ISSUE
    # ========================================================

    def edit_quality_issue(
        self,
        issue
    ):

        dialog = QualityIssueDialog(
            issue=issue,
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:

            update_quality_issue(
                issue_id=issue.id,
                title=data["title"],
                description=data["description"],
                category=data["category"],
                priority=data["priority"],
                assigned_to=data["assigned_to"],
                status=data["status"],
                root_cause=data["root_cause"],
                corrective_action=data["corrective_action"],
            )

            QMessageBox.information(
                self,
                "Success",
                "Quality issue updated successfully."
            )

            self.refresh_all()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unable to Update Issue",
                str(error)
            )

    # ========================================================
    # DELETE ISSUE
    # ========================================================

    def delete_quality_issue(
        self,
        issue
    ):

        answer = QMessageBox.question(
            self,
            "Delete Quality Issue",
            f"Are you sure you want to delete\n\n"
            f"{issue.issue_id} - {issue.title}?",
            QMessageBox.StandardButton.Yes
            |
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            delete_quality_issue(
                issue.id
            )

            QMessageBox.information(
                self,
                "Deleted",
                "Quality issue deleted successfully."
            )

            self.refresh_all()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Delete Failed",
                str(error)
            )

    # ========================================================
    # PDCA TABLE
    # ========================================================

    def refresh_pdca_table(self):

        try:

            actions = (
                get_all_improvement_actions()
            )

            self.pdca_table.setRowCount(
                len(actions)
            )

            for row, action in enumerate(
                actions
            ):

                values = [
                    action.problem,
                    action.priority,
                    action.status,
                    action.pdca_stage,
                    self.get_user_name(
                        action.responsible_person
                    ),
                    action.due_date,
                    action.created_at,
                ]

                for column, value in enumerate(
                    values
                ):

                    item = QTableWidgetItem(
                        safe_text(value)
                    )

                    item.setToolTip(
                        safe_text(value)
                    )

                    self.pdca_table.setItem(
                        row,
                        column,
                        item
                    )

                self.add_pdca_actions(
                    row,
                    action
                )

            self.pdca_table.resizeColumnsToContents()

            self.pdca_table.setColumnWidth(
                0,
                280
            )

            self.pdca_table.setColumnWidth(
                1,
                90
            )

            self.pdca_table.setColumnWidth(
                2,
                110
            )

            self.pdca_table.setColumnWidth(
                3,
                100
            )

            self.pdca_table.setColumnWidth(
                4,
                130
            )

            self.pdca_table.setColumnWidth(
                5,
                110
            )

            self.pdca_table.setColumnWidth(
                6,
                130
            )

            self.pdca_table.setColumnWidth(
                7,
                150
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "PDCA Error",
                str(error)
            )

    # ========================================================
    # PDCA ACTIONS
    # ========================================================

    def add_pdca_actions(
        self,
        row,
        action
    ):

        widget = QWidget()

        layout = QHBoxLayout(widget)

        layout.setContentsMargins(
            4,
            2,
            4,
            2
        )

        layout.setSpacing(
            4
        )

        edit = QPushButton(
            "Edit"
        )

        edit.setFixedHeight(
            28
        )

        edit.clicked.connect(
            lambda checked=False, x=action:
            self.edit_improvement_action(x)
        )

        edit.setStyleSheet(
            f"""
            QPushButton {{
                background: {PURPLE}22;
                color: {PURPLE};
                border: 1px solid {PURPLE}44;
                border-radius: 6px;
                font-size: 8px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {PURPLE};
                color: white;
            }}
            """
        )

        delete = QPushButton(
            "Delete"
        )

        delete.setFixedHeight(
            28
        )

        delete.clicked.connect(
            lambda checked=False, x=action:
            self.delete_improvement_action(x)
        )

        delete.setStyleSheet(
            f"""
            QPushButton {{
                background: {RED}22;
                color: {RED};
                border: 1px solid {RED}44;
                border-radius: 6px;
                font-size: 8px;
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: {RED};
                color: white;
            }}
            """
        )

        layout.addWidget(
            edit
        )

        layout.addWidget(
            delete
        )

        self.pdca_table.setCellWidget(
            row,
            7,
            widget
        )

    # ========================================================
    # ADD PDCA
    # ========================================================

    def add_improvement_action(self):

        dialog = ImprovementDialog(
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:

            create_improvement_action(
                problem=data["problem"],
                root_cause=data["root_cause"],
                corrective_action=data["corrective_action"],
                preventive_action=data["preventive_action"],
                responsible_person=data["responsible_person"],
                priority=data["priority"],
                status=data["status"],
                due_date=data["due_date"],
                pdca_stage=data["pdca_stage"],
            )

            QMessageBox.information(
                self,
                "Success",
                "PDCA improvement action created successfully."
            )

            self.refresh_all()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unable to Create Improvement",
                str(error)
            )

    # ========================================================
    # EDIT PDCA
    # ========================================================

    def edit_improvement_action(
        self,
        action
    ):

        dialog = ImprovementDialog(
            action=action,
            parent=self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:

            update_improvement_action(
                action_id=action.id,
                problem=data["problem"],
                root_cause=data["root_cause"],
                corrective_action=data["corrective_action"],
                preventive_action=data["preventive_action"],
                responsible_person=data["responsible_person"],
                priority=data["priority"],
                status=data["status"],
                due_date=data["due_date"],
                pdca_stage=data["pdca_stage"],
            )

            QMessageBox.information(
                self,
                "Success",
                "PDCA improvement action updated successfully."
            )

            self.refresh_all()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unable to Update Improvement",
                str(error)
            )

    # ========================================================
    # DELETE PDCA
    # ========================================================

    def delete_improvement_action(
        self,
        action
    ):

        answer = QMessageBox.question(
            self,
            "Delete Improvement Action",
            "Are you sure you want to delete this improvement action?",
            QMessageBox.StandardButton.Yes
            |
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            delete_improvement_action(
                action.id
            )

            QMessageBox.information(
                self,
                "Deleted",
                "Improvement action deleted successfully."
            )

            self.refresh_all()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Delete Failed",
                str(error)
            )

    # ========================================================
    # USER HELPERS
    # ========================================================

    def get_current_user(self):

        try:

            user = Session.get_user()

            return user

        except Exception:

            return None

    # --------------------------------------------------------

    def get_user_name(
        self,
        user_id
    ):

        if not user_id:
            return "Unassigned"

        db = SessionLocal()

        try:

            user = (
                db.query(User)
                .filter(
                    User.id == user_id
                )
                .first()
            )

            if user:

                return user.username

            return "Unknown"

        finally:

            db.close()


# ============================================================
# STANDALONE RUNNER
# ============================================================

def run_quality_window():

    app = QApplication.instance()

    owns_app = (
        app is None
    )

    if owns_app:

        app = QApplication(
            sys.argv
        )

    # Avoid Qt invalid font warning
    font = app.font()

    if font.pointSize() <= 0:

        app.setFont(
            QFont(
                "Segoe UI",
                10
            )
        )

    window = QualityWindow()

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
        run_quality_window()
    )