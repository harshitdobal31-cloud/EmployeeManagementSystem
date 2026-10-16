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
