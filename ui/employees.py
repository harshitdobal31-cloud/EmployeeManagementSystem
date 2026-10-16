from PySide6.QtWidgets import QFileDialog
import csv

from pathlib import Path
import logging

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QPen
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
    QAbstractItemView,
    QSizePolicy,
)

from sqlalchemy.exc import SQLAlchemyError

from services.employee_service import (
    get_all_employees,
    search_employees,
    delete_employee,
)

from ui.employee_form import EmployeeFormWindow


logger = logging.getLogger(__name__)


# ============================================================
# EMPLOYEE MANAGEMENT WINDOW
# ============================================================

class EmployeeManagementWindow(QWidget):
    """
    Employee management screen.

    Features:
    - Employee listing
    - Search
    - Department and status filters
    - Profile photo display
    - Add, edit and delete
    - Employee statistics
    - Refresh
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.employee_form = None
        self.all_employees = []

        self.setWindowTitle(
            "Employee Management System | Employees"
        )

        self.setMinimumSize(1100, 700)

        self.setup_ui()
        self.refresh_employees()

    # ========================================================
    # MAIN UI
    # ========================================================

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(18)

        # ---------------- HEADER ----------------

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)

        title = QLabel("Employee Management")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Manage employee records, profiles and employment information."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.add_button = QPushButton("+  Add Employee")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setMinimumSize(160, 44)
        self.add_button.clicked.connect(self.open_add_employee)

        header_layout.addWidget(self.add_button)
        main_layout.addLayout(header_layout)

        # ---------------- STATISTICS ----------------

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self.total_card = self.create_stat_card(
            "Total Employees", "0", "totalCard"
        )

        self.active_card = self.create_stat_card(
            "Active Employees", "0", "activeCard"
        )

        self.inactive_card = self.create_stat_card(
            "Inactive Employees", "0", "inactiveCard"
        )

        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.active_card)
        stats_layout.addWidget(self.inactive_card)

        main_layout.addLayout(stats_layout)

        # ---------------- SEARCH AND FILTERS ----------------

        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")

        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(14, 12, 14, 12)
        filter_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search by employee ID, name, email, department..."
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumHeight(42)
        self.search_input.textChanged.connect(self.apply_filters)

        filter_layout.addWidget(self.search_input, 1)

        self.department_filter = QComboBox()
        self.department_filter.setMinimumWidth(175)
        self.department_filter.setMinimumHeight(42)
        self.department_filter.addItem("All Departments")
        self.department_filter.currentTextChanged.connect(
            self.apply_filters
        )

        filter_layout.addWidget(self.department_filter)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(140)
        self.status_filter.setMinimumHeight(42)
        self.status_filter.addItems([
            "All Status",
            "Active",
            "Inactive",
        ])
        self.status_filter.currentTextChanged.connect(
            self.apply_filters
        )

        filter_layout.addWidget(self.status_filter)

        self.refresh_button = QPushButton("↻  Refresh")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.setMinimumSize(105, 42)
        self.refresh_button.clicked.connect(self.refresh_employees)

        filter_layout.addWidget(self.refresh_button)
        self.export_button = QPushButton('Export CSV')
        self.export_button.setObjectName('secondaryButton')
        self.export_button.setMinimumSize(115, 42)
        self.export_button.setToolTip(
            'Export the currently displayed employee records to CSV'
        )
        self.export_button.clicked.connect(self.export_employees)
        filter_layout.addWidget(self.export_button)
        main_layout.addWidget(filter_frame)

        # ---------------- EMPLOYEE TABLE ----------------

        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(11)

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

        self.employee_table.setAlternatingRowColors(True)
        self.employee_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.employee_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.employee_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.employee_table.setWordWrap(False)
        self.employee_table.setShowGrid(False)
        self.employee_table.setSortingEnabled(False)
        self.employee_table.setMinimumHeight(350)
        self.employee_table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        header = self.employee_table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            9, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            10, QHeaderView.ResizeMode.ResizeToContents
        )

        self.employee_table.verticalHeader().setVisible(False)
        self.employee_table.verticalHeader().setDefaultSectionSize(60)

        main_layout.addWidget(self.employee_table, 1)

        # ---------------- FOOTER ----------------

        self.result_label = QLabel("Showing 0 employees")
        self.result_label.setObjectName("pageSubtitle")
        main_layout.addWidget(self.result_label)

        self.apply_styles()

    # ========================================================
    # STATISTIC CARDS
    # ========================================================

    def create_stat_card(self, title, value, object_name):
        card = QFrame()
        card.setObjectName("statCard")
        card.setProperty("cardType", object_name)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")

        value_label = QLabel(value)
        value_label.setObjectName("statValue")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        card.setMinimumHeight(95)
        return card

    def set_card_value(self, card, value):
        label = card.findChild(QLabel, "statValue")
        if label:
            label.setText(str(value))

    def update_statistics(self, employees):
        """
        Statistics are based on all loaded employees, not just
        the currently filtered table rows.
        """
        total = len(employees)

        active = sum(
            1 for employee in employees
            if str(getattr(employee, "status", "") or "").strip().lower()
            == "active"
        )

        inactive = sum(
            1 for employee in employees
            if str(getattr(employee, "status", "") or "").strip().lower()
            == "inactive"
        )

        self.set_card_value(self.total_card, total)
        self.set_card_value(self.active_card, active)
        self.set_card_value(self.inactive_card, inactive)

    # ========================================================
    # LOAD AND REFRESH
    # ========================================================

    def load_employees(self, employees=None):
        """
        Load employees from the existing service layer.
        Passing a list displays that list without querying again.
        """
        try:
            if employees is None:
                employees = get_all_employees()

            self.all_employees = list(employees or [])

            self.update_statistics(self.all_employees)
            self.update_department_options(self.all_employees)
            self.apply_filters()

        except Exception as exc:
            logger.exception("Unable to load employees")

            QMessageBox.critical(
                self,
                "Loading Error",
                "Employees could not be loaded.\n\n"
                f"Details: {exc}",
            )

    def refresh_employees(self):
        """
        Reload the data and reset filters to show all employees.
        """
        try:
            self.search_input.blockSignals(True)
            self.department_filter.blockSignals(True)
            self.status_filter.blockSignals(True)

            self.search_input.clear()
            self.department_filter.setCurrentIndex(0)
            self.status_filter.setCurrentIndex(0)

        finally:
            self.search_input.blockSignals(False)
            self.department_filter.blockSignals(False)
            self.status_filter.blockSignals(False)

        self.load_employees()

    def update_department_options(self, employees):
        """
        Populate departments from actual employee records while
        keeping the common department names available.
        """
        common_departments = [
            "Human Resources",
            "Information Technology",
            "Finance",
            "Administration",
        ]

        existing_departments = {
            str(getattr(employee, "department", "") or "").strip()
            for employee in employees
            if str(getattr(employee, "department", "") or "").strip()
        }

        departments = sorted(
            existing_departments.union(common_departments),
            key=str.casefold,
        )

        current_value = self.department_filter.currentText()

        self.department_filter.blockSignals(True)
        self.department_filter.clear()
        self.department_filter.addItem("All Departments")
        self.department_filter.addItems(departments)

        index = self.department_filter.findText(current_value)
        self.department_filter.setCurrentIndex(index if index >= 0 else 0)

        self.department_filter.blockSignals(False)

    # ========================================================
    # SEARCH AND FILTERS
    # ========================================================

    def apply_filters(self, *_):
        """
        Search through the existing search service, then apply
        department and status filters.
        """
        search_text = self.search_input.text().strip()
        department = self.department_filter.currentText()
        status = self.status_filter.currentText()

        try:
            if search_text:
                employees = search_employees(search_text)
                employees = list(employees or [])
            else:
                employees = list(self.all_employees)

        except Exception as exc:
            logger.exception("Employee search failed")

            QMessageBox.warning(
                self,
                "Search Error",
                "The employee search could not be completed.\n\n"
                f"Details: {exc}",
            )
            employees = list(self.all_employees)

        filtered_employees = []

        search_lower = search_text.casefold()

        for employee in employees:
            employee_department = str(
                getattr(employee, "department", "") or ""
            ).strip()

            employee_status = str(
                getattr(employee, "status", "") or ""
            ).strip()

            # Search locally too, so results remain useful if the
            # service search only checks a subset of fields.
            if search_lower:
                searchable_values = [
                    getattr(employee, "employee_id", ""),
                    getattr(employee, "full_name", ""),
                    getattr(employee, "email", ""),
                    getattr(employee, "department", ""),
                    getattr(employee, "designation", ""),
                    getattr(employee, "phone", ""),
                ]

                searchable_text = " ".join(
                    str(value or "") for value in searchable_values
                ).casefold()

                if search_lower not in searchable_text:
                    continue

            if (
                department != "All Departments"
                and employee_department.casefold()
                != department.casefold()
            ):
                continue

            if (
                status != "All Status"
                and employee_status.casefold() != status.casefold()
            ):
                continue

            filtered_employees.append(employee)

        self.populate_table(filtered_employees)

        self.result_label.setText(
            f"Showing {len(filtered_employees)} of "
            f"{len(self.all_employees)} employees"
        )

    # ========================================================
    # PROFILE PHOTO
    # ========================================================

    def create_circular_photo(self, photo_path, size=42):
        """
        Create a circular employee photo.
        Missing or invalid photo files display a fallback icon.
        """
        label = QLabel()
        label.setFixedSize(size, size)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("employeePhoto")

        fallback_style = f"""
            QLabel#employeePhoto {{
                background-color: #E2E8F0;
                border: 1px solid #CBD5E1;
                border-radius: {size // 2}px;
                color: #475569;
                font-size: 18px;
                font-weight: 600;
            }}
        """

        if not photo_path:
            label.setText("👤")
            label.setStyleSheet(fallback_style)
            return label

        try:
            photo_file = Path(str(photo_path)).expanduser()

            if not photo_file.is_file():
                label.setText("👤")
                label.setStyleSheet(fallback_style)
                return label

            source_pixmap = QPixmap(str(photo_file))

            if source_pixmap.isNull():
                label.setText("👤")
                label.setStyleSheet(fallback_style)
                return label

            # Scale and crop the image into a square.
            scaled = source_pixmap.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )

            x = max(0, (scaled.width() - size) // 2)
            y = max(0, (scaled.height() - size) // 2)

            cropped = scaled.copy(x, y, size, size)

            circular = QPixmap(size, size)
            circular.fill(Qt.GlobalColor.transparent)

            painter = QPainter(circular)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(
                QPainter.RenderHint.SmoothPixmapTransform
            )

            clip_path = QPainterPath()
            clip_path.addEllipse(0, 0, size, size)
            painter.setClipPath(clip_path)
            painter.drawPixmap(0, 0, cropped)
            painter.end()

            # Add a subtle border around the photo.
            painter = QPainter(circular)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            pen = QPen()
            pen.setColor(Qt.GlobalColor.white)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(1, 1, size - 2, size - 2)
            painter.end()

            label.setPixmap(circular)
            label.setToolTip(str(photo_file))
            return label

        except Exception:
            logger.exception("Unable to display employee photo")
            label.setText("👤")
            label.setStyleSheet(fallback_style)
            return label

    # ========================================================
    # TABLE POPULATION
    # ========================================================

    def populate_table(self, employees):
        self.employee_table.setUpdatesEnabled(False)
        self.employee_table.setRowCount(0)

        try:
            for employee in employees:
                row = self.employee_table.rowCount()
                self.employee_table.insertRow(row)

                # Keep the employee object attached to the row.
                id_item = QTableWidgetItem(
                    str(getattr(employee, "id", ""))
                )
                id_item.setData(
                    Qt.ItemDataRole.UserRole,
                    getattr(employee, "id", None),
                )

                # Photo
                photo_label = self.create_circular_photo(
                    getattr(employee, "profile_photo", None),
                    42,
                )

                photo_container = QWidget()
                photo_layout = QHBoxLayout(photo_container)
                photo_layout.setContentsMargins(2, 2, 2, 2)
                photo_layout.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                photo_layout.addWidget(photo_label)

                self.employee_table.setCellWidget(
                    row, 0, photo_container
                )

                # Database ID
                self.employee_table.setItem(row, 1, id_item)

                # Employee ID
                self.employee_table.setItem(
                    row,
                    2,
                    self.make_item(
                        getattr(employee, "employee_id", "")
                    ),
                )

                # Full name
                self.employee_table.setItem(
                    row,
                    3,
                    self.make_item(
                        getattr(employee, "full_name", "")
                    ),
                )

                # Email
                self.employee_table.setItem(
                    row,
                    4,
                    self.make_item(
                        getattr(employee, "email", "")
                    ),
                )

                # Department
                self.employee_table.setItem(
                    row,
                    5,
                    self.make_item(
                        getattr(employee, "department", None) or "-"
                    ),
                )

                # Designation
                self.employee_table.setItem(
                    row,
                    6,
                    self.make_item(
                        getattr(employee, "designation", None) or "-"
                    ),
                )

                # Salary
                salary = getattr(employee, "salary", None)

                try:
                    salary_text = (
                        f"₹ {float(salary):,.2f}"
                        if salary is not None
                        else "-"
                    )
                except (TypeError, ValueError):
                    salary_text = str(salary or "-")

                self.employee_table.setItem(
                    row, 7, self.make_item(salary_text)
                )

                # Status
                employee_status = str(
                    getattr(employee, "status", "") or "Unknown"
                )

                status_item = self.make_item(
                    f"●  {employee_status}",
                    center=True,
                )

                if employee_status.casefold() == "active":
                    status_item.setForeground(
                        Qt.GlobalColor.darkGreen
                    )
                elif employee_status.casefold() == "inactive":
                    status_item.setForeground(
                        Qt.GlobalColor.darkRed
                    )

                self.employee_table.setItem(row, 8, status_item)

                # Edit button
                edit_button = QPushButton("Edit")
                edit_button.setObjectName("editButton")
                edit_button.setToolTip(
                    f"Edit {getattr(employee, 'full_name', 'employee')}"
                )
                edit_button.clicked.connect(
                    lambda checked=False, emp=employee:
                    self.open_edit_employee(emp)
                )

                self.employee_table.setCellWidget(
                    row, 9, edit_button
                )

                # Delete button
                delete_button = QPushButton("Delete")
                delete_button.setObjectName("deleteButton")
                delete_button.setToolTip(
                    f"Delete {getattr(employee, 'full_name', 'employee')}"
                )
                delete_button.clicked.connect(
                    lambda checked=False, emp=employee:
                    self.confirm_delete(emp)
                )

                self.employee_table.setCellWidget(
                    row, 10, delete_button
                )

                self.employee_table.setRowHeight(row, 58)

        finally:
            self.employee_table.setUpdatesEnabled(True)

    @staticmethod
    def make_item(value, center=False):
        item = QTableWidgetItem(str(value or ""))

        if center:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
        else:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignLeft
            )

        return item

    # ========================================================
    # ADD EMPLOYEE
    # ========================================================

    def open_add_employee(self):
        try:
            self.employee_form = EmployeeFormWindow()

            # Keep the form alive while it is open.
            self.employee_form.setAttribute(
                Qt.WidgetAttribute.WA_DeleteOnClose,
                True,
            )

            self.employee_form.destroyed.connect(
                self.refresh_employees
            )

            self.employee_form.show()
            self.employee_form.raise_()
            self.employee_form.activateWindow()

        except Exception as exc:
            logger.exception("Unable to open Add Employee form")

            QMessageBox.critical(
                self,
                "Unable to Open Form",
                f"The Add Employee form could not be opened.\n\n{exc}",
            )

    # ========================================================
    # EDIT EMPLOYEE
    # ========================================================

    def open_edit_employee(self, employee):
        try:
            self.employee_form = EmployeeFormWindow(employee)

            self.employee_form.setAttribute(
                Qt.WidgetAttribute.WA_DeleteOnClose,
                True,
            )

            self.employee_form.destroyed.connect(
                self.refresh_employees
            )

            self.employee_form.show()
            self.employee_form.raise_()
            self.employee_form.activateWindow()

        except Exception as exc:
            logger.exception("Unable to open Edit Employee form")

            QMessageBox.critical(
                self,
                "Unable to Open Form",
                f"The Edit Employee form could not be opened.\n\n{exc}",
            )

    # ========================================================
    # DELETE EMPLOYEE
    # ========================================================

    def confirm_delete(self, employee):
        employee_name = str(
            getattr(employee, "full_name", "this employee")
        )

        employee_id = getattr(employee, "id", None)

        if employee_id is None:
            QMessageBox.warning(
                self,
                "Delete Failed",
                "This employee record has no valid database ID.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            (
                f"Are you sure you want to delete "
                f"'{employee_name}'?\n\n"
                "This action may not be reversible."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            success, message = delete_employee(employee_id)

            if success:
                QMessageBox.information(
                    self,
                    "Employee Deleted",
                    str(message or "Employee deleted successfully."),
                )
                self.refresh_employees()

            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    str(message or "The employee could not be deleted."),
                )

        except Exception as exc:
            logger.exception("Unable to delete employee")

            QMessageBox.critical(
                self,
                "Delete Error",
                "An unexpected error occurred while deleting "
                "the employee.\n\n"
                f"Details: {exc}",
            )

    def export_employees(self):
        """Export the currently visible employee rows to a CSV file."""
        row_count = self.employee_table.rowCount()

        if row_count == 0:
            QMessageBox.information(
                self,
                "Export Employees",
                "There are no employee records to export."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Employee Records",
            "employee_records.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"

        try:
            with open(
                file_path, "w", newline="", encoding="utf-8-sig"
            ) as csv_file:
                writer = csv.writer(csv_file)

                headers = [
                    self.employee_table.horizontalHeaderItem(column).text()
                    for column in range(1, 9)
                ]
                writer.writerow(headers)

                for row in range(row_count):
                    values = []
                    for column in range(1, 9):
                        item = self.employee_table.item(row, column)
                        values.append(item.text() if item else "")
                    writer.writerow(values)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {row_count} employee record(s) to:\\n"
                f"{file_path}"
            )

        except (OSError, csv.Error) as exc:
            logger.exception("Unable to export employee records")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"The employee report could not be saved.\\n\\n{exc}"
            )

    # ========================================================
    # STYLING
    # ========================================================

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
                font-size: 12px;
            }

            QFrame#statCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }

            QLabel#statTitle {
                background: transparent;
                color: #64748B;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#statValue {
                background: transparent;
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
                selection-background-color: #DBEAFE;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 2px solid #2563EB;
            }

            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #0F172A;
                selection-background-color: #DBEAFE;
                selection-color: #0F172A;
                border: 1px solid #CBD5E1;
            }

            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                gridline-color: #F1F5F9;
                selection-background-color: #DBEAFE;
                selection-color: #0F172A;
                outline: none;
            }

            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #F1F5F9;
            }

            QTableWidget::item:selected {
                background-color: #DBEAFE;
                color: #0F172A;
            }

            QHeaderView::section {
                background-color: #0F172A;
                color: #FFFFFF;
                padding: 12px 8px;
                border: none;
                font-weight: 700;
            }

            QPushButton {
                border-radius: 7px;
                padding: 7px 12px;
                font-weight: 600;
            }

            QPushButton#primaryButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
            }

            QPushButton#primaryButton:hover {
                background-color: #1D4ED8;
            }

            QPushButton#primaryButton:pressed {
                background-color: #1E40AF;
            }

            QPushButton#secondaryButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
            }

            QPushButton#secondaryButton:hover {
                background-color: #F1F5F9;
            }

            QPushButton#editButton {
                background-color: #EFF6FF;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                padding: 6px 10px;
            }

            QPushButton#editButton:hover {
                background-color: #DBEAFE;
            }

            QPushButton#deleteButton {
                background-color: #FEF2F2;
                color: #DC2626;
                border: 1px solid #FECACA;
                padding: 6px 10px;
            }

            QPushButton#deleteButton:hover {
                background-color: #FEE2E2;
            }

            QPushButton:disabled {
                background-color: #E2E8F0;
                color: #94A3B8;
            }
        """)