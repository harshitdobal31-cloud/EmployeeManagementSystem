# ============================================================
# EMPLOYEE MANAGEMENT SYSTEM
# PROFESSIONAL THEME MANAGER
# ============================================================

from PySide6.QtWidgets import QApplication


# ============================================================
# THEMES
# ============================================================

THEMES = {

    "Dark": {
        "background": "#0F172A",
        "secondary": "#111827",
        "card": "#1E293B",
        "border": "#334155",
        "text": "#F8FAFC",
        "muted": "#94A3B8",
        "accent": "#3B82F6",
        "accent_hover": "#2563EB",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },

    "Light": {
        "background": "#F1F5F9",
        "secondary": "#FFFFFF",
        "card": "#FFFFFF",
        "border": "#CBD5E1",
        "text": "#0F172A",
        "muted": "#64748B",
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "success": "#16A34A",
        "warning": "#D97706",
        "danger": "#DC2626",
    },

    "Blue": {
        "background": "#071A2B",
        "secondary": "#0B2742",
        "card": "#123B5D",
        "border": "#28577F",
        "text": "#F0F9FF",
        "muted": "#93C5FD",
        "accent": "#0EA5E9",
        "accent_hover": "#0284C7",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },

    "Purple": {
        "background": "#171329",
        "secondary": "#211A3A",
        "card": "#302454",
        "border": "#493B70",
        "text": "#FAF5FF",
        "muted": "#C4B5FD",
        "accent": "#8B5CF6",
        "accent_hover": "#7C3AED",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#F43F5E",
    },

    "Green": {
        "background": "#071C14",
        "secondary": "#0D2B20",
        "card": "#164A34",
        "border": "#286347",
        "text": "#F0FDF4",
        "muted": "#86EFAC",
        "accent": "#22C55E",
        "accent_hover": "#16A34A",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },

    "Rose": {
        "background": "#211017",
        "secondary": "#30151F",
        "card": "#4A1D2C",
        "border": "#713047",
        "text": "#FFF1F2",
        "muted": "#FDA4AF",
        "accent": "#F43F5E",
        "accent_hover": "#E11D48",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },

    "Orange": {
        "background": "#21140A",
        "secondary": "#321B0B",
        "card": "#4A270D",
        "border": "#7C4314",
        "text": "#FFF7ED",
        "muted": "#FDBA74",
        "accent": "#F97316",
        "accent_hover": "#EA580C",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },

    "Teal": {
        "background": "#071C1D",
        "secondary": "#0B292B",
        "card": "#104447",
        "border": "#1F6468",
        "text": "#F0FDFA",
        "muted": "#5EEAD4",
        "accent": "#14B8A6",
        "accent_hover": "#0D9488",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },

    "Midnight": {
        "background": "#080B16",
        "secondary": "#101525",
        "card": "#182038",
        "border": "#293556",
        "text": "#F8FAFC",
        "muted": "#9CA3AF",
        "accent": "#6366F1",
        "accent_hover": "#4F46E5",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },

    "Slate": {
        "background": "#111827",
        "secondary": "#1F2937",
        "card": "#374151",
        "border": "#4B5563",
        "text": "#F9FAFB",
        "muted": "#9CA3AF",
        "accent": "#64748B",
        "accent_hover": "#475569",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    },
}


# ============================================================
# DENSITY SETTINGS
# ============================================================

DENSITY_SETTINGS = {

    "Comfortable": {
        "input_padding": "9px 11px",
        "button_padding": "9px 17px",
        "table_padding": "9px",
        "tab_padding": "10px 18px",
        "group_padding": "18px",
        "checkbox_spacing": "9px",
    },

    "Compact": {
        "input_padding": "6px 9px",
        "button_padding": "6px 13px",
        "table_padding": "6px",
        "tab_padding": "7px 13px",
        "group_padding": "13px",
        "checkbox_spacing": "6px",
    },
}


# ============================================================
# THEME NAMES
# ============================================================

def get_theme_names():
    return list(THEMES.keys())


# ============================================================
# CURRENT THEME
# ============================================================

def get_current_theme():

    from services.settings_service import get_setting

    theme = get_setting(
        "theme",
        "Dark"
    )

    if theme not in THEMES:
        return "Dark"

    return theme


# ============================================================
# THEME DATA
# ============================================================

def get_theme_data(theme_name=None):

    if theme_name is None:
        theme_name = get_current_theme()

    return THEMES.get(
        theme_name,
        THEMES["Dark"]
    )


# ============================================================
# SAVE THEME
# ============================================================

def save_theme(theme_name):

    from services.settings_service import set_setting

    if theme_name not in THEMES:
        theme_name = "Dark"

    return set_setting(
        "theme",
        theme_name
    )


# ============================================================
# ACCENT COLOR
# ============================================================

def save_accent_color(color):

    from services.settings_service import set_setting

    return set_setting(
        "accent_color",
        color
    )


def get_accent_color():

    from services.settings_service import get_setting

    return get_setting(
        "accent_color",
        ""
    )


# ============================================================
# CURRENT DENSITY
# ============================================================

def get_current_density():

    from services.settings_service import get_setting

    density = get_setting(
        "ui_density",
        "Comfortable"
    )

    if density not in DENSITY_SETTINGS:
        return "Comfortable"

    return density


# ============================================================
# DENSITY DATA
# ============================================================

def get_density_data(density=None):

    if density is None:
        density = get_current_density()

    return DENSITY_SETTINGS.get(
        density,
        DENSITY_SETTINGS["Comfortable"]
    )


# ============================================================
# BUILD APPLICATION STYLESHEET
# ============================================================

def build_application_stylesheet(
    theme_name=None,
    density=None
):

    theme = get_theme_data(
        theme_name
    )

    density_data = get_density_data(
        density
    )

    accent = (
        get_accent_color()
        or theme["accent"]
    )

    return f"""

    /* ========================================================
       GLOBAL
       ======================================================== */

    QWidget {{
        font-family: "Segoe UI";
        color: {theme["text"]};
    }}

    QMainWindow,
    QDialog {{
        background-color: {theme["background"]};
    }}

    QLabel {{
        color: {theme["text"]};
        background: transparent;
    }}


    /* ========================================================
       INPUTS
       ======================================================== */

    QLineEdit,
    QTextEdit,
    QPlainTextEdit,
    QDateEdit,
    QTimeEdit,
    QDateTimeEdit,
    QSpinBox,
    QDoubleSpinBox {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        border-radius: 8px;

        padding: {density_data["input_padding"]};
    }}

    QLineEdit:focus,
    QTextEdit:focus,
    QPlainTextEdit:focus,
    QDateEdit:focus,
    QTimeEdit:focus,
    QDateTimeEdit:focus,
    QSpinBox:focus,
    QDoubleSpinBox:focus {{
        border: 1px solid {accent};
    }}


    /* ========================================================
       COMBO BOX
       ======================================================== */

    QComboBox {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        border-radius: 8px;

        padding: {density_data["input_padding"]};
    }}

    QComboBox:hover {{
        border-color: {accent};
    }}

    QComboBox:focus {{
        border-color: {accent};
    }}

    QComboBox QAbstractItemView {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};

        selection-background-color: {accent};
        selection-color: white;
    }}


    /* ========================================================
       BUTTONS
       ======================================================== */

    QPushButton {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        border-radius: 8px;

        padding: {density_data["button_padding"]};

        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {accent};
        color: white;
        border-color: {accent};
    }}

    QPushButton:pressed {{
        background-color: {theme["accent_hover"]};
        border-color: {theme["accent_hover"]};
    }}

    QPushButton:disabled {{
        background-color: {theme["card"]};
        color: {theme["muted"]};
        border-color: {theme["border"]};
    }}


    /* ========================================================
       CHECKBOX
       ======================================================== */

    QCheckBox {{
        color: {theme["text"]};
        spacing: {density_data["checkbox_spacing"]};
        padding: 5px;
    }}

    QRadioButton {{
        color: {theme["text"]};
        spacing: {density_data["checkbox_spacing"]};
    }}


    /* ========================================================
       GROUP BOX
       ======================================================== */

    QGroupBox {{
        background-color: {theme["card"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        border-radius: 10px;

        margin-top: 12px;
        padding: {density_data["group_padding"]};

        font-weight: 600;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;

        left: 12px;

        padding: 0 6px;

        color: {theme["text"]};
        font-weight: 700;
    }}


    /* ========================================================
       FRAME
       ======================================================== */

    QFrame {{
        color: {theme["text"]};
    }}


    /* ========================================================
       TABLE
       ======================================================== */

    QTableWidget,
    QTableView {{
        background-color: {theme["card"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        gridline-color: {theme["border"]};

        selection-background-color: {accent};
        selection-color: white;

        alternate-background-color: {theme["secondary"]};
    }}

    QTableWidget::item,
    QTableView::item {{
        padding: {density_data["table_padding"]};
    }}

    QHeaderView::section {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};

        border: none;
        border-bottom: 1px solid {theme["border"]};

        padding: {density_data["table_padding"]};

        font-weight: 600;
    }}


    /* ========================================================
       TABS
       ======================================================== */

    QTabWidget::pane {{
        border: 1px solid {theme["border"]};
        background: {theme["background"]};
    }}

    QTabBar::tab {{
        background: {theme["secondary"]};
        color: {theme["muted"]};

        padding: {density_data["tab_padding"]};

        border: 1px solid {theme["border"]};
    }}

    QTabBar::tab:selected {{
        background: {accent};
        color: white;
        border-color: {accent};
    }}

    QTabBar::tab:hover {{
        color: {theme["text"]};
    }}


    /* ========================================================
       SCROLLBARS
       ======================================================== */

    QScrollBar:vertical {{
        background: {theme["background"]};
        width: 10px;
        border: none;
    }}

    QScrollBar::handle:vertical {{
        background: {theme["border"]};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {accent};
    }}

    QScrollBar:horizontal {{
        background: {theme["background"]};
        height: 10px;
        border: none;
    }}

    QScrollBar::handle:horizontal {{
        background: {theme["border"]};
        border-radius: 5px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {accent};
    }}


    /* ========================================================
       LIST / TREE
       ======================================================== */

    QListWidget,
    QTreeWidget {{
        background-color: {theme["card"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
    }}

    QListWidget::item:selected,
    QTreeWidget::item:selected {{
        background-color: {accent};
        color: white;
    }}


    /* ========================================================
       CALENDAR
       ======================================================== */

    QCalendarWidget {{
        background-color: {theme["card"]};
        color: {theme["text"]};
    }}

    QCalendarWidget QToolButton {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};
        border: none;
        padding: 6px;
    }}

    QCalendarWidget QToolButton:hover {{
        background-color: {accent};
        color: white;
    }}

    QCalendarWidget QAbstractItemView {{
        background-color: {theme["card"]};
        color: {theme["text"]};
        selection-background-color: {accent};
        selection-color: white;
    }}


    /* ========================================================
       PROGRESS BAR
       ======================================================== */

    QProgressBar {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        border-radius: 7px;

        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {accent};
        border-radius: 6px;
    }}


    /* ========================================================
       SLIDER
       ======================================================== */

    QSlider::groove:horizontal {{
        height: 5px;
        background: {theme["border"]};
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        width: 14px;
        margin: -5px 0;
        background: {accent};
        border-radius: 7px;
    }}


    /* ========================================================
       MESSAGE BOX
       ======================================================== */

    QMessageBox {{
        background-color: {theme["card"]};
        color: {theme["text"]};
    }}

    QMessageBox QLabel {{
        color: {theme["text"]};
        background: transparent;
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
    }}


    /* ========================================================
       TOOLTIP
       ======================================================== */

    QToolTip {{
        background-color: {theme["card"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        padding: 6px;
    }}


    /* ========================================================
       MENU
       ======================================================== */

    QMenu {{
        background-color: {theme["card"]};
        color: {theme["text"]};

        border: 1px solid {theme["border"]};
        padding: 5px;
    }}

    QMenu::item {{
        padding: 7px 25px;
    }}

    QMenu::item:selected {{
        background-color: {accent};
        color: white;
    }}


    /* ========================================================
       MENU BAR
       ======================================================== */

    QMenuBar {{
        background-color: {theme["secondary"]};
        color: {theme["text"]};
    }}

    QMenuBar::item {{
        padding: 6px 10px;
    }}

    QMenuBar::item:selected {{
        background-color: {accent};
        color: white;
    }}


    /* ========================================================
       TOOLBAR
       ======================================================== */

    QToolBar {{
        background-color: {theme["secondary"]};
        border: none;
        spacing: 5px;
    }}


    /* ========================================================
       SPLITTER
       ======================================================== */

    QSplitter::handle {{
        background-color: {theme["border"]};
    }}

    QSplitter::handle:hover {{
        background-color: {accent};
    }}

    """


# ============================================================
# APPLY THEME
# ============================================================

def apply_theme(
    app=None,
    theme_name=None,
    density=None
):

    if app is None:
        app = QApplication.instance()

    if app is None:
        return False

    if theme_name is None:
        theme_name = get_current_theme()

    if density is None:
        density = get_current_density()

    if theme_name not in THEMES:
        theme_name = "Dark"

    if density not in DENSITY_SETTINGS:
        density = "Comfortable"

    stylesheet = build_application_stylesheet(
        theme_name=theme_name,
        density=density
    )

    app.setStyleSheet(stylesheet)

    return True