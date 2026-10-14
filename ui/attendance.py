from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QAbstractItemView,
)

from services.attendance_service import (
    add_attendance,
    update_attendance,
    delete_attendance,
    get_all_attendance,
    search_attendance,
    get_attendance_statistics,
)

from services.employee_service import get_all_employees


class AttendanceWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.form_dialog = None

        self.setWindowTitle(
            "Employee Management System | Attendance"
        )

        self.setMinimumSize(
            1200,
            750
        )

        self.setup_ui()

        self.load_attendance()

    # =========================================================
    # MAIN UI
    # =========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        main_layout.setSpacing(
            18
        )

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "Attendance Management"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Track employee attendance, working hours and daily status."
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        header_layout.addLayout(
            title_layout
        )

        header_layout.addStretch()

        mark_button = QPushButton(
            "＋  Mark Attendance"
        )

        mark_button.setObjectName(
            "primaryButton"
        )

        mark_button.setFixedHeight(
            42
        )

        mark_button.clicked.connect(
            self.open_add_attendance
        )

        header_layout.addWidget(
            mark_button
        )

        main_layout.addLayout(
            header_layout
        )

        # -----------------------------------------------------
        # STATISTICS
        # -----------------------------------------------------

        stats_layout = QGridLayout()

        stats_layout.setSpacing(
            15
        )

        self.total_card = self.create_stat_card(
            "Total Records",
            "0",
            "ATTENDANCE"
        )

        self.present_card = self.create_stat_card(
            "Present",
            "0",
            "PRESENT"
        )

        self.absent_card = self.create_stat_card(
            "Absent",
            "0",
            "ABSENT"
        )

        self.late_card = self.create_stat_card(
            "Late",
            "0",
            "LATE"
        )

        stats_layout.addWidget(
            self.total_card,
            0,
            0
        )

        stats_layout.addWidget(
            self.present_card,
            0,
            1
        )

        stats_layout.addWidget(
            self.absent_card,
            0,
            2
        )

        stats_layout.addWidget(
            self.late_card,
            0,
            3
        )

        main_layout.addLayout(
            stats_layout
        )

        # -----------------------------------------------------
        # FILTER AREA
        # -----------------------------------------------------

        filter_frame = QFrame()

        filter_frame.setObjectName(
            "filterCard"
        )

        filter_layout = QHBoxLayout()

        filter_layout.setContentsMargins(
            15,
            12,
            15,
            12
        )

        # Search

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search employee, ID, date or status..."
        )

        self.search_input.setMinimumHeight(
            38
        )

        self.search_input.textChanged.connect(
            self.load_attendance
        )

        filter_layout.addWidget(
            self.search_input,
            2
        )

        # Date

        date_label = QLabel(
            "Date:"
        )

        date_label.setObjectName(
            "filterLabel"
        )

        filter_layout.addWidget(
            date_label
        )

        self.date_filter = QDateEdit()

        self.date_filter.setCalendarPopup(
            True
        )

        self.date_filter.setDisplayFormat(
            "dd-MM-yyyy"
        )

        self.date_filter.setDate(
            QDate.currentDate()
        )

        filter_layout.addWidget(
            self.date_filter
        )

        # Status

        status_label = QLabel(
            "Status:"
        )

        status_label.setObjectName(
            "filterLabel"
        )

        filter_layout.addWidget(
            status_label
        )

        self.status_filter = QComboBox()

        self.status_filter.addItems([
            "All",
            "Present",
            "Absent",
            "Late",
            "Half Day",
        ])

        self.status_filter.currentTextChanged.connect(
            self.load_attendance
        )

        filter_layout.addWidget(
            self.status_filter
        )

        # Refresh

        refresh_button = QPushButton(
            "⟳  Refresh"
        )

        refresh_button.setObjectName(
            "secondaryButton"
        )

        refresh_button.setFixedHeight(
            38
        )

        refresh_button.clicked.connect(
            self.refresh_data
        )

        filter_layout.addWidget(
            refresh_button
        )

        filter_frame.setLayout(
            filter_layout
        )

        main_layout.addWidget(
            filter_frame
        )

        # -----------------------------------------------------
        # TABLE
        # -----------------------------------------------------

        table_frame = QFrame()

        table_frame.setObjectName(
            "tableCard"
        )

        table_layout = QVBoxLayout()

        table_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            10
        )

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Date",
            "Employee ID",
            "Employee Name",
            "Check In",
            "Check Out",
            "Hours",
            "Status",
            "Edit",
            "Delete",
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            8,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            9,
            QHeaderView.ResizeMode.ResizeToContents
        )

        table_layout.addWidget(
            self.table
        )

        table_frame.setLayout(
            table_layout
        )

        main_layout.addWidget(
            table_frame,
            1
        )

        self.setLayout(
            main_layout
        )

        self.apply_styles()

    # =========================================================
    # STAT CARD
    # =========================================================

    def create_stat_card(
        self,
        title,
        value,
        small_text
    ):

        card = QFrame()

        card.setObjectName(
            "statCard"
        )

        card.setMinimumHeight(
            105
        )

        layout = QVBoxLayout()

        layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "statTitle"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "statValue"
        )

        value_label.setProperty(
            "valueLabel",
            True
        )

        small_label = QLabel(
            small_text
        )

        small_label.setObjectName(
            "statSmall"
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            small_label
        )

        card.setLayout(
            layout
        )

        return card

    # =========================================================
    # LOAD ATTENDANCE
    # =========================================================

    def load_attendance(self):

        try:

            search_text = (
                self.search_input
                .text()
                .strip()
            )

            if search_text:

                records = search_attendance(
                    search_text
                )

            else:

                records = get_all_attendance()

            # -------------------------------------------------
            # Status filter
            # -------------------------------------------------

            selected_status = (
                self.status_filter
                .currentText()
            )

            if selected_status != "All":

                records = [
                    record
                    for record in records
                    if record.status
                    == selected_status
                ]

            # -------------------------------------------------
            # Date filter
            # -------------------------------------------------

            selected_date = (
                self.date_filter
                .date()
                .toString("dd-MM-yyyy")
            )

            # Date filtering is applied only when
            # no search text is entered.

            if not search_text:

                records = [
                    record
                    for record in records
                    if record.attendance_date
                    == selected_date
                ]

            self.populate_table(
                records
            )

            self.update_statistics()

        except Exception as error:

            QMessageBox.warning(
                self,
                "Attendance Error",
                f"Unable to load attendance:\n{error}"
            )

    # =========================================================
    # POPULATE TABLE
    # =========================================================

    def populate_table(
        self,
        records
    ):

        self.table.setRowCount(
            0
        )

        for row_index, record in enumerate(
            records
        ):

            self.table.insertRow(
                row_index
            )

            employee = self.get_employee(
                record.employee_id
            )

            employee_id = (
                employee.employee_id
                if employee
                else "N/A"
            )

            employee_name = (
                employee.full_name
                if employee
                else "Unknown"
            )

            values = [
                str(record.id),
                str(record.attendance_date),
                employee_id,
                employee_name,
                record.check_in or "-",
                record.check_out or "-",
                (
                    f"{record.working_hours:.2f}"
                    if record.working_hours is not None
                    else "-"
                ),
                record.status,
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    value
                )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row_index,
                    column,
                    item
                )

            # Edit

            edit_button = QPushButton(
                "Edit"
            )

            edit_button.setObjectName(
                "editButton"
            )

            edit_button.clicked.connect(
                lambda checked=False,
                attendance=record:
                self.open_edit_attendance(
                    attendance
                )
            )

            self.table.setCellWidget(
                row_index,
                8,
                edit_button
            )

            # Delete

            delete_button = QPushButton(
                "Delete"
            )

            delete_button.setObjectName(
                "deleteButton"
            )

            delete_button.clicked.connect(
                lambda checked=False,
                attendance=record:
                self.confirm_delete(
                    attendance
                )
            )

            self.table.setCellWidget(
                row_index,
                9,
                delete_button
            )

    # =========================================================
    # EMPLOYEE LOOKUP
    # =========================================================

    def get_employee(
        self,
        employee_id
    ):

        employees = get_all_employees()

        for employee in employees:

            if employee.id == employee_id:

                return employee

        return None

    # =========================================================
    # STATISTICS
    # =========================================================

    def update_statistics(self):

        try:

            stats = (
                get_attendance_statistics()
            )

            self.set_stat_value(
                self.total_card,
                str(stats["total"])
            )

            self.set_stat_value(
                self.present_card,
                str(stats["present"])
            )

            self.set_stat_value(
                self.absent_card,
                str(stats["absent"])
            )

            self.set_stat_value(
                self.late_card,
                str(stats["late"])
            )

        except Exception:

            self.set_stat_value(
                self.total_card,
                "0"
            )

            self.set_stat_value(
                self.present_card,
                "0"
            )

            self.set_stat_value(
                self.absent_card,
                "0"
            )

            self.set_stat_value(
                self.late_card,
                "0"
            )

    # =========================================================
    # SET STAT VALUE
    # =========================================================

    def set_stat_value(
        self,
        card,
        value
    ):

        label = card.findChild(
            QLabel,
            "statValue"
        )

        if label:

            label.setText(
                value
            )

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh_data(self):

        self.search_input.clear()

        self.status_filter.setCurrentIndex(
            0
        )

        self.date_filter.setDate(
            QDate.currentDate()
        )

        self.load_attendance()

    # =========================================================
    # ADD ATTENDANCE
    # =========================================================

    def open_add_attendance(self):

        self.form_dialog = AttendanceFormDialog(
            self
        )

        if (
            self.form_dialog.exec()
            == QDialog.DialogCode.Accepted
        ):

            self.load_attendance()

    # =========================================================
    # EDIT ATTENDANCE
    # =========================================================

    def open_edit_attendance(
        self,
        attendance
    ):

        self.form_dialog = AttendanceFormDialog(
            self,
            attendance
        )

        if (
            self.form_dialog.exec()
            == QDialog.DialogCode.Accepted
        ):

            self.load_attendance()

    # =========================================================
    # DELETE
    # =========================================================

    def confirm_delete(
        self,
        attendance
    ):

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            (
                "Are you sure you want to delete "
                "this attendance record?"
            ),
            QMessageBox.StandardButton.Yes
            |
            QMessageBox.StandardButton.No
        )

        if (
            reply
            != QMessageBox.StandardButton.Yes
        ):

            return

        success, message = (
            delete_attendance(
                attendance.id
            )
        )

        if success:

            QMessageBox.information(
                self,
                "Deleted",
                message
            )

            self.load_attendance()

        else:

            QMessageBox.warning(
                self,
                "Unable to Delete",
                message
            )

    # =========================================================
    # STYLES
    # =========================================================

    def apply_styles(self):

        self.setStyleSheet("""

            QWidget {
                background-color: #F8FAFC;
                color: #0F172A;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QLabel#pageTitle {
                color: #0F172A;
                font-size: 27px;
                font-weight: 800;
            }

            QLabel#pageSubtitle {
                color: #64748B;
                font-size: 13px;
            }

            QFrame#statCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 11px;
            }

            QLabel#statTitle {
                color: #64748B;
                font-size: 11px;
                font-weight: 600;
            }

            QLabel#statValue {
                color: #0F172A;
                font-size: 25px;
                font-weight: 800;
            }

            QLabel#statSmall {
                color: #2563EB;
                font-size: 9px;
                font-weight: 700;
            }

            QFrame#filterCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }

            QLabel#filterLabel {
                color: #475569;
                font-size: 12px;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox,
            QDateEdit,
            QTimeEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 7px 9px;
                color: #0F172A;
                min-height: 22px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QTimeEdit:focus {
                border: 2px solid #2563EB;
            }

            QFrame#tableCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 11px;
            }

            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                border: none;
                gridline-color: #E2E8F0;
                selection-background-color: #DBEAFE;
                selection-color: #0F172A;
            }

            QHeaderView::section {
                background-color: #F1F5F9;
                color: #334155;
                border: none;
                border-bottom: 1px solid #CBD5E1;
                padding: 10px;
                font-size: 11px;
                font-weight: 700;
            }

            QPushButton#primaryButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                padding: 9px 15px;
                font-weight: 700;
            }

            QPushButton#primaryButton:hover {
                background-color: #1D4ED8;
            }

            QPushButton#secondaryButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 7px 13px;
                font-weight: 600;
            }

            QPushButton#secondaryButton:hover {
                background-color: #F1F5F9;
            }

            QPushButton#editButton {
                background-color: #EFF6FF;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: 600;
            }

            QPushButton#editButton:hover {
                background-color: #DBEAFE;
            }

            QPushButton#deleteButton {
                background-color: #FEF2F2;
                color: #DC2626;
                border: 1px solid #FECACA;
                border-radius: 5px;
                padding: 5px 8px;
                font-weight: 600;
            }

            QPushButton#deleteButton:hover {
                background-color: #FEE2E2;
            }

        """)


# =============================================================
# ATTENDANCE FORM DIALOG
# =============================================================

class AttendanceFormDialog(QDialog):

    def __init__(
        self,
        parent=None,
        attendance=None
    ):

        super().__init__(
            parent
        )

        self.attendance = attendance
        self.is_edit_mode = (
            attendance is not None
        )

        self.setWindowTitle(
            "Edit Attendance"
            if self.is_edit_mode
            else "Mark Attendance"
        )

        self.setMinimumWidth(
            520
        )

        self.setup_ui()

        if self.is_edit_mode:

            self.load_data()

        self.apply_styles()

    # =========================================================
    # FORM UI
    # =========================================================

    def setup_ui(self):

        layout = QVBoxLayout()

        layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        layout.setSpacing(
            15
        )

        title = QLabel(
            "Edit Attendance"
            if self.is_edit_mode
            else "Mark Employee Attendance"
        )

        title.setObjectName(
            "formTitle"
        )

        layout.addWidget(
            title
        )

        form = QFormLayout()

        form.setSpacing(
            14
        )

        # Employee

        self.employee_input = QComboBox()

        self.load_employees()

        form.addRow(
            "Employee *",
            self.employee_input
        )

        # Date

        self.date_input = QDateEdit()

        self.date_input.setCalendarPopup(
            True
        )

        self.date_input.setDisplayFormat(
            "dd-MM-yyyy"
        )

        self.date_input.setDate(
            QDate.currentDate()
        )

        form.addRow(
            "Date *",
            self.date_input
        )

        # Check In

        self.check_in_input = QTimeEdit()

        self.check_in_input.setDisplayFormat(
            "HH:mm"
        )

        self.check_in_input.setTime(
            QTime(
                9,
                0
            )
        )

        form.addRow(
            "Check In",
            self.check_in_input
        )

        # Check Out

        self.check_out_input = QTimeEdit()

        self.check_out_input.setDisplayFormat(
            "HH:mm"
        )

        self.check_out_input.setTime(
            QTime(
                18,
                0
            )
        )

        form.addRow(
            "Check Out",
            self.check_out_input
        )

        # Status

        self.status_input = QComboBox()

        self.status_input.addItems([
            "Present",
            "Absent",
            "Late",
            "Half Day",
        ])

        form.addRow(
            "Status",
            self.status_input
        )

        layout.addLayout(
            form
        )

        # Working hours preview

        self.hours_label = QLabel(
            "Working Hours: 9.00 hours"
        )

        self.hours_label.setObjectName(
            "hoursLabel"
        )

        layout.addWidget(
            self.hours_label
        )

        self.check_in_input.timeChanged.connect(
            self.update_hours_preview
        )

        self.check_out_input.timeChanged.connect(
            self.update_hours_preview
        )

        # Buttons

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            |
            QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.save_attendance
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(
            buttons
        )

        self.setLayout(
            layout
        )

    # =========================================================
    # LOAD EMPLOYEES
    # =========================================================

    def load_employees(self):

        employees = get_all_employees()

        for employee in employees:

            self.employee_input.addItem(
                f"{employee.employee_id} - {employee.full_name}",
                employee.id
            )

    # =========================================================
    # LOAD EXISTING DATA
    # =========================================================

    def load_data(self):

        attendance = self.attendance

        employee_index = (
            self.employee_input.findData(
                attendance.employee_id
            )
        )

        if employee_index >= 0:

            self.employee_input.setCurrentIndex(
                employee_index
            )

        date_value = QDate.fromString(
            attendance.attendance_date,
            "dd-MM-yyyy"
        )

        if date_value.isValid():

            self.date_input.setDate(
                date_value
            )

        if attendance.check_in:

            time_value = QTime.fromString(
                attendance.check_in,
                "HH:mm"
            )

            if time_value.isValid():

                self.check_in_input.setTime(
                    time_value
                )

        if attendance.check_out:

            time_value = QTime.fromString(
                attendance.check_out,
                "HH:mm"
            )

            if time_value.isValid():

                self.check_out_input.setTime(
                    time_value
                )

        status_index = (
            self.status_input.findText(
                attendance.status
            )
        )

        if status_index >= 0:

            self.status_input.setCurrentIndex(
                status_index
            )

        self.update_hours_preview()

    # =========================================================
    # HOURS PREVIEW
    # =========================================================

    def update_hours_preview(self):

        check_in = (
            self.check_in_input
            .time()
            .toString("HH:mm")
        )

        check_out = (
            self.check_out_input
            .time()
            .toString("HH:mm")
        )

        from services.attendance_service import (
            calculate_working_hours
        )

        hours = calculate_working_hours(
            check_in,
            check_out
        )

        if hours is None:

            self.hours_label.setText(
                "Working Hours: Invalid"
            )

        else:

            self.hours_label.setText(
                f"Working Hours: {hours:.2f} hours"
            )

    # =========================================================
    # SAVE
    # =========================================================

    def save_attendance(self):

        employee_id = (
            self.employee_input.currentData()
        )

        if employee_id is None:

            QMessageBox.warning(
                self,
                "Employee Required",
                "Please select an employee."
            )

            return

        attendance_date = (
            self.date_input
            .date()
            .toString("dd-MM-yyyy")
        )

        check_in = (
            self.check_in_input
            .time()
            .toString("HH:mm")
        )

        check_out = (
            self.check_out_input
            .time()
            .toString("HH:mm")
        )

        status = (
            self.status_input
            .currentText()
        )

        attendance_data = {

            "employee_id":
                employee_id,

            "attendance_date":
                attendance_date,

            "check_in":
                check_in,

            "check_out":
                check_out,

            "status":
                status,
        }

        # -----------------------------------------------------
        # UPDATE
        # -----------------------------------------------------

        if self.is_edit_mode:

            success, message = (
                update_attendance(
                    self.attendance.id,
                    attendance_data
                )
            )

        # -----------------------------------------------------
        # ADD
        # -----------------------------------------------------

        else:

            success, message = (
                add_attendance(
                    attendance_data
                )
            )

        if not success:

            QMessageBox.warning(
                self,
                "Unable to Save",
                message
            )

            return

        QMessageBox.information(
            self,
            "Success",
            message
        )

        self.accept()

    # =========================================================
    # STYLES
    # =========================================================

    def apply_styles(self):

        self.setStyleSheet("""

            QDialog {
                background-color: #F8FAFC;
            }

            QLabel#formTitle {
                color: #0F172A;
                font-size: 21px;
                font-weight: 800;
            }

            QLineEdit,
            QComboBox,
            QDateEdit,
            QTimeEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 8px;
                color: #0F172A;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QTimeEdit:focus {
                border: 2px solid #2563EB;
            }

            QLabel#hoursLabel {
                background-color: #EFF6FF;
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 7px;
                padding: 10px;
                font-weight: 700;
            }

            QPushButton {
                min-width: 90px;
                min-height: 32px;
                border-radius: 6px;
                padding: 6px 12px;
            }

        """)