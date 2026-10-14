from datetime import datetime

from sqlalchemy import and_

from database.database import SessionLocal
from database.models import Leave


# ============================================================
# ADD LEAVE REQUEST
# ============================================================

def submit_leave(
    employee_id,
    leave_type,
    start_date,
    end_date,
    reason
):
    db = SessionLocal()

    try:

        if not employee_id:
            return False, "Employee ID is required."

        if not leave_type:
            return False, "Please select leave type."

        if not start_date:
            return False, "Start date is required."

        if not end_date:
            return False, "End date is required."

        if not reason or not reason.strip():
            return False, "Please enter reason for leave."

        if start_date > end_date:
            return False, "Start date cannot be after end date."

        # ----------------------------------------------------
        # Check overlapping pending/approved leave
        # ----------------------------------------------------

        existing = (
            db.query(Leave)
            .filter(
                Leave.employee_id == employee_id,
                Leave.status.in_(
                    ["Pending", "Approved"]
                ),
                Leave.start_date <= str(end_date),
                Leave.end_date >= str(start_date),
            )
            .first()
        )

        if existing:

            return (
                False,
                "You already have a leave request for "
                "these dates."
            )

        # ----------------------------------------------------
        # Create leave
        # ----------------------------------------------------

        leave = Leave(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=str(start_date),
            end_date=str(end_date),
            reason=reason.strip(),
            status="Pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(leave)

        db.commit()

        db.refresh(leave)

        return (
            True,
            "Leave request submitted successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to submit leave request: {error}"
        )

    finally:

        db.close()


# ============================================================
# GET EMPLOYEE LEAVE REQUESTS
# ============================================================

def get_employee_leaves(employee_id):

    db = SessionLocal()

    try:

        rows = (
            db.query(Leave)
            .filter(
                Leave.employee_id == employee_id
            )
            .order_by(
                Leave.id.desc()
            )
            .all()
        )

        return rows

    finally:

        db.close()


# ============================================================
# GET LEAVE COUNTS
# ============================================================

def get_leave_counts(employee_id):

    db = SessionLocal()

    try:

        pending = (
            db.query(Leave)
            .filter(
                Leave.employee_id == employee_id,
                Leave.status == "Pending"
            )
            .count()
        )

        approved = (
            db.query(Leave)
            .filter(
                Leave.employee_id == employee_id,
                Leave.status == "Approved"
            )
            .count()
        )

        rejected = (
            db.query(Leave)
            .filter(
                Leave.employee_id == employee_id,
                Leave.status == "Rejected"
            )
            .count()
        )

        return {
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
        }

    finally:

        db.close()


# ============================================================
# CANCEL LEAVE REQUEST
# ============================================================

def cancel_leave(employee_id, leave_id):

    db = SessionLocal()

    try:

        leave = (
            db.query(Leave)
            .filter(
                Leave.id == leave_id,
                Leave.employee_id == employee_id
            )
            .first()
        )

        if leave is None:

            return (
                False,
                "Leave request not found."
            )

        if leave.status != "Pending":

            return (
                False,
                "Only pending leave requests can be cancelled."
            )

        leave.status = "Cancelled"
        leave.updated_at = datetime.utcnow()

        db.commit()

        return (
            True,
            "Leave request cancelled successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to cancel leave request: {error}"
        )

    finally:

        db.close()