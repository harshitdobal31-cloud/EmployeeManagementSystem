from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
    QHeaderView,
)

from services.employee_service import (
    get_all_employees,
    search_employees,
    delete_employee,
)

from ui.employee_form import EmployeeFormWindow


class EmployeeManagementWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.employee_form = None

        self.setWindowTitle(
            "Employee Management System | Employees"
        )

        self.setMinimumSize(
            1250,
            750
        )

        self.setup_ui()

        self.load_employees()

    # ======================================================
    # MAIN UI
    # ======================================================

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

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "Employee Management"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Manage employee records, profiles and employment information."
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

        add_button = QPushButton(
            "+  Add Employee"
        )

        add_button.setObjectName(
            "primaryButton"
        )

        add_button.setFixedSize(
            160,
            44
        )

        add_button.clicked.connect(
            self.open_add_employee
        )

        header_layout.addWidget(
            add_button
        )

        main_layout.addLayout(
            header_layout
        )

        # --------------------------------------------------
        # STAT CARDS
        # --------------------------------------------------

        stats_layout = QHBoxLayout()

        stats_layout.setSpacing(
            15
        )

        self.total_card = (
            self.create_stat_card(
                "Total Employees",
                "0"
            )
        )

        self.active_card = (
            self.create_stat_card(
                "Active Employees",
                "0"
            )
        )

        self.inactive_card = (
            self.create_stat_card(
                "Inactive Employees",
                "0"
            )
        )

        stats_layout.addWidget(
            self.total_card
        )

        stats_layout.addWidget(
            self.active_card
        )

        stats_layout.addWidget(
            self.inactive_card
        )

        main_layout.addLayout(
            stats_layout
        )

        # --------------------------------------------------
        # SEARCH + FILTER
        # --------------------------------------------------

        filter_frame = QFrame()

        filter_frame.setObjectName(
            "filterFrame"
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
            "Search by Employee ID, name, email, department..."
        )

        self.search_input.setMinimumHeight(
            42
        )

        self.search_input.textChanged.connect(
            self.apply_filters
        )

        filter_layout.addWidget(
            self.search_input,
            1
        )

        # Department

        self.department_filter = QComboBox()

        self.department_filter.setMinimumWidth(
            190
        )

        self.department_filter.setMinimumHeight(
            42
        )

        self.department_filter.addItems([
            "All Departments",
            "Human Resources",
            "Information Technology",
            "Finance",
            "Administration",
        ])

        self.department_filter.currentTextChanged.connect(
            self.apply_filters
        )

        filter_layout.addWidget(
            self.department_filter
        )

        # Status

        self.status_filter = QComboBox()

        self.status_filter.setMinimumWidth(
            150
        )

        self.status_filter.setMinimumHeight(
            42
        )

        self.status_filter.addItems([
            "All Status",
            "Active",
            "Inactive",
        ])

        self.status_filter.currentTextChanged.connect(
            self.apply_filters
        )

        filter_layout.addWidget(
            self.status_filter
        )

        # Refresh

        refresh_button = QPushButton(
            "↻  Refresh"
        )

        refresh_button.setObjectName(
            "secondaryButton"
        )

        refresh_button.setFixedSize(
            110,
            42
        )

        refresh_button.clicked.connect(
            self.refresh_employees
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

        # --------------------------------------------------
        # TABLE
        # --------------------------------------------------

        self.employee_table = QTableWidget()

        # PHOTO COLUMN ADDED
        self.employee_table.setColumnCount(
            11
        )

        self.employee_table.setHorizontalHeaderLabels([
            "Photo",
            "ID",
            "Employee ID",
            "Full Name",
            "Email",
            "Department",
            "Designation",
            "Salary",
            "Status",
            "Edit",
            "Delete",
        ])

        self.employee_table.setAlternatingRowColors(
            True
        )

        self.employee_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.employee_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.employee_table.setMinimumHeight(
            400
        )

        header = (
            self.employee_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        # PHOTO COLUMN
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents
        )

        # ID COLUMN
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        # EDIT
        header.setSectionResizeMode(
            9,
            QHeaderView.ResizeMode.ResizeToContents
        )

        # DELETE
        header.setSectionResizeMode(
            10,
            QHeaderView.ResizeMode.ResizeToContents
        )

        main_layout.addWidget(
            self.employee_table
        )

        self.setLayout(
            main_layout
        )

        self.apply_styles()

    # ======================================================
    # STAT CARD
    # ======================================================

    def create_stat_card(
        self,
        title,
        value
    ):

        card = QFrame()

        card.setObjectName(
            "statCard"
        )

        layout = QVBoxLayout()

        layout.setContentsMargins(
            18,
            15,
            18,
            15
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

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        card.setLayout(
            layout
        )

        return card

    # ======================================================
    # LOAD EMPLOYEES
    # ======================================================

    def load_employees(
        self,
        employees=None
    ):

        if employees is None:

            employees = get_all_employees()

        self.all_employees = employees

        self.update_statistics(
            employees
        )

        self.populate_table(
            employees
        )

    # ======================================================
    # STATISTICS
    # ======================================================

    def update_statistics(
        self,
        employees
    ):

        total = len(
            employees
        )

        active = sum(
            1
            for employee in employees
            if employee.status == "Active"
        )

        inactive = sum(
            1
            for employee in employees
            if employee.status == "Inactive"
        )

        self.total_card.findChild(
            QLabel,
            "statValue"
        ).setText(
            str(total)
        )

        self.active_card.findChild(
            QLabel,
            "statValue"
        ).setText(
            str(active)
        )

        self.inactive_card.findChild(
            QLabel,
            "statValue"
        ).setText(
            str(inactive)
        )

    # ======================================================
    # CREATE CIRCULAR PHOTO
    # ======================================================

    def create_circular_photo(
        self,
        photo_path,
        size=42
    ):

        label = QLabel()

        label.setFixedSize(
            size,
            size
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        label.setObjectName(
            "employeePhoto"
        )

        # -----------------------------------------------
        # NO PHOTO
        # -----------------------------------------------

        if not photo_path:

            label.setText(
                "👤"
            )

            label.setStyleSheet(
                f"""
                QLabel#employeePhoto {{
                    background-color: #E2E8F0;
                    border-radius: {size // 2}px;
                    color: #64748B;
                    font-size: 18px;
                    font-weight: 600;
                }}
                """
            )

            return label

        # -----------------------------------------------
        # CHECK FILE
        # -----------------------------------------------

        photo_file = Path(
            str(photo_path)
        )

        if not photo_file.exists():

            label.setText(
                "👤"
            )

            label.setStyleSheet(
                f"""
                QLabel#employeePhoto {{
                    background-color: #E2E8F0;
                    border-radius: {size // 2}px;
                    color: #64748B;
                    font-size: 18px;
                    font-weight: 600;
                }}
                """
            )

            return label

        # -----------------------------------------------
        # LOAD IMAGE
        # -----------------------------------------------

        pixmap = QPixmap(
            str(photo_file)
        )

        if pixmap.isNull():

            label.setText(
                "👤"
            )

            return label

        # -----------------------------------------------
        # SCALE IMAGE
        # -----------------------------------------------

        pixmap = pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # -----------------------------------------------
        # CIRCULAR MASK
        # -----------------------------------------------

        circular_pixmap = QPixmap(
            size,
            size
        )

        circular_pixmap.fill(
            Qt.GlobalColor.transparent
        )

        painter = QPainter(
            circular_pixmap
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform
        )

        # Circle clipping
        from PySide6.QtGui import QPainterPath

        path = QPainterPath()

        path.addEllipse(
            0,
            0,
            size,
            size
        )

        painter.setClipPath(
            path
        )

        # Center crop
        source_x = max(
            0,
            (pixmap.width() - size) // 2
        )

        source_y = max(
            0,
            (pixmap.height() - size) // 2
        )

        source_rect = pixmap.rect()

        if (
            pixmap.width() > size
            or pixmap.height() > size
        ):
            source_rect = pixmap.rect()

        painter.drawPixmap(
            0,
            0,
            pixmap
        )

        painter.end()

        # -----------------------------------------------
        # BORDER
        # -----------------------------------------------

        border_pixmap = QPixmap(
            size,
            size
        )

        border_pixmap.fill(
            Qt.GlobalColor.transparent
        )

        painter = QPainter(
            border_pixmap
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.drawPixmap(
            0,
            0,
            circular_pixmap
        )

        pen = QPen(
            Qt.GlobalColor.white
        )

        pen.setWidth(
            2
        )

        painter.setPen(
            pen
        )

        painter.setBrush(
            QBrush(
                Qt.BrushStyle.NoBrush
            )
        )

        painter.drawEllipse(
            1,
            1,
            size - 2,
            size - 2
        )

        painter.end()

        label.setPixmap(
            border_pixmap
        )

        return label

    # ======================================================
    # TABLE
    # ======================================================

    def populate_table(
        self,
        employees
    ):

        self.employee_table.setRowCount(
            0
        )

        for employee in employees:

            row = (
                self.employee_table.rowCount()
            )

            self.employee_table.insertRow(
                row
            )

            # ------------------------------------------------
            # PHOTO
            # ------------------------------------------------

            photo_label = self.create_circular_photo(
                employee.profile_photo,
                42
            )

            photo_container = QWidget()

            photo_layout = QHBoxLayout()

            photo_layout.setContentsMargins(
                0,
                0,
                0,
                0
            )

            photo_layout.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            photo_layout.addWidget(
                photo_label
            )

            photo_container.setLayout(
                photo_layout
            )

            self.employee_table.setCellWidget(
                row,
                0,
                photo_container
            )

            # ------------------------------------------------
            # ID
            # ------------------------------------------------

            self.employee_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(employee.id)
                )
            )

            # ------------------------------------------------
            # EMPLOYEE ID
            # ------------------------------------------------

            self.employee_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    employee.employee_id
                )
            )

            # ------------------------------------------------
            # NAME
            # ------------------------------------------------

            self.employee_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    employee.full_name
                )
            )

            # ------------------------------------------------
            # EMAIL
            # ------------------------------------------------

            self.employee_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    employee.email
                )
            )

            # ------------------------------------------------
            # DEPARTMENT
            # ------------------------------------------------

            self.employee_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    employee.department or "-"
                )
            )

            # ------------------------------------------------
            # DESIGNATION
            # ------------------------------------------------

            self.employee_table.setItem(
                row,
                6,
                QTableWidgetItem(
                    employee.designation or "-"
                )
            )

            # ------------------------------------------------
            # SALARY
            # ------------------------------------------------

            salary_text = "-"

            if employee.salary is not None:

                salary_text = (
                    f"₹ {employee.salary:,.2f}"
                )

            self.employee_table.setItem(
                row,
                7,
                QTableWidgetItem(
                    salary_text
                )
            )

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            status_item = QTableWidgetItem(
                f"● {employee.status}"
            )

            status_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.employee_table.setItem(
                row,
                8,
                status_item
            )

            # ------------------------------------------------
            # EDIT BUTTON
            # ------------------------------------------------

            edit_button = QPushButton(
                "Edit"
            )

            edit_button.setObjectName(
                "editButton"
            )

            edit_button.clicked.connect(
                lambda checked=False,
                emp=employee:
                self.open_edit_employee(emp)
            )

            self.employee_table.setCellWidget(
                row,
                9,
                edit_button
            )

            # ------------------------------------------------
            # DELETE BUTTON
            # ------------------------------------------------

            delete_button = QPushButton(
                "Delete"
            )

            delete_button.setObjectName(
                "deleteButton"
            )

            delete_button.clicked.connect(
                lambda checked=False,
                emp=employee:
                self.confirm_delete(emp)
            )

            self.employee_table.setCellWidget(
                row,
                10,
                delete_button
            )

            self.employee_table.setRowHeight(
                row,
                58
            )

    # ======================================================
    # SEARCH + FILTER
    # ======================================================

    def apply_filters(self):

        search_text = (
            self.search_input.text().strip()
        )

        department = (
            self.department_filter.currentText()
        )

        status = (
            self.status_filter.currentText()
        )

        if search_text:

            employees = search_employees(
                search_text
            )

        else:

            employees = get_all_employees()

        filtered_employees = []

        for employee in employees:

            if (
                department != "All Departments"
                and employee.department
                != department
            ):
                continue

            if (
                status != "All Status"
                and employee.status
                != status
            ):
                continue

            filtered_employees.append(
                employee
            )

        self.update_statistics(
            filtered_employees
        )

        self.populate_table(
            filtered_employees
        )

    # ======================================================
    # REFRESH
    # ======================================================

    def refresh_employees(self):

        self.search_input.clear()

        self.department_filter.setCurrentIndex(
            0
        )

        self.status_filter.setCurrentIndex(
            0
        )

        self.load_employees()

    # ======================================================
    # ADD
    # ======================================================

    def open_add_employee(self):

        self.employee_form = (
            EmployeeFormWindow()
        )

        self.employee_form.destroyed.connect(
            self.refresh_employees
        )

        self.employee_form.show()

    # ======================================================
    # EDIT
    # ======================================================

    def open_edit_employee(
        self,
        employee
    ):

        self.employee_form = (
            EmployeeFormWindow(
                employee
            )
        )

        self.employee_form.destroyed.connect(
            self.refresh_employees
        )

        self.employee_form.show()

    # ======================================================
    # DELETE
    # ======================================================

    def confirm_delete(
        self,
        employee
    ):

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            (
                f"Are you sure you want to delete "
                f"'{employee.full_name}'?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if (
            reply
            != QMessageBox.StandardButton.Yes
        ):
            return

        success, message = (
            delete_employee(
                employee.id
            )
        )

        if success:

            QMessageBox.information(
                self,
                "Employee Deleted",
                message
            )

            self.refresh_employees()

        else:

            QMessageBox.warning(
                self,
                "Delete Failed",
                message
            )

    # ======================================================
    # STYLES
    # ======================================================

    def apply_styles(self):

        self.setStyleSheet("""

            QWidget {
                background-color: #F8FAFC;
                color: #0F172A;
                font-family: "Segoe UI";
            }

            QLabel#pageTitle {
                color: #0F172A;
                font-size: 28px;
                font-weight: 800;
            }

            QLabel#pageSubtitle {
                color: #64748B;
                font-size: 13px;
            }

            QFrame#statCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }

            QLabel#statTitle {
                color: #64748B;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#statValue {
                color: #0F172A;
                font-size: 26px;
                font-weight: 800;
            }

            QFrame#filterFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }

            QLineEdit,
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 8px 10px;
                color: #0F172A;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 2px solid #2563EB;
            }

            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                gridline-color: #E2E8F0;
                selection-background-color: #DBEAFE;
                selection-color: #0F172A;
            }

            QTableWidget::item {
                padding: 5px;
            }

            QHeaderView::section {
                background-color: #0F172A;
                color: #FFFFFF;
                padding: 12px;
                border: none;
                font-weight: 700;
            }

            QPushButton#primaryButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
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
                padding: 5px 10px;
                font-weight: 600;
            }

            QPushButton#deleteButton:hover {
                background-color: #FEE2E2;
            }

        """)