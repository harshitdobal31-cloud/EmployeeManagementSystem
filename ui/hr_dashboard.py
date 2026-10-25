"""
ui/hr_dashboard.py

HR Dashboard for the Employee Management System (PySide6 + SQLAlchemy).

Data access
-----------
* No sqlite3, no private database file, no CREATE TABLE.
* Everything goes through the project's existing SQLAlchemy setup:
      database.database.SessionLocal  ->  data/employee_management.db
  and the existing models in database/models.py.
* HRDataService (below) is a thin adapter that converts SQLAlchemy objects
  into plain dictionaries with the keys the dashboard UI already uses
  (name, emp_code, join_date, ...), so the UI code stays unchanged.
* Activity feed  -> AuditLog
* Logged-in user -> utils.session.Session.get_user()
* Leave requests -> existing LeaveRequest model/table in database.models.
"""

import csv
import functools
import logging
import re
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from datetime import time as dtime
from string import Template

from PySide6.QtCore import (
    Qt,
    QDate,
    QPointF,
    QRectF,
    QSettings,
    QTimer,
    QTime,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
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
    QTimeEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.database import SessionLocal
from database.models import (
    Attendance,
    AuditLog,
    Department,
    Employee,
    Payroll,
    Performance,
    PerformanceLog,
    QualityIssue,
    User,
    LeaveRequest,
)
from utils.session import Session

logger = logging.getLogger(__name__)


# ==============================================================
# CONSTANTS
# ==============================================================

APP_TITLE = "Employee Management System"

ACTIVITY_COLORS = {
    "employee": "#22C55E",
    "attendance": "#3B82F6",
    "payroll": "#A855F7",
    "performance": "#F59E0B",
    "leave": "#EF4444",
    "info": "#64748B",
}

CHART_COLORS = [
    "#3B82F6",
    "#22C55E",
    "#F59E0B",
    "#A855F7",
    "#EF4444",
    "#14B8A6",
    "#EC4899",
    "#6366F1",
]

PERIOD_OPTIONS = ["This Month", "Last Month", "This Year"]

ATTENDANCE_STATUSES = ["Not marked", "Present", "Absent", "Leave"]

WORKING_DAYS_PER_MONTH = 30

# Performance.score is assumed to be on a 0..PERFORMANCE_MAX_SCORE scale.
# The dashboard UI shows ratings out of 5, so scores are scaled to /5.
# If your Performance.score is out of 100, set this to 100.0.
PERFORMANCE_MAX_SCORE = 10.0

# Payroll rows with these statuses are treated as "not paid yet".
PENDING_PAYROLL_STATUSES = {"pending", "unpaid", "draft"}

# The project has no Leave model. Keep the Leave UI, but isolated.
# To enable it later: add a Leave model/service and implement the
# "LEAVE MODULE" methods of HRDataService, then set this to True.
LEAVE_SUPPORTED = True
LEAVE_UNSUPPORTED_TEXT = "Leave module is not available."


class LeaveUnavailableError(RuntimeError):
    """Raised when a Leave operation is attempted without a Leave model."""


# ==============================================================
# DATA CONVERSION HELPERS
# ==============================================================

def to_date(value):
    """Converts date / datetime / ISO text into a date (or None)."""

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

    return None


def to_iso_date(value):

    parsed = to_date(value)

    if parsed is not None:
        return parsed.isoformat()

    return str(value) if value else ""


def to_iso_datetime(value):

    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")

    return str(value) if value else ""


def format_stamp(value):

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")

    return str(value) if value else "-"


def _py_type(attr):

    try:
        return attr.property.columns[0].type.python_type
    except (NotImplementedError, AttributeError):
        return str


def date_value(attr, day):
    """Returns `day` in the type the column stores (date/datetime/text)."""

    python_type = _py_type(attr)

    if python_type is datetime:
        return datetime.combine(day, dtime.min)

    if python_type is date:
        return day

    return day.isoformat()


def date_between(attr, start, end_exclusive):

    return and_(
        attr >= date_value(attr, start),
        attr < date_value(attr, end_exclusive),
    )


def month_bounds(month):
    """'2026-10' -> (date(2026,10,1), date(2026,11,1))"""

    year, number = int(month[:4]), int(month[5:7])

    first = date(year, number, 1)

    following = date(
        year + (1 if number == 12 else 0),
        number % 12 + 1,
        1,
    )

    return first, following


_MONTH_FORMATS = ("%Y-%m", "%B %Y", "%b %Y", "%m/%Y", "%Y-%m-%d")


def normalize_month(value, fallback_year=None):
    """Normalize payroll month values to YYYY-MM."""
    if value is None or value == "":
        return None

    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m")

    text = str(value).strip()

    for candidate in (text, text[:10], text[:7]):
        for fmt in _MONTH_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).strftime("%Y-%m")
            except ValueError:
                continue

    if fallback_year is not None:
        for fmt in ("%B", "%b"):
            try:
                parsed = datetime.strptime(text, fmt)
                return f"{fallback_year:04d}-{parsed.month:02d}"
            except ValueError:
                continue

    return None

def month_value(attr, month):
    """'YYYY-MM' in the type the payroll_month column stores."""

    python_type = _py_type(attr)

    first, _ = month_bounds(month)

    if python_type is datetime:
        return datetime.combine(first, dtime.min)

    if python_type is date:
        return first

    return month


def normalize_status(text):
    """Stored attendance status -> Present / Absent / Leave (or None)."""

    value = (text or "").strip().lower()

    if value.startswith("present") or value.startswith("late"):
        return "Present"

    if value.startswith("absent"):
        return "Absent"

    if "leave" in value:
        return "Leave"

    return None


def is_active(status):

    return (status or "").strip().lower() == "active"


def rating_from_score(score):

    return float(score or 0)


def category_for_rating(rating):

    if rating >= 9.0:
        return "Excellent"

    if rating >= 7.0:
        return "Good"

    if rating >= 5.0:
        return "Average"

    return "Needs Improvement"


def employee_to_dict(employee):
    """SQLAlchemy Employee -> the dict shape the UI expects."""

    return {
        "id": employee.id,
        "name": employee.full_name or "",
        "emp_code": employee.employee_id or "",
        "join_date": to_iso_date(employee.joining_date),
        "salary": float(employee.salary or 0),
        "department": employee.department or "",
        "designation": employee.designation or "",
        "email": employee.email or "",
        "phone": employee.phone or "",
        "status": employee.status or "Active",
    }


def activity_kind(action):

    text = (action or "").lower()

    for key in ("employee", "attendance", "payroll", "performance", "leave"):

        if key in text:
            return key

    return "info"


# ==============================================================
# SESSION HELPERS (utils.session.Session)
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

        if isinstance(user, dict):
            value = user.get(name)
        else:
            value = getattr(user, name, None)

        if value:
            return value

    return None


def get_session_info():
    """(username, role) of the logged-in user from Session.get_user()."""

    user = _session_user()

    username = _user_field(user, "username", "name", "full_name") or "User"

    role = _user_field(user, "role") or "HR Manager"

    return str(username), str(role)


def current_user_id():

    return _user_field(_session_user(), "id")


# ==============================================================
# DATABASE ACCESS (SQLAlchemy, existing SessionLocal)
# ==============================================================

@contextmanager
def session_scope():
    """Commit on success, roll back and re-raise on any error."""

    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class HRDataService:
    """
    Thin adapter between the HR dashboard UI and the existing SQLAlchemy
    models. Every method returns plain dicts / numbers so the UI never
    touches ORM objects.
    """

    # ----------------------------------------------------------
    # activity log  (AuditLog)
    # ----------------------------------------------------------

    def log(self, title, detail="", kind="info"):
        """Writes an AuditLog row. A failure here must not undo the
        operation that was just completed, so it is logged, not raised."""

        try:
            with session_scope() as session:
                session.add(
                    AuditLog(
                        user_id=current_user_id(),
                        action=title,
                        description=detail,
                    )
                )
        except SQLAlchemyError:
            logger.exception("Could not write audit log entry")

    def recent_activity(self, limit=5):

        with session_scope() as session:

            rows = (
                session.query(AuditLog)
                .order_by(AuditLog.id.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": row.id,
                    "title": row.action or "",
                    "detail": row.description or "",
                    "kind": activity_kind(row.action),
                    "created_at": to_iso_datetime(row.created_at),
                }
                for row in rows
            ]

    # ----------------------------------------------------------
    # employees
    # ----------------------------------------------------------

    def all_employees(self):

        with session_scope() as session:

            rows = session.query(Employee).order_by(Employee.id).all()

            return [employee_to_dict(row) for row in rows]

    def active_employees(self):

        with session_scope() as session:

            rows = (
                session.query(Employee)
                .filter(func.lower(Employee.status) == "active")
                .order_by(Employee.full_name)
                .all()
            )

            return [employee_to_dict(row) for row in rows]

    def get_employee(self, employee_id):

        with session_scope() as session:

            row = session.get(Employee, employee_id)

            return employee_to_dict(row) if row else None

    def search_employees(self, text="", department=None, status=None):

        with session_scope() as session:

            query = session.query(Employee)

            text = (text or "").strip()

            if text:

                like = f"%{text}%"

                query = query.filter(
                    or_(
                        Employee.full_name.ilike(like),
                        Employee.email.ilike(like),
                        Employee.department.ilike(like),
                        Employee.designation.ilike(like),
                        Employee.employee_id.ilike(like),
                    )
                )

            if department:
                query = query.filter(Employee.department == department)

            if status:
                query = query.filter(
                    func.lower(Employee.status) == status.lower()
                )

            rows = query.order_by(Employee.id.desc()).all()

            return [employee_to_dict(row) for row in rows]

    def departments(self):

        names = set()

        with session_scope() as session:

            for (name,) in session.query(Department.name).all():

                if name and name.strip():
                    names.add(name.strip())

            for (name,) in session.query(Employee.department).distinct():

                if name and name.strip():
                    names.add(name.strip())

        return sorted(names, key=str.lower)

    def department_counts(self):

        counts = {}

        for employee in self.active_employees():

            name = employee["department"].strip() or "Unassigned"

            counts[name] = counts.get(name, 0) + 1

        return [
            {"name": name, "total": total}
            for name, total in sorted(
                counts.items(),
                key=lambda pair: pair[1],
                reverse=True,
            )
        ]

    def employee_counts(self, before=None):
        """Totals now, and (if `before` is a date) as of that date."""

        total = active = total_before = active_before = 0

        for employee in self.all_employees():

            total += 1

            if is_active(employee["status"]):
                active += 1

            joined = to_date(employee["join_date"])

            if before is not None and joined is not None and joined <= before:

                total_before += 1

                if is_active(employee["status"]):
                    active_before += 1

        return {
            "total": total,
            "active": active,
            "total_before": total_before,
            "active_before": active_before,
        }

    @staticmethod
    def _next_code(session):

        best = 0
        prefix = "EMP"
        width = 3

        for (code,) in session.query(Employee.employee_id).all():

            match = re.match(r"^(\D*)(\d+)$", code or "")

            if match and int(match.group(2)) >= best:

                best = int(match.group(2))
                prefix = match.group(1) or "EMP"
                width = len(match.group(2))

        return f"{prefix}{best + 1:0{width}d}"

    def next_employee_code(self):

        with session_scope() as session:
            return self._next_code(session)

    def save_employee(self, values, employee_id=None):
        """Insert (employee_id=None) or update. Raises IntegrityError on
        duplicate email / employee code."""

        with session_scope() as session:

            if employee_id is not None:

                employee = session.get(Employee, employee_id)

                if employee is None:
                    raise LookupError("Employee no longer exists.")

            else:

                employee = Employee(employee_id=self._next_code(session))

                session.add(employee)

            joined = to_date(values["join_date"])

            employee.full_name = values["name"]
            employee.email = values["email"]
            employee.phone = values["phone"]
            employee.department = values["department"]
            employee.designation = values["designation"]
            employee.salary = values["salary"]
            employee.status = values["status"]

            if joined is not None:
                employee.joining_date = date_value(
                    Employee.joining_date,
                    joined,
                )

            department = (values["department"] or "").strip()

            if department:

                known = (
                    session.query(Department)
                    .filter(func.lower(Department.name) == department.lower())
                    .first()
                )

                if known is None:
                    session.add(Department(name=department, status="Active"))

            session.flush()

            return employee.id

    def delete_employee(self, employee_id):

        with session_scope() as session:

            for model in (Attendance, Payroll, Performance, PerformanceLog):

                session.query(model).filter(
                    model.employee_id == employee_id
                ).delete(synchronize_session=False)

            session.query(Employee).filter(
                Employee.id == employee_id
            ).delete(synchronize_session=False)

    # ----------------------------------------------------------
    # attendance
    # ----------------------------------------------------------

    @staticmethod
    def _zero_counts():

        return {"Present": 0, "Absent": 0, "Leave": 0}

    def attendance_range(self, start, end):
        """{iso_day: {'Present': n, 'Absent': n, 'Leave': n}} for active
        employees, from start to end (both inclusive, both dates)."""

        result = {}

        with session_scope() as session:

            rows = (
                session.query(Attendance)
                .join(Employee, Employee.id == Attendance.employee_id)
                .filter(func.lower(Employee.status) == "active")
                .filter(
                    date_between(
                        Attendance.attendance_date,
                        start,
                        end + timedelta(days=1),
                    )
                )
                .all()
            )

            for row in rows:

                status = normalize_status(row.status)

                if status is None:
                    continue

                key = to_iso_date(row.attendance_date)

                result.setdefault(key, self._zero_counts())[status] += 1

        return result

    def attendance_counts(self, day):

        return self.attendance_range(day, day).get(
            day.isoformat(),
            self._zero_counts(),
        )

    def attendance_for_day(self, day):
        with session_scope() as session:
            rows = session.query(Attendance).all()
            result = {}

            for row in rows:
                stored_date = to_date(row.attendance_date)
                if stored_date != day:
                    continue

                # Prefer the latest matching row when legacy duplicate dates exist.
                previous = result.get(row.employee_id)
                if previous is None or row.id > previous.get("_id", 0):
                    result[row.employee_id] = {
                        "_id": row.id,
                        "status": normalize_status(row.status),
                        "check_in": row.check_in,
                        "check_out": row.check_out,
                        "working_hours": row.working_hours,
                    }

            for values in result.values():
                values.pop("_id", None)

            return result

    @staticmethod
    def _time_minutes(value):
        if value in (None, ""):
            return None
        if isinstance(value, datetime): value = value.time()
        if isinstance(value, dtime): return value.hour * 60 + value.minute
        text = str(value).strip()
        for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M:%S", "%H:%M"):
            try:
                parsed = datetime.strptime(text, fmt).time()
                return parsed.hour * 60 + parsed.minute
            except ValueError: pass
        raise ValueError(f"Invalid time '{text}'. Use 09:00 AM or 18:00.")

    def save_attendance(self, day, marks):
        with session_scope() as session:
            all_rows = session.query(Attendance).all()
            existing = {}

            for row in all_rows:
                if to_date(row.attendance_date) == day:
                    previous = existing.get(row.employee_id)
                    if previous is None or row.id > previous.id:
                        existing[row.employee_id] = row

            for employee_id, values in marks.items():
                status = values.get("status") if isinstance(values, dict) else values
                check_in = ((values.get("check_in") or "").strip() or None) if isinstance(values, dict) else None
                check_out = ((values.get("check_out") or "").strip() or None) if isinstance(values, dict) else None
                row = existing.get(employee_id)
                if row is None:
                    if status in (None, "Not marked"): continue
                    row = Attendance(employee_id=employee_id, attendance_date=date_value(Attendance.attendance_date, day), status=status)
                    session.add(row); existing[employee_id] = row
                # HR cannot change a saved status, but can complete time fields.
                if check_in is not None:
                    self._time_minutes(check_in); row.check_in = check_in
                if check_out is not None:
                    self._time_minutes(check_out); row.check_out = check_out
                a = self._time_minutes(row.check_in); b = self._time_minutes(row.check_out)
                if a is not None and b is not None:
                    if b < a: b += 1440
                    row.working_hours = round((b-a)/60.0, 2)

    def _month_attendance(self, session, month):

        first, following = month_bounds(month)

        return (
            session.query(Attendance)
            .filter(
                date_between(Attendance.attendance_date, first, following)
            )
            .all()
        )

    def monthly_attendance_summary(self, month):

        employees = self.active_employees()

        tally = {
            employee["id"]: self._zero_counts()
            for employee in employees
        }

        with session_scope() as session:

            for row in self._month_attendance(session, month):

                status = normalize_status(row.status)

                if status is not None and row.employee_id in tally:
                    tally[row.employee_id][status] += 1

        return [
            {
                "id": employee["id"],
                "emp_code": employee["emp_code"],
                "name": employee["name"],
                "present": tally[employee["id"]]["Present"],
                "absent": tally[employee["id"]]["Absent"],
                "leave_days": tally[employee["id"]]["Leave"],
            }
            for employee in employees
        ]

    def absent_days_map(self, month):

        result = {}

        with session_scope() as session:

            for row in self._month_attendance(session, month):

                if normalize_status(row.status) == "Absent":

                    result[row.employee_id] = (
                        result.get(row.employee_id, 0) + 1
                    )

        return result

    def absent_days(self, employee_id, month):

        return self.absent_days_map(month).get(employee_id, 0)

    def employee_attendance_counts(self, employee_id, month):

        counts = self._zero_counts()

        with session_scope() as session:

            for row in self._month_attendance(session, month):

                if row.employee_id != employee_id:
                    continue

                status = normalize_status(row.status)

                if status is not None:
                    counts[status] += 1

        return counts

    # ----------------------------------------------------------
    # payroll
    # ----------------------------------------------------------

    @staticmethod
    def _payroll_dict(row):

        status = row.status or ""

        return {
            "id": row.id,
            "employee_id": row.employee_id,
            "month": (
                normalize_month(
                    row.payroll_month,
                    fallback_year=(
                        row.created_at.year
                        if row.created_at is not None
                        else None
                    ),
                )
                or to_iso_date(row.payroll_month)
            ),
            "amount": float(row.net_salary or 0),
            "basic_salary": float(row.basic_salary or 0),
            "allowances": float(row.allowances or 0),
            "deductions": float(row.deductions or 0),
            "status": status,
            "paid": status.strip().lower() not in PENDING_PAYROLL_STATUSES,
            "processed_on": format_stamp(row.created_at),
        }

    def _payroll_all(self):

        with session_scope() as session:

            return [
                self._payroll_dict(row)
                for row in session.query(Payroll).all()
            ]

    def payroll_total(self, prefix):

        return sum(
            record["amount"]
            for record in self._payroll_all()
            if record["month"].startswith(prefix)
        )

    def payroll_map(self, month):
        """Choose the best existing record for each employee in a month."""
        priority = {"locked": 3, "paid": 2, "processed": 1}
        records = [
            record for record in self._payroll_all()
            if record["month"] == month
        ]
        records.sort(
            key=lambda record: (
                priority.get((record.get("status") or "").strip().lower(), 0),
                record.get("id") or 0,
            )
        )

        result = {}
        for record in records:
            result[record["employee_id"]] = record
        return result

    def payroll_record(self, employee_id, month):

        return self.payroll_map(month).get(employee_id)

    def payroll_history(self, employee_id, limit=6):

        records = [
            record
            for record in self._payroll_all()
            if record["employee_id"] == employee_id
        ]

        records.sort(key=lambda record: record["month"], reverse=True)

        return records[:limit]

    def payroll_by_month(self, limit=6):

        groups = {}

        for record in self._payroll_all():

            group = groups.setdefault(
                record["month"],
                {"people": set(), "total": 0.0},
            )

            group["people"].add(record["employee_id"])

            group["total"] += record["amount"]

        months = sorted(groups, reverse=True)[:limit]

        return [
            {
                "month": month,
                "people": len(groups[month]["people"]),
                "total": groups[month]["total"],
            }
            for month in months
        ]

    def save_payroll_components(
        self, employee_id, month, basic_salary, allowances, deductions
    ):
        """Save editable payroll components without marking payroll as paid."""
        basic_salary = max(0.0, float(basic_salary or 0))
        allowances = max(0.0, float(allowances or 0))
        deductions = max(0.0, float(deductions or 0))
        net_salary = max(0.0, round(basic_salary + allowances - deductions, 2))

        with session_scope() as session:
            record = None
            for row in session.query(Payroll).filter(
                Payroll.employee_id == employee_id
            ).all():
                if normalize_month(row.payroll_month) == month:
                    record = row
                    break

            if record is None:
                record = Payroll(
                    employee_id=employee_id,
                    payroll_month=month_value(Payroll.payroll_month, month),
                    status="Pending",
                )
                session.add(record)

            was_paid = (record.status or "").strip().lower() not in PENDING_PAYROLL_STATUSES
            record.basic_salary = basic_salary
            record.allowances = allowances
            record.deductions = deductions
            record.net_salary = net_salary
            # Editing a processed payroll keeps its existing payment status.
            if not was_paid:
                record.status = "Pending"

        return net_salary

    def process_payroll(self, items, month):
        """Create or update pending payroll; preserve completed and locked records."""
        with session_scope() as session:
            existing = {}

            rows = session.query(Payroll).order_by(Payroll.id.desc()).all()
            for row in rows:
                row_month = normalize_month(
                    row.payroll_month,
                    fallback_year=(
                        row.created_at.year
                        if row.created_at is not None
                        else None
                    ),
                )
                if row_month != month:
                    continue

                current = existing.get(row.employee_id)
                if current is None:
                    existing[row.employee_id] = row
                elif (current.status or "").strip().lower() != "locked":
                    if (row.status or "").strip().lower() == "locked":
                        existing[row.employee_id] = row

            for item in items:
                record = existing.get(item["id"])

                if record is not None:
                    status = (record.status or "").strip().lower()
                    if status not in PENDING_PAYROLL_STATUSES:
                        continue
                else:
                    record = Payroll(
                        employee_id=item["id"],
                        payroll_month=month_value(Payroll.payroll_month, month),
                        allowances=0,
                    )
                    session.add(record)
                    existing[item["id"]] = record

                record.basic_salary = item["salary"]
                record.deductions = item["deduction"]
                record.net_salary = item["net"]
                record.status = "Paid"

    def delete_payroll(self, employee_id, month):

        with session_scope() as session:

            for row in (
                session.query(Payroll)
                .filter(Payroll.employee_id == employee_id)
                .all()
            ):

                if normalize_month(row.payroll_month) == month:
                    session.delete(row)

    # ----------------------------------------------------------
    # performance
    # ----------------------------------------------------------

    def _review_rows(self):

        with session_scope() as session:

            rows = (
                session.query(Performance, Employee)
                .join(Employee, Employee.id == Performance.employee_id)
                .order_by(Performance.id.desc())
                .all()
            )

            return [
                {
                    "id": review.id,
                    "employee_id": employee.id,
                    "name": employee.full_name or "",
                    "department": employee.department or "",
                    "designation": employee.designation or "",
                    "rating": rating_from_score(review.score),
                    "remarks": review.comments or "",
                    "review_date": to_iso_date(review.review_date),
                }
                for review, employee in rows
            ]

    def average_rating(self, prefix=None):

        ratings = [
            row["rating"]
            for row in self._review_rows()
            if prefix is None or row["review_date"].startswith(prefix)
        ]

        if not ratings:
            return None

        return sum(ratings) / len(ratings)

    def top_performers(self, limit=5):

        groups = {}

        for row in self._review_rows():

            group = groups.setdefault(
                row["employee_id"],
                {
                    "name": row["name"],
                    "designation": row["designation"],
                    "total": 0.0,
                    "reviews": 0,
                },
            )

            group["total"] += row["rating"]
            group["reviews"] += 1

        ranked = [
            {
                "name": group["name"],
                "designation": group["designation"],
                "rating": group["total"] / group["reviews"],
                "reviews": group["reviews"],
            }
            for group in groups.values()
        ]

        ranked.sort(
            key=lambda item: (item["rating"], item["reviews"]),
            reverse=True,
        )

        return ranked[:limit]

    def reviews(self, employee_id=None):

        rows = self._review_rows()

        if employee_id is not None:
            rows = [row for row in rows if row["employee_id"] == employee_id]

        return rows

    def employee_reviews(self, employee_id, limit=6):

        return self.reviews(employee_id)[:limit]

    def add_review(self, employee_id, rating, remarks):

        if employee_id is None:
            raise ValueError("A valid employee must be selected before saving a performance review.")

        with session_scope() as session:

            employee = session.get(Employee, int(employee_id))
            if employee is None:
                raise LookupError("The selected employee was not found. Refresh the employee list and try again.")

            session.add(
                Performance(
                    employee_id=employee_id,
                    review_date=date_value(
                        Performance.review_date,
                        date.today(),
                    ),
                    score=rating,
                    percentage=rating / 10 * 100,
                    category=category_for_rating(rating),
                    comments=remarks,
                )
            )

    def delete_review(self, review_id):

        with session_scope() as session:

            session.query(Performance).filter(
                Performance.id == review_id
            ).delete(synchronize_session=False)

    # ----------------------------------------------------------
    # LEAVE MODULE
    # ----------------------------------------------------------

    def leave_supported(self):

        return LEAVE_SUPPORTED

    @staticmethod
    def _leave_dict(row, employee_name=""):
        return {
            "id": row.id,
            "employee_id": row.employee_id,
            "name": employee_name or "Unknown",
            "leave_type": row.leave_type or "",
            "start_date": to_iso_date(row.start_date),
            "end_date": to_iso_date(row.end_date),
            "reason": row.reason or "",
            "status": row.status or "Pending",
            "created_at": to_iso_datetime(row.created_at),
        }

    def pending_leaves(self):
        """All pending employee leave requests for HR approval."""

        with session_scope() as session:
            rows = (
                session.query(LeaveRequest, Employee.full_name)
                .join(Employee, Employee.id == LeaveRequest.employee_id)
                .filter(func.lower(LeaveRequest.status) == "pending")
                .order_by(LeaveRequest.created_at.asc(), LeaveRequest.id.asc())
                .all()
            )
            return [self._leave_dict(row, name) for row, name in rows]

    def pending_leave_count(self):
        with session_scope() as session:
            return int(
                session.query(func.count(LeaveRequest.id))
                .filter(func.lower(LeaveRequest.status) == "pending")
                .scalar()
                or 0
            )

    def leave_ranges(self):
        """Leave ranges used by the calendar page."""

        with session_scope() as session:
            rows = (
                session.query(LeaveRequest)
                .filter(
                    func.lower(LeaveRequest.status).in_(["pending", "approved"])
                )
                .order_by(LeaveRequest.start_date.asc())
                .all()
            )
            return [
                {
                    "start_date": to_iso_date(row.start_date),
                    "end_date": to_iso_date(row.end_date),
                    "status": row.status or "Pending",
                }
                for row in rows
            ]

    def leave_rows(self, selected_day, show_all):
        """Leave requests for the selected day, or all requests."""

        with session_scope() as session:
            query = (
                session.query(LeaveRequest, Employee.full_name)
                .join(Employee, Employee.id == LeaveRequest.employee_id)
                .order_by(LeaveRequest.created_at.desc(), LeaveRequest.id.desc())
            )

            rows = query.all()

            result = []
            selected = to_date(selected_day)
            for row, name in rows:
                item = self._leave_dict(row, name)
                if show_all:
                    result.append(item)
                    continue
                start = to_date(row.start_date)
                end = to_date(row.end_date)
                if selected is not None and start is not None and end is not None and start <= selected <= end:
                    result.append(item)
            return result

    def create_leave(self, employee_id, start_text, end_text, reason):
        start = to_date(start_text)
        end = to_date(end_text)
        if start is None or end is None:
            raise ValueError("Please enter valid leave dates.")
        if end < start:
            raise ValueError("End date cannot be before start date.")

        reason = (reason or "").strip()
        if not reason:
            raise ValueError("Leave reason is required.")

        with session_scope() as session:
            employee = session.get(Employee, employee_id)
            if employee is None:
                raise LookupError("Employee not found.")

            # HR-created leave is stored as Pending and follows the same
            # approval workflow as employee-submitted leave.
            overlap = (
                session.query(LeaveRequest)
                .filter(
                    LeaveRequest.employee_id == employee_id,
                    func.lower(LeaveRequest.status).in_(["pending", "approved"]),
                    LeaveRequest.start_date <= end.isoformat(),
                    LeaveRequest.end_date >= start.isoformat(),
                )
                .first()
            )
            if overlap is not None:
                raise ValueError("This employee already has an overlapping leave request.")

            request = LeaveRequest(
                employee_id=employee_id,
                leave_type="Casual Leave",
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                reason=reason,
                status="Pending",
            )
            session.add(request)
            session.flush()
            return request.id

    def update_leave_status(self, leave_id, status):
        if status not in {"Approved", "Rejected"}:
            raise ValueError("Invalid leave status.")

        with session_scope() as session:
            row = session.get(LeaveRequest, leave_id)
            if row is None:
                raise LookupError("Leave request not found.")

            if (row.status or "").strip().lower() != "pending":
                raise ValueError(f"This leave request is already {row.status}.")

            row.status = status
            try:
                row.reviewed_at = datetime.utcnow()
                row.reviewed_by = current_user_id()
            except Exception:
                pass

            session.flush()

            # Audit trail for TQM/accountability.
            try:
                session.add(
                    AuditLog(
                        user_id=current_user_id(),
                        action=f"Leave {status}",
                        description=f"Leave request #{leave_id} was {status.lower()} by HR/Admin.",
                    )
                )
            except Exception:
                logger.exception("Could not write leave audit log")

    # ----------------------------------------------------------
    # report exports
    # ----------------------------------------------------------

    def export_rows(self, name):
        """Returns (headers, rows) for the Reports page."""

        if name == "Employees":

            return (
                [
                    "Code",
                    "Name",
                    "Email",
                    "Phone",
                    "Department",
                    "Designation",
                    "Salary",
                    "Join Date",
                    "Status",
                ],
                [
                    (
                        e["emp_code"],
                        e["name"],
                        e["email"],
                        e["phone"],
                        e["department"],
                        e["designation"],
                        e["salary"],
                        e["join_date"],
                        e["status"],
                    )
                    for e in self.all_employees()
                ],
            )

        if name == "Attendance":

            with session_scope() as session:

                rows = (
                    session.query(Attendance, Employee)
                    .join(Employee, Employee.id == Attendance.employee_id)
                    .all()
                )

                data = [
                    (
                        employee.full_name,
                        to_iso_date(record.attendance_date),
                        record.status,
                    )
                    for record, employee in rows
                ]

            data.sort(key=lambda item: item[1], reverse=True)

            return ["Employee", "Date", "Status"], data

        if name == "Payroll":

            names = {e["id"]: e["name"] for e in self.all_employees()}

            data = [
                (
                    names.get(record["employee_id"], ""),
                    record["month"],
                    record["amount"],
                    record["processed_on"],
                )
                for record in self._payroll_all()
            ]

            data.sort(key=lambda item: item[1], reverse=True)

            return ["Employee", "Month", "Amount", "Processed On"], data

        if name == "Performance":

            return (
                ["Employee", "Rating", "Remarks", "Date"],
                [
                    (
                        row["name"],
                        row["rating"],
                        row["remarks"],
                        row["review_date"],
                    )
                    for row in self._review_rows()
                ],
            )

        if name == "Leaves":

            return ["Employee", "From", "To", "Reason", "Status"], []

        raise KeyError(name)


# ==============================================================
# HELPER FUNCTIONS
# ==============================================================

def format_inr(value):

    number = str(int(round(value or 0)))

    if len(number) <= 3:
        return "₹ " + number

    head = number[:-3]
    tail = number[-3:]

    groups = []

    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]

    if head:
        groups.insert(0, head)

    return "₹ " + ",".join(groups) + "," + tail


def delta_text(current, previous):
    """Returns (text, is_positive) or (None, None) if no previous data."""

    if not previous:
        return None, None

    change = (current - previous) / previous * 100

    arrow = "↑" if change >= 0 else "↓"

    return f"{arrow} {abs(change):.0f}%", change >= 0


def time_ago(iso_text):

    try:
        difference = datetime.now() - datetime.fromisoformat(iso_text)
    except (TypeError, ValueError):
        return ""

    seconds = max(0, int(difference.total_seconds()))

    if seconds < 60:
        return "just now"

    if seconds < 3600:
        return f"{seconds // 60} min ago"

    if seconds < 86400:
        return f"{seconds // 3600} hours ago"

    days = seconds // 86400

    if days == 1:
        return "1 day ago"

    return f"{days} days ago"


def month_key(day):

    return day.strftime("%Y-%m")


def previous_month(day):

    first = day.replace(day=1)

    return first - timedelta(days=1)


def period_prefixes(label):
    """Returns (current_prefix, previous_prefix, comparison_note)."""

    today = date.today()

    if label == "Last Month":

        last = previous_month(today)

        before = previous_month(last)

        return month_key(last), month_key(before), "vs previous month"

    if label == "This Year":

        return str(today.year), str(today.year - 1), "vs last year"

    return (
        month_key(today),
        month_key(previous_month(today)),
        "vs last month",
    )


def calculate_net_salary(salary, absent_days):

    salary = salary or 0

    per_day = salary / WORKING_DAYS_PER_MONTH

    deduction = round(per_day * absent_days, 2)

    deduction = min(deduction, salary)

    return deduction, round(salary - deduction, 2)


def fill_table(table, headers, rows):
    """rows = list of (row_id, [cell, cell, ...])"""

    table.clear()

    table.setColumnCount(len(headers))

    table.setHorizontalHeaderLabels(headers)

    table.setRowCount(len(rows))

    for row_index, (row_id, cells) in enumerate(rows):

        for column, value in enumerate(cells):

            item = QTableWidgetItem("" if value is None else str(value))

            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            if column == 0:
                item.setData(Qt.ItemDataRole.UserRole, row_id)

            table.setItem(row_index, column, item)


def make_table():

    table = QTableWidget()

    table.setSelectionBehavior(
        QAbstractItemView.SelectionBehavior.SelectRows
    )

    table.setSelectionMode(
        QAbstractItemView.SelectionMode.SingleSelection
    )

    table.setAlternatingRowColors(True)

    table.verticalHeader().setVisible(False)

    table.verticalHeader().setDefaultSectionSize(40)

    table.horizontalHeader().setStretchLastSection(True)

    table.horizontalHeader().setSectionResizeMode(
        QHeaderView.ResizeMode.Stretch
    )

    table.setShowGrid(False)

    table.setFrameShape(QFrame.Shape.NoFrame)

    return table


def selected_id(table):

    row = table.currentRow()

    if row < 0:
        return None

    item = table.item(row, 0)

    if item is None:
        return None

    return item.data(Qt.ItemDataRole.UserRole)


def make_button(text, object_name="primaryButton"):

    button = QPushButton(text)

    button.setObjectName(object_name)

    button.setCursor(Qt.CursorShape.PointingHandCursor)

    button.setMinimumHeight(38)

    return button


def make_label(text, object_name):

    label = QLabel(text)

    label.setObjectName(object_name)

    return label


def page_header(title, subtitle):

    box = QVBoxLayout()

    box.setSpacing(2)

    box.addWidget(make_label(title, "pageTitle"))

    box.addWidget(make_label(subtitle, "pageSubtitle"))

    return box


def export_rows_to_csv(parent, suggested_name, headers, rows):
    """Asks for a file path and writes the rows. Returns True on success."""

    if not rows:

        QMessageBox.information(
            parent,
            "Nothing to export",
            "There is no data to export yet.",
        )

        return False

    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Save CSV",
        f"{suggested_name}_{date.today().isoformat()}.csv",
        "CSV files (*.csv)",
    )

    if not path:
        return False

    try:

        with open(path, "w", newline="", encoding="utf-8-sig") as handle:

            writer = csv.writer(handle)

            writer.writerow(headers)

            for row in rows:
                writer.writerow(list(row))

    except OSError as exc:

        QMessageBox.critical(
            parent,
            "Export failed",
            f"Could not write the file:\n{exc}",
        )

        return False

    QMessageBox.information(
        parent,
        "Exported",
        f"{len(rows)} rows saved to:\n{path}",
    )

    return True


def show_db_error(parent, exc):

    logger.error("Database operation failed", exc_info=exc)

    QMessageBox.critical(
        parent,
        "Database error",
        f"The database operation failed:\n\n{exc}",
    )


def safe_action(method):
    """Wraps a button/slot method so database errors show a message box
    instead of crashing the window."""

    allowed = method.__code__.co_argcount - 1

    @functools.wraps(method)
    def wrapper(self, *args):

        try:
            return method(self, *args[:allowed])
        except LeaveUnavailableError as exc:
            QMessageBox.information(self, "Leave module", str(exc))
        except SQLAlchemyError as exc:
            show_db_error(self, exc)

    return wrapper


def clear_layout(layout):
    """Removes (and deletes) every widget inside a layout."""

    while layout.count():

        item = layout.takeAt(0)

        widget = item.widget()

        if widget is not None:
            widget.deleteLater()

        elif item.layout() is not None:
            clear_layout(item.layout())


# ==============================================================
# THEMES  (window-scoped stylesheet; does not touch app-wide theme)
# ==============================================================

LIGHT_THEME = {
    "bg": "#F1F5F9",
    "side": "#FFFFFF",
    "card": "#FFFFFF",
    "border": "#E2E8F0",
    "text": "#0F172A",
    "muted": "#64748B",
    "hover": "#F1F5F9",
    "accentSoft": "#DBEAFE",
    "input": "#FFFFFF",
    "banner": (
        "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #EFF6FF, stop:1 #DBEAFE)"
    ),
}

DARK_THEME = {
    "bg": "#0F172A",
    "side": "#020617",
    "card": "#1E293B",
    "border": "#334155",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "hover": "#273449",
    "accentSoft": "#1E3A8A",
    "input": "#0F172A",
    "banner": (
        "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #1E293B, stop:1 #1E3A8A)"
    ),
}

STYLE_TEMPLATE = Template(
    """
    QMainWindow, #root {
        background: $bg;
    }

    QWidget {
        color: $text;
        font-family: 'Segoe UI', Arial;
        font-size: 13px;
    }

    QScrollArea,
    QScrollArea > QWidget > QWidget {
        background: transparent;
    }

    QToolTip {
        background: $card;
        color: $text;
        border: 1px solid $border;
        padding: 4px;
    }

    QStatusBar {
        background: $bg;
        color: $muted;
    }

    /* ---------------- sidebar ---------------- */

    #sidebar {
        background: $side;
        border-right: 1px solid $border;
    }

    #brandLogo {
        background: #2563EB;
        color: white;
        border-radius: 12px;
        font-weight: 800;
        font-size: 14px;
    }

    #brandName {
        font-weight: 700;
        font-size: 14px;
    }

    #userBox {
        background: $card;
        border: 1px solid $border;
        border-radius: 12px;
    }

    #avatar {
        background: $accentSoft;
        color: #2563EB;
        border-radius: 22px;
        font-weight: 800;
        font-size: 16px;
    }

    #userName {
        font-weight: 700;
    }

    #userRole {
        color: $muted;
        font-size: 11px;
    }

    #online {
        color: #22C55E;
        font-size: 11px;
    }

    #navButton {
        text-align: left;
        padding: 11px 16px;
        border: none;
        border-radius: 10px;
        background: transparent;
        color: $muted;
        font-size: 13px;
        font-weight: 600;
    }

    #navButton:hover {
        background: $hover;
    }

    #navButton:checked {
        background: $accentSoft;
        color: #2563EB;
    }

    #logoutButton {
        text-align: left;
        padding: 10px 16px;
        border: none;
        background: transparent;
        color: #EF4444;
        font-weight: 600;
    }

    #logoutButton:hover {
        background: $hover;
        border-radius: 10px;
    }

    /* ---------------- top bar ---------------- */

    #topbar {
        background: $bg;
    }

    #searchBox {
        background: $card;
        border: 1px solid $border;
        border-radius: 12px;
        padding: 10px 14px;
    }

    #iconButton {
        background: $card;
        border: 1px solid $border;
        border-radius: 19px;
        font-size: 15px;
    }

    #iconButton:hover {
        background: $hover;
    }

    #dateLabel {
        font-weight: 600;
    }

    #timeLabel {
        color: $muted;
        font-size: 11px;
    }

    /* ---------------- dashboard ---------------- */

    #banner {
        background: $banner;
        border: 1px solid $border;
        border-radius: 16px;
    }

    #welcomeSmall {
        color: #3B82F6;
        font-weight: 800;
        font-size: 11px;
        letter-spacing: 2px;
    }

    #greeting {
        font-size: 28px;
        font-weight: 800;
    }

    #roleBadge {
        background: #3B82F6;
        color: white;
        border-radius: 14px;
        font-weight: 800;
        font-size: 16px;
    }

    #sectionTitle {
        font-size: 15px;
        font-weight: 700;
    }

    #pageTitle {
        font-size: 24px;
        font-weight: 800;
    }

    #pageSubtitle {
        color: $muted;
        font-size: 12px;
    }

    #statCard,
    #panel {
        background: $card;
        border: 1px solid $border;
        border-radius: 14px;
    }

    #statTitle {
        color: $muted;
        font-size: 12px;
        font-weight: 600;
    }

    #statValue {
        font-size: 24px;
        font-weight: 800;
    }

    #statDelta {
        font-size: 11px;
        font-weight: 700;
    }

    #statNote {
        color: $muted;
        font-size: 10px;
    }

    #actTitle {
        font-weight: 600;
        font-size: 12px;
    }

    #fieldLabel {
        font-weight: 700;
        font-size: 13px;
    }

    #chip {
        background: $card;
        border: 1px solid $border;
        border-radius: 10px;
        padding: 8px 14px;
        font-weight: 700;
    }

    #summaryBox {
        background: $card;
        border: 1px solid $border;
        border-radius: 12px;
        padding: 16px;
        font-size: 14px;
    }

    #emptyLabel {
        color: $muted;
        font-size: 12px;
        padding: 10px 0;
    }

    /* ---------------- buttons ---------------- */

    #linkButton {
        background: transparent;
        border: none;
        color: #3B82F6;
        font-weight: 700;
    }

    #quickButton {
        text-align: left;
        padding: 12px 14px;
        background: transparent;
        border: none;
        border-bottom: 1px solid $border;
        font-weight: 600;
    }

    #quickButton:hover {
        background: $hover;
        border-radius: 8px;
    }

    #primaryButton {
        background: #2563EB;
        color: white;
        border: none;
        border-radius: 9px;
        padding: 0 18px;
        font-weight: 700;
    }

    #primaryButton:hover {
        background: #1D4ED8;
    }

    #secondaryButton {
        background: $card;
        border: 1px solid $border;
        border-radius: 9px;
        padding: 0 18px;
        font-weight: 600;
    }

    #secondaryButton:hover {
        background: $hover;
    }

    #dangerButton {
        background: #EF4444;
        color: white;
        border: none;
        border-radius: 9px;
        padding: 0 18px;
        font-weight: 700;
    }

    #dangerButton:hover {
        background: #DC2626;
    }

    #successButton {
        background: #16A34A;
        color: white;
        border: none;
        border-radius: 9px;
        padding: 0 18px;
        font-weight: 700;
    }

    #successButton:hover {
        background: #15803D;
    }

    /* ---------------- inputs ---------------- */

    QLineEdit,
    QDateEdit,
    QTimeEdit,
    QComboBox,
    QDoubleSpinBox,
    QTextEdit {
        background: $input;
        border: 1px solid $border;
        border-radius: 8px;
        padding: 7px 10px;
        color: $text;
    }

    QLineEdit:focus,
    QDateEdit:focus,
    QComboBox:focus,
    QDoubleSpinBox:focus,
    QTextEdit:focus {
        border: 1px solid #3B82F6;
    }

    QComboBox QAbstractItemView {
        background: $card;
        color: $text;
        selection-background-color: $accentSoft;
        selection-color: $text;
        border: 1px solid $border;
    }

    #searchBox {
        background: $card;
    }

    /* ---------------- tables ---------------- */

    QTableWidget {
        background: $card;
        border: 1px solid $border;
        border-radius: 12px;
        alternate-background-color: $hover;
    }

    QTableWidget::item {
        padding: 6px;
    }

    QTableWidget::item:selected {
        background: $accentSoft;
        color: $text;
    }

    QHeaderView::section {
        background: $hover;
        color: $muted;
        border: none;
        padding: 9px;
        font-weight: 700;
    }

    /* ---------------- tabs / progress ---------------- */

    QTabWidget::pane {
        border: none;
        top: 8px;
    }

    QTabBar::tab {
        background: transparent;
        color: $muted;
        padding: 9px 18px;
        font-weight: 700;
        border-bottom: 2px solid transparent;
    }

    QTabBar::tab:selected {
        color: #2563EB;
        border-bottom: 2px solid #2563EB;
    }

    QProgressBar {
        background: $hover;
        border: none;
        border-radius: 5px;
        height: 10px;
        text-align: center;
        color: transparent;
    }

    QProgressBar::chunk {
        background: #3B82F6;
        border-radius: 5px;
    }

    /* ---------------- calendar / dialogs ---------------- */

    QCalendarWidget QWidget {
        background: $card;
        color: $text;
    }

    QCalendarWidget QAbstractItemView {
        selection-background-color: #2563EB;
        selection-color: white;
    }

    QDialog,
    QMessageBox {
        background: $card;
    }

    QCheckBox {
        spacing: 8px;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 10px;
    }

    QScrollBar::handle:vertical {
        background: $border;
        border-radius: 5px;
        min-height: 30px;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
    }
    """
)


# ==============================================================
# CUSTOM WIDGETS
# ==============================================================

class IconBox(QLabel):
    """Small rounded colored square with an emoji / symbol inside."""

    def __init__(self, symbol, background, size=38):

        super().__init__(symbol)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setFixedSize(size, size)

        self.setStyleSheet(
            f"background: {background}; "
            "border-radius: 10px; "
            "font-size: 17px; "
            "color: white;"
        )


class StatCard(QFrame):
    """One KPI card: icon, title, value, change versus previous period."""

    def __init__(self, title, symbol, accent):

        super().__init__()

        self.setObjectName("statCard")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(16, 14, 16, 14)

        layout.setSpacing(3)

        layout.addWidget(
            IconBox(symbol, accent),
            0,
            Qt.AlignmentFlag.AlignLeft,
        )

        layout.addSpacing(6)

        self.title_label = make_label(title, "statTitle")
        self.value_label = make_label("0", "statValue")
        self.delta_label = make_label("", "statDelta")
        self.note_label = make_label("", "statNote")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.delta_label)
        layout.addWidget(self.note_label)

    def set_data(self, value, current=None, previous=None,
                 note="vs last month"):

        self.value_label.setText(str(value))

        if current is None:
            text, positive = None, None
        else:
            text, positive = delta_text(current, previous)

        if text is None:

            self.delta_label.setText("— no previous data")

            self.delta_label.setStyleSheet("color: #94A3B8;")

            self.note_label.setText("")

            return

        self.delta_label.setText(text)

        self.delta_label.setStyleSheet(
            "color: #16A34A;" if positive else "color: #DC2626;"
        )

        self.note_label.setText(note)


class AttendanceChart(QWidget):
    """Grouped bar chart (present vs absent) drawn with QPainter."""

    def __init__(self):

        super().__init__()

        self.setMinimumHeight(240)

        self.labels = []
        self.present = []
        self.absent = []
        self.dark = False

    def set_data(self, labels, present, absent, dark):

        self.labels = labels
        self.present = present
        self.absent = absent
        self.dark = dark

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        text_color = QColor("#94A3B8" if self.dark else "#64748B")

        grid_color = QColor("#334155" if self.dark else "#E2E8F0")

        width = self.width()
        height = self.height()

        left = 36
        right = 8
        top = 28
        bottom = 44

        chart_width = width - left - right
        chart_height = height - top - bottom

        # ---------------- legend ----------------

        painter.setFont(QFont("Segoe UI", 8))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3B82F6"))
        painter.drawEllipse(width - 140, 8, 8, 8)

        painter.setPen(text_color)
        painter.drawText(width - 128, 16, "Present")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#22C55E"))
        painter.drawEllipse(width - 70, 8, 8, 8)

        painter.setPen(text_color)
        painter.drawText(width - 58, 16, "Absent")

        # ---------------- empty state ----------------

        highest = max(self.present + self.absent + [0])

        if highest == 0:

            painter.setFont(QFont("Segoe UI", 10))

            painter.drawText(
                QRectF(0, 0, width, height),
                Qt.AlignmentFlag.AlignCenter,
                "No attendance data yet",
            )

            return

        step = max(1, -(-highest // 5))

        top_value = step * 5

        # ---------------- grid ----------------

        painter.setFont(QFont("Segoe UI", 8))

        for index in range(6):

            value = step * index

            y = top + chart_height - (value / top_value) * chart_height

            painter.setPen(QPen(grid_color, 1))

            painter.drawLine(left, int(y), width - right, int(y))

            painter.setPen(text_color)

            painter.drawText(
                0,
                int(y) - 8,
                left - 6,
                16,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(value),
            )

        # ---------------- bars ----------------

        count = len(self.labels)

        slot = chart_width / max(count, 1)

        bar_width = min(22, slot / 3)

        series = (
            (self.present, "#3B82F6"),
            (self.absent, "#22C55E"),
        )

        for index in range(count):

            center = left + slot * index + slot / 2

            for offset, (values, color) in enumerate(series):

                bar_height = (values[index] / top_value) * chart_height

                x = center - bar_width + offset * bar_width

                painter.setPen(Qt.PenStyle.NoPen)

                painter.setBrush(QColor(color))

                painter.drawRoundedRect(
                    QRectF(
                        x,
                        top + chart_height - bar_height,
                        bar_width - 2,
                        bar_height,
                    ),
                    3,
                    3,
                )

            painter.setPen(text_color)

            painter.drawText(
                QRectF(
                    center - slot / 2,
                    top + chart_height + 4,
                    slot,
                    36,
                ),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self.labels[index],
            )


class DonutChart(QWidget):
    """Department distribution donut with a legend."""

    def __init__(self):

        super().__init__()

        self.setMinimumHeight(190)

        self.items = []
        self.dark = False

    def set_data(self, items, dark):
        """items = list of (label, value)"""

        self.items = items
        self.dark = dark

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        text_color = QColor("#CBD5E1" if self.dark else "#334155")

        muted_color = QColor("#94A3B8" if self.dark else "#64748B")

        total = sum(value for _, value in self.items)

        if total == 0:

            painter.setPen(muted_color)

            painter.setFont(QFont("Segoe UI", 10))

            painter.drawText(
                QRectF(0, 0, self.width(), self.height()),
                Qt.AlignmentFlag.AlignCenter,
                "No employees yet",
            )

            return

        diameter = min(self.height() - 30, self.width() * 0.45)

        ring = 22

        rect = QRectF(
            14 + ring / 2,
            (self.height() - diameter) / 2 + ring / 2,
            diameter - ring,
            diameter - ring,
        )

        start_angle = 90 * 16

        for index, (label, value) in enumerate(self.items):

            span = -int(value / total * 360 * 16)

            pen = QPen(QColor(CHART_COLORS[index % len(CHART_COLORS)]), ring)

            pen.setCapStyle(Qt.PenCapStyle.FlatCap)

            painter.setPen(pen)

            painter.drawArc(rect, start_angle, span)

            start_angle += span

        # center text

        painter.setPen(text_color)

        painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(total))

        # legend

        legend_x = diameter + 36

        legend_y = max(10, (self.height() - len(self.items[:6]) * 22) / 2)

        painter.setFont(QFont("Segoe UI", 9))

        for index, (label, value) in enumerate(self.items[:6]):

            y = legend_y + index * 22

            painter.setPen(Qt.PenStyle.NoPen)

            painter.setBrush(QColor(CHART_COLORS[index % len(CHART_COLORS)]))

            painter.drawRoundedRect(QRectF(legend_x, y + 3, 10, 10), 3, 3)

            painter.setPen(text_color)

            painter.drawText(
                int(legend_x + 18),
                int(y + 13),
                f"{label} ({value})",
            )


class IllustrationWidget(QWidget):
    """
    Flat vector illustration (woman at a laptop, plants, floating badge)
    drawn with QPainter, so no image file is required.
    """

    def __init__(self):

        super().__init__()

        self.setMinimumSize(300, 160)

        self.dark = False

    def set_dark(self, dark):

        self.dark = dark

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # logical canvas is 360 x 200

        scale = min(self.width() / 360, self.height() / 200)

        painter.translate(
            (self.width() - 360 * scale) / 2,
            (self.height() - 200 * scale) / 2,
        )

        painter.scale(scale, scale)

        leaf_light = QColor("#334155" if self.dark else "#BFDBFE")

        leaf_dark = QColor("#475569" if self.dark else "#93C5FD")

        self.draw_plants(painter, leaf_light, leaf_dark)

        self.draw_badge(painter)

        self.draw_person(painter)

        self.draw_laptop(painter)

        painter.setPen(QPen(leaf_dark, 2))

        painter.drawLine(30, 192, 345, 192)

    def draw_plants(self, painter, light, dark):

        painter.setPen(Qt.PenStyle.NoPen)

        angles = [-40, -18, 0, 18, 40]

        for index, angle in enumerate(angles):

            painter.save()

            painter.translate(62, 192)

            painter.rotate(angle)

            painter.setBrush(light if index % 2 == 0 else dark)

            painter.drawEllipse(
                QRectF(
                    -9,
                    -(70 - abs(angle) * 0.5),
                    18,
                    70 - abs(angle) * 0.5,
                )
            )

            painter.restore()

        painter.setBrush(dark)

        painter.drawRoundedRect(QRectF(48, 180, 28, 12), 3, 3)

    def draw_badge(self, painter):

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QColor("#1E293B" if self.dark else "white"))

        painter.drawEllipse(QRectF(248, 24, 34, 34))

        painter.setBrush(QColor("#3B82F6"))

        for x, y, size in (
            (258, 34, 8),
            (268, 36, 6),
            (252, 44, 14),
            (265, 45, 12),
        ):

            painter.drawEllipse(QRectF(x, y, size - 2, size - 2))

    def draw_person(self, painter):

        painter.setPen(Qt.PenStyle.NoPen)

        skin = QColor("#F2C4A0")
        hair = QColor("#1F2A44")
        blazer = QColor("#2F6FD6")

        # hair (back)

        painter.setBrush(hair)

        painter.drawEllipse(QRectF(151, 38, 56, 70))

        # body / blazer

        painter.setBrush(blazer)

        painter.drawRoundedRect(QRectF(134, 108, 94, 84), 28, 28)

        # shirt

        painter.setBrush(QColor("white"))

        shirt = QPolygonF(
            [
                QPointF(171, 108),
                QPointF(193, 108),
                QPointF(182, 142),
            ]
        )

        painter.drawPolygon(shirt)

        # neck

        painter.setBrush(skin)

        painter.drawRect(QRectF(175, 92, 14, 18))

        # head

        painter.drawEllipse(QRectF(161, 50, 42, 48))

        # fringe

        painter.setBrush(hair)

        fringe = QPainterPath()

        fringe.moveTo(158, 70)

        fringe.cubicTo(158, 38, 206, 38, 206, 70)

        fringe.cubicTo(196, 60, 176, 58, 158, 70)

        painter.drawPath(fringe)

        # eyes

        painter.setBrush(QColor("#1F2A44"))

        painter.drawEllipse(QRectF(171, 74, 3, 3))

        painter.drawEllipse(QRectF(188, 74, 3, 3))

        # smile

        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.setPen(QPen(QColor("#B4572E"), 1.5))

        painter.drawArc(QRectF(175, 80, 12, 8), 200 * 16, 140 * 16)

        # arm

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(blazer)

        arm = QPolygonF(
            [
                QPointF(206, 118),
                QPointF(226, 124),
                QPointF(242, 156),
                QPointF(228, 160),
            ]
        )

        painter.drawPolygon(arm)

        painter.setBrush(skin)

        painter.drawEllipse(QRectF(226, 152, 16, 12))

    def draw_laptop(self, painter):

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QColor("#172554"))

        screen = QPolygonF(
            [
                QPointF(236, 132),
                QPointF(318, 120),
                QPointF(312, 164),
                QPointF(232, 164),
            ]
        )

        painter.drawPolygon(screen)

        painter.setBrush(QColor("#1E3A8A"))

        base = QPolygonF(
            [
                QPointF(216, 164),
                QPointF(318, 164),
                QPointF(330, 176),
                QPointF(204, 176),
            ]
        )

        painter.drawPolygon(base)


class ActivityRow(QWidget):
    """One line in the Recent Activity list."""

    def __init__(self, row):

        super().__init__()

        layout = QHBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(10)

        dot = QLabel("●")

        dot.setStyleSheet(
            "color: " + ACTIVITY_COLORS.get(row["kind"], "#64748B") + ";"
        )

        text_box = QVBoxLayout()

        text_box.setSpacing(0)

        text_box.addWidget(make_label(row["title"], "actTitle"))

        text_box.addWidget(make_label(row["detail"] or "", "statNote"))

        ago = make_label(time_ago(row["created_at"]), "statNote")

        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(text_box, 1)

        layout.addWidget(ago, 0, Qt.AlignmentFlag.AlignTop)


# ==============================================================
# DIALOGS
# ==============================================================

class EmployeeDialog(QDialog):
    """Add / edit an employee."""

    def __init__(self, db, parent=None, employee=None):

        super().__init__(parent)

        self.db = db
        self.employee = employee

        self.setWindowTitle("Edit Employee" if employee else "Add Employee")

        self.setMinimumWidth(440)

        form = QFormLayout()

        form.setVerticalSpacing(12)

        self.name_input = QLineEdit()

        self.email_input = QLineEdit()

        self.phone_input = QLineEdit()

        self.department_input = QComboBox()

        self.department_input.setEditable(True)

        try:
            self.department_input.addItems(db.departments())
        except SQLAlchemyError as exc:
            show_db_error(self, exc)

        self.department_input.setCurrentText("")

        self.designation_input = QLineEdit()

        self.salary_input = QDoubleSpinBox()

        self.salary_input.setRange(0, 100000000)

        self.salary_input.setDecimals(2)

        self.salary_input.setPrefix("₹ ")

        self.join_input = QDateEdit(QDate.currentDate())

        self.join_input.setCalendarPopup(True)

        self.join_input.setDisplayFormat("yyyy-MM-dd")

        self.status_input = QComboBox()

        self.status_input.addItems(["Active", "Inactive"])

        form.addRow("Full name *", self.name_input)
        form.addRow("Email *", self.email_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Department", self.department_input)
        form.addRow("Designation", self.designation_input)
        form.addRow("Monthly salary", self.salary_input)
        form.addRow("Join date", self.join_input)
        form.addRow("Status", self.status_input)

        if employee:
            self.load_employee()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.save)

        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        layout.addLayout(form)

        layout.addSpacing(10)

        layout.addWidget(buttons)

    def load_employee(self):

        employee = self.employee

        self.name_input.setText(employee["name"] or "")

        self.email_input.setText(employee["email"] or "")

        self.phone_input.setText(employee["phone"] or "")

        self.department_input.setCurrentText(employee["department"] or "")

        self.designation_input.setText(employee["designation"] or "")

        self.salary_input.setValue(employee["salary"] or 0)

        if employee["join_date"]:

            self.join_input.setDate(
                QDate.fromString(employee["join_date"], "yyyy-MM-dd")
            )

        self.status_input.setCurrentText(employee["status"] or "Active")

    def save(self):

        name = self.name_input.text().strip()

        email = self.email_input.text().strip()

        if not name:

            QMessageBox.warning(self, "Missing", "Name is required.")

            return

        if "@" not in email or "." not in email:

            QMessageBox.warning(
                self,
                "Invalid",
                "Please enter a valid email address.",
            )

            return

        department = self.department_input.currentText().strip()

        designation = self.designation_input.text().strip()

        values = {
            "name": name,
            "email": email,
            "phone": self.phone_input.text().strip(),
            "department": department,
            "designation": designation,
            "salary": self.salary_input.value(),
            "join_date": self.join_input.date().toString("yyyy-MM-dd"),
            "status": self.status_input.currentText(),
        }

        try:

            if self.employee:

                self.db.save_employee(values, self.employee["id"])

                self.db.log("Employee updated", name, "employee")

            else:

                self.db.save_employee(values)

                self.db.log(
                    "New employee registered",
                    f"{name} - {designation or department or 'Employee'}",
                    "employee",
                )

        except IntegrityError:

            QMessageBox.warning(
                self,
                "Duplicate",
                "An employee with this email or code already exists.",
            )

            return

        except LookupError as exc:

            QMessageBox.warning(self, "Not found", str(exc))

            return

        except SQLAlchemyError as exc:

            show_db_error(self, exc)

            return

        self.accept()


class ReviewDialog(QDialog):
    """Admin-style performance review dialog for HR.

    Uses the same employee/rating/remarks fields and database method as Admin,
    so HR-created reviews remain visible to the employee dashboard.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Add Performance Review")
        self.setMinimumSize(620, 430)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("Add Performance Review")
        title.setObjectName("pageTitle")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        subtitle = QLabel("Evaluate an employee using the same rating scale as Admin.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748B; font-size: 13px;")
        root.addWidget(title)
        root.addWidget(subtitle)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_card.setStyleSheet(
            "QFrame#card { background: palette(base); border: 1px solid #D7E0EC; "
            "border-radius: 12px; }"
        )
        card_layout = QVBoxLayout(form_card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(16)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(16)

        self.employee_input = QComboBox()
        self.employee_input.setMinimumHeight(42)
        # Employee must be chosen from the database-backed list; typing a name
        # must never produce a review with employee_id=None.
        self.employee_input.setEditable(False)
        self.employee_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.employee_input.addItem("Select employee", None)
        try:
            for row in db.active_employees():
                employee_id = row.get("id")
                employee_name = str(row.get("name") or "").strip()
                if employee_id is None or not employee_name:
                    continue
                self.employee_input.addItem(employee_name, int(employee_id))
            self.employee_input.setCurrentIndex(0)
        except (SQLAlchemyError, TypeError, ValueError) as exc:
            show_db_error(self, exc)

        self.rating_input = QDoubleSpinBox()
        self.rating_input.setRange(0.0, 10.0)
        self.rating_input.setSingleStep(0.5)
        self.rating_input.setDecimals(1)
        self.rating_input.setValue(3.0)
        self.rating_input.setSuffix(" / 10")
        self.rating_input.setMinimumHeight(42)
        self.rating_input.setToolTip("Choose a rating from 0 to 10, matching Admin.")

        self.remarks_input = QTextEdit()
        self.remarks_input.setMinimumHeight(115)
        self.remarks_input.setPlaceholderText(
            "Enter achievements, strengths, areas to improve, and feedback..."
        )

        form.addRow("Employee", self.employee_input)
        form.addRow("Rating (0–10)", self.rating_input)
        form.addRow("Remarks", self.remarks_input)
        card_layout.addLayout(form)
        root.addWidget(form_card, 1)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        self.cancel_button = QPushButton("Cancel")
        self.save_button = QPushButton("Save Performance")
        self.save_button.setDefault(True)
        self.save_button.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: 600; "
            "padding: 11px 20px; border: none; border-radius: 7px; } "
            "QPushButton:hover { background: #1D4ED8; }"
        )
        self.cancel_button.setMinimumHeight(42)
        self.save_button.setMinimumHeight(42)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save)
        buttons_row.addWidget(self.cancel_button)
        buttons_row.addWidget(self.save_button)
        root.addLayout(buttons_row)

    def save(self):
        employee_id = self.employee_input.currentData()
        if self.employee_input.count() <= 1:
            QMessageBox.warning(
                self,
                "No employees",
                "No active employees were found. Add or activate an employee first.",
            )
            return

        if employee_id is None:
            QMessageBox.warning(
                self,
                "Select employee",
                "Please select an employee from the dropdown list before saving.",
            )
            self.employee_input.setFocus()
            return

        employee_name = self.employee_input.currentText().strip()
        rating = float(self.rating_input.value())
        remarks = self.remarks_input.toPlainText().strip()

        try:
            # Keep the same database method/fields used by Admin.
            self.db.add_review(employee_id, rating, remarks)
        except (ValueError, LookupError) as exc:
            QMessageBox.warning(self, "Cannot save performance review", str(exc))
            return
        except SQLAlchemyError as exc:
            show_db_error(self, exc)
            return

        try:
            self.db.log(
                "Performance review updated",
                f"{employee_name} - {rating:.1f} rating",
                "performance",
            )
        except (SQLAlchemyError, AttributeError):
            # Review is already saved; logging failure should not lose the review.
            pass

        self.accept()
class LeaveDialog(QDialog):
    """Create a leave request (works once a Leave model/service exists)."""

    def __init__(self, db, parent=None, start=None):

        super().__init__(parent)

        self.db = db

        self.setWindowTitle("New Leave Request")

        self.setMinimumWidth(420)

        self.employee_input = QComboBox()

        try:

            for row in db.active_employees():
                self.employee_input.addItem(row["name"], row["id"])

        except SQLAlchemyError as exc:

            show_db_error(self, exc)

        start = start or QDate.currentDate()

        self.start_input = QDateEdit(start)

        self.end_input = QDateEdit(start)

        for editor in (self.start_input, self.end_input):

            editor.setCalendarPopup(True)

            editor.setDisplayFormat("yyyy-MM-dd")

        self.reason_input = QLineEdit()

        form = QFormLayout()

        form.setVerticalSpacing(12)

        form.addRow("Employee", self.employee_input)
        form.addRow("From", self.start_input)
        form.addRow("To", self.end_input)
        form.addRow("Reason", self.reason_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.save)

        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        layout.addLayout(form)

        layout.addSpacing(10)

        layout.addWidget(buttons)

    def save(self):

        if self.employee_input.count() == 0:

            QMessageBox.warning(
                self,
                "No employee",
                "Please add an employee first.",
            )

            return

        if self.end_input.date() < self.start_input.date():

            QMessageBox.warning(
                self,
                "Invalid dates",
                "End date cannot be before start date.",
            )

            return

        days = (
            self.start_input.date().daysTo(self.end_input.date()) + 1
        )

        try:

            self.db.create_leave(
                self.employee_input.currentData(),
                self.start_input.date().toString("yyyy-MM-dd"),
                self.end_input.date().toString("yyyy-MM-dd"),
                self.reason_input.text().strip(),
            )

        except LeaveUnavailableError as exc:

            QMessageBox.information(self, "Leave module", str(exc))

            return

        except SQLAlchemyError as exc:

            show_db_error(self, exc)

            return

        short_date = self.start_input.date().toString("dd MMM")

        self.db.log(
            "New leave request",
            f"{self.employee_input.currentText()} - "
            f"{days} day(s) from {short_date}",
            "leave",
        )

        self.accept()


class EmployeeDetailDialog(QDialog):
    """Read-only profile: info, attendance this month, payroll, reviews."""

    def __init__(self, db, employee_id, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Employee Profile")

        self.setMinimumSize(560, 560)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        layout.setSpacing(12)

        try:

            employee = db.get_employee(employee_id)

            month = month_key(date.today())

            counts = db.employee_attendance_counts(employee_id, month)

            payroll_rows = db.payroll_history(employee_id, 6)

            review_rows = db.employee_reviews(employee_id, 6)

        except SQLAlchemyError as exc:

            show_db_error(self, exc)

            layout.addWidget(QLabel("Could not load this employee."))

            return

        if employee is None:

            layout.addWidget(QLabel("Employee not found."))

            return

        # ---------------- header ----------------

        header = QHBoxLayout()

        avatar = QLabel(employee["name"][:1].upper())

        avatar.setObjectName("avatar")

        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        avatar.setFixedSize(56, 56)

        avatar.setStyleSheet(
            "background: #DBEAFE; color: #2563EB; "
            "border-radius: 28px; font-size: 22px; "
            "font-weight: 800;"
        )

        title_box = QVBoxLayout()

        title_box.setSpacing(0)

        title_box.addWidget(make_label(employee["name"], "pageTitle"))

        title_box.addWidget(
            make_label(
                f"{employee['designation'] or '-'}  •  "
                f"{employee['department'] or '-'}  •  "
                f"{employee['emp_code']}",
                "pageSubtitle",
            )
        )

        header.addWidget(avatar)

        header.addSpacing(12)

        header.addLayout(title_box)

        header.addStretch()

        layout.addLayout(header)

        # ---------------- info ----------------

        info = QLabel(
            f"<b>Email:</b> {employee['email'] or '-'}<br>"
            f"<b>Phone:</b> {employee['phone'] or '-'}<br>"
            f"<b>Joined:</b> {employee['join_date'] or '-'}<br>"
            f"<b>Salary:</b> {format_inr(employee['salary'])} / month<br>"
            f"<b>Status:</b> {employee['status']}"
        )

        info.setObjectName("summaryBox")

        layout.addWidget(info)

        # ---------------- attendance ----------------

        layout.addWidget(make_label("Attendance this month", "sectionTitle"))

        layout.addWidget(
            make_label(
                f"Present: {counts['Present']}    "
                f"Absent: {counts['Absent']}    "
                f"Leave: {counts['Leave']}",
                "chip",
            )
        )

        # ---------------- payroll ----------------

        layout.addWidget(make_label("Payroll history", "sectionTitle"))

        payroll_table = make_table()

        payroll_table.setMaximumHeight(130)

        fill_table(
            payroll_table,
            ["Month", "Net pay", "Processed on"],
            [
                (
                    row["id"],
                    [
                        row["month"],
                        format_inr(row["amount"]),
                        row["processed_on"],
                    ],
                )
                for row in payroll_rows
            ],
        )

        layout.addWidget(payroll_table)

        # ---------------- reviews ----------------

        layout.addWidget(make_label("Performance reviews", "sectionTitle"))

        review_table = make_table()

        review_table.setMaximumHeight(130)

        fill_table(
            review_table,
            ["Date", "Rating", "Remarks"],
            [
                (
                    row["id"],
                    [
                        row["review_date"],
                        f"{row['rating']:.1f} / 10",
                        row["remarks"],
                    ],
                )
                for row in review_rows
            ],
        )

        layout.addWidget(review_table)

        close_button = make_button("Close", "secondaryButton")

        close_button.clicked.connect(self.accept)

        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)


class PayslipDialog(QDialog):
    """Salary slip with absence deduction breakdown."""

    def __init__(self, db, employee_id, month, parent=None):

        super().__init__(parent)

        self.setWindowTitle("Payslip")

        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        try:

            employee = db.get_employee(employee_id)

            absent = db.absent_days(employee_id, month)

            paid = db.payroll_record(employee_id, month)

        except SQLAlchemyError as exc:

            show_db_error(self, exc)

            layout.addWidget(QLabel("Could not load the payslip."))

            return

        if employee is None:

            layout.addWidget(QLabel("Employee not found."))

            return

        auto_deduction, net = calculate_net_salary(employee["salary"], absent)
        allowances = float(paid.get("allowances", 0) or 0) if paid else 0.0
        deduction = float(paid.get("deductions", auto_deduction) or 0) if paid else auto_deduction
        net = max(0.0, round(float(employee["salary"] or 0) + allowances - deduction, 2))

        if paid and paid["paid"]:

            status = f"Paid on {paid['processed_on']}"
            net = paid["amount"]

        else:

            status = "Not processed yet (preview)"

        layout.addWidget(make_label(f"Payslip - {month}", "pageTitle"))

        layout.addWidget(
            make_label(
                f"{employee['name']}  •  {employee['emp_code']}",
                "pageSubtitle",
            )
        )

        layout.addSpacing(8)

        body = QLabel(
            f"<table cellpadding='6' width='100%'>"
            f"<tr><td>Base salary</td>"
            f"<td align='right'>{format_inr(employee['salary'])}</td></tr>"
            f"<tr><td>Absent days</td>"
            f"<td align='right'>{absent}</td></tr>"
            f"<tr><td>Absence deduction "
            f"({WORKING_DAYS_PER_MONTH}-day basis)</td>"
            f"<td align='right'>- {format_inr(auto_deduction)}</td></tr>"
            f"<tr><td>Extra payment / bonus</td>"
            f"<td align='right'>+ {format_inr(allowances)}</td></tr>"
            f"<tr><td>Additional deduction</td>"
            f"<td align='right'>- {format_inr(max(0.0, deduction - auto_deduction))}</td></tr>"
            f"<tr><td><b>Total deductions</b></td>"
            f"<td align='right'>- {format_inr(deduction)}</td></tr>"
            f"<tr><td><b>Net pay</b></td>"
            f"<td align='right'><b>{format_inr(net)}</b></td></tr>"
            f"</table><br>{status}"
        )

        body.setObjectName("summaryBox")

        layout.addWidget(body)

        close_button = make_button("Close", "secondaryButton")

        close_button.clicked.connect(self.accept)

        layout.addSpacing(8)

        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)


class ActivityDialog(QDialog):
    """Full activity history from AuditLog (opened from 'View All')."""

    def __init__(self, db, parent=None):

        super().__init__(parent)

        self.setWindowTitle("All Activity")

        self.setMinimumSize(560, 460)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(make_label("Activity history", "pageTitle"))

        table = make_table()

        try:
            rows = db.recent_activity(200)
        except SQLAlchemyError as exc:
            show_db_error(self, exc)
            rows = []

        fill_table(
            table,
            ["Event", "Details", "When"],
            [
                (
                    row["id"],
                    [
                        row["title"],
                        row["detail"],
                        time_ago(row["created_at"]),
                    ],
                )
                for row in rows
            ],
        )

        layout.addWidget(table)

        if not rows:

            layout.addWidget(
                make_label("No activity recorded yet.", "emptyLabel")
            )


class NotificationDialog(QDialog):
    """Pending leave requests with Approve / Reject buttons."""

    def __init__(self, db, parent=None):

        super().__init__(parent)

        self.db = db

        self.changed = False

        self.setWindowTitle("Notifications")

        self.setMinimumSize(620, 420)

        self.layout_main = QVBoxLayout(self)

        self.layout_main.setContentsMargins(24, 20, 24, 20)

        self.layout_main.addWidget(
            make_label("Pending leave requests", "pageTitle")
        )

        self.table = make_table()

        self.layout_main.addWidget(self.table)

        buttons = QHBoxLayout()

        approve = make_button("Approve", "successButton")

        reject = make_button("Reject", "dangerButton")

        close = make_button("Close", "secondaryButton")

        approve.clicked.connect(lambda: self.decide("Approved"))

        reject.clicked.connect(lambda: self.decide("Rejected"))

        close.clicked.connect(self.accept)

        buttons.addStretch()

        buttons.addWidget(approve)

        buttons.addWidget(reject)

        buttons.addWidget(close)

        self.layout_main.addLayout(buttons)

        self.reload()

    def reload(self):

        try:
            rows = self.db.pending_leaves()
        except SQLAlchemyError as exc:
            show_db_error(self, exc)
            rows = []

        fill_table(
            self.table,
            ["Employee", "From", "To", "Reason"],
            [
                (
                    row["id"],
                    [
                        row["name"],
                        row["start_date"],
                        row["end_date"],
                        row["reason"],
                    ],
                )
                for row in rows
            ],
        )

    def decide(self, status):

        leave_id = selected_id(self.table)

        if leave_id is None:

            QMessageBox.information(
                self,
                "Select",
                "Please select a request first.",
            )

            return

        try:

            self.db.update_leave_status(leave_id, status)

        except LeaveUnavailableError as exc:

            QMessageBox.information(self, "Leave module", str(exc))

            return

        except SQLAlchemyError as exc:

            show_db_error(self, exc)

            return

        self.changed = True

        self.reload()


# ==============================================================
# PAGES
# ==============================================================

class BasePage(QWidget):
    """Every page gets the data service, a change callback and a toast."""

    def __init__(self, db, on_change, notify):

        super().__init__()

        self.db = db
        self.on_change = on_change
        self.notify = notify

    def guard(self, func, *args):
        """Runs func(*args); database errors become a message box."""

        try:
            return func(*args)
        except SQLAlchemyError as exc:
            show_db_error(self, exc)
            return None

    def refresh(self, *args):

        self.guard(self.load)

    def load(self):

        pass


# ==============================================================
# DASHBOARD PAGE
# ==============================================================

class DashboardPage(BasePage):

    def __init__(self, db, on_change, notify, goto, open_activity):

        super().__init__(db, on_change, notify)

        self.goto = goto
        self.open_activity = open_activity
        self.dark = False

        scroll = QScrollArea(self)

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(QFrame.Shape.NoFrame)

        outer = QVBoxLayout(self)

        outer.setContentsMargins(0, 0, 0, 0)

        outer.addWidget(scroll)

        content = QWidget()

        scroll.setWidget(content)

        layout = QVBoxLayout(content)

        layout.setContentsMargins(24, 12, 24, 24)

        layout.setSpacing(18)

        layout.addWidget(self.build_banner())

        layout.addLayout(self.build_overview_header())

        layout.addLayout(self.build_cards())

        layout.addLayout(self.build_middle_row())

        layout.addLayout(self.build_bottom_row())

    # ----------------------------------------------------------
    # builders
    # ----------------------------------------------------------

    def build_banner(self):

        banner = QFrame()

        banner.setObjectName("banner")

        banner.setMinimumHeight(190)

        row = QHBoxLayout(banner)

        row.setContentsMargins(30, 18, 30, 18)

        left = QVBoxLayout()

        left.addStretch()

        left.addWidget(make_label("WELCOME BACK", "welcomeSmall"))

        self.greeting_label = make_label("", "greeting")

        left.addWidget(self.greeting_label)

        subtitle = make_label(
            "Here's what's happening with your team today. "
            "Manage employees, attendance, payroll and "
            "performance from one place.",
            "pageSubtitle",
        )

        subtitle.setWordWrap(True)

        subtitle.setMaximumWidth(420)

        left.addWidget(subtitle)

        left.addStretch()

        row.addLayout(left, 4)

        self.illustration = IllustrationWidget()

        row.addWidget(self.illustration, 4)

        badge_box = QVBoxLayout()

        badge_box.addStretch()

        self.role_badge = QLabel("HR")

        self.role_badge.setObjectName("roleBadge")

        self.role_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.role_badge.setFixedSize(58, 58)

        self.role_label = make_label("", "fieldLabel")

        self.role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge_box.addWidget(
            self.role_badge,
            0,
            Qt.AlignmentFlag.AlignCenter,
        )

        badge_box.addWidget(self.role_label)

        badge_box.addStretch()

        row.addLayout(badge_box, 1)

        return banner

    def build_overview_header(self):

        row = QHBoxLayout()

        text_box = QVBoxLayout()

        text_box.setSpacing(0)

        text_box.addWidget(make_label("Overview", "sectionTitle"))

        text_box.addWidget(
            make_label(
                "Key statistics and insights about your organization",
                "pageSubtitle",
            )
        )

        row.addLayout(text_box)

        row.addStretch()

        self.period_box = QComboBox()

        self.period_box.addItems(PERIOD_OPTIONS)

        self.period_box.setMinimumWidth(140)

        self.period_box.currentIndexChanged.connect(self.refresh)

        row.addWidget(self.period_box)

        return row

    def build_cards(self):

        row = QHBoxLayout()

        row.setSpacing(14)

        self.card_total = StatCard("Total Employees", "👥", "#3B82F6")

        self.card_active = StatCard("Active Employees", "✔", "#22C55E")

        self.card_present = StatCard("Present Today", "🕒", "#8B5CF6")

        self.card_payroll = StatCard("Total Payroll", "₹", "#F59E0B")

        self.card_performance = StatCard("Avg. Performance", "★", "#EF4444")

        for card in (
            self.card_total,
            self.card_active,
            self.card_present,
            self.card_payroll,
            self.card_performance,
        ):

            row.addWidget(card)

        return row

    def build_middle_row(self):

        row = QHBoxLayout()

        row.setSpacing(14)

        # ---------------- attendance chart ----------------

        chart_panel = QFrame()

        chart_panel.setObjectName("panel")

        chart_layout = QVBoxLayout(chart_panel)

        chart_layout.setContentsMargins(18, 16, 18, 16)

        header = QHBoxLayout()

        header.addWidget(make_label("Attendance Overview", "sectionTitle"))

        header.addStretch()

        details = QPushButton("View Details →")

        details.setObjectName("linkButton")

        details.setCursor(Qt.CursorShape.PointingHandCursor)

        details.clicked.connect(lambda: self.goto(3))

        header.addWidget(details)

        chart_layout.addLayout(header)

        self.chart = AttendanceChart()

        chart_layout.addWidget(self.chart)

        row.addWidget(chart_panel, 5)

        # ---------------- quick actions ----------------

        quick_panel = QFrame()

        quick_panel.setObjectName("panel")

        quick_layout = QVBoxLayout(quick_panel)

        quick_layout.setContentsMargins(18, 16, 18, 16)

        quick_layout.addWidget(make_label("⚡  Quick Actions", "sectionTitle"))

        actions = [
            ("👥   Manage Employees", 2),
            ("🕒   Mark Attendance", 3),
            ("₹   Process Payroll", 4),
            ("★   View Performance", 5),
            ("📊   Generate Reports", 6),
        ]

        for text, index in actions:

            button = QPushButton(text + "          ›")

            button.setObjectName("quickButton")

            button.setCursor(Qt.CursorShape.PointingHandCursor)

            button.clicked.connect(
                lambda checked=False, i=index: self.goto(i)
            )

            quick_layout.addWidget(button)

        quick_layout.addStretch()

        row.addWidget(quick_panel, 3)

        # ---------------- recent activity ----------------

        activity_panel = QFrame()

        activity_panel.setObjectName("panel")

        activity_outer = QVBoxLayout(activity_panel)

        activity_outer.setContentsMargins(18, 16, 18, 16)

        activity_header = QHBoxLayout()

        activity_header.addWidget(
            make_label("🕘  Recent Activity", "sectionTitle")
        )

        activity_header.addStretch()

        view_all = QPushButton("View All →")

        view_all.setObjectName("linkButton")

        view_all.setCursor(Qt.CursorShape.PointingHandCursor)

        view_all.clicked.connect(self.open_activity)

        activity_header.addWidget(view_all)

        activity_outer.addLayout(activity_header)

        self.activity_layout = QVBoxLayout()

        self.activity_layout.setSpacing(12)

        activity_outer.addLayout(self.activity_layout)

        activity_outer.addStretch()

        row.addWidget(activity_panel, 4)

        return row

    def build_bottom_row(self):

        row = QHBoxLayout()

        row.setSpacing(14)

        # ---------------- departments ----------------

        dept_panel = QFrame()

        dept_panel.setObjectName("panel")

        dept_layout = QVBoxLayout(dept_panel)

        dept_layout.setContentsMargins(18, 16, 18, 16)

        dept_layout.addWidget(
            make_label("Department Distribution", "sectionTitle")
        )

        self.donut = DonutChart()

        dept_layout.addWidget(self.donut)

        row.addWidget(dept_panel, 4)

        # ---------------- pending leaves ----------------

        leave_panel = QFrame()

        leave_panel.setObjectName("panel")

        leave_outer = QVBoxLayout(leave_panel)

        leave_outer.setContentsMargins(18, 16, 18, 16)

        leave_header = QHBoxLayout()

        leave_header.addWidget(
            make_label("Pending Leave Requests", "sectionTitle")
        )

        leave_header.addStretch()

        open_calendar = QPushButton("Open →")

        open_calendar.setObjectName("linkButton")

        open_calendar.setCursor(Qt.CursorShape.PointingHandCursor)

        open_calendar.clicked.connect(lambda: self.goto(1))

        leave_header.addWidget(open_calendar)

        leave_outer.addLayout(leave_header)

        self.leave_layout = QVBoxLayout()

        self.leave_layout.setSpacing(10)

        leave_outer.addLayout(self.leave_layout)

        leave_outer.addStretch()

        row.addWidget(leave_panel, 4)

        # ---------------- top performers ----------------

        top_panel = QFrame()

        top_panel.setObjectName("panel")

        top_outer = QVBoxLayout(top_panel)

        top_outer.setContentsMargins(18, 16, 18, 16)

        top_outer.addWidget(make_label("Top Performers", "sectionTitle"))

        self.top_layout = QVBoxLayout()

        self.top_layout.setSpacing(10)

        top_outer.addLayout(self.top_layout)

        top_outer.addStretch()

        row.addWidget(top_panel, 4)

        return row

    # ----------------------------------------------------------
    # refresh
    # ----------------------------------------------------------

    def load(self):

        db = self.db

        today = date.today()

        # ---------------- banner ----------------

        username, role = get_session_info()

        hour = datetime.now().hour

        if hour < 12:
            part = "Morning"
        elif hour < 17:
            part = "Afternoon"
        else:
            part = "Evening"

        self.greeting_label.setText(f"Good {part}, {username}!")

        initials = "".join(word[0] for word in role.split()[:2]).upper()

        self.role_badge.setText(initials or "HR")

        self.role_label.setText(role)

        self.illustration.set_dark(self.dark)

        # ---------------- cards ----------------

        last_month_end = today.replace(day=1) - timedelta(days=1)

        counts = db.employee_counts(last_month_end)

        present_today = db.attendance_counts(today)["Present"]

        present_yesterday = db.attendance_counts(
            today - timedelta(days=1)
        )["Present"]

        current_prefix, previous_prefix, note = period_prefixes(
            self.period_box.currentText()
        )

        payroll_now = db.payroll_total(current_prefix)

        payroll_before = db.payroll_total(previous_prefix)

        rating_now = db.average_rating(current_prefix)

        rating_before = db.average_rating(previous_prefix)

        rating_overall = db.average_rating()

        self.card_total.set_data(
            counts["total"],
            counts["total"],
            counts["total_before"],
        )

        self.card_active.set_data(
            counts["active"],
            counts["active"],
            counts["active_before"],
        )

        self.card_present.set_data(
            present_today,
            present_today,
            present_yesterday,
            "vs yesterday",
        )

        self.card_payroll.set_data(
            format_inr(payroll_now),
            payroll_now,
            payroll_before,
            note,
        )

        self.card_performance.set_data(
            f"{rating_now:.1f}"
            if rating_now
            else (f"{rating_overall:.1f}" if rating_overall else "N/A"),
            rating_now,
            rating_before,
            note,
        )

        # ---------------- attendance chart ----------------

        start = today - timedelta(days=6)

        per_day = db.attendance_range(start, today)

        labels = []
        present_list = []
        absent_list = []

        for offset in range(6, -1, -1):

            day = today - timedelta(days=offset)

            day_counts = per_day.get(
                day.isoformat(),
                {"Present": 0, "Absent": 0, "Leave": 0},
            )

            labels.append(f"{day.strftime('%a')}\n{day.strftime('%d %b')}")

            present_list.append(day_counts["Present"])

            absent_list.append(day_counts["Absent"])

        self.chart.set_data(labels, present_list, absent_list, self.dark)

        # ---------------- recent activity ----------------

        clear_layout(self.activity_layout)

        rows = db.recent_activity(5)

        if not rows:

            self.activity_layout.addWidget(
                make_label("No recent activity yet.", "emptyLabel")
            )

        for row in rows:
            self.activity_layout.addWidget(ActivityRow(row))

        # ---------------- departments ----------------

        self.donut.set_data(
            [(row["name"], row["total"]) for row in db.department_counts()],
            self.dark,
        )

        # ---------------- pending leaves ----------------

        clear_layout(self.leave_layout)

        leaves = db.pending_leaves()[:5]

        if not leaves:

            self.leave_layout.addWidget(
                make_label(
                    "No pending requests."
                    if db.leave_supported()
                    else LEAVE_UNSUPPORTED_TEXT,
                    "emptyLabel",
                )
            )

        for leave in leaves:

            holder = QWidget()

            box = QVBoxLayout(holder)

            box.setSpacing(0)

            box.setContentsMargins(0, 0, 0, 0)

            box.addWidget(make_label(leave["name"], "actTitle"))

            box.addWidget(
                make_label(
                    f"{leave['start_date']} → "
                    f"{leave['end_date']}  •  "
                    f"{leave['reason'] or 'No reason'}",
                    "statNote",
                )
            )

            self.leave_layout.addWidget(holder)

        # ---------------- top performers ----------------

        clear_layout(self.top_layout)

        performers = db.top_performers(5)

        if not performers:

            self.top_layout.addWidget(
                make_label("No reviews yet.", "emptyLabel")
            )

        for person in performers:

            holder = QWidget()

            box = QVBoxLayout(holder)

            box.setContentsMargins(0, 0, 0, 0)

            box.setSpacing(3)

            line = QHBoxLayout()

            line.addWidget(make_label(person["name"], "actTitle"))

            line.addStretch()

            line.addWidget(
                make_label(f"{person['rating']:.1f} / 10", "statNote")
            )

            bar = QProgressBar()

            bar.setRange(0, 100)

            bar.setValue(int(person["rating"] * 10))

            bar.setFixedHeight(8)

            box.addLayout(line)

            box.addWidget(bar)

            self.top_layout.addWidget(holder)


# ==============================================================
# EMPLOYEES PAGE
# ==============================================================

class EmployeesPage(BasePage):

    HEADERS = [
        "Code",
        "Name",
        "Email",
        "Phone",
        "Department",
        "Designation",
        "Salary",
        "Joined",
        "Status",
    ]

    def __init__(self, db, on_change, notify):

        super().__init__(db, on_change, notify)

        self.reload_departments_flag = True

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 16, 24, 20)

        layout.setSpacing(12)

        # ---------------- header ----------------

        top = QHBoxLayout()

        top.addLayout(
            page_header(
                "Employees",
                "Add, edit and manage employee records",
            )
        )

        top.addStretch()

        add_button = make_button("+ Add Employee")

        add_button.clicked.connect(self.add_employee)

        top.addWidget(add_button)

        layout.addLayout(top)

        # ---------------- filters ----------------

        filters = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search name, email, code, designation..."
        )

        self.search_input.setMinimumWidth(300)

        self.search_input.textChanged.connect(self.refresh)

        self.department_filter = QComboBox()

        self.department_filter.setMinimumWidth(170)

        self.department_filter.currentIndexChanged.connect(self.refresh)

        self.status_filter = QComboBox()

        self.status_filter.addItems(["All status", "Active", "Inactive"])

        self.status_filter.currentIndexChanged.connect(self.refresh)

        filters.addWidget(self.search_input)

        filters.addWidget(self.department_filter)

        filters.addWidget(self.status_filter)

        filters.addStretch()

        view_button = make_button("View", "secondaryButton")

        view_button.clicked.connect(self.view_employee)

        edit_button = make_button("Edit", "secondaryButton")

        edit_button.clicked.connect(self.edit_employee)

        delete_button = make_button("Delete", "dangerButton")

        delete_button.clicked.connect(self.delete_employee)

        export_button = make_button("Export CSV", "secondaryButton")

        export_button.clicked.connect(self.export_csv)

        for button in (
            view_button,
            edit_button,
            delete_button,
            export_button,
        ):

            filters.addWidget(button)

        layout.addLayout(filters)

        # ---------------- table ----------------

        self.table = make_table()

        self.table.doubleClicked.connect(self.view_employee)

        layout.addWidget(self.table)

        self.count_label = make_label("", "pageSubtitle")

        layout.addWidget(self.count_label)

    # ----------------------------------------------------------

    def set_filter(self, text):

        self.search_input.setText(text)

    def reload_departments(self):

        current = self.department_filter.currentText()

        self.department_filter.blockSignals(True)

        self.department_filter.clear()

        self.department_filter.addItem("All departments")

        self.department_filter.addItems(self.db.departments())

        index = self.department_filter.findText(current)

        self.department_filter.setCurrentIndex(index if index >= 0 else 0)

        self.department_filter.blockSignals(False)

    def fetch_rows(self):

        department = self.department_filter.currentText()

        if not department or department == "All departments":
            department = None

        status = self.status_filter.currentText()

        if status == "All status":
            status = None

        return self.db.search_employees(
            self.search_input.text(),
            department,
            status,
        )

    def refresh(self, *args):

        self.reload_departments_flag = (
            self.sender() is not self.department_filter
        )

        self.guard(self.load)

    def load(self):

        if self.reload_departments_flag:
            self.reload_departments()

        rows = self.fetch_rows()

        fill_table(
            self.table,
            self.HEADERS,
            [
                (
                    row["id"],
                    [
                        row["emp_code"],
                        row["name"],
                        row["email"],
                        row["phone"],
                        row["department"],
                        row["designation"],
                        format_inr(row["salary"]),
                        row["join_date"],
                        row["status"],
                    ],
                )
                for row in rows
            ],
        )

        if rows:

            self.count_label.setText(f"{len(rows)} employee(s)")

        else:

            self.count_label.setText(
                "No employees found. Click '+ Add Employee' to create one."
            )

    # ----------------------------------------------------------

    @safe_action
    def add_employee(self):

        dialog = EmployeeDialog(self.db, self)

        if dialog.exec():

            self.refresh()

            self.on_change()

            self.notify("Employee added")

    def require_selection(self):

        employee_id = selected_id(self.table)

        if employee_id is None:

            QMessageBox.information(
                self,
                "Select",
                "Please select an employee first.",
            )

        return employee_id

    @safe_action
    def view_employee(self):

        employee_id = self.require_selection()

        if employee_id is None:
            return

        EmployeeDetailDialog(self.db, employee_id, self).exec()

    @safe_action
    def edit_employee(self):

        employee_id = self.require_selection()

        if employee_id is None:
            return

        employee = self.db.get_employee(employee_id)

        if employee is None:

            QMessageBox.warning(
                self,
                "Not found",
                "This employee no longer exists.",
            )

            self.refresh()

            return

        dialog = EmployeeDialog(self.db, self, employee)

        if dialog.exec():

            self.refresh()

            self.on_change()

            self.notify("Employee updated")

    @safe_action
    def delete_employee(self):

        employee_id = self.require_selection()

        if employee_id is None:
            return

        employee = self.db.get_employee(employee_id)

        if employee is None:

            self.refresh()

            return

        answer = QMessageBox.question(
            self,
            "Delete employee",
            f"Delete {employee['name']}?\n\n"
            "Their attendance, payroll and performance "
            "records will also be removed.",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.delete_employee(employee_id)

        self.db.log("Employee deleted", employee["name"], "employee")

        self.refresh()

        self.on_change()

        self.notify("Employee deleted")

    @safe_action
    def export_csv(self):

        rows = self.fetch_rows()

        export_rows_to_csv(
            self,
            "employees",
            [
                "Code",
                "Name",
                "Email",
                "Phone",
                "Department",
                "Designation",
                "Salary",
                "Join Date",
                "Status",
            ],
            [
                (
                    row["emp_code"],
                    row["name"],
                    row["email"],
                    row["phone"],
                    row["department"],
                    row["designation"],
                    row["salary"],
                    row["join_date"],
                    row["status"],
                )
                for row in rows
            ],
        )


# ==============================================================
# ATTENDANCE PAGE
# ==============================================================

class AttendancePage(BasePage):

    def __init__(self, db, on_change, notify):

        super().__init__(db, on_change, notify)

        self.combos = {}

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 16, 24, 20)

        layout.setSpacing(12)

        layout.addLayout(
            page_header(
                "Attendance",
                "Mark daily attendance and review monthly summaries",
            )
        )

        self.tabs = QTabWidget()

        self.tabs.addTab(self.build_daily_tab(), "Daily")

        self.tabs.addTab(self.build_monthly_tab(), "Monthly Summary")

        self.tabs.currentChanged.connect(lambda: self.refresh())

        layout.addWidget(self.tabs)

    # ----------------------------------------------------------
    # daily tab
    # ----------------------------------------------------------

    def build_daily_tab(self):

        tab = QWidget()

        layout = QVBoxLayout(tab)

        layout.setContentsMargins(0, 8, 0, 0)

        layout.setSpacing(12)

        controls = QHBoxLayout()

        previous_button = make_button("‹", "secondaryButton")

        previous_button.setFixedWidth(44)

        previous_button.clicked.connect(lambda: self.shift_day(-1))

        next_button = make_button("›", "secondaryButton")

        next_button.setFixedWidth(44)

        next_button.clicked.connect(lambda: self.shift_day(1))

        self.day_input = QDateEdit(QDate.currentDate())

        self.day_input.setCalendarPopup(True)

        self.day_input.setDisplayFormat("dd MMM yyyy")

        self.day_input.setMaximumDate(QDate.currentDate())

        self.day_input.dateChanged.connect(lambda: self.refresh())

        today_button = make_button("Today", "secondaryButton")

        today_button.clicked.connect(
            lambda: self.day_input.setDate(QDate.currentDate())
        )

        controls.addWidget(previous_button)

        controls.addWidget(self.day_input)

        controls.addWidget(next_button)

        controls.addWidget(today_button)

        controls.addStretch()

        all_present = make_button("All Present", "secondaryButton")

        all_present.clicked.connect(self.mark_all_present)

        clear_button = make_button("Clear", "secondaryButton")

        clear_button.clicked.connect(self.clear_all)

        save_button = make_button("Save Attendance")

        save_button.clicked.connect(self.save)

        controls.addWidget(all_present)

        controls.addWidget(clear_button)

        controls.addWidget(save_button)

        layout.addLayout(controls)

        chips = QHBoxLayout()

        self.chip_present = make_label("", "chip")

        self.chip_absent = make_label("", "chip")

        self.chip_leave = make_label("", "chip")

        self.chip_pending = make_label("", "chip")

        for chip in (
            self.chip_present,
            self.chip_absent,
            self.chip_leave,
            self.chip_pending,
        ):

            chips.addWidget(chip)

        chips.addStretch()

        layout.addLayout(chips)

        self.daily_table = make_table()

        layout.addWidget(self.daily_table)

        return tab

    def shift_day(self, amount):

        new_date = self.day_input.date().addDays(amount)

        if new_date <= QDate.currentDate():
            self.day_input.setDate(new_date)

    # ----------------------------------------------------------
    # monthly tab
    # ----------------------------------------------------------

    def build_monthly_tab(self):

        tab = QWidget()

        layout = QVBoxLayout(tab)

        layout.setContentsMargins(0, 8, 0, 0)

        layout.setSpacing(12)

        controls = QHBoxLayout()

        self.month_input = QDateEdit(QDate.currentDate())

        self.month_input.setCalendarPopup(True)

        self.month_input.setDisplayFormat("MMMM yyyy")

        self.month_input.dateChanged.connect(lambda: self.refresh())

        export_button = make_button("Export CSV", "secondaryButton")

        export_button.clicked.connect(self.export_monthly)

        controls.addWidget(self.month_input)

        controls.addStretch()

        controls.addWidget(export_button)

        layout.addLayout(controls)

        self.monthly_table = make_table()

        layout.addWidget(self.monthly_table)

        return tab

    # ----------------------------------------------------------
    # refresh
    # ----------------------------------------------------------

    def load(self):

        if self.tabs.currentIndex() == 0:
            self.load_daily()
        else:
            self.load_monthly()

    def selected_day(self):

        return date.fromisoformat(
            self.day_input.date().toString("yyyy-MM-dd")
        )

    def load_daily(self):

        employees = self.db.active_employees()

        marked = self.db.attendance_for_day(self.selected_day())

        self.daily_table.clear()

        self.daily_table.setColumnCount(6)
        self.daily_table.setHorizontalHeaderLabels(["Code", "Name", "Department", "Status", "Check In", "Check Out"])

        self.daily_table.setRowCount(len(employees))

        self.combos = {}
        self.time_edits = {}

        for row_index, employee in enumerate(employees):

            cells = (
                employee["emp_code"],
                employee["name"],
                employee["department"] or "",
            )

            for column, value in enumerate(cells):

                item = QTableWidgetItem(value)

                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, employee["id"])

                self.daily_table.setItem(row_index, column, item)

            combo = QComboBox()

            combo.addItems(ATTENDANCE_STATUSES)

            saved = marked.get(employee["id"], {})
            combo.setCurrentText(saved.get("status") or "Not marked")
            combo.setEnabled(saved.get("status") is None)
            combo.setToolTip("Saved status is locked; times can still be completed." if saved.get("status") else "Select status and enter check-in/out times.")
            combo.currentTextChanged.connect(self.update_chips)
            self.daily_table.setCellWidget(row_index, 3, combo)
            cin = self._make_time_combo(saved.get("check_in"), "Type/select check-in")
            cout = self._make_time_combo(saved.get("check_out"), "Type/select check-out")
            self.daily_table.setCellWidget(row_index, 4, cin)
            self.daily_table.setCellWidget(row_index, 5, cout)
            self.combos[employee["id"]] = combo
            self.time_edits[employee["id"]] = (cin, cout)

        self.update_chips()

    def _make_time_combo(self, saved_value, placeholder):
        """Create a single time editor (like the date picker), not a duplicate-prone dropdown."""
        field = QTimeEdit()
        field.setDisplayFormat("hh:mm AP")
        field.setWrapping(True)
        field.setMinimumWidth(112)
        field.setKeyboardTracking(False)
        field.setToolTip(
            "Set the time using the up/down arrows or type it directly. "
            "A saved time is loaded into this same field and can be updated."
        )

        # Use 00:00 as the empty/unset sentinel, shown as a blank field.
        # This keeps the field visually empty until a time is selected.
        field.setMinimumTime(QTime(0, 0))
        field.setSpecialValueText("")
        field.setTime(QTime(0, 0))

        display_value = self._display_time(saved_value)
        if display_value:
            parsed = None
            for fmt in ("%I:%M %p", "%H:%M:%S", "%H:%M", "%I:%M%p"):
                try:
                    parsed_dt = datetime.strptime(display_value, fmt)
                    parsed = QTime(parsed_dt.hour, parsed_dt.minute)
                    break
                except ValueError:
                    continue
            if parsed is not None:
                field.setTime(parsed)
        return field

    @staticmethod
    def _time_edit_value(field):
        """Return an empty string for an unset field, otherwise a normalized time."""
        current = field.time()
        if current == QTime(0, 0) and field.specialValueText() == "":
            return ""
        return current.toString("hh:mm AP")

    @staticmethod
    def _display_time(value):
        if value in (None, ""): return ""
        if isinstance(value, datetime): value = value.time()
        if isinstance(value, dtime): return value.strftime("%I:%M %p")
        text = str(value).strip()
        for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p"):
            try: return datetime.strptime(text, fmt).strftime("%I:%M %p")
            except ValueError: pass
        return text

    def update_chips(self, *args):

        counts = {
            "Present": 0,
            "Absent": 0,
            "Leave": 0,
            "Not marked": 0,
        }

        for combo in self.combos.values():
            counts[combo.currentText()] += 1

        self.chip_present.setText(f"✔ Present: {counts['Present']}")

        self.chip_absent.setText(f"✖ Absent: {counts['Absent']}")

        self.chip_leave.setText(f"🌴 Leave: {counts['Leave']}")

        self.chip_pending.setText(f"… Not marked: {counts['Not marked']}")

    def load_monthly(self):

        month = self.month_input.date().toString("yyyy-MM")

        rows = self.db.monthly_attendance_summary(month)

        table_rows = []

        for row in rows:

            total = row["present"] + row["absent"] + row["leave_days"]

            percent = (
                f"{row['present'] / total * 100:.0f}%" if total else "-"
            )

            table_rows.append(
                (
                    row["id"],
                    [
                        row["emp_code"],
                        row["name"],
                        row["present"],
                        row["absent"],
                        row["leave_days"],
                        percent,
                    ],
                )
            )

        fill_table(
            self.monthly_table,
            ["Code", "Name", "Present", "Absent", "Leave", "Attendance %"],
            table_rows,
        )

    # ----------------------------------------------------------
    # actions
    # ----------------------------------------------------------

    def mark_all_present(self):

        for combo in self.combos.values():
            combo.setCurrentText("Present")

    def clear_all(self):

        for combo in self.combos.values():
            combo.setCurrentText("Not marked")

    @safe_action
    def save(self):
        day = self.selected_day()
        marks = {}
        for employee_id, combo in self.combos.items():
            cin, cout = self.time_edits[employee_id]
            status = combo.currentText()
            check_in = self._time_edit_value(cin)
            check_out = self._time_edit_value(cout)
            # Entering a time for an unmarked employee means they were present.
            if status == "Not marked" and (check_in or check_out):
                status = "Present"
            if status != "Not marked" or check_in or check_out:
                marks[employee_id] = {"status": status, "check_in": check_in, "check_out": check_out}
        if not marks:
            QMessageBox.information(self, "Nothing to save", "Select a status or enter check-in/check-out times first.")
            return
        try:
            self.db.save_attendance(day, marks)
        except Exception as exc:
            QMessageBox.warning(self, "Attendance save failed", str(exc)); return
        self.db.log("Attendance/time updated", f"Attendance time details saved for {day.isoformat()}", "attendance")
        self.notify("Attendance and time details saved")
        self.on_change()
        self.refresh()

    @safe_action
    def export_monthly(self):

        month = self.month_input.date().toString("yyyy-MM")

        rows = self.db.monthly_attendance_summary(month)

        export_rows_to_csv(
            self,
            f"attendance_{month}",
            ["Code", "Name", "Present", "Absent", "Leave"],
            [
                (
                    row["emp_code"],
                    row["name"],
                    row["present"],
                    row["absent"],
                    row["leave_days"],
                )
                for row in rows
            ],
        )


# ==============================================================
# CALENDAR PAGE
# ==============================================================

class CalendarPage(BasePage):

    def __init__(self, db, on_change, notify):

        super().__init__(db, on_change, notify)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 16, 24, 20)

        layout.setSpacing(12)

        top = QHBoxLayout()

        top.addLayout(
            page_header(
                "Calendar",
                "Leave requests by date (highlighted days have leaves)",
            )
        )

        top.addStretch()

        self.show_all_box = QCheckBox("Show all leaves")

        self.show_all_box.toggled.connect(lambda: self.refresh())

        add_button = make_button("+ Leave Request")

        add_button.clicked.connect(self.add_leave)

        approve_button = make_button("Approve", "successButton")

        approve_button.clicked.connect(lambda: self.set_status("Approved"))

        reject_button = make_button("Reject", "dangerButton")

        reject_button.clicked.connect(lambda: self.set_status("Rejected"))

        top.addWidget(self.show_all_box)

        top.addWidget(add_button)

        top.addWidget(approve_button)

        top.addWidget(reject_button)

        layout.addLayout(top)

        body = QHBoxLayout()

        body.setSpacing(14)

        self.calendar = QCalendarWidget()

        self.calendar.setGridVisible(True)

        self.calendar.setMinimumWidth(430)

        self.calendar.selectionChanged.connect(lambda: self.refresh())

        body.addWidget(self.calendar, 4)

        right = QVBoxLayout()

        self.selected_label = make_label("", "sectionTitle")

        right.addWidget(self.selected_label)

        self.table = make_table()

        right.addWidget(self.table)

        self.empty_label = make_label("", "emptyLabel")

        right.addWidget(self.empty_label)

        body.addLayout(right, 6)

        layout.addLayout(body)

    def highlight_leave_days(self):

        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())

        for row in self.db.leave_ranges():

            color = "#86EFAC" if row["status"] == "Approved" else "#FDE68A"

            text_format = QTextCharFormat()

            text_format.setBackground(QBrush(QColor(color)))

            text_format.setForeground(QBrush(QColor("#0F172A")))

            current = QDate.fromString(row["start_date"], "yyyy-MM-dd")

            end = QDate.fromString(row["end_date"], "yyyy-MM-dd")

            guard = 0

            while current <= end and guard < 366:

                self.calendar.setDateTextFormat(current, text_format)

                current = current.addDays(1)

                guard += 1

    def load(self):

        self.highlight_leave_days()

        selected = self.calendar.selectedDate().toString("yyyy-MM-dd")

        show_all = self.show_all_box.isChecked()

        rows = self.db.leave_rows(selected, show_all)

        if show_all:

            self.selected_label.setText("All leave requests")

        else:

            self.selected_label.setText(
                "Leaves on "
                + self.calendar.selectedDate().toString("dd MMM yyyy")
            )

        fill_table(
            self.table,
            ["Employee", "From", "To", "Reason", "Status"],
            [
                (
                    row["id"],
                    [
                        row["name"],
                        row["start_date"],
                        row["end_date"],
                        row["reason"],
                        row["status"],
                    ],
                )
                for row in rows
            ],
        )

        if rows:
            self.empty_label.setText("")
        elif not self.db.leave_supported():
            self.empty_label.setText(LEAVE_UNSUPPORTED_TEXT)
        else:
            self.empty_label.setText("No leave requests for this selection.")

    @safe_action
    def add_leave(self):

        if not self.db.leave_supported():

            QMessageBox.information(
                self,
                "Leave module",
                LEAVE_UNSUPPORTED_TEXT,
            )

            return

        dialog = LeaveDialog(self.db, self, self.calendar.selectedDate())

        if dialog.exec():

            self.refresh()

            self.on_change()

            self.notify("Leave request created")

    @safe_action
    def set_status(self, status):

        if not self.db.leave_supported():

            QMessageBox.information(
                self,
                "Leave module",
                LEAVE_UNSUPPORTED_TEXT,
            )

            return

        leave_id = selected_id(self.table)

        if leave_id is None:

            QMessageBox.information(
                self,
                "Select",
                "Please select a leave request first.",
            )

            return

        self.db.update_leave_status(leave_id, status)

        self.refresh()

        self.on_change()

        self.notify(f"Leave {status.lower()}")


# ==============================================================
# PAYROLL COMPONENT EDITOR
# ==============================================================

class PayrollAdjustmentDialog(QDialog):
    """Edit additional pay and deductions for one employee/month."""

    def __init__(self, employee, month, absent_days, auto_deduction,
                 current_record=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjust Payroll")
        self.setMinimumWidth(470)
        self.setModal(True)
        self.employee = employee
        self.month = month
        self.auto_deduction = float(auto_deduction or 0)
        current_record = current_record or {}

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(12)
        root.addWidget(make_label("Adjust Payroll", "pageTitle"))
        root.addWidget(make_label(
            f"{employee['name']}  •  {employee['emp_code']}  •  {month}",
            "pageSubtitle"))

        form = QFormLayout()
        self.basic = QDoubleSpinBox()
        self.basic.setRange(0, 100000000)
        self.basic.setDecimals(2)
        self.basic.setPrefix("₹ ")
        self.basic.setValue(float(employee.get("salary") or 0))
        self.basic.setReadOnly(True)

        self.absence = QDoubleSpinBox()
        self.absence.setRange(0, 100000000)
        self.absence.setDecimals(2)
        self.absence.setPrefix("₹ ")
        self.absence.setValue(self.auto_deduction)
        self.absence.setReadOnly(True)

        saved_allowance = float(current_record.get("allowances") or 0)
        saved_total_deduction = float(current_record.get("deductions") or 0)
        # The saved deductions may include custom deductions in addition to absence.
        saved_extra_deduction = max(0.0, saved_total_deduction - self.auto_deduction)
        self.extra_pay = QDoubleSpinBox()
        self.extra_pay.setRange(0, 100000000)
        self.extra_pay.setDecimals(2)
        self.extra_pay.setPrefix("₹ ")
        self.extra_pay.setValue(saved_allowance)
        self.extra_pay.setToolTip("Bonus, incentive, overtime or other additional payment")

        self.extra_deduction = QDoubleSpinBox()
        self.extra_deduction.setRange(0, 100000000)
        self.extra_deduction.setDecimals(2)
        self.extra_deduction.setPrefix("₹ ")
        self.extra_deduction.setValue(saved_extra_deduction)
        self.extra_deduction.setToolTip("Advance, fine or other extra deduction")

        self.net_label = make_label("₹ 0.00", "chip")
        form.addRow("Basic salary:", self.basic)
        form.addRow(f"Absence deduction ({absent_days} day(s)):", self.absence)
        form.addRow("Extra payment / bonus:", self.extra_pay)
        form.addRow("Additional deduction:", self.extra_deduction)
        form.addRow("Estimated net pay:", self.net_label)
        root.addLayout(form)
        note = QLabel("Net pay = Basic salary + Extra payment − Absence deduction − Additional deduction")
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")
        root.addWidget(note)

        self.extra_pay.valueChanged.connect(self.update_net)
        self.extra_deduction.valueChanged.connect(self.update_net)
        self.update_net()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def update_net(self, *_):
        net = max(0.0, self.basic.value() + self.extra_pay.value()
                  - self.absence.value() - self.extra_deduction.value())
        self.net_label.setText(format_inr(net))

    def values(self):
        return {
            "basic_salary": self.basic.value(),
            "allowances": self.extra_pay.value(),
            "deductions": self.absence.value() + self.extra_deduction.value(),
        }


# ==============================================================
# PAYROLL PAGE
# ==============================================================

class PayrollPage(BasePage):

    def __init__(self, db, on_change, notify):

        super().__init__(db, on_change, notify)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 16, 24, 20)

        layout.setSpacing(12)

        top = QHBoxLayout()

        top.addLayout(
            page_header(
                "Payroll",
                "Net pay = salary minus absence deduction "
                f"({WORKING_DAYS_PER_MONTH}-day basis)",
            )
        )

        top.addStretch()

        self.month_input = QDateEdit(QDate.currentDate())

        self.month_input.setCalendarPopup(True)

        self.month_input.setDisplayFormat("MMMM yyyy")

        self.month_input.dateChanged.connect(lambda: self.refresh())

        top.addWidget(self.month_input)

        layout.addLayout(top)

        # ---------------- summary chips ----------------

        chips = QHBoxLayout()

        self.chip_payable = make_label("", "chip")

        self.chip_paid = make_label("", "chip")

        self.chip_pending = make_label("", "chip")

        for chip in (self.chip_payable, self.chip_paid, self.chip_pending):
            chips.addWidget(chip)

        chips.addStretch()

        layout.addLayout(chips)

        # ---------------- buttons ----------------

        buttons = QHBoxLayout()

        process_all = make_button("Process All Pending")

        process_all.clicked.connect(self.process_all)

        process_one = make_button("Process Selected", "secondaryButton")

        process_one.clicked.connect(self.process_selected)

        adjust_button = make_button("Adjust Salary / Deduction", "secondaryButton")

        adjust_button.clicked.connect(self.adjust_selected)

        slip_button = make_button("Payslip", "secondaryButton")

        slip_button.clicked.connect(self.show_payslip)

        revert_button = make_button("Revert Selected", "dangerButton")

        revert_button.clicked.connect(self.revert_selected)

        export_button = make_button("Export CSV", "secondaryButton")

        export_button.clicked.connect(self.export_csv)

        buttons.addWidget(process_all)

        buttons.addWidget(process_one)

        buttons.addWidget(adjust_button)

        buttons.addWidget(slip_button)

        buttons.addStretch()

        buttons.addWidget(revert_button)

        buttons.addWidget(export_button)

        layout.addLayout(buttons)

        self.table = make_table()

        layout.addWidget(self.table)

    # ----------------------------------------------------------

    def month(self):

        return self.month_input.date().toString("yyyy-MM")

    def build_rows(self):
        """Returns a list of dicts, one per active employee."""

        month = self.month()

        paid_map = self.db.payroll_map(month)

        absent_map = self.db.absent_days_map(month)

        result = []

        for employee in self.db.active_employees():

            absent = absent_map.get(employee["id"], 0)

            auto_deduction, base_net = calculate_net_salary(
                employee["salary"],
                absent,
            )

            record = paid_map.get(employee["id"])
            allowances = float(record.get("allowances", 0) or 0) if record else 0.0
            # If a payroll record exists, use its stored components. This preserves
            # HR-entered deductions/bonus after refresh and before payment processing.
            deduction = float(record.get("deductions", auto_deduction) or 0) if record else auto_deduction
            net = max(0.0, round(float(employee["salary"] or 0) + allowances - deduction, 2))
            paid = bool(record and record["paid"])

            result.append(
                {
                    "id": employee["id"],
                    "code": employee["emp_code"],
                    "name": employee["name"],
                    "department": employee["department"] or "",
                    "salary": employee["salary"] or 0,
                    "absent": absent,
                    "deduction": deduction,
                    "auto_deduction": auto_deduction,
                    "allowances": allowances,
                    "net": net,
                    "paid": paid,
                    "paid_amount": record["amount"] if paid else None,
                    "processed_on": record["processed_on"] if paid else "-",
                }
            )

        return result

    def load(self):

        rows = self.build_rows()

        fill_table(
            self.table,
            [
                "Code",
                "Name",
                "Department",
                "Base Salary",
                "Absent",
                "Deduction",
                "Net Pay",
                "Status",
                "Processed on",
            ],
            [
                (
                    row["id"],
                    [
                        row["code"],
                        row["name"],
                        row["department"],
                        format_inr(row["salary"]),
                        row["absent"],
                        format_inr(row["deduction"]),
                        format_inr(
                            row["paid_amount"] if row["paid"] else row["net"]
                        ),
                        "Paid" if row["paid"] else "Pending",
                        row["processed_on"],
                    ],
                )
                for row in rows
            ],
        )

        payable = sum(row["net"] for row in rows)

        paid_total = sum(
            row["paid_amount"] or 0 for row in rows if row["paid"]
        )

        pending = sum(1 for row in rows if not row["paid"])

        self.chip_payable.setText(f"Total payable: {format_inr(payable)}")

        self.chip_paid.setText(f"Paid: {format_inr(paid_total)}")

        self.chip_pending.setText(f"Pending employees: {pending}")

    # ----------------------------------------------------------

    @safe_action
    def adjust_selected(self):
        employee_id = selected_id(self.table)
        if employee_id is None:
            QMessageBox.information(self, "Select employee", "Please select an employee first.")
            return

        row = next((item for item in self.build_rows() if item["id"] == employee_id), None)
        employee = self.db.get_employee(employee_id)
        if not row or not employee:
            QMessageBox.warning(self, "Payroll", "Employee payroll details could not be loaded.")
            return

        existing = self.db.payroll_record(employee_id, self.month())
        dialog = PayrollAdjustmentDialog(
            employee=employee,
            month=self.month(),
            absent_days=row["absent"],
            auto_deduction=row["auto_deduction"],
            current_record=existing,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.values()
        self.db.save_payroll_components(
            employee_id,
            self.month(),
            values["basic_salary"],
            values["allowances"],
            values["deductions"],
        )
        self.db.log(
            "Payroll adjusted",
            f"{employee['name']} - {self.month()} - "
            f"Extra pay {format_inr(values['allowances'])}, "
            f"deductions {format_inr(values['deductions'])}",
            "payroll",
        )
        self.refresh()
        self.on_change()
        self.notify("Payroll adjustments saved")

    @safe_action
    def process_all(self):

        pending = [row for row in self.build_rows() if not row["paid"]]

        if not pending:

            QMessageBox.information(
                self,
                "Payroll",
                "No pending payroll for this month.",
            )

            return

        total = sum(row["net"] for row in pending)

        answer = QMessageBox.question(
            self,
            "Confirm payroll",
            f"Process payroll for {len(pending)} employee(s)?\n"
            f"Total: {format_inr(total)}",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.process_payroll(pending, self.month())

        label = self.month_input.date().toString("MMMM yyyy")

        self.db.log(
            "Payroll processed",
            f"{label} - Successfully completed",
            "payroll",
        )

        self.refresh()

        self.on_change()

        self.notify("Payroll processed")

    @safe_action
    def process_selected(self):

        employee_id = selected_id(self.table)

        if employee_id is None:

            QMessageBox.information(
                self,
                "Select",
                "Please select an employee first.",
            )

            return

        target = [
            row for row in self.build_rows() if row["id"] == employee_id
        ]

        if not target or target[0]["paid"]:

            QMessageBox.information(
                self,
                "Payroll",
                "Already processed for this month.",
            )

            return

        self.db.process_payroll(target, self.month())

        self.db.log(
            "Payroll processed",
            f"{target[0]['name']} - "
            f"{self.month_input.date().toString('MMMM yyyy')}",
            "payroll",
        )

        self.refresh()

        self.on_change()

        self.notify("Payroll processed")

    @safe_action
    def revert_selected(self):

        employee_id = selected_id(self.table)

        if employee_id is None:

            QMessageBox.information(
                self,
                "Select",
                "Please select an employee first.",
            )

            return

        if self.db.payroll_record(employee_id, self.month()) is None:

            QMessageBox.information(
                self,
                "Payroll",
                "This employee is not paid for this month.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Revert payment",
            "Remove this payment record?",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.delete_payroll(employee_id, self.month())

        self.refresh()

        self.on_change()

        self.notify("Payment reverted")

    @safe_action
    def show_payslip(self):

        employee_id = selected_id(self.table)

        if employee_id is None:

            QMessageBox.information(
                self,
                "Select",
                "Please select an employee first.",
            )

            return

        PayslipDialog(self.db, employee_id, self.month(), self).exec()

    @safe_action
    def export_csv(self):

        rows = self.build_rows()

        export_rows_to_csv(
            self,
            f"payroll_{self.month()}",
            [
                "Code",
                "Name",
                "Department",
                "Base Salary",
                "Absent Days",
                "Deduction",
                "Net Pay",
                "Status",
            ],
            [
                (
                    row["code"],
                    row["name"],
                    row["department"],
                    row["salary"],
                    row["absent"],
                    row["deduction"],
                    row["paid_amount"] if row["paid"] else row["net"],
                    "Paid" if row["paid"] else "Pending",
                )
                for row in rows
            ],
        )


# ==============================================================
# PERFORMANCE PAGE
# ==============================================================

class PerformancePage(BasePage):

    def __init__(self, db, on_change, notify):

        super().__init__(db, on_change, notify)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 16, 24, 20)

        layout.setSpacing(12)

        top = QHBoxLayout()

        top.addLayout(
            page_header("Performance", "Employee reviews and ratings")
        )

        top.addStretch()

        self.employee_filter = QComboBox()

        self.employee_filter.setMinimumWidth(200)

        self.employee_filter.currentIndexChanged.connect(
            lambda: self.guard(self.load_page, False)
        )

        add_button = make_button("+ Add Review")

        add_button.clicked.connect(self.add_review)

        delete_button = make_button("Delete", "dangerButton")

        delete_button.clicked.connect(self.delete_review)

        export_button = make_button("Export CSV", "secondaryButton")

        export_button.clicked.connect(self.export_csv)

        top.addWidget(self.employee_filter)

        top.addWidget(add_button)

        top.addWidget(delete_button)

        top.addWidget(export_button)

        layout.addLayout(top)

        body = QHBoxLayout()

        body.setSpacing(14)

        self.table = make_table()

        body.addWidget(self.table, 7)

        side = QFrame()

        side.setObjectName("panel")

        side_layout = QVBoxLayout(side)

        side_layout.setContentsMargins(18, 16, 18, 16)

        side_layout.addWidget(make_label("Ranking", "sectionTitle"))

        self.ranking_layout = QVBoxLayout()

        self.ranking_layout.setSpacing(10)

        side_layout.addLayout(self.ranking_layout)

        side_layout.addStretch()

        self.average_label = make_label("", "pageSubtitle")

        side_layout.addWidget(self.average_label)

        body.addWidget(side, 3)

        layout.addLayout(body)

    def reload_filter(self):

        self.employee_filter.blockSignals(True)

        current = self.employee_filter.currentData()

        self.employee_filter.clear()

        self.employee_filter.addItem("All employees", None)

        for employee in sorted(
            self.db.all_employees(),
            key=lambda item: item["name"].lower(),
        ):

            self.employee_filter.addItem(employee["name"], employee["id"])

        index = self.employee_filter.findData(current)

        self.employee_filter.setCurrentIndex(index if index >= 0 else 0)

        self.employee_filter.blockSignals(False)

    def fetch_rows(self):

        return self.db.reviews(self.employee_filter.currentData())

    def load(self):

        self.load_page(True)

    def load_page(self, reload_filter=True):

        if reload_filter:
            self.reload_filter()

        rows = self.fetch_rows()

        fill_table(
            self.table,
            ["Employee", "Department", "Rating", "Remarks", "Date"],
            [
                (
                    row["id"],
                    [
                        row["name"],
                        row["department"],
                        f"{row['rating']:.1f} / 10",
                        row["remarks"],
                        row["review_date"],
                    ],
                )
                for row in rows
            ],
        )

        clear_layout(self.ranking_layout)

        ranking = self.db.top_performers(8)

        if not ranking:

            self.ranking_layout.addWidget(
                make_label("No reviews yet.", "emptyLabel")
            )

        for person in ranking:

            holder = QWidget()

            box = QVBoxLayout(holder)

            box.setContentsMargins(0, 0, 0, 0)

            box.setSpacing(3)

            line = QHBoxLayout()

            line.addWidget(make_label(person["name"], "actTitle"))

            line.addStretch()

            line.addWidget(
                make_label(f"{person['rating']:.1f}", "statNote")
            )

            bar = QProgressBar()

            bar.setRange(0, 100)

            bar.setValue(int(person["rating"] * 10))

            bar.setFixedHeight(8)

            box.addLayout(line)

            box.addWidget(bar)

            self.ranking_layout.addWidget(holder)

        average = self.db.average_rating()

        self.average_label.setText(
            f"Overall average: {average:.2f} / 10"
            if average
            else "No ratings recorded."
        )

    @safe_action
    def add_review(self):

        if not self.db.active_employees():

            QMessageBox.information(
                self,
                "No employees",
                "Please add an employee first.",
            )

            return

        dialog = ReviewDialog(self.db, self)

        if dialog.exec():

            self.refresh()

            self.on_change()

            self.notify("Review added")

    @safe_action
    def delete_review(self):

        review_id = selected_id(self.table)

        if review_id is None:

            QMessageBox.information(
                self,
                "Select",
                "Please select a review first.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Delete review",
            "Delete the selected review?",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.delete_review(review_id)

        self.refresh()

        self.on_change()

        self.notify("Review deleted")

    @safe_action
    def export_csv(self):

        rows = self.fetch_rows()

        export_rows_to_csv(
            self,
            "performance",
            ["Employee", "Department", "Rating", "Remarks", "Date"],
            [
                (
                    row["name"],
                    row["department"],
                    row["rating"],
                    row["remarks"],
                    row["review_date"],
                )
                for row in rows
            ],
        )


# ==============================================================
# REPORTS PAGE
# ==============================================================

class ReportsPage(BasePage):

    REPORT_NAMES = [
        "Employees",
        "Attendance",
        "Payroll",
        "Performance",
        "Leaves",
    ]

    def __init__(self, db, on_change, notify):

        super().__init__(db, on_change, notify)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(24, 16, 24, 20)

        layout.setSpacing(12)

        layout.addLayout(
            page_header(
                "Reports",
                "Organization summary and data export",
            )
        )

        self.summary_label = make_label("", "summaryBox")

        self.summary_label.setWordWrap(True)

        layout.addWidget(self.summary_label)

        # ---------------- export buttons ----------------

        export_panel = QFrame()

        export_panel.setObjectName("panel")

        export_layout = QGridLayout(export_panel)

        export_layout.setContentsMargins(18, 16, 18, 16)

        export_layout.setHorizontalSpacing(14)

        export_layout.setVerticalSpacing(10)

        for index, name in enumerate(self.REPORT_NAMES):

            label = make_label(f"{name} report", "fieldLabel")

            button = make_button("Export CSV", "secondaryButton")

            button.clicked.connect(
                lambda checked=False, n=name: self.export(n)
            )

            export_layout.addWidget(label, index, 0)

            export_layout.addWidget(button, index, 1)

        layout.addWidget(export_panel)

        # ---------------- payroll by month ----------------

        layout.addWidget(make_label("Payroll - last 6 months", "sectionTitle"))

        self.payroll_table = make_table()

        self.payroll_table.setMaximumHeight(260)

        layout.addWidget(self.payroll_table)

        layout.addStretch()

    def load(self):

        db = self.db

        this_month = month_key(date.today())

        average = db.average_rating()

        counts = db.employee_counts()

        self.summary_label.setText(
            f"Employees: {counts['total']}"
            "   |   "
            f"Active: {counts['active']}"
            "   |   "
            f"Pending leaves: {db.pending_leave_count()}\n"
            f"Payroll this month: {format_inr(db.payroll_total(this_month))}"
            "   |   "
            f"Avg performance: {f'{average:.2f}' if average else 'N/A'}"
        )

        rows = db.payroll_by_month(6)

        fill_table(
            self.payroll_table,
            ["Month", "Employees paid", "Total paid"],
            [
                (
                    row["month"],
                    [
                        row["month"],
                        row["people"],
                        format_inr(row["total"]),
                    ],
                )
                for row in rows
            ],
        )

    @safe_action
    def export(self, name):

        if name == "Leaves" and not self.db.leave_supported():

            QMessageBox.information(
                self,
                "Leave module",
                LEAVE_UNSUPPORTED_TEXT,
            )

            return

        headers, rows = self.db.export_rows(name)

        export_rows_to_csv(self, name.lower(), headers, rows)


# ==============================================================
# MAIN WINDOW
# ==============================================================

class HRQualityIssuesPage(QWidget):
    """HR-only quality issue workflow.

    Shows issues assigned to the logged-in HR Manager and allows status,
    root-cause and corrective-action updates. Admin remains responsible for
    creating/assigning issues in the TQM module.
    """

    def __init__(self, refresh_all_callback, toast_callback, parent=None):
        super().__init__(parent)
        self.refresh_all_callback = refresh_all_callback
        self.toast = toast_callback
        self.current_user = Session.get_user()
        self.build_ui()
        self.refresh()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        title = QLabel("⚠  Assigned Quality Issues")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        subtitle = QLabel(
            "Review quality issues assigned to you, investigate the root cause, "
            "apply corrective action and update the status."
        )
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(subtitle)

        self.summary = QLabel("0 assigned issues")
        self.summary.setObjectName("qualitySummary")
        root.addWidget(self.summary)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Issue ID", "Issue", "Category", "Priority", "Status",
            "Root Cause", "Corrective Action", "Action"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 105)
        self.table.setColumnWidth(7, 95)
        root.addWidget(self.table, 1)

        refresh = QPushButton("↻  Refresh")
        refresh.setFixedWidth(120)
        refresh.clicked.connect(self.refresh)
        root.addWidget(refresh, 0, Qt.AlignmentFlag.AlignRight)

        self.setStyleSheet("""
            QLabel#pageTitle { font-size: 22px; font-weight: 900; }
            QLabel#pageSubtitle { color: #94A3B8; font-size: 11px; }
            QLabel#qualitySummary { color: #60A5FA; font-size: 12px; font-weight: 800; }
            QTableWidget { font-size: 10px; border: 1px solid #26364A; }
            QHeaderView::section { padding: 8px; font-weight: 800; }
            QPushButton { padding: 8px 16px; border-radius: 7px; font-weight: 800; }
        """)

    def refresh(self):
        self.current_user = Session.get_user()
        self.table.setRowCount(0)
        if not self.current_user:
            self.summary.setText("Please login")
            return

        db = SessionLocal()
        try:
            user_id = getattr(self.current_user, "id", None)
            issues = []
            if user_id is not None:
                issues = (db.query(QualityIssue)
                          .filter(QualityIssue.assigned_to == user_id)
                          .order_by(QualityIssue.issue_date.desc())
                          .all())

            self.summary.setText(f"{len(issues)} assigned issue(s)")
            self.table.setRowCount(len(issues))
            for row, issue in enumerate(issues):
                values = [
                    getattr(issue, "issue_id", ""),
                    getattr(issue, "title", ""),
                    getattr(issue, "category", ""),
                    getattr(issue, "priority", ""),
                    getattr(issue, "status", ""),
                    getattr(issue, "root_cause", "") or "Not investigated",
                    getattr(issue, "corrective_action", "") or "Pending",
                ]
                for col, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setToolTip(str(value))
                    self.table.setItem(row, col, item)

                button = QPushButton("Update")
                button.clicked.connect(lambda checked=False, x=issue: self.update_issue(x))
                self.table.setCellWidget(row, 7, button)
        except SQLAlchemyError as error:
            logger.exception("Unable to load assigned quality issues")
            self.summary.setText("Unable to load quality issues")
            self.toast(f"Quality issue load failed: {error}")
        finally:
            db.close()

    def update_issue(self, issue):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Update Quality Issue - {getattr(issue, 'issue_id', '')}")
        dialog.setMinimumSize(650, 500)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        status = QComboBox()
        status.addItems(["Open", "In Progress", "Resolved", "Closed"])
        status.setCurrentText(str(getattr(issue, "status", "Open")))

        root_cause = QTextEdit()
        root_cause.setPlainText(str(getattr(issue, "root_cause", "") or ""))
        corrective = QTextEdit()
        corrective.setPlainText(str(getattr(issue, "corrective_action", "") or ""))

        form.addRow("Status", status)
        form.addRow("Root Cause", root_cause)
        form.addRow("Corrective Action", corrective)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        db = SessionLocal()
        try:
            db_issue = db.query(QualityIssue).filter(QualityIssue.id == issue.id).first()
            if not db_issue:
                raise ValueError("Quality issue was not found.")
            db_issue.status = status.currentText()
            db_issue.root_cause = root_cause.toPlainText().strip()
            db_issue.corrective_action = corrective.toPlainText().strip()
            db.commit()
            self.toast("Quality issue updated successfully")
            self.refresh()
        except Exception as error:
            db.rollback()
            logger.exception("Unable to update quality issue")
            QMessageBox.critical(self, "Update Failed", str(error))
        finally:
            db.close()


class HRDashboardWindow(QMainWindow):

    NAV_ITEMS = [
        ("🏠", "Dashboard"),
        ("📅", "Calendar"),
        ("👥", "Employees"),
        ("🕒", "Attendance"),
        ("₹", "Payroll"),
        ("★", "Performance"),
        ("📊", "Reports"),
        ("⚠", "Quality Issues"),
    ]

    def __init__(self):

        super().__init__()

        # ------------------------------------------------------
        # Window settings
        # ------------------------------------------------------

        self.setWindowTitle(f"{APP_TITLE} - HR Dashboard")

        self.resize(1440, 840)

        self.setMinimumSize(1180, 720)

        # ------------------------------------------------------
        # Application state
        # ------------------------------------------------------

        self.db = HRDataService()

        self.settings = QSettings(
            "EmployeeManagementSystem",
            "EmployeeManagementSystem",
        )

        self.dark_mode = self.settings.value(
            "hr_dark_mode",
            False,
            type=bool,
        )

        self.login_window = None

        # ------------------------------------------------------
        # Build UI
        # ------------------------------------------------------

        self.setup_ui()

        self.setup_shortcuts()

        self.apply_theme()

        self.go_to(0)

        # ------------------------------------------------------
        # Live clock
        # ------------------------------------------------------

        self.clock_timer = QTimer(self)

        self.clock_timer.timeout.connect(self.update_clock)

        self.clock_timer.start(15000)

        self.update_clock()

    # ==========================================================
    # UI
    # ==========================================================

    def setup_ui(self):

        root = QWidget()

        root.setObjectName("root")

        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)

        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)

        main_layout.addWidget(self.build_sidebar())

        right_layout = QVBoxLayout()

        right_layout.setSpacing(0)

        right_layout.addWidget(self.build_topbar())

        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(
            self.db,
            self.refresh_all,
            self.toast,
            self.go_to,
            self.open_activity,
        )

        self.calendar_page = CalendarPage(
            self.db, self.refresh_all, self.toast
        )

        self.employees_page = EmployeesPage(
            self.db, self.refresh_all, self.toast
        )

        self.attendance_page = AttendancePage(
            self.db, self.refresh_all, self.toast
        )

        self.payroll_page = PayrollPage(
            self.db, self.refresh_all, self.toast
        )

        self.performance_page = PerformancePage(
            self.db, self.refresh_all, self.toast
        )

        self.reports_page = ReportsPage(
            self.db, self.refresh_all, self.toast
        )

        self.quality_issues_page = HRQualityIssuesPage(
            self.refresh_all, self.toast
        )

        self.pages = [
            self.dashboard_page,
            self.calendar_page,
            self.employees_page,
            self.attendance_page,
            self.payroll_page,
            self.performance_page,
            self.reports_page,
            self.quality_issues_page,
        ]

        for page in self.pages:
            self.stack.addWidget(page)

        right_layout.addWidget(self.stack)

        main_layout.addLayout(right_layout, 1)

        self.statusBar().setSizeGripEnabled(False)

    def build_sidebar(self):

        sidebar = QFrame()

        sidebar.setObjectName("sidebar")

        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)

        layout.setContentsMargins(16, 18, 16, 14)

        layout.setSpacing(4)

        # ---------------- brand ----------------

        brand = QHBoxLayout()

        logo = QLabel("EMS")

        logo.setObjectName("brandLogo")

        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo.setFixedSize(46, 46)

        brand_name = QLabel("Employee\nManagement System")

        brand_name.setObjectName("brandName")

        brand.addWidget(logo)

        brand.addSpacing(8)

        brand.addWidget(brand_name)

        brand.addStretch()

        layout.addLayout(brand)

        layout.addSpacing(14)

        # ---------------- user box ----------------

        username, role = get_session_info()

        user_box = QFrame()

        user_box.setObjectName("userBox")

        user_layout = QHBoxLayout(user_box)

        user_layout.setContentsMargins(12, 10, 12, 10)

        avatar = QLabel(username[:1].upper())

        avatar.setObjectName("avatar")

        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        avatar.setFixedSize(44, 44)

        user_text = QVBoxLayout()

        user_text.setSpacing(0)

        user_text.addWidget(make_label(username, "userName"))

        user_text.addWidget(make_label(role, "userRole"))

        user_text.addWidget(make_label("● Online", "online"))

        user_layout.addWidget(avatar)

        user_layout.addLayout(user_text)

        layout.addWidget(user_box)

        layout.addSpacing(12)

        # ---------------- navigation ----------------

        self.nav_buttons = []

        for index, (icon, label) in enumerate(self.NAV_ITEMS):

            button = QPushButton(f"{icon}    {label}")

            button.setObjectName("navButton")

            button.setCheckable(True)

            button.setCursor(Qt.CursorShape.PointingHandCursor)

            button.clicked.connect(
                lambda checked=False, i=index: self.go_to(i)
            )

            layout.addWidget(button)

            self.nav_buttons.append(button)

        layout.addStretch()

        # ---------------- bottom ----------------

        logout_button = QPushButton("⎋    Logout")

        logout_button.setObjectName("logoutButton")

        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)

        logout_button.clicked.connect(self.logout)

        layout.addWidget(logout_button)

        footer = make_label(f"{APP_TITLE}  v1.0", "userRole")

        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(footer)

        return sidebar

    def build_topbar(self):

        topbar = QFrame()

        topbar.setObjectName("topbar")

        layout = QHBoxLayout(topbar)

        layout.setContentsMargins(24, 14, 24, 6)

        self.search_input = QLineEdit()

        self.search_input.setObjectName("searchBox")

        self.search_input.setPlaceholderText(
            "🔍  Search employees, departments, "
            "or anything...  (press Enter)"
        )

        self.search_input.setMaximumWidth(540)

        self.search_input.returnPressed.connect(self.global_search)

        layout.addWidget(self.search_input)

        layout.addStretch()

        self.bell_button = QPushButton("🔔")

        self.bell_button.setObjectName("iconButton")

        self.bell_button.setFixedSize(38, 38)

        self.bell_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.bell_button.setToolTip("Pending leave requests")

        self.bell_button.clicked.connect(self.show_notifications)

        self.theme_button = QPushButton()

        self.theme_button.setObjectName("iconButton")

        self.theme_button.setFixedSize(38, 38)

        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.theme_button.setToolTip("Toggle dark / light theme")

        self.theme_button.clicked.connect(self.toggle_theme)

        date_box = QVBoxLayout()

        date_box.setSpacing(0)

        self.date_label = make_label("", "dateLabel")

        self.time_label = make_label("", "timeLabel")

        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        date_box.addWidget(self.date_label)

        date_box.addWidget(self.time_label)

        layout.addWidget(self.bell_button)

        layout.addWidget(self.theme_button)

        layout.addSpacing(8)

        layout.addLayout(date_box)

        return topbar

    def setup_shortcuts(self):

        QShortcut(
            QKeySequence("Ctrl+F"),
            self,
            activated=self.focus_search,
        )

        QShortcut(
            QKeySequence("F5"),
            self,
            activated=self.reload_current,
        )

        for index in range(len(self.NAV_ITEMS)):

            QShortcut(
                QKeySequence(f"Ctrl+{index + 1}"),
                self,
                activated=lambda i=index: self.go_to(i),
            )

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def go_to(self, index):

        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

        self.stack.setCurrentIndex(index)

        self.pages[index].refresh()

        self.update_bell()

    def reload_current(self):

        self.pages[self.stack.currentIndex()].refresh()

        self.update_bell()

        self.toast("Refreshed")

    def refresh_all(self):
        """Called by pages after data changes."""

        self.dashboard_page.refresh()
        self.quality_issues_page.refresh()

        self.update_bell()

    def focus_search(self):

        self.search_input.setFocus()

        self.search_input.selectAll()

    def global_search(self):

        text = self.search_input.text().strip()

        if not text:
            return

        self.go_to(2)

        self.employees_page.set_filter(text)

    def toast(self, message):

        self.statusBar().showMessage(message, 3500)

    # ==========================================================
    # NOTIFICATIONS / ACTIVITY
    # ==========================================================

    def update_bell(self):

        try:
            count = self.db.pending_leave_count()
        except SQLAlchemyError as exc:
            show_db_error(self, exc)
            count = 0

        if count:

            self.bell_button.setText(f"🔔 {count}")

            self.bell_button.setFixedWidth(64)

        else:

            self.bell_button.setText("🔔")

            self.bell_button.setFixedWidth(38)

    def show_notifications(self):

        if not self.db.leave_supported():

            QMessageBox.information(
                self,
                "Notifications",
                LEAVE_UNSUPPORTED_TEXT,
            )

            return

        try:
            pending = self.db.pending_leave_count()
        except SQLAlchemyError as exc:
            show_db_error(self, exc)
            return

        if pending == 0:

            QMessageBox.information(
                self,
                "Notifications",
                "You're all caught up. There are no pending requests.",
            )

            return

        dialog = NotificationDialog(self.db, self)

        dialog.exec()

        if dialog.changed:

            self.reload_current()

            self.refresh_all()

    def open_activity(self):

        ActivityDialog(self.db, self).exec()

    # ==========================================================
    # CLOCK
    # ==========================================================

    def update_clock(self):

        now = datetime.now()

        self.date_label.setText(now.strftime("%a, %d %b %Y"))

        self.time_label.setText(now.strftime("%I:%M %p"))

    # ==========================================================
    # THEME
    # ==========================================================

    def toggle_theme(self):

        self.dark_mode = not self.dark_mode

        self.settings.setValue("hr_dark_mode", self.dark_mode)

        self.apply_theme()

        self.dashboard_page.refresh()

    def apply_theme(self):

        palette = DARK_THEME if self.dark_mode else LIGHT_THEME

        self.setStyleSheet(STYLE_TEMPLATE.substitute(palette))

        self.theme_button.setText("☀" if self.dark_mode else "🌙")

        self.dashboard_page.dark = self.dark_mode

    # ==========================================================
    # LOGOUT
    # ==========================================================

    def logout(self):

        answer = QMessageBox.question(
            self,
            "Logout",
            "Do you want to log out?",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            Session.logout()
        except Exception as exc:
            logger.exception("Session.logout() failed")
            QMessageBox.warning(
                self,
                "Logout failed",
                f"Could not clear the session:\n{exc}",
            )
            return

        try:
            from ui.login import LoginWindow
        except ImportError as exc:
            logger.exception("Could not import ui.login.LoginWindow")
            QMessageBox.critical(
                self,
                "Logout",
                f"Could not open the login window:\n{exc}",
            )
            return

        self.login_window = LoginWindow()

        self.login_window.show()

        self.close()


# ==============================================================
# STANDALONE RUN (for testing this window on its own)
# Run from the project root:  python -m ui.hr_dashboard
# ==============================================================

if __name__ == "__main__":

    import sys

    app = QApplication(sys.argv)

    window = HRDashboardWindow()

    window.show()

    sys.exit(app.exec())
