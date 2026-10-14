from datetime import datetime

from database.database import SessionLocal
from database.models import QualityIssue, ImprovementAction


# ============================================================
# QUALITY ISSUE MANAGEMENT
# ============================================================

def create_quality_issue(
    issue_id,
    title,
    description,
    category,
    priority,
    reported_by,
    assigned_to=None,
    issue_date=None,
):
    """
    Create a new quality issue.
    """

    db = SessionLocal()

    try:
        # Check duplicate Issue ID
        existing = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.issue_id == issue_id
            )
            .first()
        )

        if existing:
            raise ValueError(
                "Quality Issue ID already exists."
            )

        issue = QualityIssue(
            issue_id=issue_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            reported_by=reported_by,
            assigned_to=assigned_to,
            issue_date=issue_date or datetime.now(),
            status="Open",
        )

        db.add(issue)
        db.commit()
        db.refresh(issue)

        return issue

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================

def get_all_quality_issues():
    """
    Get all quality issues.
    """

    db = SessionLocal()

    try:

        return (
            db.query(QualityIssue)
            .order_by(
                QualityIssue.created_at.desc()
            )
            .all()
        )

    finally:
        db.close()


# ============================================================

def search_quality_issues(
    keyword=None,
    status="All",
    priority="All",
    category="All",
):
    """
    Search and filter quality issues.
    """

    db = SessionLocal()

    try:

        query = db.query(QualityIssue)

        # Keyword search
        if keyword:

            search_text = (
                f"%{keyword.strip()}%"
            )

            query = query.filter(
                (QualityIssue.issue_id.ilike(search_text))
                |
                (QualityIssue.title.ilike(search_text))
                |
                (QualityIssue.description.ilike(search_text))
            )

        # Status
        if status and status != "All":

            query = query.filter(
                QualityIssue.status == status
            )

        # Priority
        if priority and priority != "All":

            query = query.filter(
                QualityIssue.priority == priority
            )

        # Category
        if category and category != "All":

            query = query.filter(
                QualityIssue.category == category
            )

        return (
            query
            .order_by(
                QualityIssue.created_at.desc()
            )
            .all()
        )

    finally:
        db.close()


# ============================================================

def get_quality_issue_by_id(issue_id):
    """
    Get one quality issue using database ID.
    """

    db = SessionLocal()

    try:

        return (
            db.query(QualityIssue)
            .filter(
                QualityIssue.id == issue_id
            )
            .first()
        )

    finally:
        db.close()


# ============================================================

def update_quality_issue(
    issue_id,
    title,
    description,
    category,
    priority,
    assigned_to=None,
    status="Open",
    root_cause=None,
    corrective_action=None,
    resolution_date=None,
):
    """
    Update an existing quality issue.
    """

    db = SessionLocal()

    try:

        issue = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.id == issue_id
            )
            .first()
        )

        if not issue:
            raise ValueError(
                "Quality issue not found."
            )

        issue.title = title
        issue.description = description
        issue.category = category
        issue.priority = priority
        issue.assigned_to = assigned_to
        issue.status = status
        issue.root_cause = root_cause
        issue.corrective_action = corrective_action

        if resolution_date:
            issue.resolution_date = resolution_date

        elif status in (
            "Resolved",
            "Closed",
        ):
            issue.resolution_date = datetime.now()

        else:
            issue.resolution_date = None

        db.commit()
        db.refresh(issue)

        return issue

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================

def delete_quality_issue(issue_id):
    """
    Delete a quality issue.
    """

    db = SessionLocal()

    try:

        issue = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.id == issue_id
            )
            .first()
        )

        if not issue:
            raise ValueError(
                "Quality issue not found."
            )

        db.delete(issue)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# QUALITY STATISTICS
# ============================================================

def get_quality_statistics():
    """
    Return quality issue statistics.
    """

    db = SessionLocal()

    try:

        total = (
            db.query(QualityIssue)
            .count()
        )

        open_count = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.status == "Open"
            )
            .count()
        )

        in_progress = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.status == "In Progress"
            )
            .count()
        )

        resolved = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.status == "Resolved"
            )
            .count()
        )

        closed = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.status == "Closed"
            )
            .count()
        )

        critical = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.priority == "Critical"
            )
            .count()
        )

        high = (
            db.query(QualityIssue)
            .filter(
                QualityIssue.priority == "High"
            )
            .count()
        )

        return {
            "total": total,
            "open": open_count,
            "in_progress": in_progress,
            "resolved": resolved,
            "closed": closed,
            "critical": critical,
            "high": high,
        }

    finally:
        db.close()


# ============================================================
# PDCA / CONTINUOUS IMPROVEMENT
# ============================================================

def create_improvement_action(
    problem,
    root_cause,
    corrective_action,
    preventive_action,
    responsible_person=None,
    priority="Medium",
    status="Planned",
    due_date=None,
    pdca_stage="Plan",
):
    """
    Create a PDCA improvement action.
    """

    db = SessionLocal()

    try:

        action = ImprovementAction(
            problem=problem,
            root_cause=root_cause,
            corrective_action=corrective_action,
            preventive_action=preventive_action,
            responsible_person=responsible_person,
            priority=priority,
            status=status,
            due_date=due_date,
            pdca_stage=pdca_stage,
            created_at=datetime.now(),
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        return action

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================

def get_all_improvement_actions():
    """
    Get all PDCA improvement actions.
    """

    db = SessionLocal()

    try:

        return (
            db.query(ImprovementAction)
            .order_by(
                ImprovementAction.created_at.desc()
            )
            .all()
        )

    finally:
        db.close()


# ============================================================

def update_improvement_action(
    action_id,
    problem,
    root_cause,
    corrective_action,
    preventive_action,
    responsible_person=None,
    priority="Medium",
    status="Planned",
    due_date=None,
    pdca_stage="Plan",
):
    """
    Update PDCA improvement action.
    """

    db = SessionLocal()

    try:

        action = (
            db.query(ImprovementAction)
            .filter(
                ImprovementAction.id == action_id
            )
            .first()
        )

        if not action:
            raise ValueError(
                "Improvement action not found."
            )

        action.problem = problem
        action.root_cause = root_cause
        action.corrective_action = corrective_action
        action.preventive_action = preventive_action
        action.responsible_person = responsible_person
        action.priority = priority
        action.status = status
        action.due_date = due_date
        action.pdca_stage = pdca_stage

        db.commit()
        db.refresh(action)

        return action

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================

def delete_improvement_action(
    action_id
):
    """
    Delete a PDCA improvement action.
    """

    db = SessionLocal()

    try:

        action = (
            db.query(ImprovementAction)
            .filter(
                ImprovementAction.id == action_id
            )
            .first()
        )

        if not action:
            raise ValueError(
                "Improvement action not found."
            )

        db.delete(action)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# PDCA STATISTICS
# ============================================================

def get_improvement_statistics():
    """
    Return PDCA statistics.
    """

    db = SessionLocal()

    try:

        total = (
            db.query(ImprovementAction)
            .count()
        )

        plan = (
            db.query(ImprovementAction)
            .filter(
                ImprovementAction.pdca_stage == "Plan"
            )
            .count()
        )

        do = (
            db.query(ImprovementAction)
            .filter(
                ImprovementAction.pdca_stage == "Do"
            )
            .count()
        )

        check = (
            db.query(ImprovementAction)
            .filter(
                ImprovementAction.pdca_stage == "Check"
            )
            .count()
        )

        act = (
            db.query(ImprovementAction)
            .filter(
                ImprovementAction.pdca_stage == "Act"
            )
            .count()
        )

        completed = (
            db.query(ImprovementAction)
            .filter(
                ImprovementAction.status == "Completed"
            )
            .count()
        )

        return {
            "total": total,
            "plan": plan,
            "do": do,
            "check": check,
            "act": act,
            "completed": completed,
        }

    finally:
        db.close()