from database.database import SessionLocal
from database.models import (
    Employee,
    Attendance,
    Payroll,
    Performance,
    Department,
    QualityIssue,
    AuditLog,
)


# ============================================================
# EMPLOYEE REPORT
# ============================================================

def get_employee_report(
    department=None,
    status=None,
    employment_type=None,
):
    db = SessionLocal()

    try:
        query = db.query(Employee)

        if department and department != "All":
            query = query.filter(
                Employee.department == department
            )

        if status and status != "All":
            query = query.filter(
                Employee.status == status
            )

        if employment_type and employment_type != "All":
            query = query.filter(
                Employee.employment_type == employment_type
            )

        return query.order_by(
            Employee.id.desc()
        ).all()

    finally:
        db.close()


# ============================================================
# ATTENDANCE REPORT
# ============================================================

def get_attendance_report(
    employee_id=None,
    status=None,
    from_date=None,
    to_date=None,
):
    db = SessionLocal()

    try:
        query = (
            db.query(
                Attendance,
                Employee
            )
            .join(
                Employee,
                Attendance.employee_id == Employee.id
            )
        )

        if employee_id:
            query = query.filter(
                Attendance.employee_id == employee_id
            )

        if status and status != "All":
            query = query.filter(
                Attendance.status == status
            )

        if from_date:
            query = query.filter(
                Attendance.attendance_date >= from_date
            )

        if to_date:
            query = query.filter(
                Attendance.attendance_date <= to_date
            )

        return query.order_by(
            Attendance.attendance_date.desc()
        ).all()

    finally:
        db.close()


# ============================================================
# PAYROLL REPORT
# ============================================================

def get_payroll_report(
    employee_id=None,
    payroll_month=None,
    status=None,
):
    db = SessionLocal()

    try:
        query = (
            db.query(
                Payroll,
                Employee
            )
            .join(
                Employee,
                Payroll.employee_id == Employee.id
            )
        )

        if employee_id:
            query = query.filter(
                Payroll.employee_id == employee_id
            )

        if payroll_month:
            query = query.filter(
                Payroll.payroll_month == payroll_month
            )

        if status and status != "All":
            query = query.filter(
                Payroll.status == status
            )

        return query.order_by(
            Payroll.id.desc()
        ).all()

    finally:
        db.close()


# ============================================================
# PERFORMANCE REPORT
# ============================================================

def get_performance_report(
    employee_id=None,
    category=None,
    from_date=None,
    to_date=None,
):
    db = SessionLocal()

    try:
        query = (
            db.query(
                Performance,
                Employee
            )
            .join(
                Employee,
                Performance.employee_id == Employee.id
            )
        )

        if employee_id:
            query = query.filter(
                Performance.employee_id == employee_id
            )

        if category and category != "All":
            query = query.filter(
                Performance.category == category
            )

        if from_date:
            query = query.filter(
                Performance.review_date >= from_date
            )

        if to_date:
            query = query.filter(
                Performance.review_date <= to_date
            )

        return query.order_by(
            Performance.review_date.desc()
        ).all()

    finally:
        db.close()


# ============================================================
# DEPARTMENT REPORT
# ============================================================

def get_department_report():
    db = SessionLocal()

    try:
        departments = (
            db.query(Department)
            .order_by(Department.name.asc())
            .all()
        )

        report_data = []

        for department in departments:

            total_employees = (
                db.query(Employee)
                .filter(
                    Employee.department == department.name
                )
                .count()
            )

            active_employees = (
                db.query(Employee)
                .filter(
                    Employee.department == department.name,
                    Employee.status == "Active"
                )
                .count()
            )

            inactive_employees = (
                db.query(Employee)
                .filter(
                    Employee.department == department.name,
                    Employee.status == "Inactive"
                )
                .count()
            )

            report_data.append(
                {
                    "department": department.name,
                    "total_employees": total_employees,
                    "active_employees": active_employees,
                    "inactive_employees": inactive_employees,
                }
            )

        return report_data

    finally:
        db.close()


# ============================================================
# QUALITY REPORT
# ============================================================

def get_quality_report(
    status=None,
    priority=None,
):
    db = SessionLocal()

    try:
        query = db.query(QualityIssue)

        if status and status != "All":
            query = query.filter(
                QualityIssue.status == status
            )

        if priority and priority != "All":
            query = query.filter(
                QualityIssue.priority == priority
            )

        return query.order_by(
            QualityIssue.id.desc()
        ).all()

    finally:
        db.close()


# ============================================================
# AUDIT REPORT
# ============================================================

def get_audit_report(
    user_id=None,
    from_date=None,
    to_date=None,
):
    db = SessionLocal()

    try:
        query = (
            db.query(
                AuditLog
            )
        )

        if user_id:
            query = query.filter(
                AuditLog.user_id == user_id
            )

        if from_date:
            query = query.filter(
                AuditLog.created_at >= from_date
            )

        if to_date:
            query = query.filter(
                AuditLog.created_at <= to_date
            )

        return query.order_by(
            AuditLog.id.desc()
        ).all()

    finally:
        db.close()


# ============================================================
# REPORT COUNTS
# ============================================================

def get_report_counts():
    db = SessionLocal()

    try:
        return {
            "employees": db.query(Employee).count(),

            "attendance": db.query(
                Attendance
            ).count(),

            "payroll": db.query(
                Payroll
            ).count(),

            "performance": db.query(
                Performance
            ).count(),

            "departments": db.query(
                Department
            ).count(),

            "quality_issues": db.query(
                QualityIssue
            ).count(),

            "audit_logs": db.query(
                AuditLog
            ).count(),
        }

    finally:
        db.close()