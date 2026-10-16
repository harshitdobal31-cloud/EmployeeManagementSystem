import pytest

from services.attendance_service import calculate_working_hours


@pytest.mark.parametrize(
    ("check_in", "check_out", "expected"),
    [
        ("09:00", "17:00", 8.0),
        ("22:00", "06:00", 8.0),
        ("23:30", "00:30", 1.0),
        ("09:00", "09:00", 0.0),
        ("08:15", "12:45", 4.5),
    ],
)
def test_calculate_working_hours(check_in, check_out, expected):
    assert calculate_working_hours(check_in, check_out) == expected


@pytest.mark.parametrize(
    ("check_in", "check_out"),
    [
        (None, "17:00"),
        ("09:00", None),
        ("invalid", "17:00"),
        ("09:00", "invalid"),
        ("", "17:00"),
    ],
)
def test_calculate_working_hours_handles_missing_or_invalid_times(
    check_in, check_out
):
    assert calculate_working_hours(check_in, check_out) is None

from unittest.mock import MagicMock, patch

from services.attendance_service import get_attendance_by_date


def test_get_attendance_by_date_filters_and_orders_records():
    fake_db = MagicMock()
    fake_records = [MagicMock(), MagicMock()]

    fake_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = fake_records

    with patch("services.attendance_service.SessionLocal", return_value=fake_db):
        result = get_attendance_by_date("2026-10-16")

    assert result == fake_records
    fake_db.query.return_value.filter.assert_called_once()
    fake_db.query.return_value.filter.return_value.order_by.assert_called_once()
    fake_db.close.assert_called_once()


def test_get_attendance_by_date_closes_database_when_query_fails():
    fake_db = MagicMock()
    fake_db.query.side_effect = RuntimeError("Database query failed")

    with patch("services.attendance_service.SessionLocal", return_value=fake_db):
        with pytest.raises(RuntimeError, match="Database query failed"):
            get_attendance_by_date("2026-10-16")

    fake_db.close.assert_called_once()
