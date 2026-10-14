from services.employee_service import (
    add_employee,
    get_all_employees,
    search_employees,
)


def test_add_employee():

    employee_data = {
        "employee_id": "EMP001",
        "full_name": "Rahul Sharma",
        "email": "rahul@ems.com",
        "phone": "9876543210",
        "gender": "Male",
        "date_of_birth": "15-05-2000",
        "address": "Moradabad, Uttar Pradesh",
        "department": "Information Technology",
        "designation": "Software Developer",
        "employment_type": "Full Time",
        "joining_date": "27-09-2026",
        "salary": 35000,
        "bank_account": "1234567890",
        "emergency_contact_name": "Rakesh Sharma",
        "emergency_contact_phone": "9876501234",
        "profile_photo": None,
        "status": "Active",
    }

    success, result = add_employee(employee_data)

    print("\nAdd Employee Result:")
    print(success)

    if success:
        print("Employee ID:", result.employee_id)
        print("Name:", result.full_name)
        print("Email:", result.email)
    else:
        print("Error:", result)


def test_get_employees():

    employees = get_all_employees()

    print("\nEmployee List:")

    for employee in employees:
        print(
            employee.employee_id,
            "|",
            employee.full_name,
            "|",
            employee.email
        )


def test_search_employee():

    employees = search_employees("Rahul")

    print("\nSearch Result:")

    for employee in employees:
        print(
            employee.employee_id,
            "|",
            employee.full_name
        )


if __name__ == "__main__":

    test_add_employee()
    test_get_employees()
    test_search_employee()