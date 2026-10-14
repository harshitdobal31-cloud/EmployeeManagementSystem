# ============================================================
# EMPLOYEE MANAGEMENT SYSTEM
# PROFESSIONAL DASHBOARD
# ============================================================

import importlib

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QGraphicsOpacityEffect,
)

from utils.session import Session

from utils.theme_manager import (
    get_current_theme,
    get_theme_data,
)

from services.employee_service import get_all_employees
from services.attendance_service import get_attendance_statistics
from services.payroll_service import get_payroll_summary
from services.performance_service import get_performance_summary


# ============================================================
# COLORS
# ============================================================

NAVY = "#0F172A"
NAVY_LIGHT = "#172554"
BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
BLUE_LIGHT = "#DBEAFE"

WHITE = "#FFFFFF"
BACKGROUND = "#F5F7FB"
CARD = "#FFFFFF"

TEXT = "#0F172A"
TEXT_SECONDARY = "#64748B"
BORDER = "#E2E8F0"

GREEN = "#16A34A"
GREEN_LIGHT = "#DCFCE7"

ORANGE = "#EA580C"
ORANGE_LIGHT = "#FFEDD5"

PURPLE = "#7C3AED"
PURPLE_LIGHT = "#EDE9FE"

RED = "#DC2626"
RED_LIGHT = "#FEE2E2"

CYAN = "#0891B2"
CYAN_LIGHT = "#CFFAFE"


# ============================================================
# THEME MANAGER INTEGRATION
# ============================================================

def _hex_to_rgb(value):
    """Convert #RRGGBB to RGB safely."""
    try:
        value = str(value).strip().lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        if len(value) != 6:
            return None
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return None


def _relative_luminance(value):
    """Return relative luminance for a hex color."""
    rgb = _hex_to_rgb(value)
    if rgb is None:
        return 0.5

    channels = []
    for channel in rgb:
        c = channel / 255.0
        channels.append(
            c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        )

    return (
        0.2126 * channels[0]
        + 0.7152 * channels[1]
        + 0.0722 * channels[2]
    )


def _contrast_ratio(first, second):
    """Calculate WCAG contrast ratio between two colors."""
    l1 = _relative_luminance(first)
    l2 = _relative_luminance(second)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _visible_text_color(background, preferred, light="#F8FAFC", dark="#0F172A"):
    """Keep text readable even when a theme provides a low-contrast color."""
    if _contrast_ratio(background, preferred) >= 4.5:
        return preferred

    # Pick the readable side for the actual background.
    if _relative_luminance(background) > 0.45:
        return dark

    return light


def _visible_secondary_color(background, preferred, light="#CBD5E1", dark="#64748B"):
    """Readable secondary text for the current surface."""
    if _contrast_ratio(background, preferred) >= 3.0:
        return preferred

    if _relative_luminance(background) > 0.45:
        return dark

    return light


def apply_dashboard_theme_colors():
    """
    Load Dashboard colors from the central Theme Manager.

    The Dashboard design and functionality remain unchanged.
    Only the color values are loaded dynamically.
    """

    global NAVY
    global NAVY_LIGHT
    global BLUE
    global BLUE_DARK
    global BLUE_LIGHT
    global WHITE
    global BACKGROUND
    global CARD
    global TEXT
    global TEXT_SECONDARY
    global BORDER
    global GREEN
    global GREEN_LIGHT
    global ORANGE
    global ORANGE_LIGHT
    global PURPLE
    global PURPLE_LIGHT
    global RED
    global RED_LIGHT
    global CYAN
    global CYAN_LIGHT

    try:

        theme_name = get_current_theme()
        theme = get_theme_data(theme_name) or {}

        NAVY = theme.get(
            "sidebar",
            theme.get("sidebar_background", NAVY)
        )

        NAVY_LIGHT = theme.get(
            "sidebar_hover",
            theme.get("surface_alt", NAVY_LIGHT)
        )

        BLUE = theme.get(
            "accent",
            theme.get("primary", BLUE)
        )

        BLUE_DARK = theme.get(
            "accent_hover",
            theme.get("primary_hover", BLUE_DARK)
        )

        BLUE_LIGHT = theme.get(
            "accent_light",
            theme.get("primary_light", BLUE_LIGHT)
        )

        BACKGROUND = theme.get(
            "background",
            theme.get("bg", BACKGROUND)
        )

        WHITE = theme.get(
            "surface",
            theme.get("card", WHITE)
        )

        CARD = theme.get(
            "card",
            theme.get("surface", CARD)
        )

        TEXT = theme.get(
            "text",
            theme.get("text_primary", TEXT)
        )

        TEXT_SECONDARY = theme.get(
            "muted",
            theme.get("text_secondary", TEXT_SECONDARY)
        )

        BORDER = theme.get(
            "border",
            BORDER
        )

        GREEN = theme.get(
            "success",
            GREEN
        )

        GREEN_LIGHT = theme.get(
            "success_light",
            theme.get("success_soft", GREEN_LIGHT)
        )

        ORANGE = theme.get(
            "warning",
            ORANGE
        )

        ORANGE_LIGHT = theme.get(
            "warning_light",
            theme.get("warning_soft", ORANGE_LIGHT)
        )

        PURPLE = theme.get(
            "info",
            theme.get("secondary", PURPLE)
        )

        PURPLE_LIGHT = theme.get(
            "info_light",
            theme.get("secondary_light", PURPLE_LIGHT)
        )

        RED = theme.get(
            "danger",
            theme.get("error", RED)
        )

        RED_LIGHT = theme.get(
            "danger_light",
            theme.get("error_light", RED_LIGHT)
        )

        CYAN = theme.get(
            "info",
            CYAN
        )

        CYAN_LIGHT = theme.get(
            "info_light",
            CYAN_LIGHT
        )

        # ----------------------------------------------------
        # CONTRAST SAFETY
        # ----------------------------------------------------
        # Some themes use light text values. The Dashboard also
        # contains light cards in several original widgets. Make
        # sure the text remains readable on those surfaces.
        TEXT = _visible_text_color(
            CARD,
            TEXT
        )

        TEXT_SECONDARY = _visible_secondary_color(
            CARD,
            TEXT_SECONDARY
        )

        # The main content background can be different from cards.
        # Keep the same theme text readable there as well.
        if _contrast_ratio(BACKGROUND, TEXT) < 4.5:
            TEXT = _visible_text_color(
                BACKGROUND,
                TEXT
            )

        if _contrast_ratio(BACKGROUND, TEXT_SECONDARY) < 3.0:
            TEXT_SECONDARY = _visible_secondary_color(
                BACKGROUND,
                TEXT_SECONDARY
            )

        print(
            f"Dashboard theme loaded: {theme_name}"
        )

    except Exception as error:

        print(
            "Dashboard theme loading error:",
            error
        )


# ============================================================
# ANIMATED BUTTON
# ============================================================

class DashboardButton(QPushButton):

    def __init__(
        self,
        icon_text,
        title,
        subtitle="",
        parent=None
    ):

        super().__init__(parent)

        self.icon_text = icon_text
        self.title_text = title
        self.subtitle_text = subtitle

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setMinimumHeight(76)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.setup_ui()

    def setup_ui(self):

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            14,
            10,
            14,
            10
        )

        layout.setSpacing(14)

        # ----------------------------------------------------
        # ICON
        # ----------------------------------------------------

        icon_frame = QFrame()

        icon_frame.setFixedSize(
            48,
            48
        )

        icon_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {BLUE_LIGHT};
                border-radius: 12px;
            }}
            """
        )

        icon_layout = QVBoxLayout(
            icon_frame
        )

        icon_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        icon_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label = QLabel(
            self.icon_text
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                color: {BLUE};
                background: transparent;
                font-size: 20px;
                font-weight: 700;
            }}
            """
        )

        icon_layout.addWidget(
            icon_label
        )

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            3
        )

        title_label = QLabel(
            self.title_text
        )

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                font-size: 14px;
                font-weight: 700;
            }}
            """

        )

        text_layout.addWidget(
            title_label
        )

        if self.subtitle_text:

            subtitle_label = QLabel(
                self.subtitle_text
            )

            subtitle_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_SECONDARY};
                    background: transparent;
                    font-size: 12px;
                }}
                """
            )

            text_layout.addWidget(
                subtitle_label
            )

        # ----------------------------------------------------
        # ARROW
        # ----------------------------------------------------

        arrow = QLabel(
            "›"
        )

        arrow.setStyleSheet(
            f"""
            QLabel {{
                color: #94A3B8;
                background: transparent;
                font-size: 28px;
                font-weight: 400;
            }}
            """
        )

        arrow.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            icon_frame
        )

        layout.addLayout(
            text_layout
        )

        layout.addStretch()

        layout.addWidget(
            arrow
        )

        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
                text-align: left;
            }}

            QPushButton:hover {{
                background: {BLUE_LIGHT};
                border: 1px solid {BLUE};
            }}

            QPushButton:pressed {{
                background: {BLUE_LIGHT};
            }}
            """
        )


# ============================================================
# STAT CARD
# ============================================================

class StatCard(QFrame):

    def __init__(
        self,
        title,
        value,
        subtitle,
        icon,
        icon_background=BLUE_LIGHT,
        icon_color=BLUE,
        parent=None
    ):

        super().__init__(parent)

        self.setMinimumHeight(
            145
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}

            QFrame:hover {{
                border: 1px solid #C7D7F5;
            }}
            """
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            16
        )

        layout.setSpacing(
            7
        )

        # ----------------------------------------------------
        # TOP
        # ----------------------------------------------------

        top_layout = QHBoxLayout()

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: 600;
            }}
            """
        )

        top_layout.addWidget(
            title_label
        )

        top_layout.addStretch()

        icon_frame = QFrame()

        icon_frame.setFixedSize(
            42,
            42
        )

        icon_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {icon_background};
                border: none;
                border-radius: 12px;
            }}
            """
        )

        icon_layout = QVBoxLayout(
            icon_frame
        )

        icon_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        icon_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label = QLabel(
            icon
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setStyleSheet(
            f"""
            QLabel {{
                color: {icon_color};
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: 700;
            }}
            """
        )

        icon_layout.addWidget(
            icon_label
        )

        top_layout.addWidget(
            icon_frame
        )

        layout.addLayout(
            top_layout
        )

        # ----------------------------------------------------
        # VALUE
        # ----------------------------------------------------

        self.value_label = QLabel(
            value
        )

        self.value_label.setFont(
            QFont(
                "Segoe UI",
                25,
                QFont.Weight.Bold
            )
        )

        self.value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                border: none;
            }}
            """
        )

        layout.addWidget(
            self.value_label
        )

        # ----------------------------------------------------
        # SUBTITLE
        # ----------------------------------------------------

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setStyleSheet(
            f"""
            QLabel {{
                color: {icon_color};
                background: transparent;
                border: none;
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )

        layout.addWidget(
            subtitle_label
        )

    def set_value(
        self,
        value
    ):

        self.value_label.setText(
            str(value)
        )


# ============================================================
# SYSTEM STATUS ITEM
# ============================================================

class StatusItem(QFrame):

    def __init__(
        self,
        title,
        subtitle,
        parent=None
    ):

        super().__init__(parent)

        self.setMinimumHeight(
            58
        )

        self.setStyleSheet(
            """
            QFrame {
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }
            """
        )

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            12,
            8,
            12,
            8
        )

        layout.setSpacing(
            10
        )

        dot = QLabel(
            "●"
        )

        dot.setStyleSheet(
            f"""
            QLabel {{
                color: {GREEN};
                background: transparent;
                border: none;
                font-size: 11px;
            }}
            """
        )

        layout.addWidget(
            dot
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            1
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 10px;
            }}
            """
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            subtitle_label
        )

        layout.addLayout(
            text_layout
        )

        layout.addStretch()


# ============================================================
# DASHBOARD WINDOW
# ============================================================

class DashboardWindow(QWidget):

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # WINDOW REFERENCES
        # ----------------------------------------------------

        self.employee_window = None
        self.attendance_window = None
        self.payroll_window = None
        self.performance_window = None
        self.calendar_window = None
        self.settings_window = None
        self.reports_window = None
        self.quality_window = None

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.setWindowTitle(
            "Employee Management System"
        )

        self.setMinimumSize(
            1250,
            760
        )

        self.resize(
            1450,
            850
        )

        # Load the saved Theme Manager colors BEFORE creating widgets.
        apply_dashboard_theme_colors()

        self.setup_ui()

        self.load_dashboard_data()

        QTimer.singleShot(
            120,
            self.start_welcome_animation
        )

    # ========================================================
    # MAIN UI
    # ========================================================

    def _clear_main_layout(self, layout):
        """Safely remove the current Dashboard widgets from the existing layout."""

        while layout.count():

            item = layout.takeAt(0)
            widget = item.widget()

            if widget is not None:

                widget.setParent(None)
                widget.deleteLater()

            child_layout = item.layout()

            if child_layout is not None:

                self._clear_main_layout(child_layout)

    def refresh_theme(self):
        """
        Rebuild the SAME Dashboard using the newly selected Theme Manager colors.

        This method deliberately does not use changeEvent()/StyleChange.
        Settings calls it explicitly after the user applies a theme, which avoids
        the QLayout and QPropertyAnimation warnings caused by automatic rebuilds.
        """

        try:

            # Stop the old animation before deleting its target widget.
            if hasattr(self, "welcome_animation"):

                try:
                    self.welcome_animation.stop()
                except Exception:
                    pass

                self.welcome_animation = None

            # Remove the old graphics effect before the old card is deleted.
            if hasattr(self, "welcome_card") and self.welcome_card is not None:

                try:
                    self.welcome_card.setGraphicsEffect(None)
                except Exception:
                    pass

            # Load the newly selected colors.
            apply_dashboard_theme_colors()

            # Reuse the existing QWidget layout instead of creating a second
            # layout on the DashboardWindow.
            main_layout = self.layout()

            if main_layout is None:

                self.setup_ui()

            else:

                self._clear_main_layout(main_layout)

                self.setup_ui()

            # Refresh the dashboard values exactly as before.
            self.load_dashboard_data()

            # Start animation only after the new welcome card exists.
            QTimer.singleShot(120, self.start_welcome_animation)

            print("Dashboard theme refreshed successfully!")

        except Exception as error:

            print(
                "Dashboard theme refresh error:",
                error
            )

    def setup_ui(self):

        # Reuse the existing layout during a theme refresh.
        main_layout = self.layout()

        if main_layout is None:

            main_layout = QHBoxLayout(
                self
            )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        sidebar = QFrame()

        sidebar.setFixedWidth(
            285
        )

        sidebar.setStyleSheet(
            f"""
            QFrame {{
                background: {NAVY};
                border: none;
            }}
            """
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            18,
            20,
            18,
            18
        )

        sidebar_layout.setSpacing(
            8
        )

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        logo_layout = QHBoxLayout()

        logo_frame = QFrame()

        logo_frame.setFixedSize(
            60,
            60
        )

        logo_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {BLUE};
                border-radius: 17px;
            }}
            """
        )

        logo_inner = QVBoxLayout(
            logo_frame
        )

        logo_inner.setContentsMargins(
            0,
            0,
            0,
            0
        )

        logo_label = QLabel(
            "EMS"
        )

        logo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
                font-size: 19px;
                font-weight: 800;
            }
            """
        )

        logo_inner.addWidget(
            logo_label
        )

        logo_text_layout = QVBoxLayout()

        logo_title = QLabel(
            "Employee"
        )

        logo_title.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
                border: none;
                font-size: 16px;
                font-weight: 800;
            }
            """
        )

        logo_subtitle = QLabel(
            "Management System"
        )

        logo_subtitle.setStyleSheet(
            """
            QLabel {
                color: #94A3B8;
                background: transparent;
                border: none;
                font-size: 10px;
            }
            """
        )

        logo_text_layout.addWidget(
            logo_title
        )

        logo_text_layout.addWidget(
            logo_subtitle
        )

        logo_layout.addWidget(
            logo_frame
        )

        logo_layout.addSpacing(
            10
        )

        logo_layout.addLayout(
            logo_text_layout
        )

        sidebar_layout.addLayout(
            logo_layout
        )

        sidebar_layout.addSpacing(
            20
        )

        # ----------------------------------------------------
        # MENU TITLE
        # ----------------------------------------------------

        menu_title = QLabel(
            "MAIN MENU"
        )

        menu_title.setStyleSheet(
            f"""
            QLabel {{
                color: {BLUE_LIGHT};
                background: {NAVY_LIGHT};
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 10px;
                font-weight: 800;
            }}
            """
        )

        sidebar_layout.addWidget(
            menu_title
        )

        sidebar_layout.addSpacing(
            5
        )

        # ----------------------------------------------------
        # SIDEBAR BUTTONS
        # ----------------------------------------------------

        dashboard_button = self.create_sidebar_button(
            "⌂",
            "Dashboard",
            active=True
        )

        dashboard_button.clicked.connect(
            self.scroll_to_top
        )

        sidebar_layout.addWidget(
            dashboard_button
        )

        calendar_button = self.create_sidebar_button(
            "□",
            "Calendar"
        )

        calendar_button.clicked.connect(
            self.open_calendar
        )

        sidebar_layout.addWidget(
            calendar_button
        )

        employee_button = self.create_sidebar_button(
            "♙",
            "Employees"
        )

        employee_button.clicked.connect(
            self.open_employee_management
        )

        sidebar_layout.addWidget(
            employee_button
        )

        attendance_button = self.create_sidebar_button(
            "◷",
            "Attendance"
        )

        attendance_button.clicked.connect(
            self.open_attendance
        )

        sidebar_layout.addWidget(
            attendance_button
        )

        payroll_button = self.create_sidebar_button(
            "₹",
            "Payroll"
        )

        payroll_button.clicked.connect(
            self.open_payroll
        )

        sidebar_layout.addWidget(
            payroll_button
        )

        performance_button = self.create_sidebar_button(
            "★",
            "Performance"
        )

        performance_button.clicked.connect(
            self.open_performance
        )

        sidebar_layout.addWidget(
            performance_button
        )

        reports_button = self.create_sidebar_button(
            "▤",
            "Reports"
        )

        reports_button.clicked.connect(
            self.open_reports
        )

        sidebar_layout.addWidget(
            reports_button
        )

        quality_button = self.create_sidebar_button(
            "◆",
            "Quality Management"
        )

        quality_button.clicked.connect(
            self.open_quality
        )

        sidebar_layout.addWidget(
            quality_button
        )

        sidebar_layout.addStretch()

        # ----------------------------------------------------
        # SYSTEM
        # ----------------------------------------------------

        system_title = QLabel(
            "SYSTEM"
        )

        system_title.setStyleSheet(
            f"""
            QLabel {{
                color: {BLUE_LIGHT};
                background: {NAVY_LIGHT};
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 10px;
                font-weight: 800;
            }}
            """
        )

        sidebar_layout.addWidget(
            system_title
        )

        settings_button = self.create_sidebar_button(
            "⚙",
            "Settings"
        )

        settings_button.clicked.connect(
            self.open_settings
        )

        sidebar_layout.addWidget(
            settings_button
        )

        logout_button = self.create_sidebar_button(
            "⇥",
            "Logout",
            logout=True
        )

        logout_button.clicked.connect(
            self.logout
        )

        sidebar_layout.addWidget(
            logout_button
        )

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = QLabel(
            "Employee Management System\nVersion 1.0"
        )

        footer.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        footer.setStyleSheet(
            """
            QLabel {
                color: #64748B;
                background: transparent;
                border: none;
                font-size: 9px;
                padding-top: 10px;
            }
            """
        )

        sidebar_layout.addWidget(
            footer
        )

        main_layout.addWidget(
            sidebar
        )

        # ====================================================
        # CONTENT AREA
        # ====================================================

        content_background = QWidget()

        content_background.setStyleSheet(
            f"""
            QWidget {{
                background: {BACKGROUND};
            }}
            """
        )

        content_layout = QVBoxLayout(
            content_background
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # ----------------------------------------------------
        # SCROLL AREA
        # ----------------------------------------------------

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: {BLUE_LIGHT};
                width: 10px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: {TEXT_SECONDARY};
                border-radius: 5px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background: {TEXT_SECONDARY};
            }
            """
        )

        scroll_content = QWidget()

        scroll_content.setStyleSheet(
            f"""
            QWidget {{
                background: {BACKGROUND};
            }}
            """
        )

        self.content_widget = scroll_content

        content_main_layout = QVBoxLayout(
            scroll_content
        )

        content_main_layout.setContentsMargins(
            40,
            30,
            40,
            35
        )

        content_main_layout.setSpacing(
            24
        )

        # ====================================================
        # TOP HEADER
        # ====================================================

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        dashboard_title = QLabel(
            "Dashboard"
        )

        dashboard_title.setFont(
            QFont(
                "Segoe UI",
                30,
                QFont.Weight.Bold
            )
        )

        dashboard_title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                border: none;
            }}
            """
        )

        dashboard_subtitle = QLabel(
            "Overview of your employee management system"
        )

        dashboard_subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 14px;
            }}
            """
        )

        title_layout.addWidget(
            dashboard_title
        )

        title_layout.addWidget(
            dashboard_subtitle
        )

        header_layout.addLayout(
            title_layout
        )

        header_layout.addStretch()

        # ----------------------------------------------------
        # USER PROFILE
        # ----------------------------------------------------

        user_card = QFrame()

        user_card.setMinimumSize(
            140,
            76
        )

        user_card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 15px;
            }}
            """
        )

        user_layout = QHBoxLayout(
            user_card
        )

        user_layout.setContentsMargins(
            12,
            9,
            12,
            9
        )

        user_layout.setSpacing(
            10
        )

        avatar = QFrame()

        avatar.setFixedSize(
            48,
            48
        )

        avatar.setStyleSheet(
            """
            QFrame {
                background: #DBEAFE;
                border-radius: 24px;
            }
            """
        )

        avatar_layout = QVBoxLayout(
            avatar
        )

        avatar_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        avatar_label = QLabel(
            self.get_user_initial()
        )

        avatar_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        avatar_label.setStyleSheet(
            """
            QLabel {
                color: #2563EB;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: 800;
            }
            """
        )

        avatar_layout.addWidget(
            avatar_label
        )

        user_layout.addWidget(
            avatar
        )

        user_text = QVBoxLayout()

        self.user_name_label = QLabel(
            self.get_user_name()
        )

        self.user_name_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: 800;
            }}
            """
        )

        self.user_role_label = QLabel(
            self.get_user_role()
        )

        self.user_role_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 11px;
            }}
            """
        )

        user_text.addWidget(
            self.user_name_label
        )

        user_text.addWidget(
            self.user_role_label
        )

        user_layout.addLayout(
            user_text
        )

        header_layout.addWidget(
            user_card
        )

        content_main_layout.addLayout(
            header_layout
        )

        # ====================================================
        # WELCOME CARD
        # ====================================================

        self.welcome_card = QFrame()

        self.welcome_card.setMinimumHeight(
            145
        )

        self.welcome_card.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 0,
                    stop: 0 #1E3A8A,
                    stop: 0.55 #2346A0,
                    stop: 1 #2563EB
                );
                border-radius: 18px;
                border: none;
            }}
            """
        )

        welcome_layout = QHBoxLayout(
            self.welcome_card
        )

        welcome_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        welcome_text_layout = QVBoxLayout()

        self.welcome_title = QLabel(
            f"Welcome back, {self.get_user_name()}! 👋"
        )

        self.welcome_title.setFont(
            QFont(
                "Segoe UI",
                22,
                QFont.Weight.Bold
            )
        )

        self.welcome_title.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
            """
        )

        welcome_subtitle = QLabel(
            "Manage employees, attendance, payroll and performance from one place."
        )

        welcome_subtitle.setStyleSheet(
            """
            QLabel {
                color: #DBEAFE;
                background: transparent;
                border: none;
                font-size: 13px;
            }
            """
        )

        welcome_text_layout.addWidget(
            self.welcome_title
        )

        welcome_text_layout.addSpacing(
            6
        )

        welcome_text_layout.addWidget(
            welcome_subtitle
        )

        welcome_layout.addLayout(
            welcome_text_layout
        )

        welcome_layout.addStretch()

        # ----------------------------------------------------
        # EMS CIRCLE
        # ----------------------------------------------------

        ems_circle = QFrame()

        ems_circle.setFixedSize(
            90,
            90
        )

        ems_circle.setStyleSheet(
            """
            QFrame {
                background: #3B82F6;
                border: 1px solid rgba(255,255,255,0.25);
                border-radius: 45px;
            }
            """
        )

        ems_layout = QVBoxLayout(
            ems_circle
        )

        ems_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        ems_label = QLabel(
            "EMS"
        )

        ems_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        ems_label.setStyleSheet(
            """
            QLabel {
                color: white;
                background: transparent;
                border: none;
                font-size: 22px;
                font-weight: 800;
            }
            """
        )

        ems_layout.addWidget(
            ems_label
        )

        welcome_layout.addWidget(
            ems_circle
        )

        content_main_layout.addWidget(
            self.welcome_card
        )

        # ====================================================
        # SECTION TITLE
        # ====================================================

        overview_title = QLabel(
            "System Overview"
        )

        overview_title.setFont(
            QFont(
                "Segoe UI",
                20,
                QFont.Weight.Bold
            )
        )

        overview_title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                border: none;
            }}
            """
        )

        content_main_layout.addWidget(
            overview_title
        )

        # ====================================================
        # STAT CARDS
        # ====================================================

        stats_layout = QHBoxLayout()

        stats_layout.setSpacing(
            16
        )

        self.total_employee_card = StatCard(
            "Total Employees",
            "0",
            "EMPLOYEES",
            "♟",
            BLUE_LIGHT,
            BLUE
        )

        self.active_employee_card = StatCard(
            "Active Employees",
            "0",
            "ACTIVE",
            "✓",
            GREEN_LIGHT,
            GREEN
        )

        self.present_card = StatCard(
            "Present Records",
            "0",
            "ATTENDANCE",
            "◷",
            CYAN_LIGHT,
            CYAN
        )

        self.payroll_card = StatCard(
            "Processed Payroll",
            "0",
            "PAYROLL",
            "₹",
            PURPLE_LIGHT,
            PURPLE
        )

        stats_layout.addWidget(
            self.total_employee_card
        )

        stats_layout.addWidget(
            self.active_employee_card
        )

        stats_layout.addWidget(
            self.present_card
        )

        stats_layout.addWidget(
            self.payroll_card
        )

        content_main_layout.addLayout(
            stats_layout
        )

        # ====================================================
        # LOWER AREA
        # ====================================================

        lower_layout = QHBoxLayout()

        lower_layout.setSpacing(
            22
        )

        # ====================================================
        # QUICK ACTIONS CARD
        # ====================================================

        quick_card = QFrame()

        quick_card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )

        quick_layout = QVBoxLayout(
            quick_card
        )

        quick_layout.setContentsMargins(
            24,
            22,
            24,
            22
        )

        quick_layout.setSpacing(
            12
        )

        quick_title = QLabel(
            "Quick Actions"
        )

        quick_title.setFont(
            QFont(
                "Segoe UI",
                20,
                QFont.Weight.Bold
            )
        )

        quick_title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                border: none;
            }}
            """
        )

        quick_subtitle = QLabel(
            "Frequently used modules"
        )

        quick_subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 13px;
            }}
            """
        )

        quick_layout.addWidget(
            quick_title
        )

        quick_layout.addWidget(
            quick_subtitle
        )

        quick_layout.addSpacing(
            5
        )

        # ----------------------------------------------------
        # QUICK BUTTONS
        # ----------------------------------------------------

        employee_action = DashboardButton(
            "♙",
            "Employee Management",
            "Add, edit and manage employees"
        )

        employee_action.clicked.connect(
            self.open_employee_management
        )

        attendance_action = DashboardButton(
            "◷",
            "Attendance",
            "Track employee attendance"
        )

        attendance_action.clicked.connect(
            self.open_attendance
        )

        payroll_action = DashboardButton(
            "₹",
            "Payroll",
            "Process salary and generate payslips"
        )

        payroll_action.clicked.connect(
            self.open_payroll
        )

        performance_action = DashboardButton(
            "★",
            "Performance",
            "Review employee performance"
        )

        performance_action.clicked.connect(
            self.open_performance
        )

        calendar_action = DashboardButton(
            "□",
            "Calendar",
            "Manage meetings and events"
        )

        calendar_action.clicked.connect(
            self.open_calendar
        )

        quick_layout.addWidget(
            employee_action
        )

        quick_layout.addWidget(
            attendance_action
        )

        quick_layout.addWidget(
            payroll_action
        )

        quick_layout.addWidget(
            performance_action
        )

        quick_layout.addWidget(
            calendar_action
        )

        lower_layout.addWidget(
            quick_card,
            2
        )

        # ====================================================
        # SYSTEM STATUS
        # ====================================================

        status_card = QFrame()

        status_card.setMinimumWidth(
            300
        )

        status_card.setStyleSheet(
            f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
            """
        )

        status_layout = QVBoxLayout(
            status_card
        )

        status_layout.setContentsMargins(
            24,
            22,
            24,
            22
        )

        status_layout.setSpacing(
            11
        )

        status_title = QLabel(
            "System Status"
        )

        status_title.setFont(
            QFont(
                "Segoe UI",
                20,
                QFont.Weight.Bold
            )
        )

        status_title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT};
                background: transparent;
                border: none;
            }}
            """
        )

        status_subtitle = QLabel(
            "Current system health"
        )

        status_subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background: transparent;
                border: none;
                font-size: 13px;
            }}
            """
        )

        status_layout.addWidget(
            status_title
        )

        status_layout.addWidget(
            status_subtitle
        )

        status_layout.addSpacing(
            5
        )

        status_layout.addWidget(
            StatusItem(
                "Database",
                "SQLite database connected"
            )
        )

        status_layout.addWidget(
            StatusItem(
                "Security",
                "Password encryption active"
            )
        )

        status_layout.addWidget(
            StatusItem(
                "Authentication",
                "Role-based access enabled"
            )
        )

        status_layout.addWidget(
            StatusItem(
                "Application",
                "All available modules ready"
            )
        )

        status_layout.addStretch()

        lower_layout.addWidget(
            status_card,
            1
        )

        content_main_layout.addLayout(
            lower_layout
        )

        content_main_layout.addStretch()

        # ----------------------------------------------------
        # SCROLL SETUP
        # ----------------------------------------------------

        self.scroll_area.setWidget(
            scroll_content
        )

        content_layout.addWidget(
            self.scroll_area
        )

        main_layout.addWidget(
            content_background
        )

    # ========================================================
    # SIDEBAR BUTTON
    # ========================================================

    def create_sidebar_button(
        self,
        icon,
        text,
        active=False,
        logout=False
    ):

        button = QPushButton()

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.setMinimumHeight(
            48
        )

        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QHBoxLayout(
            button
        )

        layout.setContentsMargins(
            14,
            0,
            14,
            0
        )

        layout.setSpacing(
            13
        )

        icon_label = QLabel(
            icon
        )

        icon_label.setFixedWidth(
            25
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        icon_label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                border: none;
                color: white;
                font-size: 17px;
            }
            """
        )

        text_label = QLabel(
            text
        )

        text_label.setStyleSheet(
            """
            QLabel {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
                font-weight: 500;
            }
            """
        )

        layout.addWidget(
            icon_label
        )

        layout.addWidget(
            text_label
        )

        layout.addStretch()

        if active:

            button.setStyleSheet(
                """
                QPushButton {
                    background: #2563EB;
                    border: none;
                    border-radius: 13px;
                }

                QPushButton:hover {
                    background: #1D4ED8;
                }
                """
            )

        elif logout:

            button.setStyleSheet(
                """
                QPushButton {
                    background: #431B2B;
                    border: none;
                    border-radius: 13px;
                }

                QPushButton:hover {
                    background: #5B2339;
                }
                """
            )

        else:

            button.setStyleSheet(
                """
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 13px;
                }

                QPushButton:hover {
                    background: #172554;
                }

                QPushButton:pressed {
                    background: #1E3A8A;
                }
                """
            )

        return button

    # ========================================================
    # USER INFORMATION
    # ========================================================

    def get_user_name(self):

        user = Session.get_user()

        if user is None:

            return "User"

        return (
            getattr(
                user,
                "username",
                None
            )
            or
            getattr(
                user,
                "full_name",
                None
            )
            or
            "User"
        )

    def get_user_role(self):

        user = Session.get_user()

        if user is None:

            return "User"

        return str(
            getattr(
                user,
                "role",
                "User"
            )
        )

    def get_user_initial(self):

        name = self.get_user_name()

        if not name:

            return "U"

        return name[
            0
        ].upper()

    # ========================================================
    # DASHBOARD DATA
    # ========================================================

    def load_dashboard_data(self):

        # ----------------------------------------------------
        # EMPLOYEES
        # ----------------------------------------------------

        try:

            employees = get_all_employees()

            total_employees = len(
                employees
            )

            active_employees = sum(
                1
                for employee in employees
                if str(
                    getattr(
                        employee,
                        "status",
                        ""
                    )
                ).lower()
                == "active"
            )

            self.total_employee_card.set_value(
                total_employees
            )

            self.active_employee_card.set_value(
                active_employees
            )

        except Exception as error:

            self.total_employee_card.set_value(
                "0"
            )

            self.active_employee_card.set_value(
                "0"
            )

            print(
                "Employee dashboard error:",
                error
            )

        # ----------------------------------------------------
        # ATTENDANCE
        # ----------------------------------------------------

        try:

            attendance = (
                get_attendance_statistics()
            )

            present = attendance.get(
                "present",
                0
            )

            self.present_card.set_value(
                present
            )

        except Exception as error:

            self.present_card.set_value(
                "0"
            )

            print(
                "Attendance dashboard error:",
                error
            )

        # ----------------------------------------------------
        # PAYROLL
        # ----------------------------------------------------

        try:

            payroll = (
                get_payroll_summary()
            )

            processed = payroll.get(
                "processed",
                0
            )

            self.payroll_card.set_value(
                processed
            )

        except Exception as error:

            self.payroll_card.set_value(
                "0"
            )

            print(
                "Payroll dashboard error:",
                error
            )

        # ----------------------------------------------------
        # PERFORMANCE
        # ----------------------------------------------------

        try:

            performance = (
                get_performance_summary()
            )

            print(
                "Performance summary:",
                performance
            )

        except Exception as error:

            print(
                "Performance dashboard error:",
                error
            )

    # ========================================================
    # WELCOME ANIMATION
    # ========================================================

    def start_welcome_animation(self):

        effect = QGraphicsOpacityEffect(
            self.welcome_card
        )

        self.welcome_card.setGraphicsEffect(
            effect
        )

        effect.setOpacity(
            0.0
        )

        self.welcome_animation = (
            QPropertyAnimation(
                effect,
                b"opacity"
            )
        )

        self.welcome_animation.setDuration(
            700
        )

        self.welcome_animation.setStartValue(
            0.0
        )

        self.welcome_animation.setEndValue(
            1.0
        )

        self.welcome_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.welcome_animation.start()

    # ========================================================
    # EMPLOYEE MANAGEMENT
    # ========================================================

    def open_employee_management(self):

        try:

            from ui.employees import (
                EmployeeManagementWindow
            )

            # IMPORTANT:
            # Do NOT pass parent=self.
            # Current EmployeeManagementWindow
            # does not accept parent.

            self.employee_window = (
                EmployeeManagementWindow()
            )

            self.employee_window.show()

            self.employee_window.raise_()

            self.employee_window.activateWindow()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Employee Management Error",
                f"Unable to open Employee Management.\n\n{error}"
            )

    # ========================================================
    # ATTENDANCE
    # ========================================================

    def open_attendance(self):

        try:

            from ui.attendance import (
                AttendanceWindow
            )

            # IMPORTANT:
            # Do NOT pass parent=self.

            self.attendance_window = (
                AttendanceWindow()
            )

            self.attendance_window.show()

            self.attendance_window.raise_()

            self.attendance_window.activateWindow()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Attendance Error",
                f"Unable to open Attendance.\n\n{error}"
            )

    # ========================================================
    # PAYROLL
    # ========================================================

    def open_payroll(self):

        try:

            from ui.payroll import (
                PayrollWindow
            )

            self.payroll_window = (
                PayrollWindow()
            )

            self.payroll_window.show()

            self.payroll_window.raise_()

            self.payroll_window.activateWindow()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Payroll Error",
                f"Unable to open Payroll.\n\n{error}"
            )

    # ========================================================
    # PERFORMANCE
    # ========================================================

    def open_performance(self):

        try:

            from ui.performance import (
                PerformanceWindow
            )

            self.performance_window = (
                PerformanceWindow()
            )

            self.performance_window.show()

            self.performance_window.raise_()

            self.performance_window.activateWindow()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Performance Error",
                f"Unable to open Performance.\n\n{error}"
            )

    # ========================================================
    # CALENDAR
    # ========================================================

    def open_calendar(self):

        try:

            module = importlib.import_module(
                "ui.calendar"
            )

            CalendarWindow = getattr(
                module,
                "CalendarWindow"
            )

            try:

                self.calendar_window = (
                    CalendarWindow()
                )

            except TypeError:

                self.calendar_window = (
                    CalendarWindow(
                        self
                    )
                )

            self.calendar_window.show()

            self.calendar_window.raise_()

            self.calendar_window.activateWindow()

        except ModuleNotFoundError:

            QMessageBox.information(
                self,
                "Calendar",
                "Calendar module is not available yet."
            )

        except AttributeError:

            QMessageBox.information(
                self,
                "Calendar",
                "CalendarWindow is not available yet."
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "Calendar Error",
                f"Unable to open Calendar.\n\n{error}"
            )

    # ========================================================
    # REPORTS
    # ========================================================

    def open_reports(self):

        possible_modules = [
            (
                "ui.reports",
                "ReportsWindow"
            ),
            (
                "ui.report",
                "ReportsWindow"
            ),
        ]

        for module_name, class_name in possible_modules:

            try:

                module = importlib.import_module(
                    module_name
                )

                window_class = getattr(
                    module,
                    class_name
                )

                try:

                    self.reports_window = (
                        window_class()
                    )

                except TypeError:

                    self.reports_window = (
                        window_class(
                            self
                        )
                    )

                self.reports_window.show()

                self.reports_window.raise_()

                self.reports_window.activateWindow()

                return

            except (
                ModuleNotFoundError,
                AttributeError
            ):

                continue

            except Exception as error:

                QMessageBox.warning(
                    self,
                    "Reports Error",
                    f"Unable to open Reports.\n\n{error}"
                )

                return

        QMessageBox.information(
            self,
            "Reports",
            "Reports module is not available yet."
        )

    # ========================================================
    # QUALITY MANAGEMENT
    # ========================================================

    def open_quality(self):

        possible_modules = [
            (
                "ui.quality",
                "QualityManagementWindow"
            ),
            (
                "ui.quality",
                "QualityWindow"
            ),
        ]

        for module_name, class_name in possible_modules:

            try:

                module = importlib.import_module(
                    module_name
                )

                window_class = getattr(
                    module,
                    class_name
                )

                try:

                    self.quality_window = (
                        window_class()
                    )

                except TypeError:

                    self.quality_window = (
                        window_class(
                            self
                        )
                    )

                self.quality_window.show()

                self.quality_window.raise_()

                self.quality_window.activateWindow()

                return

            except (
                ModuleNotFoundError,
                AttributeError
            ):

                continue

            except Exception as error:

                QMessageBox.warning(
                    self,
                    "Quality Management Error",
                    f"Unable to open Quality Management.\n\n{error}"
                )

                return

        QMessageBox.information(
            self,
            "Quality Management",
            "Quality Management module is not available yet."
        )

    # ========================================================
    # SETTINGS
    # ========================================================

    def open_settings(self):

        possible_modules = [
            (
                "ui.settings",
                "SettingsWindow"
            ),
            (
                "ui.settings",
                "SettingsDialog"
            ),
        ]

        for module_name, class_name in possible_modules:

            try:

                module = importlib.import_module(
                    module_name
                )

                window_class = getattr(
                    module,
                    class_name
                )

                try:

                    self.settings_window = (
                        window_class()
                    )

                except TypeError:

                    self.settings_window = (
                        window_class(
                            self
                        )
                    )

                self.settings_window.show()

                self.settings_window.raise_()

                self.settings_window.activateWindow()

                return

            except (
                ModuleNotFoundError,
                AttributeError
            ):

                continue

            except Exception as error:

                QMessageBox.warning(
                    self,
                    "Settings Error",
                    f"Unable to open Settings.\n\n{error}"
                )

                return

        QMessageBox.information(
            self,
            "Settings",
            "Settings module is not available yet."
        )

    # ========================================================
    # SCROLL TOP
    # ========================================================

    def scroll_to_top(self):

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    # ========================================================
    # LOGOUT
    # ========================================================

    def logout(self):

        answer = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes
            |
            QMessageBox.StandardButton.No
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):

            return

        Session.logout()

        try:

            from ui.login import LoginWindow

            self.login_window = LoginWindow()

            self.login_window.show()

            self.close()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Logout Error",
                f"Unable to return to login screen.\n\n{error}"
            )


# ============================================================
# END OF DASHBOARD
# ============================================================