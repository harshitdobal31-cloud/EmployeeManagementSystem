import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "employee_management.db"


def migrate_leave_requests():
    print("Checking leave_requests table...")

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        columns = [
            row[1]
            for row in cursor.execute(
                "PRAGMA table_info(leave_requests)"
            ).fetchall()
        ]

        print("Existing columns:")
        print(columns)

        if "updated_at" not in columns:
            print("Adding missing column: updated_at")

            cursor.execute(
                """
                ALTER TABLE leave_requests
                ADD COLUMN updated_at DATETIME
                """
            )

            cursor.execute(
                """
                UPDATE leave_requests
                SET updated_at = created_at
                WHERE updated_at IS NULL
                """
            )

            connection.commit()

            print("Migration completed successfully!")
        else:
            print("updated_at already exists. Nothing to change.")

    except Exception as error:
        connection.rollback()
        print(f"Migration failed: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_leave_requests()