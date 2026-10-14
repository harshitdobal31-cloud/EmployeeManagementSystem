"""
ui/employee_dashboard.py

Employee Self-Service Dashboard for the Employee Management System
(PySide6 + SQLAlchemy).

Data access
-----------
* No sqlite3, no private database, no CREATE TABLE. Everything goes through
  the existing SQLAlchemy setup:
      database.database.SessionLocal  ->  data/employee_management.db
  and the existing models in database/models.py.
* EmployeeDataService (below) is the only place that touches the database.
  EVERY query is scoped to the logged-in employee / user:
      Employee.id        == current employee id
      Attendance.employee_id == current employee id
      Payroll.employee_id    == current employee id
      Performance(.Log).employee_id == current employee id
      Notification.user_id   == current user id
  The only data that is not personal is CalendarEvent (company calendar),
  which is read-only for employees.
* Logged-in user -> utils.session.Session.get_user()
* Logout         -> utils.session.Session.logout() -> ui.login.LoginWindow
* Leave requests -> the project has no Leave model, so the Leave page keeps
  its UI but shows a clean disabled state (see LEAVE_SUPPORTED).

How the logged-in User is linked to an Employee
-----------------------------------------------
The User model has no employee FK, so the employee row is resolved (in this
order) from: Session "employee_id" (if present) -> User.email == Employee.email
-> User.username == Employee.employee_id -> User.username == Employee.full_name.
If nothing matches, NO data is shown (we never fall back to "first employee").

Themes
------
The window is styled from a palette. The palette comes from
utils.theme_manager when it exposes a recognisable theme table, otherwise from
the built-in palettes for Dark, Light, Blue, Purple, Green, Rose, Orange,
Teal, Midnight and Slate (see ThemeBridge).
"""

import csv
import functools
import logging
import re
from contextlib import contextmanager
from datetime import date, datetime, time as dtime
from pathlib import Path
from string import Template

from PySide6.QtCore import (
    QDate,
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    QRect,
    QSettings,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPixmap,
    QShortcut,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.database import SessionLocal
from database.models import (
    AppSetting,
    Attendance,
    CalendarEvent,
    Employee,
    LeaveRequest,
    Notification,
    Payroll,
    Performance,
    PerformanceLog,
    User,
)
from utils.session import Session

# Optional libraries: the dashboard still works without them.
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_OK = True
except Exception:  # pragma: no cover - depends on the environment
    MATPLOTLIB_OK = False

try:
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    REPORTLAB_OK = True
except Exception:  # pragma: no cover
    REPORTLAB_OK = False

logger = logging.getLogger(__name__)


# ==============================================================
# CONSTANTS
# ==============================================================

APP_TITLE = "Employee Management System"

SETTINGS_ORG = "EmployeeManagementSystem"
SETTINGS_APP = "EmployeeManagementSystem"

# The project has no Leave model. The Leave page keeps its UI but is disabled.
# To enable later: add a Leave model + service, implement the leave_* methods
# of EmployeeDataService, then set this flag to True.
LEAVE_SUPPORTED = True
LEAVE_UNSUPPORTED_TEXT = ""

LEAVE_TYPES = ["Casual Leave", "Sick Leave", "Earned Leave", "Unpaid Leave"]

DATE_FORMATS = {
    "DD Mon YYYY": "%d %b %Y",
    "DD-MM-YYYY": "%d-%m-%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
    "MM/DD/YYYY": "%m/%d/%Y",
}

DENSITIES = {
    "Comfortable": {"row": 44, "pad": 10},
    "Compact": {"row": 32, "pad": 6},
}

ACCENT_COLORS = {
    "Theme default": None,
    "Blue": "#2563EB",
    "Purple": "#7C3AED",
    "Green": "#16A34A",
    "Rose": "#E11D48",
    "Orange": "#EA580C",
    "Teal": "#0D9488",
}

EVENT_TYPE_COLORS = {
    "holiday": "#22C55E",
    "meeting": "#3B82F6",
    "training": "#A855F7",
    "deadline": "#EF4444",
    "birthday": "#EC4899",
    "event": "#F59E0B",
}

PAID_STATUSES = {"paid", "processed", "completed", "locked", "approved"}
PENDING_STATUSES = {"pending", "unpaid", "draft", "processing"}

NAV_ITEMS = [
    ("🏠", "Dashboard"),
    ("👤", "My Profile"),
    ("🕒", "My Attendance"),
    ("💰", "My Payroll"),
    ("⭐", "My Performance"),
    ("🌴", "Leave Request"),
    ("🔔", "Notifications"),
    ("📅", "Calendar"),
    ("⚙", "Settings"),
]


# ==============================================================
# ERRORS
# ==============================================================

class DataLoadError(Exception):
    """A read failed. `user_message` is safe to show to the employee."""

    def __init__(self, user_message, section="data"):
        super().__init__(user_message)
        self.user_message = user_message
        self.section = section


class DataWriteError(Exception):
    """A write failed or was rejected. Message is safe to show."""


class LeaveUnavailableError(RuntimeError):
    """Leave operation attempted without a Leave model."""


# ==============================================================
# COLOR / PALETTE HELPERS
# ==============================================================

def _rgb(hex_color):

    color = QColor(hex_color)

    return color.red(), color.green(), color.blue()


def luminance(hex_color):

    r, g, b = _rgb(hex_color)

    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_text(background):

    return "#0F172A" if luminance(background) > 150 else "#FFFFFF"


def shade(hex_color, amount):
    """amount > 0 lightens, amount < 0 darkens (range -1..1)."""

    r, g, b = _rgb(hex_color)

    if amount >= 0:
        r, g, b = (int(c + (255 - c) * amount) for c in (r, g, b))
    else:
        r, g, b = (int(c * (1 + amount)) for c in (r, g, b))

    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def rgba(hex_color, alpha):

    r, g, b = _rgb(hex_color)

    return f"rgba({r}, {g}, {b}, {alpha})"


def build_palette(spec, accent=None):
    """Expands a minimal theme spec into the full palette used by the QSS."""

    p = dict(spec)

    dark = bool(p.get("dark", False))

    if accent:
        p["primary"] = accent

    p["dark"] = dark
    p["primary_hover"] = shade(p["primary"], 0.12 if dark else -0.10)
    p["primary_dark"] = shade(p["primary"], -0.30)
    p["on_primary"] = contrast_text(p["primary"])

    p.setdefault("surface2", shade(p["surface"], 0.05 if dark else -0.03))
    p.setdefault("input_bg", p["surface"] if not dark else shade(p["bg"], 0.02))
    p.setdefault("sidebar", p["surface"])

    p["sidebar_text"] = p["text"]
    p["sidebar_hover"] = p["surface2"]
    p["selection"] = rgba(p["primary"], 70 if dark else 55)

    if dark:
        p["success"], p["warning"] = "#4ADE80", "#FBBF24"
        p["danger"], p["info"] = "#F87171", "#60A5FA"
    else:
        p["success"], p["warning"] = "#15803D", "#B45309"
        p["danger"], p["info"] = "#B91C1C", "#1D4ED8"

    for key in ("success", "warning", "danger", "info"):
        p[key + "_bg"] = rgba(p[key], 38)

    p["primary_bg"] = rgba(p["primary"], 38)

    return p


BUILTIN_THEMES = {
    "Dark": dict(dark=True, bg="#0F172A", surface="#1E293B", border="#334155",
                 text="#F1F5F9", muted="#94A3B8", primary="#3B82F6", sidebar="#0B1220"),
    "Light": dict(dark=False, bg="#F4F6FB", surface="#FFFFFF", border="#E2E8F0",
                  text="#0F172A", muted="#64748B", primary="#2563EB", sidebar="#FFFFFF"),
    "Blue": dict(dark=False, bg="#EEF4FF", surface="#FFFFFF", border="#D6E4FF",
                 text="#0B1B3A", muted="#5B6B8C", primary="#1D4ED8", sidebar="#E3EDFF"),
    "Purple": dict(dark=False, bg="#F5F0FF", surface="#FFFFFF", border="#E4D8FF",
                   text="#1E1033", muted="#6B5B8C", primary="#7C3AED", sidebar="#EBE1FF"),
    "Green": dict(dark=False, bg="#EFFAF3", surface="#FFFFFF", border="#CFEFDA",
                  text="#0B2916", muted="#52705C", primary="#16A34A", sidebar="#E0F5E8"),
    "Rose": dict(dark=False, bg="#FFF1F4", surface="#FFFFFF", border="#FBD3DC",
                 text="#3A0A17", muted="#8A5A66", primary="#E11D48", sidebar="#FFE1E8"),
    "Orange": dict(dark=False, bg="#FFF6EC", surface="#FFFFFF", border="#FAD9BB",
                   text="#3A1A05", muted="#8A6648", primary="#EA580C", sidebar="#FFE8D1"),
    "Teal": dict(dark=False, bg="#ECFBF9", surface="#FFFFFF", border="#C3EDE8",
                 text="#062A27", muted="#4F7A76", primary="#0D9488", sidebar="#D9F5F1"),
    "Midnight": dict(dark=True, bg="#0A0A1F", surface="#14142E", border="#2A2A52",
                     text="#E8E8FF", muted="#8E8EBF", primary="#818CF8", sidebar="#07071A"),
    "Slate": dict(dark=True, bg="#1E2329", surface="#2A3038", border="#414A56",
                  text="#E6EAF0", muted="#9AA5B4", primary="#5B7BA8", sidebar="#171B20"),
}

DEFAULT_THEME = "Dark"


# ==============================================================
# PERSONAL PREFERENCES (QSettings, per username)
# ==============================================================

class Prefs:
    """Employee-level UI preferences. Stored per user in QSettings, so they
    never touch Admin-level AppSetting rows."""

    DEFAULTS = {
        "theme": DEFAULT_THEME,
        "accent": "Theme default",
        "density": "Comfortable",
        "date_format": "DD Mon YYYY",
        "show_badge": True,
        "notify_new": True,
    }

    BOOL_KEYS = ("show_badge", "notify_new")

    def __init__(self):

        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)

        self._prefix = "employee/default/"

        self.values = dict(self.DEFAULTS)

    def attach(self, username):

        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", username or "default")

        self._prefix = f"employee/{safe}/"

        for key, default in self.DEFAULTS.items():

            if key in self.BOOL_KEYS:
                self.values[key] = self._settings.value(
                    self._prefix + key, default, type=bool
                )
            else:
                self.values[key] = str(
                    self._settings.value(self._prefix + key, default)
                )

    def has(self, key):

        return self._settings.contains(self._prefix + key)

    def get(self, key):

        return self.values.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):

        self.values[key] = value

        self._settings.setValue(self._prefix + key, value)

    def reset(self):

        for key, default in self.DEFAULTS.items():
            self.set(key, default)

    @property
    def row_height(self):

        return DENSITIES.get(self.get("density"), DENSITIES["Comfortable"])["row"]

    @property
    def pad(self):

        return DENSITIES.get(self.get("density"), DENSITIES["Comfortable"])["pad"]


PREFS = Prefs()


# ==============================================================
# THEME BRIDGE (utils.theme_manager)
# ==============================================================

class ThemeBridge:
    """Talks to the existing utils.theme_manager WITHOUT replacing it.

    * Reads / applies the current theme through whichever of the usual
      function names the module exposes.
    * Pulls a palette from the module's theme table if it has one with
      recognisable colour keys; otherwise uses BUILTIN_THEMES.
    Every step is optional and failure-tolerant.
    """

    GETTERS = ("get_current_theme", "current_theme", "get_theme_name", "get_theme")
    SETTERS = ("set_theme", "apply_theme", "change_theme", "switch_theme")
    TABLES = ("THEMES", "themes", "THEME_COLORS", "PALETTES", "THEME_PALETTES")

    KEY_ALIASES = {
        "bg": ("bg", "background", "window", "base", "main_bg"),
        "surface": ("surface", "card", "card_bg", "panel", "bg_secondary", "secondary"),
        "text": ("text", "foreground", "fg", "text_primary"),
        "muted": ("muted", "text_secondary", "subtext", "text_muted"),
        "primary": ("primary", "accent", "accent_color", "highlight"),
        "border": ("border", "outline", "divider"),
        "sidebar": ("sidebar", "sidebar_bg", "nav_bg"),
    }

    def __init__(self):

        try:
            from utils import theme_manager as module
        except Exception:
            module = None
            logger.info("utils.theme_manager not importable; using built-ins")

        self.module = module

    # -------- discovery --------

    def _table(self):

        if self.module is None:
            return {}

        for name in self.TABLES:

            table = getattr(self.module, name, None)

            if isinstance(table, dict) and table:
                return table

        return {}

    def names(self):

        names = list(BUILTIN_THEMES)

        for key in self._table():

            if isinstance(key, str) and key.title() not in names:
                names.append(key.title())

        return names

    def _match(self, name):
        """Case-insensitive built-in / table name lookup."""

        for candidate in self.names():
            if candidate.lower() == str(name).lower():
                return candidate

        return None

    def _from_manager(self):

        if self.module is None:
            return None

        for name in self.GETTERS:

            target = getattr(self.module, name, None)

            if not callable(target):
                continue

            try:
                value = target()
            except Exception:
                continue

            if isinstance(value, dict):
                value = value.get("name")

            if isinstance(value, str) and self._match(value):
                return self._match(value)

        return None

    def _from_app_setting(self):

        session = SessionLocal()

        try:
            for key in ("theme", "app_theme", "current_theme"):

                row = (
                    session.query(AppSetting)
                    .filter(AppSetting.setting_key == key)
                    .first()
                )

                if row and row.setting_value and self._match(row.setting_value):
                    return self._match(row.setting_value)

        except SQLAlchemyError:
            logger.exception("Could not read theme AppSetting")
        finally:
            session.close()

        return None

    def current_name(self):

        saved = PREFS.get("theme")

        if PREFS.has("theme") and self._match(saved):
            return self._match(saved)

        return (
            self._from_manager()
            or self._from_app_setting()
            or self._match(saved)
            or DEFAULT_THEME
        )

    def apply_name(self, name):
        """Persist the choice and let the project's theme manager know."""

        PREFS.set("theme", name)

        if self.module is None:
            return

        for setter in self.SETTERS:

            target = getattr(self.module, setter, None)

            if not callable(target):
                continue

            try:
                target(name)
                return
            except TypeError:
                continue
            except Exception:
                logger.exception("theme_manager.%s(%r) failed", setter, name)
                return

    # -------- palette --------

    def _table_entry(self, name):

        for key, value in self._table().items():

            if str(key).lower() == str(name).lower() and isinstance(value, dict):
                return value

        return None

    def _spec_from_entry(self, entry, fallback):

        spec = dict(fallback)

        found = 0

        for target, aliases in self.KEY_ALIASES.items():

            for alias in aliases:

                value = entry.get(alias)

                if isinstance(value, str) and QColor(value).isValid():
                    spec[target] = value
                    found += 1
                    break

        if found < 3 or not all(k in spec for k in ("bg", "text", "primary")):
            return None

        spec["dark"] = luminance(spec["bg"]) < 128

        return spec

    def palette(self, name, accent_name="Theme default"):

        base = BUILTIN_THEMES.get(name) or BUILTIN_THEMES[DEFAULT_THEME]

        spec = dict(base)

        entry = self._table_entry(name)

        if entry:
            try:
                spec = self._spec_from_entry(entry, base) or dict(base)
            except Exception:
                logger.exception("Could not map theme_manager palette")

        return build_palette(spec, ACCENT_COLORS.get(accent_name))


# ==============================================================
# DATA CONVERSION / FORMAT HELPERS
# ==============================================================

def to_date(value):

    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    for chunk in (text[:10], text):
        try:
            return date.fromisoformat(chunk)
        except ValueError:
            continue

    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def fmt_date(value, fallback="—"):

    parsed = to_date(value)

    if parsed is None:
        return fallback if not value else str(value)

    return parsed.strftime(DATE_FORMATS.get(PREFS.get("date_format"), "%d %b %Y"))


def fmt_datetime(value):

    if isinstance(value, datetime):
        return f"{fmt_date(value)}  {value.strftime('%I:%M %p')}"

    return fmt_date(value)


def fmt_time(value):

    if value in (None, ""):
        return "—"

    if isinstance(value, (datetime, dtime)):
        return value.strftime("%I:%M %p")

    text = str(value).strip()

    for fmt in ("%H:%M:%S", "%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(text, fmt).strftime("%I:%M %p")
        except ValueError:
            continue

    return text


def parse_hours(value):

    if value in (None, ""):
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        pass

    match = re.match(r"^\s*(\d+):(\d{1,2})", str(value))

    if match:
        return int(match.group(1)) + int(match.group(2)) / 60.0

    return 0.0


def fmt_hours(hours):

    total_minutes = int(round(hours * 60))

    return f"{total_minutes // 60}h {total_minutes % 60:02d}m"


def to_float(value):

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_money(value, symbol="₹ "):
    """Indian digit grouping, e.g. 1,25,000."""

    number = int(round(to_float(value) or 0))

    sign = "-" if number < 0 else ""

    digits = str(abs(number))

    if len(digits) > 3:

        head, tail = digits[:-3], digits[-3:]

        groups = []

        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]

        if head:
            groups.insert(0, head)

        digits = ",".join(groups) + "," + tail

    return f"{sign}{symbol}{digits}"


def normalize_month(value):
    """Any stored month representation -> 'YYYY-MM' (or None)."""

    if value in (None, ""):
        return None

    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m")

    text = str(value).strip()

    for candidate in (text, text[:10], text[:7]):
        for fmt in ("%Y-%m", "%B %Y", "%b %Y", "%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(candidate, fmt).strftime("%Y-%m")
            except ValueError:
                continue

    return None


def month_label(key):

    try:
        return datetime.strptime(key, "%Y-%m").strftime("%B %Y")
    except (TypeError, ValueError):
        return key or "—"


def short_month(key):

    try:
        return datetime.strptime(key, "%Y-%m").strftime("%b %y")
    except (TypeError, ValueError):
        return key or ""


def current_month_key():

    return date.today().strftime("%Y-%m")


def normalize_status(text):
    """Stored attendance status -> Present / Absent / Leave (or None)."""

    value = (text or "").strip().lower()

    if value.startswith(("present", "late", "half")):
        return "Present"

    if value.startswith("absent"):
        return "Absent"

    if "leave" in value:
        return "Leave"

    return None


def badge_kind_for_status(text):

    value = (text or "").strip().lower()

    if value in PAID_STATUSES or value.startswith("present") or value == "active":
        return "success"

    if value in PENDING_STATUSES or "leave" in value or value.startswith("late"):
        return "warning"

    if value.startswith("absent") or value in ("rejected", "inactive", "failed"):
        return "danger"

    return "info"


def greeting():

    hour = datetime.now().hour

    if hour < 12:
        return "Good morning"

    if hour < 17:
        return "Good afternoon"

    return "Good evening"


def initials(name):

    parts = [p for p in re.split(r"\s+", (name or "").strip()) if p]

    if not parts:
        return "?"

    if len(parts) == 1:
        return parts[0][:2].upper()

    return (parts[0][0] + parts[-1][0]).upper()


def attendance_summary(records):
    """records: list of attendance dicts -> summary dict."""

    present = sum(1 for r in records if r["category"] == "Present")
    absent = sum(1 for r in records if r["category"] == "Absent")
    leave = sum(1 for r in records if r["category"] == "Leave")

    total = present + absent + leave

    return {
        "present": present,
        "absent": absent,
        "leave": leave,
        "total": total,
        "pct": (present / total * 100.0) if total else None,
        "hours": sum(r["hours"] for r in records),
    }


def monthly_attendance(records, months=6):
    """Last N months with data (or ending now): [(key, present, absent, leave)]"""

    buckets = {}

    for record in records:

        key = record["date"].strftime("%Y-%m") if record["date"] else None

        if not key or record["category"] is None:
            continue

        bucket = buckets.setdefault(key, [0, 0, 0])

        bucket[("Present", "Absent", "Leave").index(record["category"])] += 1

    keys = sorted(buckets)[-months:]

    return [(k, *buckets[k]) for k in keys]


def pct_text(value):

    return "—" if value is None else f"{value:.0f}%"


def attendance_grade(pct):

    if pct is None:
        return "No data", "info"

    if pct >= 90:
        return "Excellent", "success"

    if pct >= 75:
        return "Good", "info"

    return "Needs attention", "warning"


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def valid_phone(text):

    if not re.fullmatch(r"[0-9+()\-\s]+", text or ""):
        return False

    digits = re.sub(r"\D", "", text)

    return 7 <= len(digits) <= 15


# ==============================================================
# SESSION HELPERS
# ==============================================================

def _session_user():

    try:
        return Session.get_user()
    except Exception:
        logger.exception("Session.get_user() failed")
        return None


def _user_field(user, *names):

    if user is None:
        return None

    for name in names:

        value = user.get(name) if isinstance(user, dict) else getattr(user, name, None)

        if value not in (None, ""):
            return value

    return None


@contextmanager
def session_scope():
    """Commit on success, roll back on error, ALWAYS close."""

    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def guarded(section):
    """Converts SQLAlchemy errors into DataLoadError (technical text is
    logged, never shown)."""

    def decorator(method):

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):

            try:
                return method(self, *args, **kwargs)
            except (DataLoadError, DataWriteError):
                raise
            except SQLAlchemyError as exc:
                logger.error("Database error while loading %s", section, exc_info=exc)
                raise DataLoadError(f"Unable to load {section} data.", section) from exc

        return wrapper

    return decorator


# ==============================================================
# DATA SERVICE  (all queries are scoped to the logged-in employee)
# ==============================================================

class EmployeeDataService:
    """Read/write adapter around the existing SQLAlchemy models.

    Returns plain dictionaries so the UI never touches detached ORM objects.
    """

    def __init__(self):

        self.employee_pk = None

        self.user_id = None

        self.username = ""

        self.role = ""

    # ---------------- identity ----------------

    def _resolve_identity(self, session):
        """Finds (user_id, employee_pk) for the logged-in user. Never guesses."""

        user = _session_user()

        if user is None:
            raise DataLoadError("You are not logged in. Please sign in again.", "profile")

        self.user_id = _user_field(user, "id", "user_id")

        self.username = str(_user_field(user, "username", "name") or "")

        self.role = str(_user_field(user, "role") or "")

        email = _user_field(user, "email")

        if self.user_id is not None and (not email or not self.username):

            row = session.query(User).filter(User.id == self.user_id).first()

            if row is not None:
                email = email or row.email
                self.username = self.username or (row.username or "")
                self.role = self.role or (row.role or "")

        base = session.query(Employee)

        employee = None

        session_emp = _user_field(user, "employee_id", "employee_pk")

        if session_emp is not None:

            if isinstance(session_emp, int):
                employee = base.filter(Employee.id == session_emp).first()
            else:
                employee = base.filter(Employee.employee_id == str(session_emp)).first()

        if employee is None and email:
            employee = base.filter(func.lower(Employee.email) == str(email).lower()).first()

        if employee is None and self.username:
            employee = base.filter(Employee.employee_id == self.username).first()

        if employee is None and self.username:
            employee = base.filter(func.lower(Employee.full_name) == self.username.lower()).first()

        if employee is None:
            raise DataLoadError(
                "Your employee profile could not be found. Please contact HR.",
                "profile",
            )

        self.employee_pk = employee.id

        return self.employee_pk

    def _pk(self, session):

        if self.employee_pk is None:
            self._resolve_identity(session)

        return self.employee_pk
    
    def _get_employee(self, session):
        """
        Get the Employee ORM object for the currently logged-in employee.
        """

        if self.employee_pk is None:
            self._resolve_identity(session)

        if self.employee_pk is None:
            return None

        return (
            session.query(Employee)
            .filter(Employee.id == self.employee_pk)
            .first()
        )
    
    def _uid(self, session):

        if self.user_id is None:
            self._resolve_identity(session)

        if self.user_id is None:
            raise DataLoadError("Your user account could not be identified.", "notifications")

        return self.user_id

    def reset_identity(self):

        self.employee_pk = None

        self.user_id = None

    # ---------------- profile ----------------

    @staticmethod
    def _employee_dict(e):

        return {
            "pk": e.id,
            "code": e.employee_id or "",
            "name": e.full_name or "",
            "email": e.email or "",
            "phone": e.phone or "",
            "gender": e.gender or "",
            "dob": e.date_of_birth,
            "address": e.address or "",
            "department": e.department or "",
            "designation": e.designation or "",
            "employment_type": e.employment_type or "",
            "joining_date": e.joining_date,
            "salary": to_float(e.salary),
            "emergency_name": e.emergency_contact_name or "",
            "emergency_phone": e.emergency_contact_phone or "",
            "photo": e.profile_photo or "",
            "status": e.status or "",
        }

    @guarded("profile")
    def get_employee(self):

        with session_scope() as session:

            pk = self._pk(session)

            employee = session.query(Employee).filter(Employee.id == pk).first()

            if employee is None:
                self.employee_pk = None
                raise DataLoadError("Your employee profile could not be found.", "profile")

            return self._employee_dict(employee)

    def update_contact(self, values):
        """Only safe, self-editable fields. Re-validated here (never trust UI)."""

        phone = (values.get("phone") or "").strip()
        email = (values.get("email") or "").strip()
        address = (values.get("address") or "").strip()
        em_name = (values.get("emergency_name") or "").strip()
        em_phone = (values.get("emergency_phone") or "").strip()

        if not EMAIL_RE.match(email):
            raise DataWriteError("Please enter a valid email address.")

        if phone and not valid_phone(phone):
            raise DataWriteError("Please enter a valid phone number.")

        if em_phone and not valid_phone(em_phone):
            raise DataWriteError("Please enter a valid emergency contact phone number.")

        try:
            with session_scope() as session:

                pk = self._pk(session)

                clash = (
                    session.query(Employee.id)
                    .filter(func.lower(Employee.email) == email.lower(), Employee.id != pk)
                    .first()
                )

                if clash:
                    raise DataWriteError("That email address is already in use.")

                employee = session.query(Employee).filter(Employee.id == pk).first()

                if employee is None:
                    raise DataWriteError("Your employee profile could not be found.")

                old_email = employee.email

                employee.phone = phone
                employee.email = email
                employee.address = address
                employee.emergency_contact_name = em_name
                employee.emergency_contact_phone = em_phone
                employee.updated_at = datetime.now()

                # Keep the login account's email in sync, otherwise the
                # User <-> Employee link (by email) would break at next login.
                if (old_email or "").lower() != email.lower() and self.user_id is not None:

                    user = session.query(User).filter(User.id == self.user_id).first()

                    if user is not None:

                        taken = (
                            session.query(User.id)
                            .filter(func.lower(User.email) == email.lower(), User.id != user.id)
                            .first()
                        )

                        if taken:
                            raise DataWriteError("That email address is already in use.")

                        user.email = email

        except IntegrityError as exc:
            logger.error("Integrity error updating profile", exc_info=exc)
            raise DataWriteError("Could not save: that value is already in use.") from exc
        except SQLAlchemyError as exc:
            logger.error("Database error updating profile", exc_info=exc)
            raise DataWriteError("Unable to save your profile right now.") from exc

    # ---------------- attendance ----------------

    @guarded("attendance")
    def attendance_records(self):

        with session_scope() as session:

            pk = self._pk(session)

            rows = (
                session.query(Attendance)
                .filter(Attendance.employee_id == pk)
                .all()
            )

            records = []

            for row in rows:

                day = to_date(row.attendance_date)

                records.append({
                    "id": row.id,
                    "date": day,
                    "check_in": row.check_in,
                    "check_out": row.check_out,
                    "hours": parse_hours(row.working_hours),
                    "status": row.status or "",
                    "category": normalize_status(row.status),
                })

        records.sort(key=lambda r: r["date"] or date.min, reverse=True)

        return records

    # ---------------- payroll ----------------

    @guarded("payroll")
    def payroll_records(self):

        with session_scope() as session:

            pk = self._pk(session)

            rows = session.query(Payroll).filter(Payroll.employee_id == pk).all()

            records = []

            for row in rows:

                records.append({
                    "id": row.id,
                    "month": normalize_month(row.payroll_month),
                    "month_raw": str(row.payroll_month or ""),
                    "basic": to_float(row.basic_salary) or 0.0,
                    "allowances": to_float(row.allowances) or 0.0,
                    "deductions": to_float(row.deductions) or 0.0,
                    "net": to_float(row.net_salary) or 0.0,
                    "status": row.status or "",
                })

        records.sort(key=lambda r: r["month"] or "", reverse=True)

        return records

    # ---------------- performance ----------------

    @guarded("performance")
    def performance_records(self):

        with session_scope() as session:

            pk = self._pk(session)

            rows = (
                session.query(Performance)
                .filter(Performance.employee_id == pk)
                .all()
            )

            records = [
                {
                    "id": r.id,
                    "date": to_date(r.review_date),
                    "score": to_float(r.score),
                    "percentage": to_float(r.percentage),
                    "category": r.category or "",
                    "comments": r.comments or "",
                }
                for r in rows
            ]

            if not records:

                logs = (
                    session.query(PerformanceLog)
                    .filter(PerformanceLog.employee_id == pk)
                    .all()
                )

                records = [
                    {
                        "id": r.id,
                        "date": to_date(r.review_date),
                        "score": to_float(r.score),
                        "percentage": None,
                        "category": r.category or "",
                        "comments": r.comments or "",
                    }
                    for r in logs
                ]

        records.sort(key=lambda r: r["date"] or date.min, reverse=True)

        return records

    # ---------------- notifications ----------------

    @guarded("notifications")
    def notifications(self):

        with session_scope() as session:

            uid = self._uid(session)

            rows = (
                session.query(Notification)
                .filter(Notification.user_id == uid)
                .order_by(Notification.created_at.desc())
                .all()
            )

            return [
                {
                    "id": r.id,
                    "title": r.title or "",
                    "message": r.message or "",
                    "type": r.notification_type or "General",
                    "read": bool(r.is_read),
                    "created": r.created_at,
                }
                for r in rows
            ]

    @guarded("notifications")
    def unread_count(self):

        with session_scope() as session:

            uid = self._uid(session)

            return (
                session.query(Notification)
                .filter(
                    Notification.user_id == uid,
                    or_(Notification.is_read.is_(False), Notification.is_read.is_(None)),
                )
                .count()
            )

    def mark_read(self, ids=None):
        """Marks the given notifications (or ALL when ids is None) as read.
        Always restricted to the current user's own rows."""

        try:
            with session_scope() as session:

                uid = self._uid(session)

                query = session.query(Notification).filter(Notification.user_id == uid)

                if ids is not None:

                    ids = [i for i in ids if i is not None]

                    if not ids:
                        return 0

                    query = query.filter(Notification.id.in_(ids))

                return query.update({Notification.is_read: True}, synchronize_session=False)

        except DataLoadError as exc:
            raise DataWriteError(exc.user_message) from exc
        except SQLAlchemyError as exc:
            logger.error("Could not update notifications", exc_info=exc)
            raise DataWriteError("Unable to update notifications right now.") from exc

    # ---------------- calendar (company calendar, read-only) ----------------

    @guarded("calendar")
    def calendar_events(self):

        with session_scope() as session:

            rows = session.query(CalendarEvent).order_by(CalendarEvent.event_date).all()

            return [
                {
                    "id": r.id,
                    "title": r.title or "",
                    "description": r.description or "",
                    "date": to_date(r.event_date),
                    "type": (r.event_type or "Event"),
                }
                for r in rows
            ]

    # ---------------- leave management ----------------

    @staticmethod
    def leave_supported():

        return True


    @guarded("leave")
    def leave_requests(self):

        with session_scope() as session:

            employee = self._get_employee(session)

            if employee is None:
                return []

            rows = (
                session.query(LeaveRequest)
                .filter(
                    LeaveRequest.employee_id == employee.id
                )
                .order_by(
                    LeaveRequest.created_at.desc()
                )
                .all()
            )

            result = []

            for row in rows:

                result.append({
                    "id": row.id,
                    "leave_type": row.leave_type or "",
                    "start_date": to_date(row.start_date),
                    "end_date": to_date(row.end_date),
                    "reason": row.reason or "",
                    "status": row.status or "Pending",
                    "created_at": row.created_at,
                })

            return result


    @guarded("leave")
    def leave_summary(self):

        with session_scope() as session:

            employee = self._get_employee(session)

            if employee is None:
                return {
                    "balance": 24,
                    "pending": 0,
                    "approved": 0,
                    "rejected": 0,
                }

            rows = (
                session.query(LeaveRequest)
                .filter(
                    LeaveRequest.employee_id == employee.id
                )
                .all()
            )

            pending = 0
            approved = 0
            rejected = 0
            approved_days = 0

            for row in rows:

                status = (
                    row.status or "Pending"
                ).strip().lower()

                if status == "pending":
                    pending += 1

                elif status == "approved":

                    approved += 1

                    start = to_date(
                        row.start_date
                    )

                    end = to_date(
                        row.end_date
                    )

                    if start and end:
                        approved_days += (
                            (end - start).days + 1
                        )

                elif status == "rejected":
                    rejected += 1

            balance = max(
                0,
                24 - approved_days
            )

            return {
                "balance": balance,
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
            }


    def submit_leave(
        self,
        leave_type,
        start,
        end,
        reason
    ):

        try:

            if start > end:
                raise DataWriteError(
                    "Start date cannot be after end date."
                )

            reason = (
                reason or ""
            ).strip()

            if not reason:
                raise DataWriteError(
                    "Please enter a reason for your leave."
                )

            with session_scope() as session:

                employee = self._get_employee(
                    session
                )

                if employee is None:
                    raise DataWriteError(
                        "Employee profile could not be found."
                    )

                # ------------------------------------------
                # Check overlapping pending/approved leave
                # ------------------------------------------

                existing = (
                    session.query(LeaveRequest)
                    .filter(
                        LeaveRequest.employee_id
                        == employee.id
                    )
                    .filter(
                        LeaveRequest.status.in_([
                            "Pending",
                            "Approved",
                        ])
                    )
                    .all()
                )

                for leave in existing:

                    existing_start = to_date(
                        leave.start_date
                    )

                    existing_end = to_date(
                        leave.end_date
                    )

                    if (
                        existing_start
                        and existing_end
                        and start <= existing_end
                        and end >= existing_start
                    ):

                        raise DataWriteError(
                            "You already have a pending or "
                            "approved leave for these dates."
                        )

                # ------------------------------------------
                # Create leave request
                # ------------------------------------------

                request = LeaveRequest(
                    employee_id=employee.id,
                    leave_type=leave_type,
                    start_date=start.isoformat(),
                    end_date=end.isoformat(),
                    reason=reason,
                    status="Pending",
                )

                session.add(request)

        except DataWriteError:
            raise

        except SQLAlchemyError as exc:

            logger.error(
                "Could not submit leave request",
                exc_info=exc
            )

            raise DataWriteError(
                "Unable to submit leave request right now."
            ) from exc

# ==============================================================
# STYLESHEET
# ==============================================================

STYLE_TEMPLATE = Template(r"""
* {
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QWidget { color: $text; }
QMainWindow, #root, QDialog { background: $bg; }
QLabel { background: transparent; }
QToolTip {
    background: $surface; color: $text; border: 1px solid $border; padding: 6px;
}

/* ---------- sidebar ---------- */
#sidebar { background: $sidebar; border-right: 1px solid $border; }
#brandTitle { font-size: 15px; font-weight: 700; color: $text; }
#brandSub { font-size: 11px; color: $muted; }
#brandIcon {
    background: $primary; color: $on_primary; border-radius: 12px;
    font-size: 18px; font-weight: 700;
}
QPushButton#navButton {
    text-align: left; padding: 11px 16px; border: none; border-radius: 10px;
    color: $sidebar_text; background: transparent; font-size: 13px;
}
QPushButton#navButton:hover { background: $sidebar_hover; }
QPushButton#navButton:checked {
    background: $primary; color: $on_primary; font-weight: 600;
}
QPushButton#logoutButton {
    text-align: left; padding: 11px 16px; border: none; border-radius: 10px;
    color: $danger; background: transparent; font-weight: 600;
}
QPushButton#logoutButton:hover { background: $danger_bg; }
#sidebarFooter { color: $muted; font-size: 11px; }

/* ---------- header ---------- */
#header { background: $surface; border-bottom: 1px solid $border; }
#headerTitle { font-size: 20px; font-weight: 700; }
#headerDate { color: $muted; font-size: 12px; }
#headerName { font-weight: 600; font-size: 13px; }
#headerMeta { color: $muted; font-size: 11px; }

/* ---------- cards ---------- */
#card, #statCard {
    background: $surface; border: 1px solid $border; border-radius: 14px;
}
#statCard:hover { border: 1px solid $primary; background: $surface2; }
#cardTitle { font-size: 15px; font-weight: 700; }
#cardSubtitle { color: $muted; font-size: 12px; }
#statTitle { color: $muted; font-size: 12px; font-weight: 600; }
#statValue { font-size: 26px; font-weight: 700; }
#statDesc { color: $muted; font-size: 11px; }
#pageTitle { font-size: 22px; font-weight: 700; }
#pageSubtitle { color: $muted; font-size: 12px; }
#muted { color: $muted; }
#fieldLabel { color: $muted; font-size: 11px; font-weight: 600; }
#fieldValue { font-size: 13px; font-weight: 500; }
#bigNumber { font-size: 34px; font-weight: 700; }
#rowTitle { font-weight: 600; }
#rowSub { color: $muted; font-size: 11px; }
#listRow { background: $surface2; border-radius: 10px; }
#summaryBox { background: $surface2; border-radius: 12px; padding: 14px; }

#welcomeCard {
    border-radius: 18px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 $primary, stop:1 $primary_dark);
}
#welcomeCard QLabel { color: $on_primary; background: transparent; }
#welcomeTitle { font-size: 24px; font-weight: 700; }
#welcomeSub { font-size: 13px; }
#welcomeChip {
    background: rgba(255, 255, 255, 38); color: $on_primary;
    border-radius: 10px; padding: 4px 12px; font-size: 12px; font-weight: 600;
}

/* ---------- banners / states ---------- */
#errorBanner {
    background: $danger_bg; border: 1px solid $danger; border-radius: 10px;
}
#errorBanner QLabel { color: $danger; font-weight: 600; }
#infoBanner {
    background: $info_bg; border: 1px solid $info; border-radius: 10px;
}
#infoBanner QLabel { color: $info; font-weight: 600; }
#emptyState { background: transparent; border: none; }
#emptyIcon { font-size: 34px; }
#emptyTitle { font-size: 15px; font-weight: 600; }
#emptyText { color: $muted; }

QLabel#badge {
    padding: 3px 10px; border-radius: 10px; font-size: 11px; font-weight: 700;
}
QLabel#badge[kind="success"] { background: $success_bg; color: $success; }
QLabel#badge[kind="warning"] { background: $warning_bg; color: $warning; }
QLabel#badge[kind="danger"]  { background: $danger_bg;  color: $danger; }
QLabel#badge[kind="info"]    { background: $info_bg;    color: $info; }
QLabel#badge[kind="primary"] { background: $primary_bg; color: $primary; }

/* ---------- buttons ---------- */
QPushButton#primaryButton {
    background: $primary; color: $on_primary; border: none;
    border-radius: 9px; padding: 8px 18px; font-weight: 600;
}
QPushButton#primaryButton:hover { background: $primary_hover; }
QPushButton#primaryButton:disabled { background: $border; color: $muted; }
QPushButton#secondaryButton {
    background: $surface2; color: $text; border: 1px solid $border;
    border-radius: 9px; padding: 8px 18px; font-weight: 600;
}
QPushButton#secondaryButton:hover { border-color: $primary; }
QPushButton#secondaryButton:disabled { color: $muted; }
QPushButton#secondaryButton::menu-indicator { width: 0px; }
QPushButton#iconButton {
    background: $surface2; color: $text; border: 1px solid $border;
    border-radius: 10px; font-size: 15px;
}
QPushButton#iconButton:hover { border-color: $primary; }

/* ---------- inputs ---------- */
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background: $input_bg; color: $text; border: 1px solid $border;
    border-radius: 8px; padding: 6px 10px; min-height: 22px;
    selection-background-color: $primary; selection-color: $on_primary;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid $primary;
}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QDateEdit:disabled {
    color: $muted; background: $surface2;
}
QComboBox::drop-down, QDateEdit::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: $surface; color: $text; border: 1px solid $border;
    selection-background-color: $primary; selection-color: $on_primary;
    outline: none;
}
QCheckBox { color: $text; spacing: 8px; background: transparent; }
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid $border;
    border-radius: 4px; background: $input_bg;
}
QCheckBox::indicator:checked { background: $primary; border: 1px solid $primary; }

/* ---------- tables ---------- */
QTableWidget {
    background: $surface; alternate-background-color: $surface2;
    border: none; color: $text; gridline-color: transparent;
    selection-background-color: $selection; selection-color: $text;
}
QTableWidget::item { padding: 4px 8px; border: none; }
QHeaderView::section {
    background: $surface2; color: $muted; padding: 8px; border: none;
    border-bottom: 1px solid $border; font-weight: 700; font-size: 12px;
}
QTableCornerButton::section { background: $surface2; border: none; }

/* ---------- progress ---------- */
QProgressBar {
    background: $surface2; border: none; border-radius: 6px;
    height: 12px; text-align: center; color: transparent;
}
QProgressBar::chunk { background: $primary; border-radius: 6px; }

/* ---------- scrolling ---------- */
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical {
    background: $border; border-radius: 4px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: $muted; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal {
    background: $border; border-radius: 4px; min-width: 30px;
}
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

/* ---------- menus / message boxes ---------- */
QMenu {
    background: $surface; color: $text; border: 1px solid $border; padding: 4px;
}
QMenu::item { padding: 7px 22px; border-radius: 6px; }
QMenu::item:selected { background: $selection; }
QMessageBox { background: $bg; }
QMessageBox QLabel { color: $text; }
QStatusBar { background: $surface; color: $muted; border-top: 1px solid $border; }

/* ---------- calendar ---------- */
QCalendarWidget QWidget { alternate-background-color: $surface2; }
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: $surface2; border-bottom: 1px solid $border;
}
QCalendarWidget QToolButton {
    color: $text; background: transparent; border: none;
    padding: 6px 10px; font-weight: 600; border-radius: 6px;
}
QCalendarWidget QToolButton:hover { background: $selection; }
QCalendarWidget QMenu { background: $surface; color: $text; }
QCalendarWidget QSpinBox { background: $input_bg; color: $text; }
QCalendarWidget QAbstractItemView:enabled {
    background: $surface; color: $text;
    selection-background-color: $primary; selection-color: $on_primary;
    outline: none;
}
QCalendarWidget QAbstractItemView:disabled { color: $muted; }
""")


def build_stylesheet(palette):

    return STYLE_TEMPLATE.substitute(palette)


# ==============================================================
# SMALL UI HELPERS
# ==============================================================

def set_prop(widget, name, value):
    """Sets a dynamic property and re-polishes so the QSS picks it up."""

    widget.setProperty(name, value)

    widget.style().unpolish(widget)

    widget.style().polish(widget)


def make_label(text, object_name="", wrap=False):

    label = QLabel(text)

    if object_name:
        label.setObjectName(object_name)

    label.setWordWrap(wrap)

    return label


def make_button(text, object_name="primaryButton"):

    button = QPushButton(text)

    button.setObjectName(object_name)

    button.setCursor(Qt.CursorShape.PointingHandCursor)

    button.setMinimumHeight(36)

    return button


def clear_layout(layout):
    """Removes and deletes everything in a layout (nested layouts included)."""

    while layout.count():

        item = layout.takeAt(0)

        widget = item.widget()

        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
            continue

        child = item.layout()

        if child is not None:
            clear_layout(child)
            child.deleteLater()


def make_card(title=None, subtitle=None):
    """Returns (frame, body_layout) for a standard card."""

    frame = QFrame()

    frame.setObjectName("card")

    outer = QVBoxLayout(frame)

    outer.setContentsMargins(18, 16, 18, 16)

    outer.setSpacing(10)

    if title:

        head = QVBoxLayout()

        head.setSpacing(0)

        head.addWidget(make_label(title, "cardTitle"))

        if subtitle:
            head.addWidget(make_label(subtitle, "cardSubtitle"))

        outer.addLayout(head)

    return frame, outer


def project_root():

    return Path(__file__).resolve().parent.parent


def load_photo(path_text):

    if not path_text:
        return None

    candidates = [Path(path_text), project_root() / path_text]

    for candidate in candidates:

        try:
            if candidate.is_file():

                pixmap = QPixmap(str(candidate))

                if not pixmap.isNull():
                    return pixmap

        except OSError:
            continue

    return None


def make_avatar(name, size, photo_path, color):
    """Circular avatar: the profile photo when available, else initials."""

    pixmap = QPixmap(size, size)

    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)

    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    clip = QPainterPath()

    clip.addEllipse(0, 0, size, size)

    painter.setClipPath(clip)

    photo = load_photo(photo_path)

    if photo is not None:

        scaled = photo.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        offset_x = (scaled.width() - size) // 2

        offset_y = (scaled.height() - size) // 2

        painter.drawPixmap(0, 0, scaled, offset_x, offset_y, size, size)

    else:

        painter.fillRect(0, 0, size, size, QColor(color))

        painter.setPen(QColor(contrast_text(color)))

        font = painter.font()

        font.setPixelSize(max(10, int(size * 0.38)))

        font.setBold(True)

        painter.setFont(font)

        painter.drawText(
            QRect(0, 0, size, size),
            Qt.AlignmentFlag.AlignCenter,
            initials(name),
        )

    painter.end()

    return pixmap


# ==============================================================
# ANIMATION (references kept alive, effect removed when finished)
# ==============================================================

class Fader(QObject):
    """Fades a widget in. Keeps animation + effect alive, and removes the
    effect afterwards so no stale graphics-effect / target errors occur."""

    def __init__(self, parent=None):

        super().__init__(parent)

        self._widget = None

        self._effect = None

        self._anim = None

    def _cleanup(self):

        anim, widget = self._anim, self._widget

        self._anim = None

        self._effect = None

        self._widget = None

        if anim is not None:
            try:
                anim.stop()
            except RuntimeError:
                pass

        if widget is not None:
            try:
                widget.setGraphicsEffect(None)
            except RuntimeError:
                pass

    def start(self, widget, duration=260):

        self._cleanup()

        try:

            effect = QGraphicsOpacityEffect(widget)

            effect.setOpacity(0.0)

            widget.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity", self)

            anim.setDuration(duration)

            anim.setStartValue(0.0)

            anim.setEndValue(1.0)

            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            anim.finished.connect(self._cleanup)

            self._widget, self._effect, self._anim = widget, effect, anim

            anim.start()

        except RuntimeError:
            logger.exception("Fade animation skipped")
            self._cleanup()


# ==============================================================
# EXPORT HELPERS (only ever called with the employee's own rows)
# ==============================================================

def pdf_text(value):
    """ReportLab's built-in fonts are Latin-1: swap ₹ and drop emoji."""

    text = str(value).replace("₹", "Rs.").replace("—", "-")

    return text.encode("cp1252", "replace").decode("cp1252")


def export_csv(parent, suggested, headers, rows):

    path, _ = QFileDialog.getSaveFileName(
        parent, "Export CSV", suggested + ".csv", "CSV Files (*.csv)"
    )

    if not path:
        return False

    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)
    except OSError:
        logger.exception("CSV export failed")
        QMessageBox.warning(parent, "Export", "Unable to save the file.")
        return False

    QMessageBox.information(parent, "Export", "Report exported successfully.")

    return True


def export_pdf(parent, suggested, title, subtitle, headers, rows):

    if not REPORTLAB_OK:
        QMessageBox.information(parent, "Export", "PDF export requires the ReportLab package.")
        return False

    path, _ = QFileDialog.getSaveFileName(
        parent, "Export PDF", suggested + ".pdf", "PDF Files (*.pdf)"
    )

    if not path:
        return False

    try:

        styles = getSampleStyleSheet()

        doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=14 * mm,
                                rightMargin=14 * mm, topMargin=14 * mm,
                                bottomMargin=14 * mm)

        data = [[pdf_text(h) for h in headers]]

        data += [[pdf_text(c) for c in row] for row in rows]

        table = Table(data, repeatRows=1)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [rl_colors.white, rl_colors.HexColor("#F1F5F9")]),
            ("GRID", (0, 0), (-1, -1), 0.25, rl_colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        doc.build([
            Paragraph(pdf_text(title), styles["Title"]),
            Paragraph(pdf_text(subtitle), styles["Normal"]),
            Spacer(1, 8 * mm),
            table,
        ])

    except Exception:
        logger.exception("PDF export failed")
        QMessageBox.warning(parent, "Export", "Unable to create the PDF.")
        return False

    QMessageBox.information(parent, "Export", "Report exported successfully.")

    return True


def build_payslip_pdf(path, employee, record):

    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm)

    money = lambda v: pdf_text(fmt_money(v, "Rs. "))  # noqa: E731

    info = Table([
        ["Employee", pdf_text(employee["name"]), "Employee ID", pdf_text(employee["code"])],
        ["Department", pdf_text(employee["department"]), "Designation",
         pdf_text(employee["designation"])],
        ["Pay period", pdf_text(month_label(record["month"]) if record["month"]
                                else record["month_raw"]),
         "Status", pdf_text(record["status"] or "-")],
    ], colWidths=[28 * mm, 52 * mm, 28 * mm, 52 * mm])

    info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, rl_colors.HexColor("#CBD5E1")),
    ]))

    amounts = Table([
        ["Component", "Amount"],
        ["Basic Salary", money(record["basic"])],
        ["Allowances", money(record["allowances"])],
        ["Deductions", "- " + money(record["deductions"])],
        ["NET SALARY", money(record["net"])],
    ], colWidths=[100 * mm, 60 * mm])

    amounts.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), rl_colors.HexColor("#E0E7FF")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, rl_colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    doc.build([
        Paragraph(pdf_text(APP_TITLE), styles["Title"]),
        Paragraph("Payslip", styles["Heading2"]),
        Spacer(1, 4 * mm),
        info,
        Spacer(1, 8 * mm),
        amounts,
        Spacer(1, 10 * mm),
        Paragraph(
            "This is a system generated payslip. Generated on "
            + datetime.now().strftime("%d %b %Y, %I:%M %p"),
            styles["Italic"],
        ),
    ])


def download_payslip(parent, employee, record):

    if not REPORTLAB_OK:
        QMessageBox.information(parent, "Payslip", "PDF export requires the ReportLab package.")
        return

    key = record["month"] or "payslip"

    path, _ = QFileDialog.getSaveFileName(
        parent, "Save Payslip", f"Payslip_{employee['code']}_{key}.pdf",
        "PDF Files (*.pdf)",
    )

    if not path:
        return

    try:
        build_payslip_pdf(path, employee, record)
    except Exception:
        logger.exception("Payslip PDF failed")
        QMessageBox.warning(parent, "Payslip", "Unable to create the payslip PDF.")
        return

    QMessageBox.information(parent, "Payslip", "Payslip saved successfully.")


def make_export_button(parent, provider):
    """Button with a CSV / PDF menu. provider() -> (base, title, subtitle,
    headers, rows) built from the employee's own data."""

    button = make_button("⬇  Export", "secondaryButton")

    menu = QMenu(button)

    def run(kind):

        base, title, subtitle, headers, rows = provider()

        if not rows:
            QMessageBox.information(parent, "Export", "There is nothing to export yet.")
            return

        if kind == "csv":
            export_csv(parent, base, headers, rows)
        else:
            export_pdf(parent, base, title, subtitle, headers, rows)

    menu.addAction("Export as CSV", lambda: run("csv"))

    menu.addAction("Export as PDF", lambda: run("pdf"))

    button.setMenu(menu)

    return button


# ==============================================================
# REUSABLE WIDGETS
# ==============================================================

class Badge(QLabel):

    def __init__(self, text="", kind="info"):

        super().__init__(text)

        self.setObjectName("badge")

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        self.set_kind(text, kind)

    def set_kind(self, text, kind):

        self.setText(text)

        set_prop(self, "kind", kind)


class EmptyState(QFrame):

    def __init__(self, icon="📭", title="Nothing here yet", text=""):

        super().__init__()

        self.setObjectName("emptyState")

        layout = QVBoxLayout(self)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.setSpacing(4)

        self.icon_label = make_label(icon, "emptyIcon")

        self.title_label = make_label(title, "emptyTitle")

        self.text_label = make_label(text, "emptyText", wrap=True)

        for label in (self.icon_label, self.title_label, self.text_label):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

        self.text_label.setVisible(bool(text))

    def set_text(self, title, text=""):

        self.title_label.setText(title)

        self.text_label.setText(text)

        self.text_label.setVisible(bool(text))


class ErrorBanner(QFrame):
    """Inline error with a Retry button (hidden until needed)."""

    retry = Signal()

    def __init__(self):

        super().__init__()

        self.setObjectName("errorBanner")

        layout = QHBoxLayout(self)

        layout.setContentsMargins(14, 10, 14, 10)

        self.label = QLabel("")

        self.label.setWordWrap(True)

        layout.addWidget(self.label, 1)

        button = make_button("Retry", "secondaryButton")

        button.clicked.connect(self.retry.emit)

        layout.addWidget(button)

        self.hide()

    def show_message(self, text):

        self.label.setText("⚠  " + text)

        self.show()


class InfoBanner(QFrame):

    def __init__(self, text):

        super().__init__()

        self.setObjectName("infoBanner")

        layout = QHBoxLayout(self)

        layout.setContentsMargins(14, 10, 14, 10)

        self.label = QLabel("ⓘ  " + text)

        self.label.setWordWrap(True)

        layout.addWidget(self.label)


class StatCard(QFrame):
    """Summary tile: icon, title, large value, description and optional badge."""

    clicked = Signal()

    def __init__(self, icon, title, color):

        super().__init__()

        self.setObjectName("statCard")

        self.setMinimumHeight(132)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(18, 14, 18, 14)

        layout.setSpacing(4)

        top = QHBoxLayout()

        icon_label = QLabel(icon)

        icon_label.setFixedSize(42, 42)

        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label.setStyleSheet(
            f"background: {rgba(color, 48)}; color: {color};"
            "border-radius: 12px; font-size: 19px;"
        )

        top.addWidget(icon_label)

        top.addSpacing(6)

        top.addWidget(make_label(title, "statTitle"), 1)

        self.badge = Badge("", "info")

        self.badge.hide()

        top.addWidget(self.badge)

        layout.addLayout(top)

        self.value_label = make_label("—", "statValue")

        layout.addWidget(self.value_label)

        self.desc_label = make_label("", "statDesc", wrap=True)

        layout.addWidget(self.desc_label)

    def set_data(self, value, desc="", badge_text=None, badge_kind="info"):

        self.value_label.setText(str(value))

        self.desc_label.setText(desc)

        if badge_text:
            self.badge.set_kind(badge_text, badge_kind)
            self.badge.show()
        else:
            self.badge.hide()

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)


class InfoGrid(QWidget):
    """Read-only label/value pairs in a two-column grid."""

    def __init__(self, columns=2):

        super().__init__()

        self.columns = columns

        self.grid = QGridLayout(self)

        self.grid.setContentsMargins(0, 4, 0, 0)

        self.grid.setHorizontalSpacing(30)

        self.grid.setVerticalSpacing(14)

    def set_items(self, items):

        clear_layout(self.grid)

        for index, (label, value) in enumerate(items):

            cell = QVBoxLayout()

            cell.setSpacing(2)

            cell.addWidget(make_label(label.upper(), "fieldLabel"))

            value_label = make_label(str(value) if value not in (None, "") else "—",
                                     "fieldValue", wrap=True)

            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            cell.addWidget(value_label)

            self.grid.addLayout(cell, index // self.columns, index % self.columns)

        for column in range(self.columns):
            self.grid.setColumnStretch(column, 1)


class ListRow(QFrame):
    """Compact row used in 'recent' lists."""

    def __init__(self, title, subtitle, right_text="", accent=None):

        super().__init__()

        self.setObjectName("listRow")

        layout = QHBoxLayout(self)

        layout.setContentsMargins(12, 9, 12, 9)

        if accent:

            dot = QLabel("●")

            dot.setStyleSheet(f"color: {accent}; background: transparent;")

            layout.addWidget(dot)

        text = QVBoxLayout()

        text.setSpacing(0)

        title_label = make_label(title, "rowTitle")

        title_label.setToolTip(title)

        text.addWidget(title_label)

        sub = make_label(subtitle, "rowSub")

        sub.setToolTip(subtitle)

        text.addWidget(sub)

        layout.addLayout(text, 1)

        if right_text:
            layout.addWidget(make_label(right_text, "rowSub"))


class DataTable(QWidget):
    """QTableWidget + professional empty state, read-only."""

    def __init__(self, multi=False, icon="📭", empty_title="No records", empty_text=""):

        super().__init__()

        self.table = QTableWidget()

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
            if multi else QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.table.setAlternatingRowColors(True)

        self.table.setShowGrid(False)

        self.table.setFrameShape(QFrame.Shape.NoFrame)

        self.table.setWordWrap(False)

        self.table.verticalHeader().setVisible(False)

        self.table.horizontalHeader().setHighlightSections(False)

        self.empty = EmptyState(icon, empty_title, empty_text)

        self.stack = QStackedLayout(self)

        self.stack.addWidget(self.table)

        self.stack.addWidget(self.empty)

        self.setMinimumHeight(180)

    def set_empty_text(self, title, text=""):

        self.empty.set_text(title, text)

    def set_rows(self, headers, rows, fit=(), right=()):
        """rows: list of (row_id, [cells], opts) ; opts: {'bold': bool,
        'colors': {column: '#hex'}}  (opts optional)."""

        self.table.setUpdatesEnabled(False)

        self.table.clearContents()

        self.table.setColumnCount(len(headers))

        self.table.setHorizontalHeaderLabels(headers)

        self.table.setRowCount(len(rows))

        self.table.verticalHeader().setDefaultSectionSize(PREFS.row_height)

        for row_index, entry in enumerate(rows):

            row_id, cells = entry[0], entry[1]

            opts = entry[2] if len(entry) > 2 else {}

            for column, value in enumerate(cells):

                text = "" if value is None else str(value)

                item = QTableWidgetItem(text)

                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                item.setToolTip(text)

                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row_id)

                if column in right:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )

                color = opts.get("colors", {}).get(column)

                if color:
                    item.setForeground(QColor(color))

                if opts.get("bold"):
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.table.setItem(row_index, column, item)

        header = self.table.horizontalHeader()

        header.setStretchLastSection(False)

        for column in range(len(headers)):

            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents
                if column in fit else QHeaderView.ResizeMode.Stretch,
            )

        self.table.setUpdatesEnabled(True)

        self.stack.setCurrentWidget(self.table if rows else self.empty)

    def selected_ids(self):

        ids = []

        for index in self.table.selectionModel().selectedRows():

            item = self.table.item(index.row(), 0)

            if item is not None:
                ids.append(item.data(Qt.ItemDataRole.UserRole))

        return ids

    def selected_id(self):

        row = self.table.currentRow()

        item = self.table.item(row, 0) if row >= 0 else None

        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None


class ChartCanvas(QWidget):
    """Matplotlib chart that follows the active palette, with an empty state."""

    def __init__(self, empty_title, empty_text="", height=250):

        super().__init__()

        self.setMinimumHeight(height)

        self.stack = QStackedLayout(self)

        self.empty = EmptyState("📊", empty_title, empty_text)

        self.fig = None

        self.canvas = None

        self._draw = None

        self._theme = None

        if MATPLOTLIB_OK:

            self.fig = Figure(figsize=(5, 2.6), dpi=100)

            self.canvas = FigureCanvasQTAgg(self.fig)

            self.canvas.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

            self.stack.addWidget(self.canvas)

        else:

            self.empty.set_text("Charts unavailable", "Install matplotlib to see charts.")

        self.stack.addWidget(self.empty)

        self.stack.setCurrentWidget(self.empty)

    def show_chart(self, draw_fn, theme):
        """draw_fn(ax, palette) -> False when there is no data."""

        self._draw = draw_fn

        self._theme = theme

        self.redraw()

    def set_theme(self, theme):

        self._theme = theme

        self.redraw()

    def redraw(self):

        if not MATPLOTLIB_OK or self._draw is None or self._theme is None:
            return

        p = self._theme

        try:

            self.fig.clear()

            self.fig.patch.set_facecolor(p["surface"])

            ax = self.fig.add_subplot(111)

            ax.set_facecolor(p["surface"])

            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)

            for spine in ("left", "bottom"):
                ax.spines[spine].set_color(p["border"])

            ax.tick_params(colors=p["muted"], labelsize=8)

            ax.yaxis.label.set_color(p["muted"])

            ax.grid(axis="y", color=p["border"], linewidth=0.6, alpha=0.7)

            ax.set_axisbelow(True)

            if self._draw(ax, p) is False:
                self.stack.setCurrentWidget(self.empty)
                return

            try:
                self.fig.tight_layout()
            except Exception:
                pass

            self.canvas.draw_idle()

            self.stack.setCurrentWidget(self.canvas)

        except Exception:
            logger.exception("Chart rendering failed")
            self.empty.set_text("Chart unavailable", "The chart could not be drawn.")
            self.stack.setCurrentWidget(self.empty)

    def clear(self, title=None, text=""):

        self._draw = None

        if title:
            self.empty.set_text(title, text)

        self.stack.setCurrentWidget(self.empty)


# ==============================================================
# CHART DRAWING FUNCTIONS
# ==============================================================

def _legend(ax, p):

    legend = ax.legend(fontsize=8, frameon=True, loc="upper left", ncol=3)

    legend.get_frame().set_facecolor(p["surface"])

    legend.get_frame().set_edgecolor(p["border"])

    for text in legend.get_texts():
        text.set_color(p["text"])


def draw_attendance_months(data):
    """data: [(month_key, present, absent, leave)]"""

    def draw(ax, p):

        if not data:
            return False

        labels = [short_month(row[0]) for row in data]

        positions = list(range(len(data)))

        present = [row[1] for row in data]
        absent = [row[2] for row in data]
        leave = [row[3] for row in data]

        ax.bar(positions, present, color=p["success"], label="Present", width=0.55)

        ax.bar(positions, absent, bottom=present, color=p["danger"], label="Absent", width=0.55)

        bottoms = [a + b for a, b in zip(present, absent)]

        ax.bar(positions, leave, bottom=bottoms, color=p["warning"], label="Leave", width=0.55)

        ax.set_xticks(positions)

        ax.set_xticklabels(labels)

        ax.set_ylabel("Days")

        _legend(ax, p)

        return True

    return draw


def draw_performance_trend(records):
    """records: performance dicts (any order)."""

    def draw(ax, p):

        ordered = sorted((r for r in records if r["date"]), key=lambda r: r["date"])

        if not ordered:
            return False

        use_pct = any(r["percentage"] is not None for r in ordered)

        points = [
            (r["date"], r["percentage"] if use_pct else r["score"])
            for r in ordered
        ]

        points = [(d, v) for d, v in points if v is not None]

        if not points:
            return False

        xs = list(range(len(points)))

        ys = [v for _, v in points]

        ax.plot(xs, ys, color=p["primary"], linewidth=2.2, marker="o", markersize=6)

        ax.fill_between(xs, ys, min(ys + [0]), color=p["primary"], alpha=0.12)

        step = max(1, len(xs) // 7)

        ax.set_xticks(xs[::step])

        ax.set_xticklabels([d.strftime("%d %b %y") for d, _ in points][::step], rotation=0)

        ax.set_ylabel("Percentage" if use_pct else "Score")

        if use_pct:
            ax.set_ylim(0, 105)

        for x, y in zip(xs, ys):
            ax.annotate(f"{y:g}", (x, y), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8, color=p["text"])

        return True

    return draw


def draw_salary_breakdown(record):

    def draw(ax, p):

        if record is None:
            return False

        labels = ["Basic", "Allowances", "Deductions", "Net"]

        values = [record["basic"], record["allowances"], record["deductions"], record["net"]]

        if not any(values):
            return False

        colors = [p["info"], p["success"], p["danger"], p["primary"]]

        bars = ax.bar(labels, values, color=colors, width=0.55)

        top = max(values) or 1

        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + top * 0.02,
                    fmt_money(value, ""), ha="center", fontsize=8, color=p["text"])

        ax.set_ylim(0, top * 1.18)

        ax.set_ylabel("Amount")

        return True

    return draw


# ==============================================================
# DIALOGS
# ==============================================================

class EditProfileDialog(QDialog):
    """Only the safe, self-editable fields."""

    def __init__(self, employee, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Edit Profile")

        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        layout.setSpacing(12)

        layout.addWidget(make_label("Edit contact details", "pageTitle"))

        layout.addWidget(
            make_label(
                "Employee ID, department, designation, salary, employment type "
                "and status can only be changed by HR.",
                "pageSubtitle",
                wrap=True,
            )
        )

        form = QFormLayout()

        form.setSpacing(10)

        self.phone = QLineEdit(employee["phone"])

        self.email = QLineEdit(employee["email"])

        self.address = QLineEdit(employee["address"])

        self.em_name = QLineEdit(employee["emergency_name"])

        self.em_phone = QLineEdit(employee["emergency_phone"])

        form.addRow("Phone", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Address", self.address)
        form.addRow("Emergency contact", self.em_name)
        form.addRow("Emergency phone", self.em_phone)

        layout.addLayout(form)

        self.error = make_label("", "muted", wrap=True)

        self.error.setStyleSheet("color: #EF4444; font-weight: 600;")

        self.error.hide()

        layout.addWidget(self.error)

        buttons = QHBoxLayout()

        buttons.addStretch()

        cancel = make_button("Cancel", "secondaryButton")

        cancel.clicked.connect(self.reject)

        save = make_button("Save Changes", "primaryButton")

        save.clicked.connect(self.try_accept)

        buttons.addWidget(cancel)

        buttons.addWidget(save)

        layout.addLayout(buttons)

    def values(self):

        return {
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
            "address": self.address.text().strip(),
            "emergency_name": self.em_name.text().strip(),
            "emergency_phone": self.em_phone.text().strip(),
        }

    def validation_error(self):

        v = self.values()

        if not EMAIL_RE.match(v["email"]):
            return "Please enter a valid email address."

        if v["phone"] and not valid_phone(v["phone"]):
            return "Please enter a valid phone number (7-15 digits)."

        if v["emergency_phone"] and not valid_phone(v["emergency_phone"]):
            return "Please enter a valid emergency phone number."

        if v["emergency_phone"] and not v["emergency_name"]:
            return "Please enter the emergency contact's name."

        return None

    def try_accept(self):

        message = self.validation_error()

        if message:
            self.error.setText(message)
            self.error.show()
            return

        self.accept()


class PayslipDialog(QDialog):
    """Read-only payslip preview for the employee's own payroll record."""

    def __init__(self, employee, record, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Payslip")

        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        period = month_label(record["month"]) if record["month"] else record["month_raw"]

        layout.addWidget(make_label(f"Payslip — {period}", "pageTitle"))

        layout.addWidget(
            make_label(f"{employee['name']}  •  {employee['code']}", "pageSubtitle")
        )

        layout.addSpacing(6)

        body = QLabel(
            "<table cellpadding='7' width='100%'>"
            f"<tr><td>Basic salary</td><td align='right'>{fmt_money(record['basic'])}</td></tr>"
            f"<tr><td>Allowances</td><td align='right'>+ {fmt_money(record['allowances'])}</td></tr>"
            f"<tr><td>Deductions</td><td align='right'>- {fmt_money(record['deductions'])}</td></tr>"
            f"<tr><td><b>Net salary</b></td><td align='right'><b>{fmt_money(record['net'])}</b></td></tr>"
            "</table>"
        )

        body.setObjectName("summaryBox")

        body.setTextFormat(Qt.TextFormat.RichText)

        layout.addWidget(body)

        status_row = QHBoxLayout()

        status_row.addWidget(make_label("Status", "muted"))

        status_row.addWidget(Badge(record["status"] or "Unknown",
                                   badge_kind_for_status(record["status"])))

        status_row.addStretch()

        layout.addLayout(status_row)

        layout.addSpacing(8)

        buttons = QHBoxLayout()

        buttons.addStretch()

        download = make_button("⬇  Download PDF", "primaryButton")

        download.clicked.connect(lambda: download_payslip(self, employee, record))

        close = make_button("Close", "secondaryButton")

        close.clicked.connect(self.accept)

        buttons.addWidget(download)

        buttons.addWidget(close)

        layout.addLayout(buttons)


# ==============================================================
# PAGES
# ==============================================================

class BasePage(QWidget):
    """Common page frame: title row, error banner, scrollable body.

    Subclasses implement load(); refresh() wraps it with error handling and
    returns True/False so the window can report failures once.
    """

    TITLE = ""
    SUBTITLE = ""
    SECTION = "data"

    def __init__(self, window):

        super().__init__()

        self.win = window

        self.svc = window.svc

        outer = QVBoxLayout(self)

        outer.setContentsMargins(26, 20, 26, 10)

        outer.setSpacing(12)

        head = QHBoxLayout()

        titles = QVBoxLayout()

        titles.setSpacing(0)

        titles.addWidget(make_label(self.TITLE, "pageTitle"))

        titles.addWidget(make_label(self.SUBTITLE, "pageSubtitle"))

        head.addLayout(titles, 1)

        self.actions = QHBoxLayout()

        self.actions.setSpacing(8)

        head.addLayout(self.actions)

        outer.addLayout(head)

        self.banner = ErrorBanner()

        self.banner.retry.connect(self.refresh)

        outer.addWidget(self.banner)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()

        container.setObjectName("pageBody")

        container.setStyleSheet("#pageBody { background: transparent; }")

        self.body = QVBoxLayout(container)

        self.body.setContentsMargins(0, 4, 4, 16)

        self.body.setSpacing(14)

        scroll.setWidget(container)

        outer.addWidget(scroll, 1)

        self.build()

    # ---- hooks ----

    def build(self):
        """Create widgets once."""

    def load(self):
        """Fetch data and fill widgets. May raise DataLoadError."""

    def apply_theme(self, theme):
        """Re-render theme-dependent content (charts etc.)."""

    # ---- behaviour ----

    def refresh(self):

        try:

            self.banner.hide()

            self.load()

            return True

        except DataLoadError as exc:

            self.banner.show_message(exc.user_message)

        except Exception:

            logger.exception("Unexpected error while loading %s", self.SECTION)

            self.banner.show_message(f"Unable to load {self.SECTION} data.")

        return False

    def theme(self):

        return self.win.theme

    def require_employee(self):

        return self.svc.get_employee()


# --------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------

class DashboardPage(BasePage):

    TITLE = "Dashboard"
    SUBTITLE = "Your personal work overview"
    SECTION = "dashboard"

    def build(self):

        self.fader = Fader(self)

        self.first_load = True

        # ---------- welcome ----------
        self.welcome = QFrame()

        self.welcome.setObjectName("welcomeCard")

        wl = QVBoxLayout(self.welcome)

        wl.setContentsMargins(26, 22, 26, 22)

        wl.setSpacing(6)

        self.welcome_title = make_label("", "welcomeTitle")

        self.welcome_sub = make_label("Here is your personal work overview.", "welcomeSub")

        wl.addWidget(self.welcome_title)

        wl.addWidget(self.welcome_sub)

        chips = QHBoxLayout()

        chips.setSpacing(8)

        self.chip_id = make_label("", "welcomeChip")

        self.chip_dept = make_label("", "welcomeChip")

        self.chip_role = make_label("", "welcomeChip")

        for chip in (self.chip_id, self.chip_dept, self.chip_role):
            chips.addWidget(chip)

        chips.addStretch()

        wl.addSpacing(6)

        wl.addLayout(chips)

        self.body.addWidget(self.welcome)

        # ---------- stat cards ----------
        grid = QGridLayout()

        grid.setSpacing(14)

        specs = [
            ("attendance", "📊", "Attendance", "#3B82F6", 2),
            ("present", "✅", "Present Days", "#22C55E", 2),
            ("salary", "💰", "Net Salary (This Month)", "#A855F7", 3),
            ("performance", "⭐", "Performance Score", "#F59E0B", 4),
            ("leave", "🌴", "Pending Leave Requests", "#14B8A6", 5),
            ("notes", "🔔", "Unread Notifications", "#EF4444", 6),
        ]

        self.cards = {}

        for index, (key, icon, title, color, target) in enumerate(specs):

            card = StatCard(icon, title, color)

            card.clicked.connect(lambda t=target: self.win.go_to(t))

            self.cards[key] = card

            grid.addWidget(card, index // 3, index % 3)

        for column in range(3):
            grid.setColumnStretch(column, 1)

        self.body.addLayout(grid)

        # ---------- charts ----------
        charts = QHBoxLayout()

        charts.setSpacing(14)

        att_card, att_layout = make_card("Monthly Attendance", "Last 6 months")

        self.att_chart = ChartCanvas("No attendance records available.")

        att_layout.addWidget(self.att_chart)

        perf_card, perf_layout = make_card("Performance Trend", "Your review history")

        self.perf_chart = ChartCanvas("No performance records available.")

        perf_layout.addWidget(self.perf_chart)

        charts.addWidget(att_card, 1)

        charts.addWidget(perf_card, 1)

        self.body.addLayout(charts)

        # ---------- lists ----------
        lists = QHBoxLayout()

        lists.setSpacing(14)

        notes_card, notes_layout = make_card("Recent Notifications")

        self.notes_list = QVBoxLayout()

        self.notes_list.setSpacing(8)

        notes_layout.addLayout(self.notes_list)

        notes_layout.addStretch()

        events_card, events_layout = make_card("Upcoming Events")

        self.events_list = QVBoxLayout()

        self.events_list.setSpacing(8)

        events_layout.addLayout(self.events_list)

        events_layout.addStretch()

        lists.addWidget(notes_card, 1)

        lists.addWidget(events_card, 1)

        self.body.addLayout(lists)

        self.body.addStretch()

    # ---- data ----

    @staticmethod
    def _try(errors, fn, default):

        try:
            return fn()
        except DataLoadError as exc:
            errors.append(exc.user_message)
            return default

    def load(self):

        errors = []

        employee = self._try(errors, self.svc.get_employee, None)

        attendance = self._try(errors, self.svc.attendance_records, [])

        payroll = self._try(errors, self.svc.payroll_records, [])

        performance = self._try(errors, self.svc.performance_records, [])

        notes = self._try(errors, self.svc.notifications, [])

        events = self._try(errors, self.svc.calendar_events, [])

        if employee:

            self.welcome_title.setText(f"{greeting()}, {employee['name'] or 'there'}")

            self.chip_id.setText(f"🆔  {employee['code'] or '—'}")

            self.chip_dept.setText(f"🏢  {employee['department'] or '—'}")

            self.chip_role.setText(f"💼  {employee['designation'] or '—'}")

        self._fill_cards(attendance, payroll, performance, notes)

        theme = self.theme()

        self.att_chart.show_chart(draw_attendance_months(monthly_attendance(attendance)), theme)

        self.perf_chart.show_chart(draw_performance_trend(performance), theme)

        self._fill_notifications(notes)

        self._fill_events(events)

        if self.first_load:
            self.first_load = False
            self.fader.start(self.welcome, 500)

        if errors:
            raise DataLoadError(" ".join(dict.fromkeys(errors)), "dashboard")

    def _fill_cards(self, attendance, payroll, performance, notes):

        key = current_month_key()

        month_records = [
            r for r in attendance if r["date"] and r["date"].strftime("%Y-%m") == key
        ]

        summary = attendance_summary(month_records)

        grade, kind = attendance_grade(summary["pct"])

        self.cards["attendance"].set_data(
            pct_text(summary["pct"]),
            f"{month_label(key)} • {summary['total']} recorded days",
            grade,
            kind,
        )

        self.cards["present"].set_data(
            summary["present"],
            f"Absent {summary['absent']} • Leave {summary['leave']}",
        )

        current = next((r for r in payroll if r["month"] == key), None)

        if current:
            self.cards["salary"].set_data(
                fmt_money(current["net"]),
                f"Payroll for {month_label(key)}",
                current["status"] or None,
                badge_kind_for_status(current["status"]),
            )
        else:
            self.cards["salary"].set_data(
                "—", f"Not generated for {month_label(key)}"
            )

        latest = performance[0] if performance else None

        if latest and (latest["score"] is not None or latest["percentage"] is not None):

            value = f"{latest['score']:g}" if latest["score"] is not None else pct_text(latest["percentage"])

            extra = f"{latest['percentage']:g}% • " if latest["percentage"] is not None else ""

            self.cards["performance"].set_data(
                value,
                f"{extra}Reviewed {fmt_date(latest['date'])}",
                latest["category"] or None,
                "primary",
            )
        else:
            self.cards["performance"].set_data("—", "No performance records available.")

        if self.svc.leave_supported():
            self.cards["leave"].set_data("0", "Awaiting approval")
        else:
            self.cards["leave"].set_data("N/A", "Leave module not enabled")

        unread = sum(1 for n in notes if not n["read"])

        self.cards["notes"].set_data(
            unread,
            "You're all caught up." if unread == 0 else "Waiting for you",
            "New" if unread else None,
            "danger",
        )

    def _fill_notifications(self, notes):

        clear_layout(self.notes_list)

        if not notes:
            self.notes_list.addWidget(EmptyState("🎉", "You're all caught up."))
            return

        for note in notes[:5]:

            self.notes_list.addWidget(
                ListRow(
                    note["title"] or "Notification",
                    note["message"][:90],
                    fmt_date(note["created"]),
                    None if note["read"] else self.theme()["primary"],
                )
            )

    def _fill_events(self, events):

        clear_layout(self.events_list)

        today = date.today()

        upcoming = [e for e in events if e["date"] and e["date"] >= today][:5]

        if not upcoming:
            self.events_list.addWidget(EmptyState("📅", "No upcoming events."))
            return

        for event in upcoming:

            color = EVENT_TYPE_COLORS.get(event["type"].lower(), "#64748B")

            self.events_list.addWidget(
                ListRow(event["title"], event["type"], fmt_date(event["date"]), color)
            )

    def apply_theme(self, theme):

        self.att_chart.set_theme(theme)

        self.perf_chart.set_theme(theme)


# --------------------------------------------------------------
# PROFILE
# --------------------------------------------------------------

class ProfilePage(BasePage):

    TITLE = "My Profile"
    SUBTITLE = "Your personal and employment details"
    SECTION = "profile"

    def build(self):

        self.employee = None

        self.edit_button = make_button("✏  Edit Profile", "primaryButton")

        self.edit_button.clicked.connect(self.edit_profile)

        self.actions.addWidget(self.edit_button)

        # header card
        header, hl = make_card()

        row = QHBoxLayout()

        row.setSpacing(18)

        self.avatar = QLabel()

        self.avatar.setFixedSize(96, 96)

        row.addWidget(self.avatar)

        info = QVBoxLayout()

        info.setSpacing(3)

        self.name_label = make_label("", "pageTitle")

        self.role_label = make_label("", "pageSubtitle")

        self.status_badge = Badge("", "info")

        info.addStretch()

        info.addWidget(self.name_label)

        info.addWidget(self.role_label)

        info.addSpacing(4)

        info.addWidget(self.status_badge)

        info.addStretch()

        row.addLayout(info, 1)

        hl.addLayout(row)

        self.body.addWidget(header)

        personal, pl = make_card("Personal Information")

        self.personal_grid = InfoGrid(2)

        pl.addWidget(self.personal_grid)

        self.body.addWidget(personal)

        job, jl = make_card("Employment Details", "Managed by HR (read-only)")

        self.job_grid = InfoGrid(2)

        jl.addWidget(self.job_grid)

        self.body.addWidget(job)

        emergency, el = make_card("Emergency Contact")

        self.emergency_grid = InfoGrid(2)

        el.addWidget(self.emergency_grid)

        self.body.addWidget(emergency)

        self.body.addStretch()

    def load(self):

        self.employee = employee = self.require_employee()

        self.name_label.setText(employee["name"] or "—")

        self.role_label.setText(
            f"{employee['designation'] or '—'}  •  {employee['department'] or '—'}"
        )

        self.status_badge.set_kind(
            employee["status"] or "Unknown", badge_kind_for_status(employee["status"])
        )

        self.refresh_avatar()

        self.personal_grid.set_items([
            ("Full Name", employee["name"]),
            ("Email", employee["email"]),
            ("Phone", employee["phone"]),
            ("Gender", employee["gender"]),
            ("Date of Birth", fmt_date(employee["dob"], "")),
            ("Address", employee["address"]),
        ])

        self.job_grid.set_items([
            ("Employee ID", employee["code"]),
            ("Department", employee["department"]),
            ("Designation", employee["designation"]),
            ("Employment Type", employee["employment_type"]),
            ("Joining Date", fmt_date(employee["joining_date"], "")),
            ("Salary", fmt_money(employee["salary"]) if employee["salary"] is not None else ""),
            ("Status", employee["status"]),
        ])

        self.emergency_grid.set_items([
            ("Contact Name", employee["emergency_name"]),
            ("Contact Phone", employee["emergency_phone"]),
        ])

    def refresh_avatar(self):

        if self.employee:

            self.avatar.setPixmap(
                make_avatar(self.employee["name"], 96, self.employee["photo"],
                            self.theme()["primary"])
            )

    def apply_theme(self, theme):

        self.refresh_avatar()

    def edit_profile(self):

        if not self.employee:
            QMessageBox.information(self, "Edit Profile", "Your profile is not loaded yet.")
            return

        dialog = EditProfileDialog(self.employee, self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.svc.update_contact(dialog.values())
        except DataWriteError as exc:
            QMessageBox.warning(self, "Edit Profile", str(exc))
            return

        QMessageBox.information(self, "Edit Profile", "Your profile was updated.")

        self.win.refresh_all()


# --------------------------------------------------------------
# ATTENDANCE
# --------------------------------------------------------------

class AttendancePage(BasePage):

    TITLE = "My Attendance"
    SUBTITLE = "Read-only history of your attendance"
    SECTION = "attendance"

    def build(self):

        self.records = []

        self.filtered = []

        self._loading = False

        self.export_button = make_export_button(self, self.export_data)

        self.actions.addWidget(self.export_button)

        # ---- filters ----
        filters, fl = make_card()

        row = QHBoxLayout()

        row.setSpacing(10)

        self.month_combo = QComboBox()

        self.status_combo = QComboBox()

        self.status_combo.addItems(["All Statuses", "Present", "Absent", "Leave"])

        self.range_check = QCheckBox("Date range")

        self.from_edit = QDateEdit(QDate.currentDate().addDays(-30))

        self.to_edit = QDateEdit(QDate.currentDate())

        for edit in (self.from_edit, self.to_edit):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("dd MMM yyyy")
            edit.setEnabled(False)

        reset = make_button("Reset", "secondaryButton")

        reset.clicked.connect(self.reset_filters)

        row.addWidget(make_label("Month", "muted"))
        row.addWidget(self.month_combo)
        row.addWidget(make_label("Status", "muted"))
        row.addWidget(self.status_combo)
        row.addWidget(self.range_check)
        row.addWidget(self.from_edit)
        row.addWidget(make_label("to", "muted"))
        row.addWidget(self.to_edit)
        row.addStretch()
        row.addWidget(reset)

        fl.addLayout(row)

        self.body.addWidget(filters)

        self.month_combo.currentIndexChanged.connect(self.apply_filters)

        self.status_combo.currentIndexChanged.connect(self.apply_filters)

        self.range_check.toggled.connect(self._range_toggled)

        self.from_edit.dateChanged.connect(self.apply_filters)

        self.to_edit.dateChanged.connect(self.apply_filters)

        # ---- summary tiles ----
        self.summary_title = make_label("", "cardSubtitle")

        self.body.addWidget(self.summary_title)

        tiles = QHBoxLayout()

        tiles.setSpacing(14)

        self.tiles = {}

        for key, icon, title, color in [
            ("pct", "📊", "Attendance %", "#3B82F6"),
            ("present", "✅", "Present Days", "#22C55E"),
            ("absent", "❌", "Absent Days", "#EF4444"),
            ("leave", "🌴", "Leave Days", "#F59E0B"),
            ("hours", "⏱", "Total Working Hours", "#A855F7"),
        ]:
            tile = StatCard(icon, title, color)

            tile.setMinimumHeight(112)

            tile.setCursor(Qt.CursorShape.ArrowCursor)

            self.tiles[key] = tile

            tiles.addWidget(tile, 1)

        self.body.addLayout(tiles)

        self.progress = QProgressBar()

        self.progress.setRange(0, 100)

        self.progress.setFixedHeight(12)

        self.body.addWidget(self.progress)

        # ---- chart + table ----
        chart_card, cl = make_card("Monthly Attendance", "Last 6 months (all records)")

        self.chart = ChartCanvas("No attendance records available.")

        cl.addWidget(self.chart)

        self.body.addWidget(chart_card)

        table_card, tl = make_card("Attendance History")

        self.table = DataTable(
            icon="🕒",
            empty_title="No attendance records available.",
            empty_text="Records appear here once attendance is marked.",
        )

        self.table.setMinimumHeight(320)

        tl.addWidget(self.table)

        self.body.addWidget(table_card)

    # ---- filters ----

    def _range_toggled(self, enabled):

        self.from_edit.setEnabled(enabled)

        self.to_edit.setEnabled(enabled)

        self.apply_filters()

    def reset_filters(self):

        self._loading = True

        self.month_combo.setCurrentIndex(self._month_index(current_month_key()))

        self.status_combo.setCurrentIndex(0)

        self.range_check.setChecked(False)

        self._loading = False

        self.apply_filters()

    def _month_index(self, key):

        index = self.month_combo.findData(key)

        return index if index >= 0 else 0

    def _rebuild_months(self):

        first = self.month_combo.count() == 0

        keep = self.month_combo.currentData()

        keys = {r["date"].strftime("%Y-%m") for r in self.records if r["date"]}

        keys.add(current_month_key())

        self._loading = True

        self.month_combo.clear()

        self.month_combo.addItem("All Months", None)

        for key in sorted(keys, reverse=True):
            self.month_combo.addItem(month_label(key), key)

        if first or (keep is not None and keep not in keys):
            wanted = current_month_key()
        else:
            wanted = keep

        self.month_combo.setCurrentIndex(self._month_index(wanted) if wanted else 0)

        self._loading = False

    def apply_filters(self, *_):

        if self._loading:
            return

        month = self.month_combo.currentData()

        status = self.status_combo.currentText()

        use_range = self.range_check.isChecked()

        start = self.from_edit.date().toPython()

        end = self.to_edit.date().toPython()

        result = []

        for record in self.records:

            day = record["date"]

            if month and (not day or day.strftime("%Y-%m") != month):
                continue

            if status != "All Statuses" and record["category"] != status:
                continue

            if use_range and (not day or day < start or day > end):
                continue

            result.append(record)

        self.filtered = result

        self.render()

    # ---- rendering ----

    def render(self):

        summary = attendance_summary(self.filtered)

        month = self.month_combo.currentData()

        self.summary_title.setText(
            f"Summary — {month_label(month) if month else 'All months'}"
            f"  ({len(self.filtered)} records)"
        )

        grade, kind = attendance_grade(summary["pct"])

        self.tiles["pct"].set_data(pct_text(summary["pct"]), "Present ÷ recorded days", grade, kind)

        self.tiles["present"].set_data(summary["present"], "Days present")

        self.tiles["absent"].set_data(summary["absent"], "Days absent")

        self.tiles["leave"].set_data(summary["leave"], "Days on leave")

        self.tiles["hours"].set_data(fmt_hours(summary["hours"]), "Logged working time")

        self.progress.setValue(int(summary["pct"] or 0))

        rows = []

        for record in self.filtered:

            color = {"success": self.theme()["success"], "warning": self.theme()["warning"],
                     "danger": self.theme()["danger"], "info": self.theme()["info"]}[
                badge_kind_for_status(record["status"])
            ]

            rows.append((
                record["id"],
                [
                    fmt_date(record["date"]),
                    fmt_time(record["check_in"]),
                    fmt_time(record["check_out"]),
                    fmt_hours(record["hours"]) if record["hours"] else "—",
                    record["status"] or "—",
                ],
                {"colors": {4: color}},
            ))

        if self.records and not rows:
            self.table.set_empty_text("No records match your filters.", "Try resetting the filters.")
        else:
            self.table.set_empty_text(
                "No attendance records available.",
                "Records appear here once attendance is marked.",
            )

        self.table.set_rows(
            ["Date", "Check In", "Check Out", "Working Hours", "Status"], rows
        )

    def load(self):

        self.records = self.svc.attendance_records()

        self._rebuild_months()

        self.chart.show_chart(
            draw_attendance_months(monthly_attendance(self.records)), self.theme()
        )

        self.apply_filters()

    def export_data(self):

        employee = self.svc.get_employee()

        rows = [
            [fmt_date(r["date"]), fmt_time(r["check_in"]), fmt_time(r["check_out"]),
             fmt_hours(r["hours"]) if r["hours"] else "", r["status"]]
            for r in self.filtered
        ]

        return (
            f"My_Attendance_{employee['code']}",
            "My Attendance Report",
            f"{employee['name']} ({employee['code']}) - generated "
            f"{datetime.now().strftime('%d %b %Y')}",
            ["Date", "Check In", "Check Out", "Working Hours", "Status"],
            rows,
        )

    def apply_theme(self, theme):

        self.chart.set_theme(theme)

        if self.records:
            self.render()


# --------------------------------------------------------------
# PAYROLL
# --------------------------------------------------------------

class PayrollPage(BasePage):

    TITLE = "My Payroll"
    SUBTITLE = "Your salary details (read-only)"
    SECTION = "payroll"

    def build(self):

        self.records = []

        self.employee = None

        self.export_button = make_export_button(self, self.export_data)

        self.actions.addWidget(self.export_button)

        top = QHBoxLayout()

        top.setSpacing(14)

        # ---- current month card ----
        self.current_card, cl = make_card()

        title_row = QHBoxLayout()

        self.current_title = make_label("Current Month Payroll", "cardTitle")

        title_row.addWidget(self.current_title, 1)

        self.status_badge = Badge("", "info")

        self.status_badge.hide()

        title_row.addWidget(self.status_badge)

        cl.addLayout(title_row)

        self.current_sub = make_label("", "cardSubtitle")

        cl.addWidget(self.current_sub)

        self.current_grid = InfoGrid(2)

        cl.addWidget(self.current_grid)

        self.net_label = make_label("—", "bigNumber")

        cl.addWidget(make_label("NET SALARY", "fieldLabel"))

        cl.addWidget(self.net_label)

        self.current_empty = EmptyState("💰", "No payroll records available.")

        cl.addWidget(self.current_empty)

        buttons = QHBoxLayout()

        self.view_button = make_button("👁  View Payslip", "secondaryButton")

        self.pdf_button = make_button("⬇  Download Payslip PDF", "primaryButton")

        self.view_button.clicked.connect(self.view_payslip)

        self.pdf_button.clicked.connect(self.download_pdf)

        buttons.addWidget(self.view_button)

        buttons.addWidget(self.pdf_button)

        buttons.addStretch()

        cl.addLayout(buttons)

        top.addWidget(self.current_card, 1)

        # ---- breakdown chart ----
        chart_card, chl = make_card("Salary Breakdown", "Selected payroll record")

        self.chart = ChartCanvas("No payroll records available.")

        chl.addWidget(self.chart)

        top.addWidget(chart_card, 1)

        self.body.addLayout(top)

        # ---- history ----
        history, hl = make_card("Payroll History", "Select a row to view its payslip")

        self.table = DataTable(
            icon="💰",
            empty_title="No payroll records available.",
            empty_text="Your payslips will appear here once payroll is generated.",
        )

        self.table.setMinimumHeight(300)

        self.table.table.itemSelectionChanged.connect(self.selection_changed)

        self.table.table.doubleClicked.connect(lambda *_: self.view_payslip())

        hl.addWidget(self.table)

        self.body.addWidget(history)

    # ---- helpers ----

    def _record_by_id(self, record_id):

        return next((r for r in self.records if r["id"] == record_id), None)

    def current_record(self):
        """This month's record, if payroll has been generated."""

        key = current_month_key()

        return next((r for r in self.records if r["month"] == key), None)

    def active_record(self):
        """Selected row -> this month -> latest."""

        selected = self._record_by_id(self.table.selected_id())

        if selected:
            return selected

        return self.current_record() or (self.records[0] if self.records else None)

    # ---- load ----

    def load(self):

        self.employee = self.svc.get_employee()

        self.records = self.svc.payroll_records()

        self._fill_current()

        rows = []

        for record in self.records:

            kind = badge_kind_for_status(record["status"])

            rows.append((
                record["id"],
                [
                    month_label(record["month"]) if record["month"] else record["month_raw"],
                    fmt_money(record["basic"]),
                    fmt_money(record["allowances"]),
                    fmt_money(record["deductions"]),
                    fmt_money(record["net"]),
                    record["status"] or "—",
                ],
                {"colors": {5: self.theme()[kind]}},
            ))

        self.table.set_rows(
            ["Payroll Month", "Basic Salary", "Allowances", "Deductions", "Net Salary", "Status"],
            rows,
            right=(1, 2, 3, 4),
        )

        self.update_chart()

        has = bool(self.records)

        self.view_button.setEnabled(has)

        self.pdf_button.setEnabled(has)

    def _fill_current(self):

        key = current_month_key()

        record = self.current_record()

        self.current_title.setText("Current Month Payroll")

        if record is None:

            self.current_sub.setText(f"{month_label(key)} — payroll not generated yet")

            self.current_grid.hide()

            self.net_label.hide()

            self.status_badge.hide()

            self.current_empty.set_text(
                "No payroll for this month yet.",
                "Your latest payslip is available in the history below."
                if self.records else "No payroll records available.",
            )

            self.current_empty.show()

            return

        self.current_empty.hide()

        self.current_grid.show()

        self.net_label.show()

        self.current_sub.setText(month_label(key))

        self.current_grid.set_items([
            ("Basic Salary", fmt_money(record["basic"])),
            ("Allowances", fmt_money(record["allowances"])),
            ("Deductions", fmt_money(record["deductions"])),
            ("Status", record["status"] or "—"),
        ])

        self.net_label.setText(fmt_money(record["net"]))

        self.status_badge.set_kind(record["status"] or "Unknown",
                                   badge_kind_for_status(record["status"]))

        self.status_badge.show()

    def update_chart(self):

        record = self.active_record()

        self.chart.show_chart(draw_salary_breakdown(record), self.theme())

    def selection_changed(self):

        self.update_chart()

    # ---- actions ----

    def view_payslip(self):

        record = self.active_record()

        if not record or not self.employee:
            QMessageBox.information(self, "Payslip", "No payroll record is available.")
            return

        PayslipDialog(self.employee, record, self).exec()

    def download_pdf(self):

        record = self.active_record()

        if not record or not self.employee:
            QMessageBox.information(self, "Payslip", "No payroll record is available.")
            return

        download_payslip(self, self.employee, record)

    def export_data(self):

        employee = self.svc.get_employee()

        rows = [
            [month_label(r["month"]) if r["month"] else r["month_raw"],
             fmt_money(r["basic"]), fmt_money(r["allowances"]),
             fmt_money(r["deductions"]), fmt_money(r["net"]), r["status"]]
            for r in self.records
        ]

        return (
            f"My_Payroll_{employee['code']}",
            "My Payroll Report",
            f"{employee['name']} ({employee['code']}) - generated "
            f"{datetime.now().strftime('%d %b %Y')}",
            ["Payroll Month", "Basic Salary", "Allowances", "Deductions", "Net Salary", "Status"],
            rows,
        )

    def apply_theme(self, theme):

        self.chart.set_theme(theme)

        if self.records:
            self.refresh()


# --------------------------------------------------------------
# PERFORMANCE
# --------------------------------------------------------------

class PerformancePage(BasePage):

    TITLE = "My Performance"
    SUBTITLE = "Your review scores and feedback (read-only)"
    SECTION = "performance"

    def build(self):

        self.records = []

        self.export_button = make_export_button(self, self.export_data)

        self.actions.addWidget(self.export_button)

        top = QHBoxLayout()

        top.setSpacing(14)

        # ---- summary card ----
        summary, sl = make_card("Performance Summary", "Latest review")

        head = QHBoxLayout()

        score_box = QVBoxLayout()

        score_box.setSpacing(0)

        score_box.addWidget(make_label("LATEST SCORE", "fieldLabel"))

        self.score_label = make_label("—", "bigNumber")

        score_box.addWidget(self.score_label)

        head.addLayout(score_box, 1)

        self.category_badge = Badge("", "primary")

        self.category_badge.hide()

        head.addWidget(self.category_badge, 0, Qt.AlignmentFlag.AlignTop)

        sl.addLayout(head)

        self.pct_label = make_label("Percentage: —", "muted")

        sl.addWidget(self.pct_label)

        self.progress = QProgressBar()

        self.progress.setRange(0, 100)

        self.progress.setFixedHeight(12)

        sl.addWidget(self.progress)

        self.summary_grid = InfoGrid(2)

        sl.addWidget(self.summary_grid)

        sl.addWidget(make_label("COMMENTS", "fieldLabel"))

        self.comments_label = make_label("—", "fieldValue", wrap=True)

        sl.addWidget(self.comments_label)

        self.summary_empty = EmptyState("⭐", "No performance records available.")

        sl.addWidget(self.summary_empty)

        sl.addStretch()

        top.addWidget(summary, 1)

        # ---- chart ----
        chart_card, cl = make_card("Performance Trend", "Across your reviews")

        self.chart = ChartCanvas("No performance records available.")

        cl.addWidget(self.chart)

        top.addWidget(chart_card, 1)

        self.body.addLayout(top)

        # ---- history ----
        history, hl = make_card("Performance History")

        self.table = DataTable(
            icon="⭐",
            empty_title="No performance records available.",
            empty_text="Your reviews will appear here once HR records them.",
        )

        self.table.setMinimumHeight(300)

        hl.addWidget(self.table)

        self.body.addWidget(history)

    def load(self):

        self.records = self.svc.performance_records()

        self._fill_summary()

        rows = []

        for record in self.records:

            rows.append((
                record["id"],
                [
                    fmt_date(record["date"]),
                    f"{record['score']:g}" if record["score"] is not None else "—",
                    f"{record['percentage']:g}%" if record["percentage"] is not None else "—",
                    record["category"] or "—",
                    record["comments"] or "—",
                ],
            ))

        self.table.set_rows(
            ["Review Date", "Score", "Percentage", "Category", "Comments"],
            rows,
            fit=(0, 1, 2, 3),
        )

        self.chart.show_chart(draw_performance_trend(self.records), self.theme())

    def _fill_summary(self):

        has = bool(self.records)

        for widget in (self.score_label, self.pct_label, self.progress,
                       self.summary_grid, self.comments_label):
            widget.setVisible(has)

        self.summary_empty.setVisible(not has)

        if not has:
            self.category_badge.hide()
            return

        latest = self.records[0]

        self.score_label.setText(f"{latest['score']:g}" if latest["score"] is not None else "—")

        pct = latest["percentage"]

        self.pct_label.setText(f"Percentage: {pct:g}%" if pct is not None else "Percentage: —")

        self.progress.setValue(int(max(0, min(100, pct or 0))))

        if latest["category"]:
            self.category_badge.set_kind(latest["category"], "primary")
            self.category_badge.show()
        else:
            self.category_badge.hide()

        self.summary_grid.set_items([
            ("Review Date", fmt_date(latest["date"])),
            ("Category", latest["category"]),
            ("Total Reviews", len(self.records)),
        ])

        self.comments_label.setText(latest["comments"] or "No comments.")

    def export_data(self):

        employee = self.svc.get_employee()

        rows = [
            [fmt_date(r["date"]),
             f"{r['score']:g}" if r["score"] is not None else "",
             f"{r['percentage']:g}" if r["percentage"] is not None else "",
             r["category"], r["comments"]]
            for r in self.records
        ]

        return (
            f"My_Performance_{employee['code']}",
            "My Performance Report",
            f"{employee['name']} ({employee['code']}) - generated "
            f"{datetime.now().strftime('%d %b %Y')}",
            ["Review Date", "Score", "Percentage", "Category", "Comments"],
            rows,
        )

    def apply_theme(self, theme):

        self.chart.set_theme(theme)


# --------------------------------------------------------------
# LEAVE (module not available in this project: disabled state)
# --------------------------------------------------------------

class LeavePage(BasePage):

    TITLE = "Leave Request"
    SUBTITLE = "Apply for leave and track your requests"
    SECTION = "leave"

    def build(self):

        self.enabled = self.svc.leave_supported()

        if not self.enabled:
            self.body.addWidget(InfoBanner(LEAVE_UNSUPPORTED_TEXT))

        tiles = QHBoxLayout()

        tiles.setSpacing(14)

        self.tiles = {}

        for key, icon, title, color in [
            ("balance", "🌴", "Leave Balance", "#14B8A6"),
            ("pending", "⏳", "Pending Requests", "#F59E0B"),
            ("approved", "✅", "Approved Requests", "#22C55E"),
            ("rejected", "❌", "Rejected Requests", "#EF4444"),
        ]:
            tile = StatCard(icon, title, color)

            tile.setCursor(Qt.CursorShape.ArrowCursor)

            self.tiles[key] = tile

            tiles.addWidget(tile, 1)

        self.body.addLayout(tiles)

        # ---- form ----
        form_card, fl = make_card("New Leave Request")

        form = QFormLayout()

        form.setSpacing(10)

        self.type_combo = QComboBox()

        self.type_combo.addItems(LEAVE_TYPES)

        self.start_edit = QDateEdit(QDate.currentDate())

        self.end_edit = QDateEdit(QDate.currentDate())

        for edit in (self.start_edit, self.end_edit):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("dd MMM yyyy")

        self.reason_edit = QTextEdit()

        self.reason_edit.setPlaceholderText("Reason for leave...")

        self.reason_edit.setFixedHeight(90)

        form.addRow("Leave type", self.type_combo)
        form.addRow("Start date", self.start_edit)
        form.addRow("End date", self.end_edit)
        form.addRow("Reason", self.reason_edit)

        fl.addLayout(form)

        self.form_error = make_label("", "muted", wrap=True)

        self.form_error.setStyleSheet("color: #EF4444; font-weight: 600;")

        self.form_error.hide()

        fl.addWidget(self.form_error)

        row = QHBoxLayout()

        row.addStretch()

        self.submit_button = make_button("Submit Request", "primaryButton")

        self.submit_button.clicked.connect(self.submit)

        row.addWidget(self.submit_button)

        fl.addLayout(row)

        for widget in (self.type_combo, self.start_edit, self.end_edit,
                       self.reason_edit, self.submit_button):
            widget.setEnabled(self.enabled)

        self.body.addWidget(form_card)

        # ---- requests ----
        history, hl = make_card("My Leave Requests")

        self.table = DataTable(
            icon="🌴",
            empty_title="No leave requests",
            empty_text=LEAVE_UNSUPPORTED_TEXT if not self.enabled
            else "Your submitted requests will appear here.",
        )

        self.table.setMinimumHeight(220)

        hl.addWidget(self.table)

        self.body.addWidget(history)

        self.body.addStretch()
    def load(self):

    # ----------------------------------------------------------
    # Load leave summary cards
    # ----------------------------------------------------------

        if not self.enabled:
            for tile in self.tiles.values():
                tile.set_data("N/A", "Leave module not enabled")

            self.table.set_rows(
                ["Type", "Start", "End", "Reason", "Status"],
                []
            )
            return

        summary = self.svc.leave_summary()

        self.tiles["balance"].set_data(
            summary["balance"],
            "Remaining leave days"
        )

        self.tiles["pending"].set_data(
            summary["pending"],
            "Pending requests"
        )

        self.tiles["approved"].set_data(
            summary["approved"],
            "Approved requests"
        )

        self.tiles["rejected"].set_data(
            summary["rejected"],
            "Rejected requests"
        )

        # ----------------------------------------------------------
        # Load leave request history
        # ----------------------------------------------------------

        leave_rows = self.svc.leave_requests()

        self.table.set_rows(
            ["Type", "Start", "End", "Reason", "Status"],
            [
                (
                    row["id"],
                    [
                        row["leave_type"],
                        fmt_date(row["start_date"]),
                        fmt_date(row["end_date"]),
                        row["reason"],
                        row["status"],
                    ],
                )
                for row in leave_rows
            ],
        )
    def validation_error(self):

        start = self.start_edit.date().toPython()

        end = self.end_edit.date().toPython()

        if start > end:
            return "Start date cannot be after end date."

        if not self.reason_edit.toPlainText().strip():
            return "Please enter a reason for your leave."

        return None

    def submit(self):

        if not self.enabled:
            QMessageBox.information(self, "Leave", LEAVE_UNSUPPORTED_TEXT)
            return

        message = self.validation_error()

        if message:
            self.form_error.setText(message)
            self.form_error.show()
            return

        self.form_error.hide()

        try:
            self.svc.submit_leave(
                self.type_combo.currentText(),
                self.start_edit.date().toPython(),
                self.end_edit.date().toPython(),
                self.reason_edit.toPlainText().strip(),
            )
        except LeaveUnavailableError as exc:
            QMessageBox.information(self, "Leave", str(exc))
            return
        except DataWriteError as exc:
            QMessageBox.warning(self, "Leave", str(exc))
            return

        self.reason_edit.clear()

        self.refresh()


# --------------------------------------------------------------
# NOTIFICATIONS
# --------------------------------------------------------------

class NotificationsPage(BasePage):

    TITLE = "Notifications"
    SUBTITLE = "Messages addressed to you"
    SECTION = "notifications"

    def build(self):

        self.notes = []

        self.unread_badge = Badge("0 unread", "info")

        self.actions.addWidget(self.unread_badge)

        self.mark_selected_button = make_button("Mark selected as read", "secondaryButton")

        self.mark_all_button = make_button("✔  Mark all as read", "primaryButton")

        self.refresh_button = make_button("⟳  Refresh", "secondaryButton")

        self.mark_selected_button.clicked.connect(self.mark_selected)

        self.mark_all_button.clicked.connect(self.mark_all)

        self.refresh_button.clicked.connect(self.refresh)

        for button in (self.refresh_button, self.mark_selected_button, self.mark_all_button):
            self.actions.addWidget(button)

        card, layout = make_card()

        bar = QHBoxLayout()

        bar.addWidget(make_label("Show", "muted"))

        self.filter_combo = QComboBox()

        self.filter_combo.addItems(["All", "Unread"])

        self.filter_combo.currentIndexChanged.connect(self.render)

        bar.addWidget(self.filter_combo)

        bar.addStretch()

        layout.addLayout(bar)

        self.table = DataTable(
            multi=True,
            icon="🎉",
            empty_title="You're all caught up.",
            empty_text="New notifications will show up here.",
        )

        self.table.setMinimumHeight(340)

        self.table.table.itemSelectionChanged.connect(self.show_detail)

        self.table.table.doubleClicked.connect(self.mark_current)

        layout.addWidget(self.table)

        self.body.addWidget(card)

        detail, dl = make_card("Message")

        self.detail_label = make_label("Select a notification to read it.", "muted", wrap=True)

        self.detail_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        dl.addWidget(self.detail_label)

        self.body.addWidget(detail)

    def load(self):

        self.notes = self.svc.notifications()

        self.render()

        self.win.update_bell(count=sum(1 for n in self.notes if not n["read"]))

    def render(self, *_):

        unread = sum(1 for n in self.notes if not n["read"])

        self.unread_badge.set_kind(
            f"{unread} unread" if unread else "All read",
            "danger" if unread else "success",
        )

        self.mark_all_button.setEnabled(unread > 0)

        only_unread = self.filter_combo.currentText() == "Unread"

        rows = []

        for note in self.notes:

            if only_unread and note["read"]:
                continue

            rows.append((
                note["id"],
                [
                    note["title"] or "—",
                    note["message"].replace("\n", " ")[:120],
                    note["type"],
                    fmt_datetime(note["created"]),
                    "Read" if note["read"] else "Unread",
                ],
                {
                    "bold": not note["read"],
                    "colors": {4: self.theme()["muted" if note["read"] else "primary"]},
                },
            ))

        self.table.set_empty_text(
            "You're all caught up." if not self.notes else "No unread notifications.",
            "New notifications will show up here.",
        )

        self.table.set_rows(
            ["Title", "Message", "Type", "Date", "Status"], rows, fit=(2, 3, 4)
        )

        self.detail_label.setText("Select a notification to read it.")

    def _note(self, note_id):

        return next((n for n in self.notes if n["id"] == note_id), None)

    def show_detail(self):

        ids = self.table.selected_ids()

        note = self._note(ids[0]) if ids else None

        if note:
            self.detail_label.setText(
                f"{note['title']}\n\n{note['message']}\n\n{fmt_datetime(note['created'])}"
            )

    def _mark(self, ids):

        try:
            self.svc.mark_read(ids)
        except DataWriteError as exc:
            QMessageBox.warning(self, "Notifications", str(exc))
            return

        self.win.refresh_after_notifications()

    def mark_selected(self):

        ids = [i for i in self.table.selected_ids()
               if (self._note(i) and not self._note(i)["read"])]

        if not ids:
            QMessageBox.information(self, "Notifications", "Select an unread notification first.")
            return

        self._mark(ids)

    def mark_current(self, *_):

        note = self._note(self.table.selected_id())

        if note and not note["read"]:
            self._mark([note["id"]])

    def mark_all(self):

        self._mark(None)


# --------------------------------------------------------------
# CALENDAR (view only)
# --------------------------------------------------------------

class CalendarPage(BasePage):

    TITLE = "My Calendar"
    SUBTITLE = "Company events and important dates (view only)"
    SECTION = "calendar"

    def build(self):

        self.events = []

        row = QHBoxLayout()

        row.setSpacing(14)

        cal_card, cl = make_card()

        self.calendar = QCalendarWidget()

        self.calendar.setGridVisible(False)

        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

        self.calendar.setMinimumHeight(340)

        self.calendar.selectionChanged.connect(self.show_selected_day)

        cl.addWidget(self.calendar)

        row.addWidget(cal_card, 3)

        side = QVBoxLayout()

        side.setSpacing(14)

        day_card, dl = make_card("Selected Day")

        self.day_label = make_label("", "cardSubtitle")

        dl.addWidget(self.day_label)

        self.day_list = QVBoxLayout()

        self.day_list.setSpacing(8)

        dl.addLayout(self.day_list)

        side.addWidget(day_card)

        up_card, ul = make_card("Upcoming Events")

        self.upcoming_list = QVBoxLayout()

        self.upcoming_list.setSpacing(8)

        ul.addLayout(self.upcoming_list)

        side.addWidget(up_card)

        side.addStretch()

        row.addLayout(side, 2)

        self.body.addLayout(row)

        self.body.addStretch()

    def _event_row(self, event, with_date):

        color = EVENT_TYPE_COLORS.get(event["type"].lower(), "#64748B")

        subtitle = event["type"] + (f" • {event['description']}" if event["description"] else "")

        return ListRow(event["title"], subtitle[:110],
                       fmt_date(event["date"]) if with_date else "", color)

    def load(self):

        self.events = self.svc.calendar_events()

        self.apply_theme(self.theme())

        self.show_selected_day()

        clear_layout(self.upcoming_list)

        today = date.today()

        upcoming = [e for e in self.events if e["date"] and e["date"] >= today][:8]

        if not upcoming:
            self.upcoming_list.addWidget(EmptyState("📅", "No upcoming events."))

        for event in upcoming:
            self.upcoming_list.addWidget(self._event_row(event, True))

    def apply_theme(self, theme):

        text_format = QTextCharFormat()

        text_format.setForeground(QColor(theme["text"]))

        for day in (Qt.DayOfWeek.Monday, Qt.DayOfWeek.Tuesday, Qt.DayOfWeek.Wednesday,
                    Qt.DayOfWeek.Thursday, Qt.DayOfWeek.Friday, Qt.DayOfWeek.Saturday,
                    Qt.DayOfWeek.Sunday):
            self.calendar.setWeekdayTextFormat(day, text_format)

        header_format = QTextCharFormat()

        header_format.setForeground(QColor(theme["muted"]))

        header_format.setBackground(QColor(theme["surface2"]))

        self.calendar.setHeaderTextFormat(header_format)

        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())

        marked = QTextCharFormat()

        marked.setBackground(QColor(theme["primary"]).lighter(160 if not theme["dark"] else 100))

        marked.setForeground(QColor(contrast_text(theme["primary"])))

        marked.setFontWeight(700)

        for event in self.events:

            if event["date"]:
                self.calendar.setDateTextFormat(
                    QDate(event["date"].year, event["date"].month, event["date"].day), marked
                )

    def show_selected_day(self):

        selected = self.calendar.selectedDate().toPython()

        self.day_label.setText(fmt_date(selected))

        clear_layout(self.day_list)

        todays = [e for e in self.events if e["date"] == selected]

        if not todays:
            self.day_list.addWidget(EmptyState("🗓", "No events on this day."))

        for event in todays:
            self.day_list.addWidget(self._event_row(event, False))


# --------------------------------------------------------------
# SETTINGS (personal UI preferences only)
# --------------------------------------------------------------

class SettingsPage(BasePage):

    TITLE = "Settings"
    SUBTITLE = "Personalise how your dashboard looks and behaves"
    SECTION = "settings"

    def build(self):

        appearance, al = make_card("Appearance", "Applies to your dashboard only")

        form = QFormLayout()

        form.setSpacing(12)

        self.theme_combo = QComboBox()

        self.theme_combo.addItems(self.win.bridge.names())

        self.accent_combo = QComboBox()

        self.accent_combo.addItems(list(ACCENT_COLORS))

        self.density_combo = QComboBox()

        self.density_combo.addItems(list(DENSITIES))

        self.date_combo = QComboBox()

        self.date_combo.addItems(list(DATE_FORMATS))

        form.addRow("Theme", self.theme_combo)
        form.addRow("Accent color", self.accent_combo)
        form.addRow("UI density", self.density_combo)
        form.addRow("Date format", self.date_combo)

        al.addLayout(form)

        self.body.addWidget(appearance)

        notify, nl = make_card("Notifications")

        self.badge_check = QCheckBox("Show unread count on the notification bell")

        self.notify_check = QCheckBox("Tell me when new notifications arrive")

        nl.addWidget(self.badge_check)

        nl.addWidget(self.notify_check)

        self.body.addWidget(notify)

        account, acl = make_card("My Account", "Read-only")

        self.account_grid = InfoGrid(2)

        acl.addWidget(self.account_grid)

        self.body.addWidget(account)

        row = QHBoxLayout()

        row.addStretch()

        reset = make_button("Reset to defaults", "secondaryButton")

        reset.clicked.connect(self.reset_defaults)

        save = make_button("Save Settings", "primaryButton")

        save.clicked.connect(self.save)

        row.addWidget(reset)

        row.addWidget(save)

        self.body.addLayout(row)

        self.body.addStretch()

    def _select(self, combo, text):

        index = combo.findText(text)

        combo.setCurrentIndex(index if index >= 0 else 0)

    def load(self):

        self._select(self.theme_combo, self.win.theme_name)

        self._select(self.accent_combo, PREFS.get("accent"))

        self._select(self.density_combo, PREFS.get("density"))

        self._select(self.date_combo, PREFS.get("date_format"))

        self.badge_check.setChecked(bool(PREFS.get("show_badge")))

        self.notify_check.setChecked(bool(PREFS.get("notify_new")))

        employee = self.svc.get_employee()

        self.account_grid.set_items([
            ("Username", self.svc.username),
            ("Role", self.svc.role or "Employee"),
            ("Employee ID", employee["code"]),
            ("Email", employee["email"]),
        ])

    def save(self):

        PREFS.set("accent", self.accent_combo.currentText())

        PREFS.set("density", self.density_combo.currentText())

        PREFS.set("date_format", self.date_combo.currentText())

        PREFS.set("show_badge", self.badge_check.isChecked())

        PREFS.set("notify_new", self.notify_check.isChecked())

        self.win.bridge.apply_name(self.theme_combo.currentText())

        self.win.theme_name = self.theme_combo.currentText()

        self.win.apply_theme()

        self.win.refresh_all(quiet=True)

        self.win.toast("Settings saved")

    def reset_defaults(self):

        answer = QMessageBox.question(
            self, "Reset settings", "Reset your personal settings to the defaults?"
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        PREFS.reset()

        self.win.bridge.apply_name(PREFS.get("theme"))

        self.win.theme_name = PREFS.get("theme")

        self.win.apply_theme()

        self.win.refresh_all(quiet=True)

        self.win.toast("Settings reset")


# ==============================================================
# MAIN WINDOW
# ==============================================================

class EmployeeDashboardWindow(QMainWindow):
    """Employee self-service dashboard. Shows ONLY the logged-in employee's
    own data; contains no Admin / HR functionality."""

    def __init__(self):

        super().__init__()

        self.setWindowTitle(f"{APP_TITLE} - Employee Dashboard")

        self.resize(1320, 800)

        self.setMinimumSize(1100, 700)

        self.svc = EmployeeDataService()

        self.bridge = ThemeBridge()

        self.login_window = None

        self.employee = None

        self.last_unread = None

        self.startup_error = None

        username = _user_field(_session_user(), "username", "name") or "default"

        PREFS.attach(str(username))

        self.theme_name = self.bridge.current_name()

        self.theme = self.bridge.palette(self.theme_name, PREFS.get("accent"))

        self.page_fader = Fader(self)

        self.setup_ui()

        self.setup_shortcuts()

        self.apply_theme()

        self.load_header()

        self.go_to(0)

        self.clock = QTimer(self)

        self.clock.timeout.connect(self.update_date)

        self.clock.start(30000)

        self.update_date()

        if self.startup_error:
            QTimer.singleShot(250, self.show_startup_error)

    # ==========================================================
    # UI
    # ==========================================================

    def setup_ui(self):

        root = QWidget()

        root.setObjectName("root")

        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        layout.addWidget(self.build_sidebar())

        right = QVBoxLayout()

        right.setSpacing(0)

        right.addWidget(self.build_header())

        self.stack = QStackedWidget()

        self.pages = [
            DashboardPage(self),
            ProfilePage(self),
            AttendancePage(self),
            PayrollPage(self),
            PerformancePage(self),
            LeavePage(self),
            NotificationsPage(self),
            CalendarPage(self),
            SettingsPage(self),
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        right.addWidget(self.stack, 1)

        layout.addLayout(right, 1)

        self.statusBar().setSizeGripEnabled(False)

    def build_sidebar(self):

        sidebar = QFrame()

        sidebar.setObjectName("sidebar")

        sidebar.setFixedWidth(236)

        layout = QVBoxLayout(sidebar)

        layout.setContentsMargins(14, 18, 14, 14)

        layout.setSpacing(4)

        brand = QHBoxLayout()

        icon = QLabel("E")

        icon.setObjectName("brandIcon")

        icon.setFixedSize(40, 40)

        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand.addWidget(icon)

        titles = QVBoxLayout()

        titles.setSpacing(0)

        titles.addWidget(make_label("Employee Portal", "brandTitle"))

        titles.addWidget(make_label("Self-service", "brandSub"))

        brand.addLayout(titles)

        brand.addStretch()

        layout.addLayout(brand)

        layout.addSpacing(18)

        self.nav_buttons = []

        for index, (symbol, text) in enumerate(NAV_ITEMS):

            button = QPushButton(f"{symbol}   {text}")

            button.setObjectName("navButton")

            button.setCheckable(True)

            button.setCursor(Qt.CursorShape.PointingHandCursor)

            button.clicked.connect(lambda checked=False, i=index: self.go_to(i))

            layout.addWidget(button)

            self.nav_buttons.append(button)

        layout.addStretch()

        logout = QPushButton("⎋   Logout")

        logout.setObjectName("logoutButton")

        logout.setCursor(Qt.CursorShape.PointingHandCursor)

        logout.clicked.connect(self.logout)

        layout.addWidget(logout)

        footer = make_label(f"{APP_TITLE}  v1.0", "sidebarFooter")

        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(footer)

        return sidebar

    def build_header(self):

        header = QFrame()

        header.setObjectName("header")

        header.setFixedHeight(76)

        layout = QHBoxLayout(header)

        layout.setContentsMargins(26, 8, 22, 8)

        layout.setSpacing(10)

        titles = QVBoxLayout()

        titles.setSpacing(0)

        self.title_label = make_label("Dashboard", "headerTitle")

        self.date_label = make_label("", "headerDate")

        titles.addWidget(self.title_label)

        titles.addWidget(self.date_label)

        layout.addLayout(titles)

        layout.addStretch()

        self.refresh_button = QPushButton("⟳")

        self.refresh_button.setObjectName("iconButton")

        self.refresh_button.setFixedSize(40, 40)

        self.refresh_button.setToolTip("Refresh all data (F5)")

        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.refresh_button.clicked.connect(lambda: self.refresh_all())

        self.bell_button = QPushButton("🔔")

        self.bell_button.setObjectName("iconButton")

        self.bell_button.setFixedSize(40, 40)

        self.bell_button.setToolTip("Notifications")

        self.bell_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.bell_button.clicked.connect(lambda: self.go_to(6))

        layout.addWidget(self.refresh_button)

        layout.addWidget(self.bell_button)

        layout.addSpacing(10)

        self.avatar_label = QLabel()

        self.avatar_label.setFixedSize(44, 44)

        layout.addWidget(self.avatar_label)

        who = QVBoxLayout()

        who.setSpacing(0)

        self.name_label = make_label("", "headerName")

        self.meta_label = make_label("", "headerMeta")

        who.addWidget(self.name_label)

        who.addWidget(self.meta_label)

        layout.addLayout(who)

        return header

    def setup_shortcuts(self):

        QShortcut(QKeySequence("F5"), self, activated=lambda: self.refresh_all())

        for index in range(len(NAV_ITEMS)):
            QShortcut(
                QKeySequence(f"Ctrl+{index + 1}"),
                self,
                activated=lambda i=index: self.go_to(i),
            )

    # ==========================================================
    # HEADER
    # ==========================================================

    def load_header(self):

        try:

            self.employee = self.svc.get_employee()

            employee = self.employee

            self.name_label.setText(employee["name"] or "Employee")

            self.meta_label.setText(
                f"{employee['code'] or '—'}  •  {employee['department'] or '—'}"
                f"  •  {employee['designation'] or '—'}"
            )

        except DataLoadError as exc:

            self.employee = None

            self.startup_error = self.startup_error or exc.user_message

            self.name_label.setText(self.svc.username or "Employee")

            self.meta_label.setText("Profile unavailable")

        self.refresh_avatar()

    def refresh_avatar(self):

        name = self.employee["name"] if self.employee else (self.svc.username or "?")

        photo = self.employee["photo"] if self.employee else ""

        self.avatar_label.setPixmap(make_avatar(name, 44, photo, self.theme["primary"]))

    def show_startup_error(self):

        QMessageBox.warning(self, "Employee Dashboard", self.startup_error)

        self.startup_error = None

    def update_date(self):

        self.date_label.setText(datetime.now().strftime("%A, %d %B %Y"))

    # ==========================================================
    # NAVIGATION / REFRESH
    # ==========================================================

    def go_to(self, index):

        if not 0 <= index < len(self.pages):
            return

        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

        self.stack.setCurrentIndex(index)

        self.title_label.setText(NAV_ITEMS[index][1])

        page = self.pages[index]

        page.refresh()

        self.page_fader.start(page, 180)

        self.update_bell()

    def refresh_all(self, quiet=False):
        """Reloads employee, attendance, payroll, performance, notifications
        and the dashboard statistics without recreating any window."""

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        failed = []

        try:

            self.svc.reset_identity()

            self.load_header()

            for page in self.pages:

                if not page.refresh():
                    failed.append(NAV_ITEMS[self.pages.index(page)][1])

            self.update_bell()

        finally:
            QApplication.restoreOverrideCursor()

        if failed:
            QMessageBox.warning(
                self,
                "Refresh",
                "Some information could not be loaded:\n\n• " + "\n• ".join(failed)
                + "\n\nPlease try again in a moment.",
            )
        elif not quiet:
            self.toast("Refreshed")

    def refresh_after_notifications(self):

        self.pages[6].refresh()

        self.pages[0].refresh()

        self.update_bell()

    def toast(self, message):

        self.statusBar().showMessage(message, 3500)

    # ==========================================================
    # BELL
    # ==========================================================

    def update_bell(self, count=None):

        if count is None:

            try:
                count = self.svc.unread_count()
            except DataLoadError:
                count = 0

        if count and PREFS.get("show_badge"):
            self.bell_button.setText(f"🔔 {count}")
            self.bell_button.setFixedWidth(64)
        else:
            self.bell_button.setText("🔔")
            self.bell_button.setFixedWidth(40)

        if (
            self.last_unread is not None
            and count > self.last_unread
            and PREFS.get("notify_new")
        ):
            self.toast(f"You have {count - self.last_unread} new notification(s)")

        self.last_unread = count

    # ==========================================================
    # THEME
    # ==========================================================

    def apply_theme(self):

        self.theme = self.bridge.palette(self.theme_name, PREFS.get("accent"))

        self.setStyleSheet(build_stylesheet(self.theme))

        for page in self.pages:

            try:
                page.apply_theme(self.theme)
            except Exception:
                logger.exception("Theme update failed for %s", type(page).__name__)

        if self.employee is not None or self.svc.username:
            self.refresh_avatar()

    # ==========================================================
    # LOGOUT
    # ==========================================================

    def logout(self):

        answer = QMessageBox.question(self, "Logout", "Do you want to log out?")

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            Session.logout()
        except Exception as exc:
            logger.exception("Session.logout() failed")
            QMessageBox.warning(self, "Logout failed", f"Could not clear the session:\n{exc}")
            return

        try:
            from ui.login import LoginWindow
        except ImportError as exc:
            logger.exception("Could not import ui.login.LoginWindow")
            QMessageBox.critical(self, "Logout", f"Could not open the login window:\n{exc}")
            return

        self.login_window = LoginWindow()

        self.login_window.show()

        self.close()

    def closeEvent(self, event):

        self.clock.stop()

        super().closeEvent(event)


# ==============================================================
# STANDALONE RUN (testing only; normally opened from ui/login.py)
# Run from the project root:  python -m ui.employee_dashboard
# ==============================================================

if __name__ == "__main__":

    import sys

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)

    window = EmployeeDashboardWindow()

    window.show()

    sys.exit(app.exec())
