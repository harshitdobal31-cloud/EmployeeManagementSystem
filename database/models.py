from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


# ============================================================
# USER
# ============================================================

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Employee"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# EMPLOYEE
# ============================================================

class Employee(Base):

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # Basic Information
    employee_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    date_of_birth: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    # Contact
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    # Employment
    department: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    designation: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    employment_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    joining_date: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    salary: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    # Bank
    bank_account: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    # Emergency Contact
    emergency_contact_name: Mapped[str] = mapped_column(
        String(150),
        nullable=True
    )

    emergency_contact_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    # Profile
    profile_photo: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# ============================================================
# ATTENDANCE
# ============================================================

class Attendance(Base):

    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    attendance_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    check_in: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    check_out: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    working_hours: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Present"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# PAYROLL
# ============================================================

class Payroll(Base):

    __tablename__ = "payroll"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    payroll_month: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    basic_salary: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    allowances: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    deductions: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    net_salary: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Processed"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# PERFORMANCE
# ============================================================

class Performance(Base):

    __tablename__ = "performance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    review_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    percentage: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    comments: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

class Notification(Base):

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    is_read: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(Base):

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# DEPARTMENT
# ============================================================

class Department(Base):

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(300),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# PAYROLL DETAILS
# ============================================================

class PayrollDetail(Base):

    __tablename__ = "payroll_details"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    payroll_id: Mapped[int] = mapped_column(
        ForeignKey("payroll.id"),
        nullable=False
    )

    component_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    component_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# PERFORMANCE LOG
# ============================================================

class PerformanceLog(Base):

    __tablename__ = "performance_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False
    )

    review_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    comments: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# CALENDAR EVENT
# ============================================================

class CalendarEvent(Base):

    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    event_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# QUALITY ISSUE
# ============================================================

class QualityIssue(Base):

    __tablename__ = "quality_issues"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    issue_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Medium"
    )

    reported_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    assigned_to: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    issue_date: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Open"
    )

    root_cause: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    corrective_action: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    resolution_date: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# IMPROVEMENT ACTION
# ============================================================

class ImprovementAction(Base):

    __tablename__ = "improvement_actions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    problem: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    root_cause: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    corrective_action: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    preventive_action: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    responsible_person: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Medium"
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Open"
    )

    due_date: Mapped[str] = mapped_column(
        String(20),
        nullable=True
    )

    pdca_stage: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        default="Plan"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# APP SETTINGS
# ============================================================

class AppSetting(Base):

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    setting_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    setting_value: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    description: Mapped[str] = mapped_column(
        String(300),
        nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    # ============================================================
# LEAVE REQUEST
# ============================================================

class LeaveRequest(Base):

    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    employee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    leave_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    start_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    end_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="Pending"
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )