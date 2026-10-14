from sqlalchemy import text

from database.database import engine


def migrate_employee_table():
    new_columns = {
        "gender": "VARCHAR(20)",
        "date_of_birth": "VARCHAR(20)",
        "address": "VARCHAR(500)",
        "employment_type": "VARCHAR(50)",
        "bank_account": "VARCHAR(50)",
        "emergency_contact_name": "VARCHAR(150)",
        "emergency_contact_phone": "VARCHAR(20)",
        "profile_photo": "VARCHAR(500)",
        "updated_at": "DATETIME",
    }

    with engine.connect() as connection:

        result = connection.execute(
            text("PRAGMA table_info(employees)")
        )

        existing_columns = {
            row[1] for row in result
        }

        for column_name, column_type in new_columns.items():

            if column_name not in existing_columns:

                connection.execute(
                    text(
                        f"ALTER TABLE employees "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )

                print(
                    f"Added column: {column_name}"
                )

        connection.commit()

    print("\nEmployee table migration completed!")


if __name__ == "__main__":
    migrate_employee_table()