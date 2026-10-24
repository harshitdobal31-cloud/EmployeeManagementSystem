from sqlalchemy import or_
from database.database import SessionLocal
from database.models import Employee, Payroll


# ============================================================
# CALCULATE PAYROLL
# ============================================================

def calculate_payroll(
    employee,
    basic_salary=None,
    allowances=0,
    deductions=0
):

    if basic_salary is None:
        basic_salary = employee.salary or 0

    basic_salary = float(
        basic_salary or 0
    )

    allowances = float(
        allowances or 0
    )

    deductions = float(
        deductions or 0
    )

    net_salary = (
        basic_salary
        + allowances
        - deductions
    )

    if net_salary < 0:
        net_salary = 0

    return {
        "basic_salary": round(
            basic_salary,
            2
        ),
        "allowances": round(
            allowances,
            2
        ),
        "deductions": round(
            deductions,
            2
        ),
        "net_salary": round(
            net_salary,
            2
        )
    }


# ============================================================
# GET ACTIVE EMPLOYEES
# ============================================================

def get_payroll_employees():

    db = SessionLocal()

    try:

        return (
            db.query(Employee)
            .filter(
                Employee.status == "Active"
            )
            .order_by(
                Employee.full_name.asc()
            )
            .all()
        )

    finally:

        db.close()


# ============================================================
# GET EXISTING PAYROLL
# ============================================================

def get_existing_payroll(
    employee_id,
    payroll_month
):

    db = SessionLocal()

    try:

        return (
            db.query(Payroll)
            .filter(
                Payroll.employee_id == employee_id,
                Payroll.payroll_month == payroll_month
            )
            .first()
        )

    finally:

        db.close()


# ============================================================
# CREATE PAYROLL
# ============================================================

def create_payroll(
    employee_id,
    payroll_month,
    allowances=0,
    deductions=0
):

    db = SessionLocal()

    try:

        employee = (
            db.query(Employee)
            .filter(
                Employee.id == employee_id
            )
            .first()
        )

        if employee is None:

            return False, "Employee not found."

        existing = (
            db.query(Payroll)
            .filter(
                Payroll.employee_id == employee_id,
                Payroll.payroll_month == payroll_month
            )
            .first()
        )

        if existing:

            return (
                False,
                "Payroll already exists for this employee "
                "for the selected month."
            )

        salary_data = calculate_payroll(
            employee=employee,
            allowances=allowances,
            deductions=deductions
        )

        payroll = Payroll(
            employee_id=employee_id,
            payroll_month=payroll_month,
            basic_salary=salary_data["basic_salary"],
            allowances=salary_data["allowances"],
            deductions=salary_data["deductions"],
            net_salary=salary_data["net_salary"],
            status="Processed"
        )

        db.add(payroll)

        db.commit()

        db.refresh(payroll)

        return (
            True,
            "Payroll processed successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to process payroll: {error}"
        )

    finally:

        db.close()


# ============================================================
# GET ALL PAYROLL
# ============================================================

def get_all_payroll():

    db = SessionLocal()

    try:

        return (
            db.query(Payroll)
            .order_by(
                Payroll.id.desc()
            )
            .all()
        )

    finally:

        db.close()


# ============================================================
# SEARCH + FILTER PAYROLL
# ============================================================

def search_payroll(
    search_text="",
    payroll_month=None,
    status=None
):

    db = SessionLocal()

    try:

        search_text = (
            search_text or ""
        ).strip()

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

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        if search_text:

            pattern = (
                f"%{search_text}%"
            )

            query = query.filter(
                (Employee.employee_id.ilike(pattern))
                |
                (Employee.full_name.ilike(pattern))
                |
                (Payroll.payroll_month.ilike(pattern))
            )

        # ----------------------------------------------------
        # MONTH FILTER
        # ----------------------------------------------------

        if payroll_month and payroll_month != "All Months":
            month_names = {
                "january": "01", "february": "02",
                "march": "03", "april": "04",
                "may": "05", "june": "06",
                "july": "07", "august": "08",
                "september": "09", "october": "10",
                "november": "11", "december": "12",
            }
            selected = payroll_month.strip()
            month_number = month_names.get(selected.lower())

            if month_number:
                query = query.filter(
                    or_(
                        Payroll.payroll_month.ilike(selected),
                        Payroll.payroll_month.like(f"%-{month_number}"),
                        Payroll.payroll_month.like(f"%-{month_number}-%"),
                    )
                )
            else:
                query = query.filter(
                    Payroll.payroll_month == selected
                )

        # ----------------------------------------------------
        # STATUS FILTER
        # ----------------------------------------------------

        if (
            status
            and status != "All Status"
        ):

            query = query.filter(
                Payroll.status == status
            )

        return (
            query
            .order_by(
                Payroll.id.desc()
            )
            .all()
        )

    finally:

        db.close()


# ============================================================
# UPDATE PAYROLL
# ============================================================

def update_payroll(
    payroll_id,
    allowances,
    deductions
):

    db = SessionLocal()

    try:

        payroll = (
            db.query(Payroll)
            .filter(
                Payroll.id == payroll_id
            )
            .first()
        )

        if payroll is None:

            return (
                False,
                "Payroll record not found."
            )

        if payroll.status == "Locked":

            return (
                False,
                "This payroll is locked and cannot be modified."
            )

        employee = (
            db.query(Employee)
            .filter(
                Employee.id == payroll.employee_id
            )
            .first()
        )

        if employee is None:

            return (
                False,
                "Employee not found."
            )

        salary_data = calculate_payroll(
            employee=employee,
            allowances=allowances,
            deductions=deductions
        )

        payroll.basic_salary = (
            salary_data["basic_salary"]
        )

        payroll.allowances = (
            salary_data["allowances"]
        )

        payroll.deductions = (
            salary_data["deductions"]
        )

        payroll.net_salary = (
            salary_data["net_salary"]
        )

        payroll.status = "Processed"

        db.commit()

        db.refresh(payroll)

        return (
            True,
            "Payroll updated successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to update payroll: {error}"
        )

    finally:

        db.close()


# ============================================================
# LOCK PAYROLL
# ============================================================

def lock_payroll(
    payroll_id
):

    db = SessionLocal()

    try:

        payroll = (
            db.query(Payroll)
            .filter(
                Payroll.id == payroll_id
            )
            .first()
        )

        if payroll is None:

            return (
                False,
                "Payroll record not found."
            )

        if payroll.status == "Locked":

            return (
                False,
                "Payroll is already locked."
            )

        payroll.status = "Locked"

        db.commit()

        return (
            True,
            "Payroll locked successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to lock payroll: {error}"
        )

    finally:

        db.close()


# ============================================================
# DELETE PAYROLL
# ============================================================

def delete_payroll(
    payroll_id
):

    db = SessionLocal()

    try:

        payroll = (
            db.query(Payroll)
            .filter(
                Payroll.id == payroll_id
            )
            .first()
        )

        if payroll is None:

            return (
                False,
                "Payroll record not found."
            )

        if payroll.status == "Locked":

            return (
                False,
                "Locked payroll cannot be deleted."
            )

        db.delete(payroll)

        db.commit()

        return (
            True,
            "Payroll deleted successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to delete payroll: {error}"
        )

    finally:

        db.close()


# ============================================================
# PAYROLL SUMMARY
# ============================================================

def get_payroll_summary():

    db = SessionLocal()

    try:

        payroll_records = (
            db.query(Payroll)
            .all()
        )

        total_payroll = len(
            payroll_records
        )

        processed = 0
        locked = 0

        total_basic = 0
        total_allowances = 0
        total_deductions = 0
        total_net = 0

        for payroll in payroll_records:

            if payroll.status == "Processed":

                processed += 1

            elif payroll.status == "Locked":

                locked += 1

            total_basic += float(
                payroll.basic_salary or 0
            )

            total_allowances += float(
                payroll.allowances or 0
            )

            total_deductions += float(
                payroll.deductions or 0
            )

            total_net += float(
                payroll.net_salary or 0
            )

        return {

            "total_payroll":
                total_payroll,

            "processed":
                processed,

            "locked":
                locked,

            "total_basic":
                round(
                    total_basic,
                    2
                ),

            "total_allowances":
                round(
                    total_allowances,
                    2
                ),

            "total_deductions":
                round(
                    total_deductions,
                    2
                ),

            "total_net":
                round(
                    total_net,
                    2
                )
        }

    finally:

        db.close()