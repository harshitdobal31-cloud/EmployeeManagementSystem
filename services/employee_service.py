import re
from email_validator import validate_email, EmailNotValidError
from database.database import SessionLocal
from database.models import Employee, User
from utils.security import hash_password


# ============================================================
# ADD EMPLOYEE + CREATE LOGIN ACCOUNT
# ============================================================

def is_valid_employee_email(email):
    if not isinstance(email, str):
        return False

    email = email.strip()

    if not email or len(email) > 254 or email.count("@") != 1:
        return False

    local, domain = email.rsplit("@", 1)

    if (
        not local
        or len(local) > 64
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
        or ".." in domain
    ):
        return False

    pattern = (
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
    )

    if not re.fullmatch(pattern, email):
        return False

    labels = domain.split(".")

    if any(not label or len(label) > 63 for label in labels):
        return False

    return len(labels[-1]) >= 2 and labels[-1].isalpha()



def generate_employee_id():
    """Generate the next unused ID in EMP + digits format."""
    db = SessionLocal()
    try:
        existing_ids = db.query(Employee.employee_id).all()
        highest_number = 0

        for row in existing_ids:
            value = (row[0] or "").strip().upper()
            match = re.fullmatch(r"EMP([0-9]+)", value)
            if match:
                highest_number = max(highest_number, int(match.group(1)))

        candidate_number = highest_number + 1
        while True:
            candidate = f"EMP{candidate_number:03d}"
            if not db.query(Employee).filter(
                Employee.employee_id == candidate
            ).first():
                return candidate
            candidate_number += 1
    finally:
        db.close()


def add_employee(employee_data):
    db = SessionLocal()

    try:
        employee_id = employee_data["employee_id"].strip().upper()
        email = employee_data["email"].strip().lower()

        if not re.fullmatch(r"EMP[0-9]+", employee_id):
            return (
                False,
                "Invalid Employee ID. Use EMP followed by numbers only, "
                "for example EMP001."
            )

        if not is_valid_employee_email(email):
            return (False, "Invalid email address. Please enter a valid email.")

        password = employee_data.get("login_password", "").strip()

        # ----------------------------------------------------
        # REQUIRED LOGIN PASSWORD
        # ----------------------------------------------------
        if not password:
            return (
                False,
                "Login password is required for a new employee."
            )

        if len(password) < 6:
            return (
                False,
                "Login password must contain at least 6 characters."
            )

        # ----------------------------------------------------
        # DUPLICATE EMPLOYEE ID
        # ----------------------------------------------------
        existing_employee = (
            db.query(Employee)
            .filter(
                Employee.employee_id == employee_id
            )
            .first()
        )

        if existing_employee:
            return (
                False,
                "Employee ID already exists."
            )

        # ----------------------------------------------------
        # DUPLICATE EMPLOYEE EMAIL
        # ----------------------------------------------------
        existing_employee_email = (
            db.query(Employee)
            .filter(
                Employee.email == email
            )
            .first()
        )

        if existing_employee_email:
            return (
                False,
                "Employee email already exists."
            )

        # ----------------------------------------------------
        # DUPLICATE USERNAME
        # Employee ID is used as login username
        # ----------------------------------------------------
        existing_user_username = (
            db.query(User)
            .filter(
                User.username == employee_id
            )
            .first()
        )

        if existing_user_username:
            return (
                False,
                "This Employee ID is already registered as a login username."
            )

        # ----------------------------------------------------
        # DUPLICATE USER EMAIL
        # ----------------------------------------------------
        existing_user_email = (
            db.query(User)
            .filter(
                User.email == email
            )
            .first()
        )

        if existing_user_email:
            return (
                False,
                "This email is already registered with a user account."
            )

        # ----------------------------------------------------
        # CREATE EMPLOYEE
        # ----------------------------------------------------
        employee = Employee(
            employee_id=employee_id,
            full_name=employee_data["full_name"],
            email=email,
            phone=employee_data.get("phone"),
            gender=employee_data.get("gender"),
            date_of_birth=employee_data.get("date_of_birth"),
            address=employee_data.get("address"),
            department=employee_data.get("department"),
            designation=employee_data.get("designation"),
            employment_type=employee_data.get("employment_type"),
            joining_date=employee_data.get("joining_date"),
            salary=employee_data.get("salary"),
            bank_account=employee_data.get("bank_account"),
            emergency_contact_name=employee_data.get(
                "emergency_contact_name"
            ),
            emergency_contact_phone=employee_data.get(
                "emergency_contact_phone"
            ),
            profile_photo=employee_data.get(
                "profile_photo"
            ),
            status=employee_data.get(
                "status",
                "Active"
            ),
        )

        db.add(employee)

        # ----------------------------------------------------
        # CREATE USER LOGIN ACCOUNT
        # ----------------------------------------------------
        user = User(
            username=employee_id,
            email=email,
            password=hash_password(password),
            role="Employee",
            status=employee_data.get(
                "status",
                "Active"
            ),
        )

        db.add(user)

        # ----------------------------------------------------
        # SAVE BOTH TOGETHER
        # ----------------------------------------------------
        db.commit()

        db.refresh(employee)
        db.refresh(user)

        return (
            True,
            "Employee and login account created successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to add employee: {error}"
        )

    finally:
        db.close()


# ============================================================
# GET ALL EMPLOYEES
# ============================================================

def get_all_employees():

    db = SessionLocal()

    try:
        return (
            db.query(Employee)
            .order_by(
                Employee.id.desc()
            )
            .all()
        )

    finally:
        db.close()


# ============================================================
# SEARCH EMPLOYEES
# ============================================================

def search_employees(search_text):

    db = SessionLocal()

    try:

        search_text = search_text.strip()

        if not search_text:
            return get_all_employees()

        search_pattern = (
            f"%{search_text}%"
        )

        return (
            db.query(Employee)
            .filter(
                (Employee.employee_id.ilike(search_pattern))
                | (Employee.full_name.ilike(search_pattern))
                | (Employee.email.ilike(search_pattern))
                | (Employee.department.ilike(search_pattern))
                | (Employee.designation.ilike(search_pattern))
            )
            .order_by(
                Employee.id.desc()
            )
            .all()
        )

    finally:
        db.close()


# ============================================================
# UPDATE EMPLOYEE
# ============================================================

def update_employee(
    employee_id,
    employee_data
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
            return (
                False,
                "Employee not found."
            )

        old_employee_id = employee.employee_id
        old_email = employee.email

        new_email = (
            employee_data["email"]
            .strip()
            .lower()
        )

        # ----------------------------------------------------
        # DUPLICATE EMAIL IN EMPLOYEE TABLE
        # ----------------------------------------------------
        existing_email = (
            db.query(Employee)
            .filter(
                Employee.email == new_email,
                Employee.id != employee_id
            )
            .first()
        )

        if existing_email:
            return (
                False,
                "Another employee already uses this email."
            )

        # ----------------------------------------------------
        # EMPLOYEE ID IS NOT CHANGED IN EDIT MODE
        # ----------------------------------------------------
        employee.full_name = (
            employee_data["full_name"]
        )

        employee.email = new_email

        employee.phone = (
            employee_data.get("phone")
        )

        employee.gender = (
            employee_data.get("gender")
        )

        employee.date_of_birth = (
            employee_data.get("date_of_birth")
        )

        employee.address = (
            employee_data.get("address")
        )

        employee.department = (
            employee_data.get("department")
        )

        employee.designation = (
            employee_data.get("designation")
        )

        employee.employment_type = (
            employee_data.get("employment_type")
        )

        employee.joining_date = (
            employee_data.get("joining_date")
        )

        employee.salary = (
            employee_data.get("salary")
        )

        employee.bank_account = (
            employee_data.get("bank_account")
        )

        employee.emergency_contact_name = (
            employee_data.get(
                "emergency_contact_name"
            )
        )

        employee.emergency_contact_phone = (
            employee_data.get(
                "emergency_contact_phone"
            )
        )

        employee.profile_photo = (
            employee_data.get(
                "profile_photo"
            )
        )

        employee.status = (
            employee_data.get(
                "status",
                "Active"
            )
        )

        # ----------------------------------------------------
        # UPDATE LOGIN ACCOUNT
        # ----------------------------------------------------
        user = (
            db.query(User)
            .filter(
                User.username == old_employee_id
            )
            .first()
        )

        # Fallback: find by old email
        if user is None:
            user = (
                db.query(User)
                .filter(
                    User.email == old_email
                )
                .first()
            )

        if user:

            # Check whether another user already owns new email
            duplicate_user_email = (
                db.query(User)
                .filter(
                    User.email == new_email,
                    User.id != user.id
                )
                .first()
            )

            if duplicate_user_email:
                return (
                    False,
                    "Another user account already uses this email."
                )

            user.email = new_email

            # Keep employee login status synchronized
            user.status = employee_data.get(
                "status",
                "Active"
            )

            # ------------------------------------------------
            # OPTIONAL PASSWORD RESET
            # ------------------------------------------------
            new_password = (
                employee_data.get(
                    "login_password",
                    ""
                ).strip()
            )

            if new_password:

                if len(new_password) < 6:
                    return (
                        False,
                        "Login password must contain at least 6 characters."
                    )

                user.password = (
                    hash_password(new_password)
                )

        db.commit()

        db.refresh(employee)

        return (
            True,
            "Employee updated successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to update employee: {error}"
        )

    finally:
        db.close()


# ============================================================
# DELETE EMPLOYEE + DELETE LOGIN ACCOUNT
# ============================================================

def delete_employee(employee_id):

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
            return (
                False,
                "Employee not found."
            )

        # ----------------------------------------------------
        # DELETE ASSOCIATED USER ACCOUNT
        # ----------------------------------------------------
        user = (
            db.query(User)
            .filter(
                User.username == employee.employee_id
            )
            .first()
        )

        if user:
            db.delete(user)

        # ----------------------------------------------------
        # DELETE EMPLOYEE
        # ----------------------------------------------------
        db.delete(employee)

        db.commit()

        return (
            True,
            "Employee and login account deleted successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to delete employee: {error}"
        )

    finally:
        db.close()