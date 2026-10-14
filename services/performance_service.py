# ============================================================
# PERFORMANCE SERVICE
# ============================================================

from database.database import SessionLocal
from database.models import Employee, Performance


# ============================================================
# PERFORMANCE CATEGORIES
# ============================================================

PERFORMANCE_CATEGORIES = [
    "Excellent",
    "Very Good",
    "Good",
    "Needs Improvement",
]


# ============================================================
# CATEGORY CALCULATION
# ============================================================

def calculate_percentage(score):
    """
    Convert score out of 10 into percentage.
    """

    score = float(score or 0)

    percentage = score * 10

    return round(percentage, 2)


def calculate_grade(percentage):
    """
    Calculate performance grade from percentage.
    """

    percentage = float(percentage or 0)

    if percentage >= 90:
        return "Excellent"

    elif percentage >= 75:
        return "Very Good"

    elif percentage >= 60:
        return "Good"

    else:
        return "Needs Improvement"


# ============================================================
# GET EMPLOYEES
# ============================================================

def get_performance_employees():

    db = SessionLocal()

    try:

        employees = (
            db.query(Employee)
            .filter(
                Employee.status == "Active"
            )
            .order_by(
                Employee.full_name.asc()
            )
            .all()
        )

        return employees

    finally:

        db.close()


# ============================================================
# ADD PERFORMANCE
# ============================================================

def add_performance(
    employee_id,
    review_date,
    category,
    score,
    comments=""
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # CHECK EMPLOYEE
        # ----------------------------------------------------

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
        # VALIDATE SCORE
        # ----------------------------------------------------

        score = float(score)

        if score < 1 or score > 10:

            return (
                False,
                "Performance score must be between 1 and 10."
            )

        # ----------------------------------------------------
        # VALIDATE CATEGORY
        # ----------------------------------------------------

        if not category:

            return (
                False,
                "Please select a performance category."
            )

        # ----------------------------------------------------
        # CHECK DUPLICATE
        # ----------------------------------------------------

        existing = (
            db.query(Performance)
            .filter(
                Performance.employee_id == employee_id,
                Performance.review_date == review_date
            )
            .first()
        )

        if existing:

            return (
                False,
                "Performance review already exists "
                "for this employee on the selected date."
            )

        # ----------------------------------------------------
        # CALCULATE PERCENTAGE
        # ----------------------------------------------------

        percentage = calculate_percentage(
            score
        )

        # ----------------------------------------------------
        # CREATE RECORD
        # ----------------------------------------------------

        performance = Performance(
            employee_id=employee_id,
            review_date=review_date,
            score=score,
            percentage=percentage,
            category=category,
            comments=comments or None
        )

        db.add(
            performance
        )

        db.commit()

        db.refresh(
            performance
        )

        return (
            True,
            "Performance review added successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to add performance review.\n\n{error}"
        )

    finally:

        db.close()


# ============================================================
# UPDATE PERFORMANCE
# ============================================================

def update_performance(
    performance_id,
    score,
    comments="",
    category=None
):

    db = SessionLocal()

    try:

        performance = (
            db.query(Performance)
            .filter(
                Performance.id == performance_id
            )
            .first()
        )

        if performance is None:

            return (
                False,
                "Performance record not found."
            )

        # ----------------------------------------------------
        # VALIDATE SCORE
        # ----------------------------------------------------

        score = float(score)

        if score < 1 or score > 10:

            return (
                False,
                "Performance score must be between 1 and 10."
            )

        # ----------------------------------------------------
        # VALIDATE CATEGORY
        # ----------------------------------------------------

        if category is not None:

            if not category:

                return (
                    False,
                    "Please select a performance category."
                )

            performance.category = category

        # ----------------------------------------------------
        # UPDATE SCORE
        # ----------------------------------------------------

        performance.score = score

        # ----------------------------------------------------
        # UPDATE PERCENTAGE
        # ----------------------------------------------------

        performance.percentage = (
            calculate_percentage(score)
        )

        # ----------------------------------------------------
        # UPDATE COMMENTS
        # ----------------------------------------------------

        performance.comments = (
            comments or None
        )

        db.commit()

        db.refresh(
            performance
        )

        return (
            True,
            "Performance review updated successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to update performance review.\n\n{error}"
        )

    finally:

        db.close()


# ============================================================
# GET ALL PERFORMANCE
# ============================================================

def get_all_performance():

    db = SessionLocal()

    try:

        records = (
            db.query(
                Performance,
                Employee
            )
            .join(
                Employee,
                Performance.employee_id == Employee.id
            )
            .order_by(
                Performance.id.desc()
            )
            .all()
        )

        return records

    finally:

        db.close()


# ============================================================
# SEARCH PERFORMANCE
# ============================================================

def search_performance(
    search_text=""
):

    db = SessionLocal()

    try:

        search_text = (
            search_text
            .strip()
        )

        query = (
            db.query(
                Performance,
                Employee
            )
            .join(
                Employee,
                Performance.employee_id == Employee.id
            )
        )

        if search_text:

            pattern = (
                f"%{search_text}%"
            )

            query = query.filter(

                (Employee.employee_id.ilike(pattern))
                |

                (Employee.full_name.ilike(pattern))
                |

                (Performance.category.ilike(pattern))
                |

                (Performance.review_date.ilike(pattern))
            )

        return (
            query
            .order_by(
                Performance.id.desc()
            )
            .all()
        )

    finally:

        db.close()


# ============================================================
# DELETE PERFORMANCE
# ============================================================

def delete_performance(
    performance_id
):

    db = SessionLocal()

    try:

        performance = (
            db.query(Performance)
            .filter(
                Performance.id == performance_id
            )
            .first()
        )

        if performance is None:

            return (
                False,
                "Performance record not found."
            )

        db.delete(
            performance
        )

        db.commit()

        return (
            True,
            "Performance record deleted successfully."
        )

    except Exception as error:

        db.rollback()

        return (
            False,
            f"Unable to delete performance.\n\n{error}"
        )

    finally:

        db.close()


# ============================================================
# PERFORMANCE SUMMARY
# ============================================================

def get_performance_summary():

    db = SessionLocal()

    try:

        records = (
            db.query(
                Performance
            )
            .all()
        )

        total_records = len(
            records
        )

        if total_records == 0:

            return {
                "total_records": 0,
                "average_score": 0,
                "average_percentage": 0,
                "excellent": 0
            }

        total_score = sum(
            float(
                record.score or 0
            )
            for record in records
        )

        total_percentage = sum(
            float(
                record.percentage or 0
            )
            for record in records
        )

        excellent = sum(
            1
            for record in records
            if float(
                record.percentage or 0
            ) >= 90
        )

        return {

            "total_records":
                total_records,

            "average_score":
                round(
                    total_score / total_records,
                    2
                ),

            "average_percentage":
                round(
                    total_percentage / total_records,
                    2
                ),

            "excellent":
                excellent
        }

    finally:

        db.close()


# ============================================================
# EMPLOYEE PERFORMANCE SUMMARY
# ============================================================

def get_employee_performance_summary(
    employee_id
):

    db = SessionLocal()

    try:

        records = (
            db.query(Performance)
            .filter(
                Performance.employee_id
                == employee_id
            )
            .order_by(
                Performance.review_date.asc()
            )
            .all()
        )

        if not records:

            return {
                "total_reviews": 0,
                "average_score": 0,
                "average_percentage": 0,
                "records": []
            }

        total_score = sum(
            float(
                record.score or 0
            )
            for record in records
        )

        total_percentage = sum(
            float(
                record.percentage or 0
            )
            for record in records
        )

        return {

            "total_reviews":
                len(records),

            "average_score":
                round(
                    total_score / len(records),
                    2
                ),

            "average_percentage":
                round(
                    total_percentage / len(records),
                    2
                ),

            "records":
                records
        }

    finally:

        db.close()