# ============================================================
# EMPLOYEE MANAGEMENT SYSTEM
# PROFESSIONAL DASHBOARD
# File: ui/dashboard.py   (replaces the existing file)
# ============================================================

import importlib
import math
from collections import Counter
from datetime import date, datetime, timedelta

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils.session import Session
from database.database import SessionLocal
from database.models import Notification, User
from utils.theme_manager import get_current_theme, get_theme_data

from services.employee_service import get_all_employees
from services.attendance_service import get_attendance_statistics
from services.payroll_service import get_payroll_summary


# ============================================================
# SETTINGS
# ============================================================

ANIMATIONS_ENABLED = True          # Set to False to disable all motion.
EXPANDED_SIDEBAR_WIDTH = 285
COLLAPSED_SIDEBAR_WIDTH = 84
RECENT_ROW_LIMIT = 8
SEARCH_ROW_LIMIT = 100
DEPARTMENT_SLICE_LIMIT = 5
GROWTH_MONTHS = 6


# ============================================================
# COLORS (filled from utils/theme_manager.py at runtime)
# ============================================================

PALETTE = {
    "sidebar": "#0F172A",
    "sidebar_hover": "#172554",
    "sidebar_text": "#FFFFFF",
    "sidebar_muted": "#94A3B8",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_light": "#DBEAFE",
    "background": "#F5F7FB",
    "surface": "#FFFFFF",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "border": "#E2E8F0",
    "success": "#16A34A",
    "success_light": "#DCFCE7",
    "warning": "#EA580C",
    "warning_light": "#FFEDD5",
    "info": "#0891B2",
    "info_light": "#CFFAFE",
    "secondary": "#7C3AED",
    "secondary_light": "#EDE9FE",
    "danger": "#DC2626",
    "danger_light": "#FEE2E2",
}

# Palette key -> candidate keys in the theme dictionary (first match wins).
THEME_KEY_MAP = {
    "sidebar": ("sidebar", "sidebar_background"),
    "sidebar_hover": ("sidebar_hover", "surface_alt"),
    "sidebar_text": ("sidebar_text",),
    "sidebar_muted": ("sidebar_muted",),
    "accent": ("accent", "primary"),
    "accent_hover": ("accent_hover", "primary_hover"),
    "accent_light": ("accent_light", "primary_light"),
    "background": ("background", "bg"),
    "surface": ("surface", "card"),
    "text": ("text", "text_primary"),
    "text_muted": ("muted", "text_secondary"),
    "border": ("border",),
    "success": ("success",),
    "success_light": ("success_light", "success_soft"),
    "warning": ("warning",),
    "warning_light": ("warning_light", "warning_soft"),
    "info": ("info",),
    "info_light": ("info_light",),
    "secondary": ("secondary",),
    "secondary_light": ("secondary_light",),
    "danger": ("danger", "error"),
    "danger_light": ("danger_light", "error_light"),
}


# ============================================================
# COLOR HELPERS
# ============================================================

def _hex_to_rgb(value):
    """Convert #RGB or #RRGGBB to an RGB tuple. Returns None if not hex."""
    text = str(value or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return None
    try:
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _relative_luminance(color):
    rgb = _hex_to_rgb(color)
    if rgb is None:
        return 0.5
    channels = []
    for channel in rgb:
        c = channel / 255.0
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(first, second):
    l1 = _relative_luminance(first)
    l2 = _relative_luminance(second)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def _ensure_contrast(foreground, background, minimum):
    """Return the foreground if readable on the background, else a readable fallback."""
    if _hex_to_rgb(foreground) is None or _hex_to_rgb(background) is None:
        return foreground
    if _contrast_ratio(foreground, background) >= minimum:
        return foreground
    return "#0F172A" if _relative_luminance(background) > 0.45 else "#F8FAFC"


def apply_dashboard_theme_colors():
    """Load Dashboard colors from the central Theme Manager into PALETTE."""
    try:
        theme_name = get_current_theme()
        theme = get_theme_data(theme_name) or {}
        print("Dashboard theme loaded:", theme_name)
    except Exception as error:
        print("Dashboard theme loading error:", error)
        theme = {}

    for palette_key, candidates in THEME_KEY_MAP.items():
        for candidate in candidates:
            value = theme.get(candidate)
            if isinstance(value, str) and value.strip():
                PALETTE[palette_key] = value.strip()
                break

    PALETTE["text"] = _ensure_contrast(PALETTE["text"], PALETTE["surface"], 4.5)
    PALETTE["text"] = _ensure_contrast(PALETTE["text"], PALETTE["background"], 4.5)
    PALETTE["text_muted"] = _ensure_contrast(PALETTE["text_muted"], PALETTE["surface"], 3.0)
    PALETTE["text_muted"] = _ensure_contrast(PALETTE["text_muted"], PALETTE["background"], 3.0)
    PALETTE["sidebar_text"] = _ensure_contrast(PALETTE["sidebar_text"], PALETTE["sidebar"], 4.5)


# ============================================================
# GENERIC HELPERS
# ============================================================

def _label_qss(color, size=13, weight=400):
    return (
        f"QLabel {{ color: {color}; background: transparent; border: none; "
        f"font-size: {size}px; font-weight: {weight}; }}"
    )


def _make_label(text, color=None, size=13, weight=400, parent=None):
    label = QLabel(str(text), parent)
    label.setStyleSheet(_label_qss(color or PALETTE["text"], size, weight))
    label.setWordWrap(True)
    return label


def _pen(color, width):
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _make_animation(parent, start, end, callback, duration=900):
    animation = QVariantAnimation(parent)
    animation.setStartValue(start)
    animation.setEndValue(end)
    animation.setDuration(duration)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.valueChanged.connect(callback)
    return animation


def _dispose_animation(animation):
    """Stop an animation and schedule its deletion. Returns None for convenience."""
    if animation is not None:
        try:
            animation.stop()
            animation.deleteLater()
        except RuntimeError:
            pass
    return None


def _clear_layout(layout):
    """Remove and delete every widget inside a layout, recursively."""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        child_layout = item.layout()
        if child_layout is not None:
            _clear_layout(child_layout)


def _is_window_open(window):
    if window is None:
        return False
    try:
        return bool(window.isVisible())
    except RuntimeError:
        return False


def _short(text, limit=70):
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _nice_ceiling(value):
    if value <= 0:
        return 5.0
    base = 10 ** math.floor(math.log10(value))
    for multiplier in (1, 2, 2.5, 5, 10):
        if multiplier * base >= value:
            return multiplier * base
    return 10 * base


def _shift_month(first_of_month, months):
    index = first_of_month.year * 12 + (first_of_month.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def _status_color(status):
    value = str(status).lower()
    if value == "active":
        return PALETTE["success"]
    if value in ("inactive", "terminated", "resigned", "suspended"):
        return PALETTE["danger"]
    return PALETTE["warning"]


def _department_colors():
    return [
        PALETTE["accent"],
        PALETTE["success"],
        PALETTE["info"],
        PALETTE["secondary"],
        PALETTE["warning"],
        PALETTE["danger"],
    ]


# ============================================================
# DATA HELPERS (defensive: tolerate unknown model attributes)
# ============================================================

def _attr(obj, *names):
    """Return the first non-empty attribute among names, or None."""
    for name in names:
        value = getattr(obj, name, None)
        if value is not None and value != "":
            return value
    return None


def _to_date(value):
    """Normalize dates saved by older and newer employee forms.

    The employee form has historically stored dates as ``dd-MM-yyyy`` strings,
    while SQLAlchemy Date columns and newer code may return ``date`` objects or
    ISO strings. Accept these formats so the growth chart and recent table use
    the same real joining-date values without changing any database records.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    # First try ISO values, including ISO datetime strings.
    try:
        return date.fromisoformat(text[:10])
    except (TypeError, ValueError):
        pass

    # Compatibility with the formats used by the employee form and imports.
    for fmt in (
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%Y/%m/%d", "%Y-%m-%d",
        "%d-%m-%y", "%d/%m/%y",
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except (TypeError, ValueError):
            continue

    # Some older records may contain a datetime after the date portion.
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except (TypeError, ValueError):
            continue
    return None


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _department_name(employee):
    value = _attr(employee, "department_name", "department")
    if value is None:
        return None
    if not isinstance(value, str):
        value = getattr(value, "name", None) or getattr(value, "title", None) or ""
    value = str(value).strip()
    return value or None


def _summarize_employees(employees, data):
    """Fill data with employee-derived values. Only real records are used."""
    today = date.today()
    cutoff = today - timedelta(days=30)
    active_count = 0
    joined_dates = []
    department_counts = Counter()
    records = []

    for employee in employees:
        status = str(_attr(employee, "status", "employment_status") or "").strip()
        if status.lower() == "active":
            active_count += 1

        joined = _to_date(_attr(employee, "joining_date", "date_joined", "hire_date", "join_date"))
        if joined is not None:
            joined_dates.append(joined)

        department = _department_name(employee) or "Unassigned"
        department_counts[department] += 1

        name = _attr(employee, "full_name", "name")
        if name is None:
            parts = (_attr(employee, "first_name"), _attr(employee, "last_name"))
            name = " ".join(str(part) for part in parts if part)

        emp_id = _attr(employee, "employee_id", "emp_id", "id")
        record = {
            "id": str(emp_id) if emp_id is not None else "-",
            "name": str(name or "").strip() or "Unnamed",
            "department": department,
            "status": status or "Unknown",
            "joined": joined,
        }
        record["search_text"] = " ".join(
            [record["id"], record["name"], record["department"], record["status"]]
        ).lower()
        records.append(record)

    records.sort(
        key=lambda r: (r["joined"] is not None, r["joined"] or date.min),
        reverse=True,
    )

    data["total"] = len(employees)
    data["active"] = active_count
    data["new_last_30_days"] = sum(1 for d in joined_dates if d >= cutoff)
    data["recent"] = records

    # Cumulative headcount at the end of each of the last N months.
    if joined_dates:
        current_month = date(today.year, today.month, 1)
        labels, values = [], []
        for offset in range(-(GROWTH_MONTHS - 1), 1):
            month_start = _shift_month(current_month, offset)
            next_start = _shift_month(current_month, offset + 1)
            labels.append(month_start.strftime("%b %y"))
            values.append(sum(1 for d in joined_dates if d < next_start))
        data["growth_labels"] = labels
        data["growth_values"] = values

    ranked = department_counts.most_common()
    slices = ranked[:DEPARTMENT_SLICE_LIMIT]
    other = sum(count for _, count in ranked[DEPARTMENT_SLICE_LIMIT:])
    if other:
        slices.append(("Other", other))
    data["departments"] = slices


def collect_dashboard_data():
    """Gather all dashboard values from the service layer. No UI code here."""
    errors = {}
    data = {
        "total": None,
        "active": None,
        "present": None,
        "processed": None,
        "new_last_30_days": None,
        "growth_labels": [],
        "growth_values": [],
        "departments": [],
        "recent": [],
        "errors": errors,
    }

    try:
        _summarize_employees(list(get_all_employees() or []), data)
    except Exception as error:
        errors["Employees"] = str(error)
        data["total"] = data["active"] = data["new_last_30_days"] = None
        data["recent"] = []
        data["departments"] = []
        data["growth_labels"] = []
        data["growth_values"] = []
        print("Employee dashboard error:", error)

    try:
        attendance = get_attendance_statistics() or {}
        data["present"] = _as_int(attendance.get("present"))
    except Exception as error:
        errors["Attendance"] = str(error)
        print("Attendance dashboard error:", error)

    try:
        payroll = get_payroll_summary() or {}
        data["processed"] = _as_int(payroll.get("processed"))
    except Exception as error:
        errors["Payroll"] = str(error)
        print("Payroll dashboard error:", error)

    return data


# ============================================================
# WIDGETS
# ============================================================

class NavButton(QPushButton):
    """Sidebar navigation button. Supports active, danger, and collapsed states."""

    def __init__(self, icon, text, active=False, danger=False, parent=None):
        super().__init__(parent)
        self._active = active
        self._danger = danger

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setToolTip(text)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(13)

        self.icon_label = QLabel(icon)
        self.icon_label.setFixedWidth(25)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet(_label_qss(PALETTE["sidebar_text"], 17, 500))

        self.text_label = QLabel(text)
        self.text_label.setStyleSheet(
            _label_qss(PALETTE["sidebar_text"], 14, 600 if active else 500)
        )

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()

        self._apply_style()

    def _apply_style(self):
        if self._active:
            background = PALETTE["accent"]
            hover = PALETTE["accent_hover"]
        elif self._danger:
            background = "#431B2B"
            hover = "#5B2339"
        else:
            background = "transparent"
            hover = PALETTE["sidebar_hover"]

        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {background};
                border: none;
                border-radius: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
            QPushButton:pressed {{
                background: {PALETTE['sidebar_hover']};
            }}
            """
        )

    def set_collapsed(self, collapsed):
        self.text_label.setVisible(not collapsed)


class DashboardButton(QPushButton):
    """Quick action card with an icon, title, and subtitle."""

    def __init__(self, icon_text, title, subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("quickAction")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(68)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"""
            QPushButton#quickAction {{
                background: {PALETTE['surface']};
                border: 1px solid {PALETTE['border']};
                border-radius: 14px;
                text-align: left;
            }}
            QPushButton#quickAction:hover {{
                background: {PALETTE['accent_light']};
                border: 1px solid {PALETTE['accent']};
            }}
            QPushButton#quickAction:pressed {{
                background: {PALETTE['accent_light']};
            }}
            QPushButton#quickAction:focus {{
                border: 2px solid {PALETTE['accent']};
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        icon_frame = QFrame()
        icon_frame.setObjectName("quickIcon")
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(
            f"QFrame#quickIcon {{ background: {PALETTE['accent_light']}; "
            f"border: none; border-radius: 12px; }}"
        )
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = _make_label(icon_text, PALETTE["accent"], 19, 700)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.addWidget(_make_label(title, PALETTE["text"], 14, 700))
        if subtitle:
            text_layout.addWidget(_make_label(subtitle, PALETTE["text_muted"], 12))

        arrow = _make_label("›", PALETTE["text_muted"], 24)

        layout.addWidget(icon_frame)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(arrow)


class StatCard(QFrame):
    """Clickable KPI card with a count-up animation."""

    clicked = Signal()

    def __init__(self, title, icon, accent, accent_light, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Open {title}")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background: {PALETTE['surface']};
                border: 1px solid {PALETTE['border']};
                border-radius: 16px;
            }}
            QFrame#statCard:hover {{
                border: 2px solid {accent};
                background: {PALETTE["background"]};
            }}
            QFrame#statCard:focus {{
                border: 2px solid {accent};
            }}
            """
        )
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.addWidget(_make_label(title, PALETTE["text_muted"], 13, 600))
        top.addStretch()

        icon_frame = QFrame()
        icon_frame.setObjectName("statIcon")
        icon_frame.setFixedSize(42, 42)
        icon_frame.setStyleSheet(
            f"QFrame#statIcon {{ background: {accent_light}; border: none; border-radius: 12px; }}"
        )
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = _make_label(icon, accent, 18, 700)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)
        top.addWidget(icon_frame)
        layout.addLayout(top)

        self.value_label = _make_label("0", PALETTE["text"], 26, 700)
        layout.addWidget(self.value_label)

        self.subtitle_label = _make_label("", accent, 11, 700)
        layout.addWidget(self.subtitle_label)

        self._displayed = 0
        self._animation = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def set_value(self, value, subtitle="", animate=True):
        self.subtitle_label.setText(subtitle)
        if isinstance(value, int) and not isinstance(value, bool):
            self._count_to(value, animate)
        else:
            self._animation = _dispose_animation(self._animation)
            self.value_label.setText("—" if value is None else str(value))

    def _count_to(self, target, animate):
        self._animation = _dispose_animation(self._animation)
        start = self._displayed
        if not (ANIMATIONS_ENABLED and animate) or start == target:
            self._show_number(target)
            return
        self._animation = _make_animation(self, start, target, self._on_tick)
        self._animation.start()

    def _on_tick(self, value):
        self._show_number(int(value))

    def _show_number(self, value):
        self._displayed = value
        self.value_label.setText(f"{value:,}")


class StatusItem(QFrame):
    """Live health row showing whether a data source loaded successfully."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("statusItem")
        self.setStyleSheet(
            f"QFrame#statusItem {{ background: {PALETTE['surface']}; "
            f"border: 1px solid {PALETTE['border']}; border-radius: 10px; }}"
        )
        self.setMinimumHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self.dot = _make_label("●", PALETTE["text_muted"], 11)
        layout.addWidget(self.dot)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        text_layout.addWidget(_make_label(title, PALETTE["text"], 12, 700))
        self.detail_label = _make_label("Waiting for data…", PALETTE["text_muted"], 10)
        text_layout.addWidget(self.detail_label)
        layout.addLayout(text_layout, 1)

    def set_state(self, ok, detail):
        color = PALETTE["success"] if ok else PALETTE["danger"]
        self.dot.setStyleSheet(_label_qss(color, 11))
        self.detail_label.setText(detail)


class LineChartWidget(QWidget):
    """Custom-painted line chart with a left-to-right entrance animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._labels = []
        self._values = []
        self._progress = 1.0
        self._animation = None
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_series(self, labels, values, animate=True):
        self._labels = list(labels)
        self._values = [float(v) for v in values]
        self._animation = _dispose_animation(self._animation)
        if animate and ANIMATIONS_ENABLED and self._values:
            self._progress = 0.0
            self._animation = _make_animation(self, 0.0, 1.0, self._on_progress)
            self._animation.start()
        else:
            self._progress = 1.0
            self.update()

    def _on_progress(self, value):
        self._progress = float(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont("Segoe UI", 9))
        rect = QRectF(self.rect())

        if not self._values:
            painter.setPen(QColor(PALETTE["text_muted"]))
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                "No joining-date records yet.\nAdd employees to see growth.",
            )
            painter.end()
            return

        left, right, top, bottom = 44.0, 12.0, 10.0, 28.0
        plot = QRectF(
            rect.left() + left,
            rect.top() + top,
            rect.width() - left - right,
            rect.height() - top - bottom,
        )
        if plot.width() < 20 or plot.height() < 20:
            painter.end()
            return

        max_value = _nice_ceiling(max(self._values))

        # Grid and Y-axis labels.
        for i in range(5):
            y = plot.bottom() - plot.height() * i / 4
            painter.setPen(QColor(PALETTE["border"]))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor(PALETTE["text_muted"]))
            axis_value = max_value * i / 4
            painter.drawText(
                QRectF(rect.left(), y - 9, left - 8, 18),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{axis_value:g}",
            )

        # Point positions.
        count = len(self._values)
        step = plot.width() / (count - 1) if count > 1 else 0.0
        points = []
        for index, value in enumerate(self._values):
            x = plot.left() + step * index if count > 1 else plot.center().x()
            y = plot.bottom() - plot.height() * (value / max_value)
            points.append(QPointF(x, y))

        line_color = QColor(PALETTE["accent"])

        # Clip to the animation progress so the line draws in from the left.
        painter.save()
        painter.setClipRect(
            QRectF(0, 0, plot.left() + plot.width() * self._progress + 12, rect.height())
        )

        path = QPainterPath()
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)

        fill_path = QPainterPath(path)
        fill_path.lineTo(points[-1].x(), plot.bottom())
        fill_path.lineTo(points[0].x(), plot.bottom())
        fill_path.closeSubpath()

        fill_color = QColor(line_color)
        fill_color.setAlpha(45)
        painter.fillPath(fill_path, fill_color)

        painter.setPen(_pen(line_color.name(), 3.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        painter.setPen(_pen(line_color.name(), 2.0))
        painter.setBrush(QColor(PALETTE["surface"]))
        for point in points:
            painter.drawEllipse(point, 4.5, 4.5)
        painter.restore()

        # X-axis labels (always visible).
        painter.setPen(QColor(PALETTE["text_muted"]))
        for index, label in enumerate(self._labels[:count]):
            x = points[index].x()
            painter.drawText(
                QRectF(x - 30, plot.bottom() + 6, 60, 18),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

        painter.end()


class DonutChartWidget(QWidget):
    """Custom-painted donut chart with a sweep-in animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slices = []
        self._progress = 1.0
        self._animation = None
        self.setMinimumSize(180, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_slices(self, slices, animate=True):
        """slices: list of (label, count, color)."""
        self._slices = list(slices)
        self._animation = _dispose_animation(self._animation)
        if animate and ANIMATIONS_ENABLED and self._slices:
            self._progress = 0.0
            self._animation = _make_animation(self, 0.0, 1.0, self._on_progress)
            self._animation.start()
        else:
            self._progress = 1.0
            self.update()

    def _on_progress(self, value):
        self._progress = float(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())

        size = min(rect.width(), rect.height()) - 12
        if size <= 20:
            painter.end()
            return

        outer = QRectF((rect.width() - size) / 2, (rect.height() - size) / 2, size, size)
        ring = max(14.0, size * 0.16)
        arc_rect = outer.adjusted(ring / 2, ring / 2, -ring / 2, -ring / 2)

        total = sum(count for _, count, _ in self._slices)

        if total <= 0:
            painter.setPen(_pen(PALETTE["border"], ring))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(arc_rect)
            painter.setFont(QFont("Segoe UI", 10))
            painter.setPen(QColor(PALETTE["text_muted"]))
            painter.drawText(outer, Qt.AlignmentFlag.AlignCenter, "No data")
            painter.end()
            return

        start_angle = 90.0
        for _name, count, color in self._slices:
            full_span = 360.0 * (count / total)
            visible_span = full_span * self._progress
            if visible_span > 0:
                pen = _pen(color, ring)
                pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawArc(arc_rect, int(start_angle * 16), int(-visible_span * 16))
            start_angle -= full_span

        painter.setPen(QColor(PALETTE["text"]))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(
            QRectF(outer.left(), outer.center().y() - 30, outer.width(), 30),
            Qt.AlignmentFlag.AlignCenter,
            f"{total:,}",
        )
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor(PALETTE["text_muted"]))
        painter.drawText(
            QRectF(outer.left(), outer.center().y() + 2, outer.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "Total",
        )
        painter.end()


# ============================================================
# DASHBOARD WINDOW
# ============================================================

class DashboardWindow(QWidget):

    def __init__(self):
        super().__init__()

        # Window references (kept so windows are not garbage-collected).
        self.employee_window = None
        self.attendance_window = None
        self.payroll_window = None
        self.performance_window = None
        self.calendar_window = None
        self.settings_window = None
        self.reports_window = None
        self.quality_window = None
        self.notifications_window = None

        # State
        self.sidebar_collapsed = False
        self.sidebar = None
        self.sidebar_layout = None
        self.sidebar_text_widgets = []
        self.nav_buttons = []
        self.settings_nav = None
        self.logout_nav = None
        self.welcome_card = None
        self.welcome_animation = None
        self.clock_label = None
        self.search_input = None
        self.recent_table = None
        self.recent_title_label = None
        self.table_footer_label = None
        self.last_updated_label = None
        self.legend_layout = None
        self.status_items = {}
        self._all_recent_rows = []
        self._search_text = ""

        self.setWindowTitle("Employee Management System")
        self.setMinimumSize(1100, 700)
        self.resize(1450, 850)

        apply_dashboard_theme_colors()
        self.setup_ui()
        self.load_dashboard_data()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        QTimer.singleShot(120, self.start_welcome_animation)

    # ========================================================
    # THEME REFRESH
    # ========================================================

    def refresh_theme(self):
        """
        Rebuild the same Dashboard with the newly selected theme colors.
        Settings calls this after the user applies a theme.
        """
        try:
            self._stop_all_animations()
            self.welcome_animation = None

            apply_dashboard_theme_colors()

            _clear_layout(self.layout())
            self.setup_ui()
            self.load_dashboard_data()

            QTimer.singleShot(120, self.start_welcome_animation)
            print("Dashboard theme refreshed successfully!")

        except Exception as error:
            print("Dashboard theme refresh error:", error)
            QMessageBox.warning(
                self,
                "Theme",
                f"Unable to refresh the dashboard theme.\n\n{error}",
            )

    def _stop_all_animations(self):
        for animation in self.findChildren(QAbstractAnimation):
            animation.stop()

    # ========================================================
    # MAIN LAYOUT
    # ========================================================

    def setup_ui(self):
        main_layout = self.layout()
        if main_layout is None:
            main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._build_sidebar())

        content = QWidget()
        content.setObjectName("contentArea")
        content.setStyleSheet(
            f"QWidget#contentArea {{ background: {PALETTE['background']}; }}"
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_top_bar())

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet(
            f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0px; }}
            QScrollBar::handle:vertical {{
                background: {PALETTE['border']};
                border-radius: 5px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {PALETTE['text_muted']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            """
        )

        self.content_widget = self._build_page()
        self.scroll_area.setWidget(self.content_widget)
        content_layout.addWidget(self.scroll_area, 1)

        main_layout.addWidget(content, 1)

    # ========================================================
    # SIDEBAR
    # ========================================================

    def _section_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(
            f"""
            QLabel {{
                color: {PALETTE['accent_light']};
                background: {PALETTE['sidebar_hover']};
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 10px;
                font-weight: 800;
            }}
            """
        )
        return label

    def _build_sidebar(self):
        collapsed = self.sidebar_collapsed
        margin = 12 if collapsed else 18

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(
            f"""
            QFrame#sidebar {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {PALETTE['sidebar']},
                    stop: 1 {PALETTE['sidebar_hover']}
                );
                border: none;
            }}
            """
        )
        sidebar.setFixedWidth(COLLAPSED_SIDEBAR_WIDTH if collapsed else EXPANDED_SIDEBAR_WIDTH)
        self.sidebar = sidebar

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(margin, 20, margin, 18)
        layout.setSpacing(8)
        self.sidebar_layout = layout

        self.sidebar_text_widgets = []
        self.nav_buttons = []

        # Logo
        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)

        logo_frame = QFrame()
        logo_frame.setObjectName("logoBadge")
        logo_frame.setFixedSize(60, 60)
        logo_frame.setStyleSheet(
            f"QFrame#logoBadge {{ background: {PALETTE['accent']}; "
            f"border: none; border-radius: 17px; }}"
        )
        logo_inner = QVBoxLayout(logo_frame)
        logo_inner.setContentsMargins(0, 0, 0, 0)
        logo_text = _make_label("EMS", PALETTE["sidebar_text"], 19, 800)
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_inner.addWidget(logo_text)
        logo_row.addWidget(logo_frame)

        logo_title_box = QWidget()
        logo_title_layout = QVBoxLayout(logo_title_box)
        logo_title_layout.setContentsMargins(0, 0, 0, 0)
        logo_title_layout.setSpacing(0)
        logo_title_layout.addWidget(_make_label("Employee", PALETTE["sidebar_text"], 16, 800))
        logo_title_layout.addWidget(
            _make_label("Management System", PALETTE["sidebar_muted"], 10)
        )
        logo_row.addWidget(logo_title_box)
        logo_row.addStretch()
        self.sidebar_text_widgets.append(logo_title_box)

        layout.addLayout(logo_row)
        layout.addSpacing(18)

        menu_title = self._section_label("MAIN MENU")
        layout.addWidget(menu_title)
        self.sidebar_text_widgets.append(menu_title)
        layout.addSpacing(4)

        nav_items = [
            ("⌂", "Dashboard", self.scroll_to_top),
            ("♙", "Employees", self.open_employee_management),
            ("◷", "Attendance", self.open_attendance),
            ("₹", "Payroll", self.open_payroll),
            ("★", "Performance", self.open_performance),
            ("□", "Calendar", self.open_calendar),
            ("▤", "Reports", self.open_reports),
            ("◆", "Quality Management", self.open_quality),
            ("🔔", "Notifications", self.open_notifications),
        ]

        for icon, text, handler in nav_items:
            button = NavButton(icon, text, active=(text == "Dashboard"))
            button.clicked.connect(handler)
            layout.addWidget(button)
            self.nav_buttons.append(button)

        layout.addStretch()

        system_title = self._section_label("SYSTEM")
        layout.addWidget(system_title)
        self.sidebar_text_widgets.append(system_title)

        self.settings_nav = NavButton("⚙", "Settings")
        self.settings_nav.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_nav)
        self.nav_buttons.append(self.settings_nav)

        self.logout_nav = NavButton("⇥", "Logout", danger=True)
        self.logout_nav.clicked.connect(self.logout)
        layout.addWidget(self.logout_nav)
        self.nav_buttons.append(self.logout_nav)

        footer = _make_label(
            "Employee Management System\nVersion 1.0", PALETTE["sidebar_muted"], 9
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        self.sidebar_text_widgets.append(footer)

        for button in self.nav_buttons:
            button.set_collapsed(collapsed)
        for widget in self.sidebar_text_widgets:
            widget.setVisible(not collapsed)

        return sidebar

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed
        collapsed = self.sidebar_collapsed

        if self.sidebar is not None:
            self.sidebar.setFixedWidth(
                COLLAPSED_SIDEBAR_WIDTH if collapsed else EXPANDED_SIDEBAR_WIDTH
            )
        if self.sidebar_layout is not None:
            margin = 12 if collapsed else 18
            self.sidebar_layout.setContentsMargins(margin, 20, margin, 18)

        for widget in self.sidebar_text_widgets:
            widget.setVisible(not collapsed)
        for button in self.nav_buttons:
            button.set_collapsed(collapsed)

    # ========================================================
    # TOP BAR
    # ========================================================

    def _icon_button(self, text, tooltip):
        button = QPushButton(text)
        button.setObjectName("topIcon")
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(40, 40)
        button.setStyleSheet(
            f"""
            QPushButton#topIcon {{
                background: {PALETTE['background']};
                color: {PALETTE['text']};
                border: 1px solid {PALETTE['border']};
                border-radius: 12px;
                font-size: 16px;
            }}
            QPushButton#topIcon:hover {{
                background: {PALETTE['accent_light']};
                border: 1px solid {PALETTE['accent']};
            }}
            QPushButton#topIcon:pressed {{ background: {PALETTE['accent_light']}; }}
            """
        )
        return button

    def _build_top_bar(self):
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(72)
        bar.setStyleSheet(
            f"QFrame#topBar {{ background: {PALETTE['surface']}; border: none; "
            f"border-bottom: 1px solid {PALETTE['border']}; }}"
        )

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(14)

        menu_button = self._icon_button("☰", "Collapse or expand the sidebar")
        menu_button.clicked.connect(self.toggle_sidebar)
        layout.addWidget(menu_button)

        # Set the saved text BEFORE connecting the signal so the table is not
        # rendered against stale widgets during a theme rebuild.
        self.search_input = QLineEdit()
        self.search_input.setText(self._search_text)
        self.search_input.setPlaceholderText("Search employees by name, ID or department…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumHeight(40)
        self.search_input.setMinimumWidth(260)
        self.search_input.setMaximumWidth(520)
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: {PALETTE['background']};
                color: {PALETTE['text']};
                border: 1px solid {PALETTE['border']};
                border-radius: 12px;
                padding: 0px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {PALETTE['accent']}; }}
            """
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input, 1)

        notifications_button = self._icon_button("🔔", "Open notifications")
        notifications_button.clicked.connect(self.open_notifications)
        layout.addWidget(notifications_button)

        fullscreen_button = self._icon_button("⛶", "Toggle full screen")
        fullscreen_button.clicked.connect(self.toggle_fullscreen)
        layout.addWidget(fullscreen_button)

        self.clock_label = _make_label("", PALETTE["text"], 12, 700)
        self.clock_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.clock_label)

        layout.addWidget(self._build_user_card())
        return bar

    def _build_user_card(self):
        card = QFrame()
        card.setObjectName("userCard")
        card.setStyleSheet(
            f"QFrame#userCard {{ background: {PALETTE['background']}; "
            f"border: 1px solid {PALETTE['border']}; border-radius: 14px; }}"
        )

        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 6, 14, 6)
        layout.setSpacing(10)

        avatar = QLabel(self.get_user_initial())
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"QLabel {{ background: {PALETTE['accent_light']}; color: {PALETTE['accent']}; "
            f"border: none; border-radius: 20px; font-size: 16px; font-weight: 800; }}"
        )
        layout.addWidget(avatar)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        self.user_name_label = _make_label(self.get_user_name(), PALETTE["text"], 13, 800)
        self.user_role_label = _make_label(self.get_user_role(), PALETTE["text_muted"], 11)
        text_layout.addWidget(self.user_name_label)
        text_layout.addWidget(self.user_role_label)
        layout.addLayout(text_layout)

        return card

    def _on_search_changed(self, text):
        self._search_text = text
        self._render_recent_table()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _update_clock(self):
        if self.clock_label is None:
            return
        self.clock_label.setText(datetime.now().strftime("%a, %d %b %Y\n%I:%M %p"))

    # ========================================================
    # PAGE
    # ========================================================

    def _card(self, object_name):
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setStyleSheet(
            f"QFrame#{object_name} {{ background: {PALETTE['surface']}; "
            f"border: 1px solid {PALETTE['border']}; border-radius: 16px; }}"
        )
        return frame

    def _build_page(self):
        page = QWidget()
        page.setObjectName("dashboardPage")
        page.setStyleSheet(
            f"QWidget#dashboardPage {{ background: {PALETTE['background']}; }}"
        )

        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 26, 32, 30)
        layout.setSpacing(22)

        layout.addLayout(self._build_page_header())
        layout.addWidget(self._build_welcome_banner())
        layout.addLayout(self._build_kpi_row())
        layout.addLayout(self._build_chart_row())
        layout.addLayout(self._build_bottom_row())
        layout.addStretch()

        return page

    def _build_page_header(self):
        row = QHBoxLayout()

        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(_make_label("Dashboard", PALETTE["text"], 28, 800))
        titles.addWidget(
            _make_label("Overview of your employee management system", PALETTE["text_muted"], 14)
        )
        row.addLayout(titles)
        row.addStretch()

        self.last_updated_label = _make_label("", PALETTE["text_muted"], 12)
        row.addWidget(self.last_updated_label, 0, Qt.AlignmentFlag.AlignBottom)
        return row

    def _build_welcome_banner(self):
        card = QFrame()
        card.setObjectName("welcomeBanner")
        card.setMinimumHeight(140)
        card.setStyleSheet(
            """
            QFrame#welcomeBanner {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1E3A8A, stop: 0.55 #2346A0, stop: 1 #2563EB
                );
                border: none;
                border-radius: 18px;
            }
            """
        )
        self.welcome_card = card

        layout = QHBoxLayout(card)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        text_column = QVBoxLayout()
        text_column.setSpacing(6)
        text_column.addWidget(
            _make_label(f"Welcome back, {self.get_user_name()}! 👋", "#FFFFFF", 22, 800)
        )
        text_column.addWidget(
            _make_label(
                "Manage employees, attendance, payroll and performance from one place.",
                "#DBEAFE",
                13,
            )
        )
        layout.addLayout(text_column, 1)

        badge = QFrame()
        badge.setObjectName("welcomeBadge")
        badge.setFixedSize(90, 90)
        badge.setStyleSheet(
            "QFrame#welcomeBadge { background: rgba(255,255,255,0.14); "
            "border: 1px solid rgba(255,255,255,0.28); border-radius: 45px; }"
        )
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_label = _make_label("EMS", "#FFFFFF", 22, 800)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addWidget(badge_label)
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)

        return card

    def _build_kpi_row(self):
        row = QHBoxLayout()
        row.setSpacing(16)

        self.kpi_total = StatCard(
            "Total Employees", "♟", PALETTE["accent"], PALETTE["accent_light"]
        )
        self.kpi_active = StatCard(
            "Active Employees", "✓", PALETTE["success"], PALETTE["success_light"]
        )
        self.kpi_present = StatCard(
            "Present (Attendance)", "◷", PALETTE["info"], PALETTE["info_light"]
        )
        self.kpi_payroll = StatCard(
            "Processed Payroll", "₹", PALETTE["secondary"], PALETTE["secondary_light"]
        )

        # KPI cards are interactive shortcuts to their actual modules.
        self.kpi_total.clicked.connect(self.open_employee_management)
        self.kpi_active.clicked.connect(self.open_employee_management)
        self.kpi_present.clicked.connect(self.open_attendance)
        self.kpi_payroll.clicked.connect(self.open_payroll)

        for card in (self.kpi_total, self.kpi_active, self.kpi_present, self.kpi_payroll):
            row.addWidget(card, 1)

        return row

    def _build_chart_row(self):
        row = QHBoxLayout()
        row.setSpacing(18)

        growth_card = self._card("growthCard")
        growth_layout = QVBoxLayout(growth_card)
        growth_layout.setContentsMargins(22, 20, 22, 18)
        growth_layout.setSpacing(8)
        growth_layout.addWidget(_make_label("Employee Growth", PALETTE["text"], 17, 800))
        growth_layout.addWidget(
            _make_label(
                f"Cumulative headcount over the last {GROWTH_MONTHS} months, from joining dates",
                PALETTE["text_muted"],
                12,
            )
        )
        self.growth_chart = LineChartWidget()
        growth_layout.addWidget(self.growth_chart, 1)
        row.addWidget(growth_card, 3)

        department_card = self._card("departmentCard")
        department_layout = QVBoxLayout(department_card)
        department_layout.setContentsMargins(22, 20, 22, 18)
        department_layout.setSpacing(8)
        department_layout.addWidget(
            _make_label("Department Distribution", PALETTE["text"], 17, 800)
        )
        department_layout.addWidget(
            _make_label("Employees per department", PALETTE["text_muted"], 12)
        )

        body = QHBoxLayout()
        body.setSpacing(16)
        self.department_chart = DonutChartWidget()
        body.addWidget(self.department_chart, 1)

        legend_box = QWidget()
        self.legend_layout = QVBoxLayout(legend_box)
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        self.legend_layout.setSpacing(8)
        body.addWidget(legend_box, 1)

        department_layout.addLayout(body, 1)
        row.addWidget(department_card, 2)

        return row

    def _build_bottom_row(self):
        row = QHBoxLayout()
        row.setSpacing(18)

        # ---------- Recent employees table ----------
        table_card = self._card("recentCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(22, 20, 22, 18)
        table_layout.setSpacing(12)

        header = QHBoxLayout()
        self.recent_title_label = _make_label("Recent Employees", PALETTE["text"], 17, 800)
        header.addWidget(self.recent_title_label)
        header.addStretch()

        refresh_button = QPushButton("⟳  Refresh")
        refresh_button.setObjectName("refreshButton")
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.setFixedHeight(34)
        refresh_button.setStyleSheet(
            f"""
            QPushButton#refreshButton {{
                background: {PALETTE['accent_light']};
                color: {PALETTE['accent']};
                border: none;
                border-radius: 10px;
                padding: 0px 14px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton#refreshButton:hover {{ background: {PALETTE['accent']}; color: #FFFFFF; }}
            QPushButton#refreshButton:pressed {{ background: {PALETTE['accent_hover']}; color: #FFFFFF; }}
            """
        )
        refresh_button.clicked.connect(self.load_dashboard_data)
        header.addWidget(refresh_button)
        table_layout.addLayout(header)

        table_layout.addWidget(
            _make_label(
                "Newest joiners first. Use the search bar to find any employee.",
                PALETTE["text_muted"],
                12,
            )
        )

        self.recent_table = self._build_recent_table()
        table_layout.addWidget(self.recent_table, 1)

        self.table_footer_label = _make_label("", PALETTE["text_muted"], 11)
        table_layout.addWidget(self.table_footer_label)

        row.addWidget(table_card, 3)

        # ---------- Right column: quick actions + system status ----------
        side = QVBoxLayout()
        side.setSpacing(18)

        actions_card = self._card("quickCard")
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(22, 20, 22, 18)
        actions_layout.setSpacing(10)
        actions_layout.addWidget(_make_label("Quick Actions", PALETTE["text"], 17, 800))
        actions_layout.addWidget(
            _make_label("Frequently used modules", PALETTE["text_muted"], 12)
        )

        quick_actions = [
            ("♙", "Manage Employees", "Add, edit and manage employees", self.open_employee_management),
            ("◷", "Attendance", "Track daily attendance", self.open_attendance),
            ("₹", "Payroll", "Process salary and payslips", self.open_payroll),
            ("★", "Performance", "Review employee performance", self.open_performance),
            ("▤", "Reports", "Generate and view reports", self.open_reports),
            ("□", "Calendar", "Meetings and events", self.open_calendar),
        ]
        for icon, title, subtitle, handler in quick_actions:
            button = DashboardButton(icon, title, subtitle)
            button.clicked.connect(handler)
            actions_layout.addWidget(button)

        side.addWidget(actions_card)

        status_card = self._card("statusCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(22, 20, 22, 18)
        status_layout.setSpacing(10)
        status_layout.addWidget(_make_label("System Status", PALETTE["text"], 17, 800))
        status_layout.addWidget(
            _make_label("Live health of data sources", PALETTE["text_muted"], 12)
        )

        self.status_items = {}
        for key in ("Employees", "Attendance", "Payroll"):
            item = StatusItem(key)
            self.status_items[key] = item
            status_layout.addWidget(item)

        side.addWidget(status_card)
        side.addStretch()

        row.addLayout(side, 2)
        return row

    def _build_recent_table(self):
        table = QTableWidget(0, 5)
        table.setObjectName("recentTable")
        table.setHorizontalHeaderLabels(["ID", "Name", "Department", "Status", "Joining Date"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setShowGrid(False)
        table.setSortingEnabled(True)
        table.setMinimumHeight(320)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setHighlightSections(False)

        table.setStyleSheet(
            f"""
            QTableWidget#recentTable {{
                background: {PALETTE['surface']};
                color: {PALETTE['text']};
                border: none;
                selection-background-color: {PALETTE['accent_light']};
                selection-color: {PALETTE['text']};
            }}
            QTableWidget#recentTable::item {{
                padding: 6px;
                border-bottom: 1px solid {PALETTE['border']};
            }}
            QHeaderView::section {{
                background: {PALETTE['surface']};
                color: {PALETTE['text_muted']};
                border: none;
                border-bottom: 1px solid {PALETTE['border']};
                padding: 8px 6px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )
        return table

    def _render_recent_table(self):
        """Show the newest employees, or search results across all employees."""
        table = self.recent_table
        if table is None or self.recent_title_label is None:
            return

        query = self._search_text.strip().lower()
        rows = self._all_recent_rows

        if query:
            matches = [row for row in rows if query in row["search_text"]]
            visible = matches[:SEARCH_ROW_LIMIT]
            self.recent_title_label.setText("Search Results")
            footer = f"{len(matches)} match(es)"
            if len(matches) > SEARCH_ROW_LIMIT:
                footer += f" — showing the first {SEARCH_ROW_LIMIT}"
        else:
            visible = rows[:RECENT_ROW_LIMIT]
            self.recent_title_label.setText("Recent Employees")
            footer = (
                f"Showing {len(visible)} of {len(rows)} employee(s)"
                if rows
                else "No employees found. Add employees in Employee Management."
            )
        self.table_footer_label.setText(footer)

        table.setSortingEnabled(False)
        table.setRowCount(0)
        for record in visible:
            row_index = table.rowCount()
            table.insertRow(row_index)
            joined_text = record["joined"].strftime("%d %b %Y") if record["joined"] else "—"
            values = [
                record["id"],
                record["name"],
                record["department"],
                record["status"],
                joined_text,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                if column == 3:
                    item.setForeground(QBrush(QColor(_status_color(record["status"]))))
                table.setItem(row_index, column, item)
        table.setSortingEnabled(True)

    def _rebuild_legend(self, slices):
        _clear_layout(self.legend_layout)

        if not slices:
            self.legend_layout.addWidget(
                _make_label("No department data yet.", PALETTE["text_muted"], 12)
            )
            self.legend_layout.addStretch()
            return

        total = sum(count for _, count, _ in slices)
        for name, count, color in slices:
            row = QHBoxLayout()
            row.setSpacing(8)
            percent = (count / total * 100) if total else 0
            row.addWidget(_make_label("●", color, 12))
            row.addWidget(_make_label(name, PALETTE["text"], 12, 600), 1)
            row.addWidget(_make_label(f"{count}", PALETTE["text"], 12, 700))
            row.addWidget(_make_label(f"{percent:.1f}%", PALETTE["text_muted"], 11))
            self.legend_layout.addLayout(row)

        self.legend_layout.addStretch()

    # ========================================================
    # DATA
    # ========================================================

    def load_dashboard_data(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            data = collect_dashboard_data()
            self._apply_data(data)
        except Exception as error:
            print("Dashboard data error:", error)
            QMessageBox.warning(
                self,
                "Dashboard",
                f"Unable to refresh dashboard data.\n\n{error}",
            )
        finally:
            QApplication.restoreOverrideCursor()

    def _apply_data(self, data):
        errors = data["errors"]

        # KPI cards
        total = data["total"]
        active = data["active"]
        new_30 = data["new_last_30_days"]

        if total is None:
            self.kpi_total.set_value(None, "Employee data unavailable")
            self.kpi_active.set_value(None, "Employee data unavailable")
        else:
            self.kpi_total.set_value(
                total,
                f"+{new_30} joined in last 30 days" if new_30 else "Employees on record",
            )
            percent = (active / total * 100) if total else 0
            self.kpi_active.set_value(active, f"{percent:.0f}% of workforce")

        present = data["present"]
        if present is None:
            reason = "Attendance data unavailable" if "Attendance" in errors else "No count returned"
            self.kpi_present.set_value(None, reason)
        else:
            # Do not show a percentage here: the legacy service may count multiple
            # attendance rows per employee. The attendance screen is the source of detail.
            subtitle = "Present today"
            if total is not None and present > total:
                subtitle = "Check attendance records"
            self.kpi_present.set_value(present, subtitle)

        processed = data["processed"]
        if processed is None:
            reason = "Payroll data unavailable" if "Payroll" in errors else "No count returned"
            self.kpi_payroll.set_value(None, reason)
        else:
            self.kpi_payroll.set_value(processed, "Payroll records · click to open")

        # Charts
        self.growth_chart.set_series(data["growth_labels"], data["growth_values"])

        colors = _department_colors()
        colored_slices = []
        for index, (name, count) in enumerate(data["departments"]):
            if name == "Other":
                color = PALETTE["text_muted"]
            else:
                color = colors[index % len(colors)]
            colored_slices.append((name, count, color))

        self.department_chart.set_slices(
            [(name, count, color) for name, count, color in colored_slices]
        )
        self._rebuild_legend(colored_slices)

        # Table
        self._all_recent_rows = data["recent"]
        self._render_recent_table()

        # System status
        for key, item in self.status_items.items():
            if key in errors:
                item.set_state(False, f"Unavailable: {_short(errors[key])}")
            else:
                item.set_state(True, "Data loaded successfully")

        # Footer timestamp
        timestamp = datetime.now().strftime("%I:%M %p")
        if errors:
            self.last_updated_label.setText(
                f"Updated {timestamp} · {len(errors)} data source(s) unavailable"
            )
        else:
            self.last_updated_label.setText(f"Updated {timestamp}")

    # ========================================================
    # ANIMATION
    # ========================================================

    def start_welcome_animation(self):
        card = self.welcome_card
        if card is None or not ANIMATIONS_ENABLED:
            return

        try:
            if self.welcome_animation is not None:
                self.welcome_animation.stop()
        except RuntimeError:
            pass

        effect = QGraphicsOpacityEffect(card)
        effect.setOpacity(0.0)
        card.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", card)
        animation.setDuration(700)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.welcome_animation = animation
        animation.start()

    # ========================================================
    # NAVIGATION
    # ========================================================

    def scroll_to_top(self):
        self.scroll_area.verticalScrollBar().setValue(0)

    def _instantiate_window(self, window_class):
        try:
            return window_class()
        except TypeError:
            return window_class(self)

    def _open_module_window(self, attribute_name, candidates, title):
        """
        Open a window from the first importable (module, class) candidate.
        Missing modules show a friendly message. Other errors are displayed,
        never silently ignored.
        """
        existing = getattr(self, attribute_name, None)
        if _is_window_open(existing):
            existing.show()
            existing.raise_()
            existing.activateWindow()
            return

        for module_name, class_name in candidates:
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError as error:
                if error.name == module_name:
                    continue
                self._show_module_error(title, error)
                return
            except Exception as error:
                self._show_module_error(title, error)
                return

            window_class = getattr(module, class_name, None)
            if window_class is None:
                continue

            try:
                window = self._instantiate_window(window_class)
            except Exception as error:
                self._show_module_error(title, error)
                return

            setattr(self, attribute_name, window)
            window.show()
            window.raise_()
            window.activateWindow()
            return

        QMessageBox.information(
            self,
            title,
            f"{title} module is not available yet.",
        )

    def _show_module_error(self, title, error):
        QMessageBox.warning(
            self,
            f"{title} Error",
            f"Unable to open {title}.\n\n{error}",
        )

    def open_employee_management(self):
        self._open_module_window(
            "employee_window",
            (("ui.employees", "EmployeeManagementWindow"),),
            "Employee Management",
        )

    def open_attendance(self):
        self._open_module_window(
            "attendance_window",
            (("ui.attendance", "AttendanceWindow"),),
            "Attendance",
        )

    def open_payroll(self):
        self._open_module_window(
            "payroll_window",
            (("ui.payroll", "PayrollWindow"),),
            "Payroll",
        )

    def open_performance(self):
        self._open_module_window(
            "performance_window",
            (("ui.performance", "PerformanceWindow"),),
            "Performance",
        )

    def open_calendar(self):
        self._open_module_window(
            "calendar_window",
            (("ui.calendar", "CalendarWindow"),),
            "Calendar",
        )

    def open_reports(self):
        self._open_module_window(
            "reports_window",
            (("ui.reports", "ReportsWindow"), ("ui.report", "ReportsWindow")),
            "Reports",
        )

    def open_quality(self):
        self._open_module_window(
            "quality_window",
            (("ui.quality", "QualityManagementWindow"), ("ui.quality", "QualityWindow")),
            "Quality Management",
        )

    def open_notifications(self):
        """Open the admin composer for persistent HR/employee notifications."""
        role = self.get_user_role().strip().lower().replace("_", " ")
        if role not in {"admin", "administrator"}:
            QMessageBox.warning(
                self,
                "Permission denied",
                "Only an Admin can send company-wide notifications.",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Send Company Notification")
        dialog.setMinimumWidth(560)
        dialog.setStyleSheet("""
            QDialog { background: #F8FAFC; }
            QLabel { color: #0F172A; font-size: 13px; }
            QLineEdit, QTextEdit, QComboBox {
                background: white; color: #0F172A; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 8px; font-size: 13px;
            }
            QPushButton {
                background: #2563EB; color: white; border: none;
                border-radius: 8px; padding: 9px 16px; font-weight: 600;
            }
            QPushButton:hover { background: #1D4ED8; }
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        heading = QLabel("Send a message to all active HR and employee accounts")
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        heading.setWordWrap(True)
        layout.addWidget(heading)

        form = QFormLayout()
        title_input = QLineEdit()
        title_input.setMaxLength(200)
        title_input.setPlaceholderText("e.g. Monthly meeting announcement")
        message_input = QTextEdit()
        message_input.setPlaceholderText("Write your message here...")
        message_input.setMinimumHeight(135)
        type_input = QComboBox()
        type_input.addItems(["Announcement", "General", "Important", "Reminder"])
        form.addRow("Title:", title_input)
        form.addRow("Message:", message_input)
        form.addRow("Type:", type_input)
        layout.addLayout(form)

        hint = QLabel("Messages are saved in the existing database and remain available after restart.")
        hint.setStyleSheet("color: #64748B; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_button = QPushButton("Cancel")
        send_button = QPushButton("Send to Everyone")
        cancel_button.setStyleSheet("QPushButton { background: #E2E8F0; color: #0F172A; }")
        buttons.addWidget(cancel_button)
        buttons.addWidget(send_button)
        layout.addLayout(buttons)
        cancel_button.clicked.connect(dialog.reject)

        def send_notification():
            title = title_input.text().strip()
            message = message_input.toPlainText().strip()
            if not title or not message:
                QMessageBox.warning(dialog, "Missing information", "Enter both a title and a message.")
                return

            db = SessionLocal()
            try:
                users = db.query(User).all()
                recipients = []
                accepted_roles = {
                    "hr", "hr manager", "hrmanager", "hr executive",
                    "human resources", "human resource", "employee", "staff",
                }
                inactive_statuses = {"blocked", "inactive", "disabled", "0", "false", "terminated"}
                for user in users:
                    user_role = " ".join(
                        str(getattr(user, "role", "") or "").strip().lower().replace("_", " ").split()
                    )
                    if user_role not in accepted_roles:
                        continue
                    status_value = getattr(user, "status", None)
                    if status_value is not None:
                        status = str(status_value).strip().lower()
                        if status in inactive_statuses:
                            continue
                    recipients.append(user)

                if not recipients:
                    QMessageBox.information(
                        dialog, "No recipients",
                        "No HR or employee accounts were found. Nothing was sent.",
                    )
                    return

                for recipient in recipients:
                    db.add(Notification(
                        user_id=recipient.id,
                        title=title,
                        message=message,
                        notification_type=type_input.currentText(),
                        is_read=False,
                    ))
                db.commit()
                QMessageBox.information(
                    dialog,
                    "Notification sent",
                    f"Saved notification for {len(recipients)} HR/employee account(s). "
                    "HR and employee accounts can read it from their dashboard notification bell.",
                )
                dialog.accept()
            except Exception as error:
                db.rollback()
                QMessageBox.critical(
                    dialog, "Notification failed",
                    f"The notification could not be saved. Existing records were not intentionally changed.\n\n{error}",
                )
            finally:
                db.close()

        send_button.clicked.connect(send_notification)
        dialog.exec()

    def open_settings(self):
        self._open_module_window(
            "settings_window",
            (("ui.settings", "SettingsWindow"), ("ui.settings", "SettingsDialog")),
            "Settings",
        )

        # Refresh Dashboard after Settings applies a new theme.
        settings_window = getattr(self, "settings_window", None)
        if settings_window is not None and hasattr(settings_window, "theme_changed"):
            try:
                settings_window.theme_changed.disconnect(self.refresh_theme)
            except (TypeError, RuntimeError):
                pass
            settings_window.theme_changed.connect(self.refresh_theme)

    # ========================================================
    # USER INFORMATION
    # ========================================================

    def get_user_name(self):
        user = Session.get_user()
        if user is None:
            return "User"
        return (
            getattr(user, "username", None)
            or getattr(user, "full_name", None)
            or "User"
        )

    def get_user_role(self):
        user = Session.get_user()
        if user is None:
            return "User"
        return str(getattr(user, "role", "User"))

    def get_user_initial(self):
        name = self.get_user_name()
        if not name:
            return "U"
        return name[0].upper()

    # ========================================================
    # LOGOUT
    # ========================================================

    def logout(self):
        answer = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
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
                f"Unable to return to login screen.\n\n{error}",
            )


# ============================================================
# END OF DASHBOARD
# ============================================================