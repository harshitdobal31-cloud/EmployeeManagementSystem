import ui.dashboard as dashboard


def test_collect_dashboard_data_returns_service_values(monkeypatch):
    monkeypatch.setattr(dashboard, "get_all_employees", lambda: [])
    monkeypatch.setattr(
        dashboard,
        "get_attendance_statistics",
        lambda: {"present": 7},
    )
    monkeypatch.setattr(
        dashboard,
        "get_payroll_summary",
        lambda: {"processed": 4},
    )

    data = dashboard.collect_dashboard_data()

    assert data["total"] == 0
    assert data["active"] == 0
    assert data["present"] == 7
    assert data["processed"] == 4
    assert data["errors"] == {}


def test_attendance_failure_does_not_break_payroll_data(monkeypatch):
    monkeypatch.setattr(dashboard, "get_all_employees", lambda: [])
    monkeypatch.setattr(
        dashboard,
        "get_attendance_statistics",
        lambda: (_ for _ in ()).throw(RuntimeError("Attendance unavailable")),
    )
    monkeypatch.setattr(
        dashboard,
        "get_payroll_summary",
        lambda: {"processed": 3},
    )

    data = dashboard.collect_dashboard_data()

    assert "Attendance" in data["errors"]
    assert data["present"] is None
    assert data["processed"] == 3


def test_payroll_failure_does_not_break_attendance_data(monkeypatch):
    monkeypatch.setattr(dashboard, "get_all_employees", lambda: [])
    monkeypatch.setattr(
        dashboard,
        "get_attendance_statistics",
        lambda: {"present": 5},
    )
    monkeypatch.setattr(
        dashboard,
        "get_payroll_summary",
        lambda: (_ for _ in ()).throw(RuntimeError("Payroll unavailable")),
    )

    data = dashboard.collect_dashboard_data()

    assert "Payroll" in data["errors"]
    assert data["present"] == 5
    assert data["processed"] is None


def test_employee_failure_does_not_break_other_dashboard_data(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "get_all_employees",
        lambda: (_ for _ in ()).throw(RuntimeError("Employees unavailable")),
    )
    monkeypatch.setattr(
        dashboard,
        "get_attendance_statistics",
        lambda: {"present": 6},
    )
    monkeypatch.setattr(
        dashboard,
        "get_payroll_summary",
        lambda: {"processed": 2},
    )

    data = dashboard.collect_dashboard_data()

    assert "Employees" in data["errors"]
    assert data["total"] is None
    assert data["active"] is None
    assert data["present"] == 6
    assert data["processed"] == 2
