from datetime import datetime

from database.database import SessionLocal
from database.models import Attendance, Employee


# ============================================================
# ADD ATTENDANCE
# ============================================================

def add_attendance(attendance_data):
    db = SessionLocal()

    try:
        employee_id = attendance_data["employee_id"]
        attendance_date = attendance_data["attendance_date"]

        # ----------------------------------------------------
        # Check employee exists
        # ----------------------------------------------------

        employee = (
            db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )

        if employee is None:
            return False, "Employee not found."

        # ----------------------------------------------------
        # Prevent duplicate attendance
        # ----------------------------------------------------

        existing_attendance = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date == attendance_date
            )
            .first()
        )

        if existing_attendance:
            return (
                False,
                "Attendance already exists for this employee on this date."
            )

        # ----------------------------------------------------
        # Calculate working hours
        # ----------------------------------------------------

        working_hours = calculate_working_hours(
            attendance_data.get("check_in"),
            attendance_data.get("check_out")
        )

        # ----------------------------------------------------
        # Create attendance
        # ----------------------------------------------------

        attendance = Attendance(
            employee_id=employee_id,
            attendance_date=attendance_date,
            check_in=attendance_data.get("check_in"),
            check_out=attendance_data.get("check_out"),
            working_hours=working_hours,
            status=attendance_data.get(
                "status",
                "Present"
            ),
        )

        db.add(attendance)
        db.commit()
        db.refresh(attendance)

        return True, "Attendance added successfully."

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to add attendance: {error}"
        )

    finally:

        db.close()


# ============================================================
# CALCULATE WORKING HOURS
# ============================================================

def calculate_working_hours(check_in, check_out):
    """Calculate working hours, including overnight shifts."""
    if not check_in or not check_out:
        return None

    try:
        start_time = datetime.strptime(check_in, "%H:%M")
        end_time = datetime.strptime(check_out, "%H:%M")

        difference = (end_time - start_time).total_seconds() / 3600

        if difference < 0:
            difference += 24

        return round(difference, 2)

    except (ValueError, TypeError):
        return None

# GET ALL ATTENDANCE
# ============================================================

def get_all_attendance():

    db = SessionLocal()

    try:

        return (
            db.query(
                Attendance
            )
            .order_by(
                Attendance.id.desc()
            )
            .all()
        )

    finally:

        db.close()


# ============================================================
# SEARCH ATTENDANCE
# ============================================================

def search_attendance(
    search_text=""
):

    db = SessionLocal()

    try:

        search_text = (
            search_text
            .strip()
        )

        if not search_text:

            return (
                db.query(Attendance)
                .order_by(
                    Attendance.id.desc()
                )
                .all()
            )

        search_pattern = (
            f"%{search_text}%"
        )

        # Search by date, status or employee ID
        attendance_records = (
            db.query(Attendance)
            .join(
                Employee,
                Attendance.employee_id
                == Employee.id
            )
            .filter(
                (Attendance.attendance_date.ilike(
                    search_pattern
                ))
                |
                (Attendance.status.ilike(
                    search_pattern
                ))
                |
                (Employee.employee_id.ilike(
                    search_pattern
                ))
                |
                (Employee.full_name.ilike(
                    search_pattern
                ))
            )
            .order_by(
                Attendance.id.desc()
            )
            .all()
        )

        return attendance_records

    finally:

        db.close()


# ============================================================
# GET ATTENDANCE BY DATE
# ============================================================

def get_attendance_by_date(
    attendance_date
):

    db = SessionLocal()

    try:

        return (
            db.query(
                Attendance
            )
            .filter(
                Attendance.attendance_date
                == attendance_date
            )
            .order_by(
                Attendance.id.desc()
            )
            .all()
        )

    finally:

        db.close()


# ============================================================
# GET ATTENDANCE BY EMPLOYEE
# ============================================================

def get_employee_attendance(
    employee_id
):

    db = SessionLocal()

    try:

        return (
            db.query(
                Attendance
            )
            .filter(
                Attendance.employee_id
                == employee_id
            )
            .order_by(
                Attendance.attendance_date.desc()
            )
            .all()
        )

    finally:

        db.close()


# ============================================================
# UPDATE ATTENDANCE
# ============================================================

def update_attendance(
    attendance_id,
    attendance_data
):

    db = SessionLocal()

    try:

        attendance = (
            db.query(
                Attendance
            )
            .filter(
                Attendance.id
                == attendance_id
            )
            .first()
        )

        if attendance is None:

            return (
                False,
                "Attendance record not found."
            )

        employee_id = (
            attendance_data["employee_id"]
        )

        attendance_date = (
            attendance_data["attendance_date"]
        )

        # ----------------------------------------------------
        # Check employee
        # ----------------------------------------------------

        employee = (
            db.query(Employee)
            .filter(
                Employee.id
                == employee_id
            )
            .first()
        )

        if employee is None:

            return (
                False,
                "Employee not found."
            )

        # ----------------------------------------------------
        # Duplicate check
        # ----------------------------------------------------

        duplicate = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id
                == employee_id,
                Attendance.attendance_date
                == attendance_date,
                Attendance.id
                != attendance_id
            )
            .first()
        )

        if duplicate:

            return (
                False,
                "Another attendance record already exists for this employee on this date."
            )

        # ----------------------------------------------------
        # Calculate hours
        # ----------------------------------------------------

        working_hours = calculate_working_hours(
            attendance_data.get("check_in"),
            attendance_data.get("check_out")
        )

        # ----------------------------------------------------
        # Update
        # ----------------------------------------------------

        attendance.employee_id = (
            employee_id
        )

        attendance.attendance_date = (
            attendance_date
        )

        attendance.check_in = (
            attendance_data.get(
                "check_in"
            )
        )

        attendance.check_out = (
            attendance_data.get(
                "check_out"
            )
        )

        attendance.working_hours = (
            working_hours
        )

        attendance.status = (
            attendance_data.get(
                "status",
                "Present"
            )
        )

        db.commit()
        db.refresh(attendance)

        return (
            True,
            "Attendance updated successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to update attendance: {error}"
        )

    finally:

        db.close()


# ============================================================
# DELETE ATTENDANCE
# ============================================================

def delete_attendance(
    attendance_id
):

    db = SessionLocal()

    try:

        attendance = (
            db.query(
                Attendance
            )
            .filter(
                Attendance.id
                == attendance_id
            )
            .first()
        )

        if attendance is None:

            return (
                False,
                "Attendance record not found."
            )

        db.delete(
            attendance
        )

        db.commit()

        return (
            True,
            "Attendance deleted successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to delete attendance: {error}"
        )

    finally:

        db.close()


# ============================================================
# ATTENDANCE STATISTICS
# ============================================================

def get_attendance_statistics():

    db = SessionLocal()

    try:

        total = (
            db.query(Attendance)
            .count()
        )

        present = (
            db.query(Attendance)
            .filter(
                Attendance.status
                == "Present"
            )
            .count()
        )

        absent = (
            db.query(Attendance)
            .filter(
                Attendance.status
                == "Absent"
            )
            .count()
        )

        late = (
            db.query(Attendance)
            .filter(
                Attendance.status
                == "Late"
            )
            .count()
        )

        half_day = (
            db.query(Attendance)
            .filter(
                Attendance.status
                == "Half Day"
            )
            .count()
        )

        return {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "half_day": half_day,
        }

    finally:

        db.close()
