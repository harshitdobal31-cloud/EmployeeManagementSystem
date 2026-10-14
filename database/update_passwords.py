from database.database import SessionLocal
from database.models import User
from utils.security import hash_password


def update_demo_passwords():
    db = SessionLocal()

    try:
        demo_users = {
            "admin": "admin123",
            "hrmanager": "hr123",
            "employee": "employee123"
        }

        for username, password in demo_users.items():

            user = (
                db.query(User)
                .filter(User.username == username)
                .first()
            )

            if user:
                user.password = hash_password(password)
                print(f"Password updated for: {username}")

        db.commit()

        print("\nDemo passwords hashed successfully!")

    except Exception as error:
        db.rollback()
        print("Error:", error)

    finally:
        db.close()


if __name__ == "__main__":
    update_demo_passwords()