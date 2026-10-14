from datetime import date

from database.database import SessionLocal
from database.models import User, Employee
from utils.security import verify_password, hash_password


# ============================================================
# LOGIN
# ============================================================

def login_user(login_value: str, password: str):
    """
    Authenticate a user using username or email and password.

    Returns:
        User object if login is successful.
        None if login fails.
    """

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(
                (User.username == login_value)
                | (User.email == login_value)
            )
            .first()
        )

        if user is None:
            return None

        if user.status != "Active":
            return None

        if not verify_password(
            password,
            user.password
        ):
            return None

        return user

    finally:
        db.close()


# ============================================================
# GENERATE USERNAME
# ============================================================

def generate_username(db, full_name: str):
    """
    Generate a unique username from full name.

    Example:
        Harshit Dobal
        -> harshitdobal

        If already exists:
        -> harshitdobal1
        -> harshitdobal2
    """

    base_username = "".join(
        character.lower()
        for character in full_name
        if character.isalnum()
    )

    if not base_username:
        base_username = "user"

    username = base_username
    counter = 1

    while (
        db.query(User)
        .filter(User.username == username)
        .first()
        is not None
    ):
        username = f"{base_username}{counter}"
        counter += 1

    return username


# ============================================================
# GENERATE EMPLOYEE ID
# ============================================================

def generate_employee_id(db):
    """
    Generate unique employee ID.

    Example:
        EMP001
        EMP002
        EMP003
    """

    employees = (
        db.query(Employee)
        .order_by(Employee.id.desc())
        .all()
    )

    if not employees:
        return "EMP001"

    highest_number = 0

    for employee in employees:

        employee_code = employee.employee_id or ""

        if employee_code.upper().startswith("EMP"):

            number_part = employee_code[3:]

            if number_part.isdigit():

                highest_number = max(
                    highest_number,
                    int(number_part)
                )

    return f"EMP{highest_number + 1:03d}"


# ============================================================
# REGISTER USER
# ============================================================

def register_user(
    full_name: str,
    email: str,
    password: str,
    role: str,
):
    """
    Register a new Employee or HR Manager.

    Employee:
        Creates User + Employee profile.

    HR Manager:
        Creates User account only.

    Returns:
        (True, message)
        or
        (False, error_message)
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Clean input
        # ----------------------------------------------------

        full_name = full_name.strip()
        email = email.strip().lower()
        role = role.strip()

        # ----------------------------------------------------
        # Validate full name
        # ----------------------------------------------------

        if not full_name:
            return False, "Full name is required."

        if len(full_name) < 3:
            return False, (
                "Full name must contain at least 3 characters."
            )

        # ----------------------------------------------------
        # Validate email
        # ----------------------------------------------------

        if not email:
            return False, "Email address is required."

        if (
            "@" not in email
            or "." not in email.split("@")[-1]
        ):
            return False, "Please enter a valid email address."

        # ----------------------------------------------------
        # Validate password
        # ----------------------------------------------------

        if not password:
            return False, "Password is required."

        if len(password) < 6:
            return False, (
                "Password must contain at least 6 characters."
            )

        # ----------------------------------------------------
        # Public signup roles
        # ----------------------------------------------------

        allowed_roles = {
            "Employee": "Employee",
            "HR Manager": "HR Manager",
        }

        if role not in allowed_roles:
            return False, "Invalid signup role."

        role = allowed_roles[role]

        # ----------------------------------------------------
        # Check duplicate email in USERS
        # ----------------------------------------------------

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user is not None:
            return False, (
                "An account with this email already exists."
            )

        # ----------------------------------------------------
        # Check duplicate email in EMPLOYEES
        # ----------------------------------------------------

        existing_employee = (
            db.query(Employee)
            .filter(Employee.email == email)
            .first()
        )

        if existing_employee is not None:
            return False, (
                "An employee profile with this email already exists."
            )

        # ----------------------------------------------------
        # Generate username
        # ----------------------------------------------------

        username = generate_username(
            db,
            full_name
        )

        # ----------------------------------------------------
        # Hash password
        # ----------------------------------------------------

        hashed_password = hash_password(
            password
        )

        # ----------------------------------------------------
        # Create USER account
        # ----------------------------------------------------

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role=role,
            status="Active",
        )

        db.add(user)

        # Get user ID before commit
        db.flush()

        # ----------------------------------------------------
        # CREATE EMPLOYEE PROFILE
        # ----------------------------------------------------

        if role == "Employee":

            employee_code = generate_employee_id(
                db
            )

            employee = Employee(
                employee_id=employee_code,
                full_name=full_name,
                email=email,

                # Optional fields
                phone="",
                gender="",
                date_of_birth="",
                address="",

                # Employment
                department="Not Assigned",
                designation="Employee",
                employment_type="Full Time",
                joining_date=str(date.today()),
                salary=0.0,

                # Bank
                bank_account="",

                # Emergency contact
                emergency_contact_name="",
                emergency_contact_phone="",

                # Profile
                profile_photo="",

                status="Active",
            )

            db.add(employee)

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        db.commit()

        return (
            True,
            f"Account created successfully.\n\n"
            f"Username: {username}\n"
            f"Role: {role}"
        )

    except Exception as error:

        db.rollback()

        print("\n" + "=" * 70)
        print("REGISTRATION ERROR")
        print("=" * 70)
        print(str(error))
        print("=" * 70 + "\n")

        return (
            False,
            f"Unable to create account:\n{error}"
        )

    finally:
        db.close()