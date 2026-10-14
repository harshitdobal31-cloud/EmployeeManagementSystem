from database import database
from database import models
from database.database import SessionLocal
from database.models import User, Department
from utils.security import hash_password

def seed_database():
    """
    Insert initial demo data into the database.
    """

    db = SessionLocal()

    try:
        # -------------------------------------------------
        # 1. Create Departments
        # -------------------------------------------------

        departments = [
            {
                "name": "Human Resources",
                "description": "Handles employee management and HR activities."
            },
            {
                "name": "Information Technology",
                "description": "Handles software, systems and technical activities."
            },
            {
                "name": "Finance",
                "description": "Handles payroll and financial activities."
            },
            {
                "name": "Administration",
                "description": "Handles administrative activities."
            }
        ]

        for department_data in departments:

            existing_department = (
                db.query(Department)
                .filter(
                    Department.name == department_data["name"]
                )
                .first()
            )

            if not existing_department:

                department = Department(
                    name=department_data["name"],
                    description=department_data["description"],
                    status="Active"
                )

                db.add(department)

        # -------------------------------------------------
        # 2. Create Demo Users
        # -------------------------------------------------

        users = [
            {
                "username": "admin",
                "email": "admin@ems.com",
                "password": hash_password("admin123"),
                "role": "Admin",
                "status": "Active"
            },
            {
                "username": "hrmanager",
                "email": "hr@ems.com",
                "password": hash_password("hr123"),
                "role": "HR Manager",
                "status": "Active"
            },
            {
                "username": "employee",
                "email": "employee@ems.com",
                "password": hash_password("employee123"),
                "role": "Employee",
                "status": "Active"
            }
        ]

        for user_data in users:

            existing_user = (
                db.query(User)
                .filter(
                    User.username == user_data["username"]
                )
                .first()
            )

            if not existing_user:

                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                    role=user_data["role"],
                    status=user_data["status"]
                )

                db.add(user)

        # -------------------------------------------------
        # Save changes
        # -------------------------------------------------

        db.commit()

        print("Seed data inserted successfully!")

    except Exception as error:

        db.rollback()

        print("Error while inserting seed data:")
        print(error)

    finally:

        db.close()


if __name__ == "__main__":
    seed_database()