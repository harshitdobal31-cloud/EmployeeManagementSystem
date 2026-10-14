from datetime import date, datetime

from sqlalchemy import Date, DateTime

from database.database import SessionLocal
from database.models import CalendarEvent


# ============================================================
# DATE HELPERS
# ============================================================

def normalize_date(value):
    """
    Convert different date formats into Python date object.

    Supports:
    - datetime
    - date
    - string: YYYY-MM-DD
    - string: DD-MM-YYYY
    - string: DD/MM/YYYY
    - string: YYYY-MM-DD HH:MM:SS
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
        ]

        for fmt in formats:

            try:
                return datetime.strptime(
                    value,
                    fmt
                ).date()

            except ValueError:
                continue

    return None


def format_date(value):
    """
    Safely convert date into display format.
    """

    normalized = normalize_date(value)

    if normalized is None:
        return "-"

    return normalized.strftime("%d-%m-%Y")


def get_model_date_value(value):
    """
    Prepare date according to CalendarEvent.event_date
    column type.

    This keeps the service compatible whether the
    database column is Date, DateTime or String.
    """

    normalized = normalize_date(value)

    if normalized is None:
        return None

    column_type = CalendarEvent.__table__.c.event_date.type

    if isinstance(column_type, DateTime):
        return datetime.combine(
            normalized,
            datetime.min.time()
        )

    if isinstance(column_type, Date):
        return normalized

    # If database column is String
    return normalized.strftime("%Y-%m-%d")


# ============================================================
# ADD EVENT
# ============================================================

def add_event(
    title,
    description=None,
    event_date=None,
    event_type="Other",
    created_by=None
):

    db = SessionLocal()

    try:

        event = CalendarEvent(
            title=title.strip(),
            description=(
                description.strip()
                if description
                else None
            ),
            event_date=get_model_date_value(
                event_date
            ),
            event_type=event_type,
            created_by=created_by,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# GET ALL EVENTS
# ============================================================

def get_all_events():

    db = SessionLocal()

    try:

        events = (
            db.query(CalendarEvent)
            .order_by(
                CalendarEvent.event_date.asc()
            )
            .all()
        )

        return events

    finally:

        db.close()


# ============================================================
# GET EVENTS BY DATE
# ============================================================

def get_events_by_date(target_date):

    target_date = normalize_date(
        target_date
    )

    if target_date is None:
        return []

    db = SessionLocal()

    try:

        # Python-side comparison makes this work
        # with Date and String database values.
        events = (
            db.query(CalendarEvent)
            .order_by(
                CalendarEvent.event_date.asc()
            )
            .all()
        )

        result = []

        for event in events:

            event_date = normalize_date(
                event.event_date
            )

            if event_date == target_date:
                result.append(event)

        return result

    finally:

        db.close()


# ============================================================
# GET EVENTS BY MONTH
# ============================================================

def get_events_by_month(year, month):

    db = SessionLocal()

    try:

        events = (
            db.query(CalendarEvent)
            .order_by(
                CalendarEvent.event_date.asc()
            )
            .all()
        )

        result = []

        for event in events:

            event_date = normalize_date(
                event.event_date
            )

            if event_date is None:
                continue

            if (
                event_date.year == year
                and event_date.month == month
            ):
                result.append(event)

        return result

    finally:

        db.close()


# ============================================================
# GET UPCOMING EVENTS
# ============================================================

def get_upcoming_events(limit=10):

    today = date.today()

    db = SessionLocal()

    try:

        events = (
            db.query(CalendarEvent)
            .order_by(
                CalendarEvent.event_date.asc()
            )
            .all()
        )

        result = []

        for event in events:

            event_date = normalize_date(
                event.event_date
            )

            if event_date is None:
                continue

            if event_date >= today:

                result.append(event)

            if len(result) >= limit:
                break

        return result

    finally:

        db.close()


# ============================================================
# SEARCH EVENTS
# ============================================================

def search_events(search_text):

    search_text = (
        search_text or ""
    ).strip().lower()

    if not search_text:
        return get_all_events()

    db = SessionLocal()

    try:

        events = (
            db.query(CalendarEvent)
            .order_by(
                CalendarEvent.event_date.asc()
            )
            .all()
        )

        result = []

        for event in events:

            title = (
                event.title or ""
            ).lower()

            description = (
                event.description or ""
            ).lower()

            event_type = (
                event.event_type or ""
            ).lower()

            event_date = format_date(
                event.event_date
            ).lower()

            if (
                search_text in title
                or search_text in description
                or search_text in event_type
                or search_text in event_date
            ):
                result.append(event)

        return result

    finally:

        db.close()


# ============================================================
# UPDATE EVENT
# ============================================================

def update_event(
    event_id,
    title,
    description=None,
    event_date=None,
    event_type="Other"
):

    db = SessionLocal()

    try:

        event = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.id == event_id
            )
            .first()
        )

        if event is None:
            raise ValueError(
                "Calendar event not found."
            )

        event.title = title.strip()

        event.description = (
            description.strip()
            if description
            else None
        )

        event.event_date = (
            get_model_date_value(
                event_date
            )
        )

        event.event_type = event_type

        db.commit()
        db.refresh(event)

        return event

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ============================================================
# DELETE EVENT
# ============================================================

def delete_event(event_id):

    db = SessionLocal()

    try:

        event = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.id == event_id
            )
            .first()
        )

        if event is None:
            raise ValueError(
                "Calendar event not found."
            )

        db.delete(event)
        db.commit()

        return True

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ============================================================
# EVENT STATISTICS
# ============================================================

def get_event_statistics():

    today = date.today()

    events = get_all_events()

    total_events = len(events)
    today_events = 0
    upcoming_events = 0
    meeting_events = 0

    for event in events:

        event_date = normalize_date(
            event.event_date
        )

        if event_date is None:
            continue

        if event_date == today:
            today_events += 1

        if event_date >= today:
            upcoming_events += 1

        if (
            (event.event_type or "").lower()
            == "meeting"
        ):
            meeting_events += 1

    return {
        "total_events": total_events,
        "today_events": today_events,
        "upcoming_events": upcoming_events,
        "meeting_events": meeting_events,
    }