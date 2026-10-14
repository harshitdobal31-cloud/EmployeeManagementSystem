from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from services.payroll_service import (
    get_payroll_employees,
    create_payroll,
    update_payroll,
    get_all_payroll,
    search_payroll,
    lock_payroll,
    get_payroll_summary,
)

from reports.payslip_generator import (
    generate_payslip_pdf
)

from reports.payroll_excel import (
    export_payroll_to_excel
)


# ============================================================
# PAYROLL FORM DIALOG
# ============================================================

class PayrollFormDialog(QDialog):

    def __init__(
        self,
        payroll=None,
        parent=None
    ):

        super().__init__(parent)

        self.payroll = payroll

        if payroll:

            self.setWindowTitle(
                "Edit Payroll"
            )

        else:

            self.setWindowTitle(
                "Process Payroll"
            )

        self.setMinimumSize(
            650,
            720
        )

        self.setModal(True)

        self.setup_ui()

        self.load_employees()

        self.load_months()

        if self.payroll:

            self.load_payroll_data()

        self.update_net_salary()

    # ========================================================
    # UI SETUP
    # ========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            35,
            30,
            35,
            30
        )

        main_layout.setSpacing(
            18
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        title = QLabel(
            "Edit Payroll"
            if self.payroll
            else "Process Payroll"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                24,
                QFont.Weight.Bold
            )
        )

        title.setStyleSheet(
            """
            QLabel {
                color: #0F2747;
                background: transparent;
            }
            """
        )

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Update monthly payroll information"
            if self.payroll
            else "Create monthly payroll for an employee"
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color: #6B7A90;
                font-size: 15px;
                background: transparent;
            }
            """
        )

        main_layout.addWidget(
            subtitle
        )

        # ----------------------------------------------------
        # FORM CARD
        # ----------------------------------------------------

        form_card = QFrame()

        form_card.setStyleSheet(
            """
            QFrame {
                background: #FFFFFF;
                border: 1px solid #D9E2EF;
                border-radius: 14px;
            }
            """
        )

        form_layout = QGridLayout(
            form_card
        )

        form_layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        form_layout.setHorizontalSpacing(
            18
        )

        form_layout.setVerticalSpacing(
            18
        )

        # ====================================================
        # EMPLOYEE
        # ====================================================

        employee_label = QLabel(
            "Employee:"
        )

        employee_label.setStyleSheet(
            """
            QLabel {
                color: #0F2747;
                font-size: 14px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
            """
        )

        self.employee_input = QComboBox()

        self.employee_input.setMinimumHeight(
            44
        )

        self.employee_input.setStyleSheet(
            self.combo_style()
        )

        form_layout.addWidget(
            employee_label,
            0,
            0
        )

        form_layout.addWidget(
            self.employee_input,
            0,
            1
        )

        # ====================================================
        # MONTH
        # ====================================================

        month_label = QLabel(
            "Payroll Month:"
        )

        month_label.setStyleSheet(
            employee_label.styleSheet()
        )

        self.month_input = QComboBox()

        self.month_input.setMinimumHeight(
            44
        )

        self.month_input.setStyleSheet(
            self.combo_style()
        )

        form_layout.addWidget(
            month_label,
            1,
            0
        )

        form_layout.addWidget(
            self.month_input,
            1,
            1
        )

        # ====================================================
        # BASIC SALARY
        # ====================================================

        basic_label = QLabel(
            "Basic Salary:"
        )

        basic_label.setStyleSheet(
            employee_label.styleSheet()
        )

        self.basic_salary_input = QDoubleSpinBox()

        self.basic_salary_input.setRange(
            0,
            999999999
        )

        self.basic_salary_input.setDecimals(
            2
        )

        self.basic_salary_input.setPrefix(
            "₹ "
        )

        self.basic_salary_input.setMinimumHeight(
            44
        )

        self.basic_salary_input.setReadOnly(
            True
        )

        self.basic_salary_input.setStyleSheet(
            self.spinbox_style()
        )

        form_layout.addWidget(
            basic_label,
            2,
            0
        )

        form_layout.addWidget(
            self.basic_salary_input,
            2,
            1
        )

        # ====================================================
        # ALLOWANCES
        # ====================================================

        allowances_label = QLabel(
            "Allowances:"
        )

        allowances_label.setStyleSheet(
            employee_label.styleSheet()
        )

        self.allowances_input = QDoubleSpinBox()

        self.allowances_input.setRange(
            0,
            999999999
        )

        self.allowances_input.setDecimals(
            2
        )

        self.allowances_input.setPrefix(
            "₹ "
        )

        self.allowances_input.setMinimumHeight(
            44
        )

        self.allowances_input.setStyleSheet(
            self.spinbox_style()
        )

        form_layout.addWidget(
            allowances_label,
            3,
            0
        )

        form_layout.addWidget(
            self.allowances_input,
            3,
            1
        )

        # ====================================================
        # DEDUCTIONS
        # ====================================================

        deductions_label = QLabel(
            "Deductions:"
        )

        deductions_label.setStyleSheet(
            employee_label.styleSheet()
        )

        self.deductions_input = QDoubleSpinBox()

        self.deductions_input.setRange(
            0,
            999999999
        )

        self.deductions_input.setDecimals(
            2
        )

        self.deductions_input.setPrefix(
            "₹ "
        )

        self.deductions_input.setMinimumHeight(
            44
        )

        self.deductions_input.setStyleSheet(
            self.spinbox_style()
        )

        form_layout.addWidget(
            deductions_label,
            4,
            0
        )

        form_layout.addWidget(
            self.deductions_input,
            4,
            1
        )

        main_layout.addWidget(
            form_card
        )

        # ====================================================
        # SALARY PREVIEW
        # ====================================================

        preview_card = QFrame()

        preview_card.setStyleSheet(
            """
            QFrame {
                background: #F4F8FF;
                border: 1px solid #BBD7FF;
                border-radius: 14px;
            }
            """
        )

        preview_layout = QVBoxLayout(
            preview_card
        )

        preview_layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        preview_title = QLabel(
            "Salary Preview"
        )

        preview_title.setStyleSheet(
            """
            QLabel {
                color: #164A9B;
                font-size: 14px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            """
        )

        preview_layout.addWidget(
            preview_title
        )

        self.net_salary_label = QLabel(
            "₹ 0.00"
        )

        self.net_salary_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            |
            Qt.AlignmentFlag.AlignVCenter
        )

        self.net_salary_label.setMinimumHeight(
            55
        )

        self.net_salary_label.setStyleSheet(
            """
            QLabel {
                color: #2563EB;
                background: #FFFFFF;
                border: 1px solid #BBD7FF;
                border-radius: 10px;
                font-size: 30px;
                font-weight: 700;
                padding-left: 12px;
            }
            """
        )

        preview_layout.addWidget(
            self.net_salary_label
        )

        main_layout.addWidget(
            preview_card
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        cancel_button = QPushButton(
            "Cancel"
        )

        cancel_button.setMinimumSize(
            110,
            44
        )

        cancel_button.setStyleSheet(
            """
            QPushButton {
                background: #E7ECF3;
                color: #1F2937;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 8px 18px;
            }

            QPushButton:hover {
                background: #D8E0EA;
            }
            """
        )

        cancel_button.clicked.connect(
            self.reject
        )

        save_button = QPushButton(
            "Update Payroll"
            if self.payroll
            else "Process Payroll"
        )

        save_button.setMinimumSize(
            150,
            44
        )

        save_button.setStyleSheet(
            """
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 18px;
            }

            QPushButton:hover {
                background: #1D4ED8;
            }

            QPushButton:pressed {
                background: #1E40AF;
            }
            """
        )

        save_button.clicked.connect(
            self.save_payroll
        )

        button_layout.addWidget(
            save_button
        )

        button_layout.addWidget(
            cancel_button
        )

        main_layout.addLayout(
            button_layout
        )

        # ====================================================
        # SIGNALS
        # ====================================================

        self.employee_input.currentIndexChanged.connect(
            self.on_employee_changed
        )

        self.allowances_input.valueChanged.connect(
            self.update_net_salary
        )

        self.deductions_input.valueChanged.connect(
            self.update_net_salary
        )

    # ========================================================
    # COMBO STYLE
    # ========================================================

    def combo_style(self):

        return """
        QComboBox {
            background: #FFFFFF;
            color: #0F2747;
            border: 1px solid #C9D5E5;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
        }

        QComboBox:hover {
            border: 1px solid #7AA7E8;
        }

        QComboBox:focus {
            border: 1px solid #2563EB;
        }

        QComboBox::drop-down {
            border: none;
            width: 35px;
        }

        QComboBox QAbstractItemView {
            background: #FFFFFF;
            color: #0F2747;
            border: 1px solid #C9D5E5;
            selection-background-color: #2563EB;
            selection-color: #FFFFFF;
            padding: 5px;
        }
        """

    # ========================================================
    # SPINBOX STYLE
    # ========================================================

    def spinbox_style(self):

        return """
        QDoubleSpinBox {
            background: #FFFFFF;
            color: #0F2747;
            border: 1px solid #C9D5E5;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
        }

        QDoubleSpinBox:focus {
            border: 1px solid #2563EB;
        }

        QDoubleSpinBox:read-only {
            background: #F5F7FA;
            color: #53657A;
        }
        """

    # ========================================================
    # LOAD EMPLOYEES
    # ========================================================

    def load_employees(self):

        self.employee_input.clear()

        self.employee_input.addItem(
            "Select Employee",
            None
        )

        try:

            employees = get_payroll_employees()

            for employee in employees:

                display_text = (
                    f"{employee.employee_id} - "
                    f"{employee.full_name}"
                )

                self.employee_input.addItem(
                    display_text,
                    employee.id
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                f"Unable to load employees.\n\n{error}"
            )

    # ========================================================
    # LOAD MONTHS
    # ========================================================

    def load_months(self):

        self.month_input.clear()

        self.month_input.addItem(
            "Select Payroll Month",
            None
        )

        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        for month in months:

            self.month_input.addItem(
                month,
                month
            )

    # ========================================================
    # EMPLOYEE CHANGED
    # ========================================================

    def on_employee_changed(
        self,
        index
    ):

        employee_id = (
            self.employee_input.itemData(
                index
            )
        )

        if employee_id is None:

            self.basic_salary_input.setValue(
                0
            )

            self.update_net_salary()

            return

        try:

            employees = get_payroll_employees()

            for employee in employees:

                if employee.id == employee_id:

                    self.basic_salary_input.setValue(
                        float(
                            employee.salary or 0
                        )
                    )

                    break

            self.update_net_salary()

        except Exception as error:

            QMessageBox.warning(
                self,
                "Error",
                f"Unable to load employee salary.\n\n{error}"
            )

    # ========================================================
    # LOAD EXISTING PAYROLL
    # ========================================================

    def load_payroll_data(self):

        if not self.payroll:

            return

        employee_index = (
            self.employee_input.findData(
                self.payroll.employee_id
            )
        )

        if employee_index >= 0:

            self.employee_input.setCurrentIndex(
                employee_index
            )

        month_index = (
            self.month_input.findData(
                self.payroll.payroll_month
            )
        )

        if month_index >= 0:

            self.month_input.setCurrentIndex(
                month_index
            )

        self.basic_salary_input.setValue(
            float(
                self.payroll.basic_salary or 0
            )
        )

        self.allowances_input.setValue(
            float(
                self.payroll.allowances or 0
            )
        )

        self.deductions_input.setValue(
            float(
                self.payroll.deductions or 0
            )
        )

        self.employee_input.setEnabled(
            False
        )

        self.month_input.setEnabled(
            False
        )

    # ========================================================
    # UPDATE NET SALARY
    # ========================================================

    def update_net_salary(self):

        basic_salary = (
            self.basic_salary_input.value()
        )

        allowances = (
            self.allowances_input.value()
        )

        deductions = (
            self.deductions_input.value()
        )

        net_salary = (
            basic_salary
            + allowances
            - deductions
        )

        if net_salary < 0:

            net_salary = 0

        self.net_salary_label.setText(
            f"₹ {net_salary:,.2f}"
        )

    # ========================================================
    # SAVE PAYROLL
    # ========================================================

    def save_payroll(self):

        employee_id = (
            self.employee_input.currentData()
        )

        payroll_month = (
            self.month_input.currentData()
        )

        allowances = (
            self.allowances_input.value()
        )

        deductions = (
            self.deductions_input.value()
        )

        if employee_id is None:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select an employee."
            )

            return

        if payroll_month is None:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select a payroll month."
            )

            return

        if self.payroll:

            success, message = update_payroll(
                self.payroll.id,
                allowances,
                deductions
            )

        else:

            success, message = create_payroll(
                employee_id=employee_id,
                payroll_month=payroll_month,
                allowances=allowances,
                deductions=deductions
            )

        if success:

            QMessageBox.information(
                self,
                "Success",
                message
            )

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Payroll Error",
                message
            )


# ============================================================
# PAYROLL MANAGEMENT WINDOW
# ============================================================

class PayrollWindow(QWidget):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)

        self.setWindowTitle(
            "Payroll Management"
        )

        self.setMinimumSize(
            1350,
            800
        )

        self.setup_ui()

        self.load_summary()

        self.load_payroll()

    # ========================================================
    # UI SETUP
    # ========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        main_layout.setSpacing(
            20
        )

        # ====================================================
        # HEADER
        # ====================================================

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "Payroll Management"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                26,
                QFont.Weight.Bold
            )
        )

        title.setStyleSheet(
            """
            QLabel {
                color: #0F2747;
            }
            """
        )

        subtitle = QLabel(
            "Process, manage and track employee payroll"
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color: #718096;
                font-size: 14px;
            }
            """
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

        # ----------------------------------------------------
        # EXPORT EXCEL BUTTON
        # ----------------------------------------------------

        export_button = QPushButton(
            "Export Excel"
        )

        export_button.setMinimumSize(
            140,
            45
        )

        export_button.setStyleSheet(
            """
            QPushButton {
                background: #E8F5E9;
                color: #166534;
                border: 1px solid #BBF7D0;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background: #DCFCE7;
            }

            QPushButton:pressed {
                background: #BBF7D0;
            }
            """
        )

        export_button.clicked.connect(
            self.export_excel
        )

        header_layout.addWidget(
            export_button
        )

        # ----------------------------------------------------
        # PROCESS PAYROLL BUTTON
        # ----------------------------------------------------

        add_button = QPushButton(
            "+ Process Payroll"
        )

        add_button.setMinimumSize(
            170,
            45
        )

        add_button.setStyleSheet(
            """
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background: #1D4ED8;
            }
            """
        )

        add_button.clicked.connect(
            self.open_add_payroll
        )

        header_layout.addWidget(
            add_button
        )

        main_layout.addLayout(
            header_layout
        )

        # ====================================================
        # SUMMARY CARDS
        # ====================================================

        cards_layout = QHBoxLayout()

        self.total_card = (
            self.create_summary_card(
                "Total Payroll",
                "0"
            )
        )

        self.processed_card = (
            self.create_summary_card(
                "Processed",
                "0"
            )
        )

        self.locked_card = (
            self.create_summary_card(
                "Locked",
                "0"
            )
        )

        self.net_card = (
            self.create_summary_card(
                "Total Net Payroll",
                "₹ 0.00"
            )
        )

        cards_layout.addWidget(
            self.total_card
        )

        cards_layout.addWidget(
            self.processed_card
        )

        cards_layout.addWidget(
            self.locked_card
        )

        cards_layout.addWidget(
            self.net_card
        )

        main_layout.addLayout(
            cards_layout
        )

        # ====================================================
        # SEARCH + FILTERS
        # ====================================================

        filter_layout = QHBoxLayout()

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search by employee ID, employee name or payroll month..."
        )

        self.search_input.setMinimumHeight(
            44
        )

        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background: white;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 14px;
                color: #0F2747;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #2563EB;
            }
            """
        )

        self.search_input.textChanged.connect(
            self.load_payroll
        )

        filter_layout.addWidget(
            self.search_input,
            4
        )

        # ----------------------------------------------------
        # MONTH FILTER
        # ----------------------------------------------------

        self.month_filter = QComboBox()

        self.month_filter.setMinimumSize(
            180,
            44
        )

        self.month_filter.setStyleSheet(
            self.filter_combo_style()
        )

        self.month_filter.addItem(
            "All Months"
        )

        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        for month in months:

            self.month_filter.addItem(
                month
            )

        self.month_filter.currentIndexChanged.connect(
            self.load_payroll
        )

        filter_layout.addWidget(
            self.month_filter
        )

        # ----------------------------------------------------
        # STATUS FILTER
        # ----------------------------------------------------

        self.status_filter = QComboBox()

        self.status_filter.setMinimumSize(
            160,
            44
        )

        self.status_filter.setStyleSheet(
            self.filter_combo_style()
        )

        self.status_filter.addItems(
            [
                "All Status",
                "Processed",
                "Locked",
            ]
        )

        self.status_filter.currentIndexChanged.connect(
            self.load_payroll
        )

        filter_layout.addWidget(
            self.status_filter
        )

        # ----------------------------------------------------
        # REFRESH
        # ----------------------------------------------------

        refresh_button = QPushButton(
            "Refresh"
        )

        refresh_button.setMinimumSize(
            100,
            44
        )

        refresh_button.setStyleSheet(
            """
            QPushButton {
                background: #E8EEF7;
                color: #0F2747;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #D8E3F2;
            }
            """
        )

        refresh_button.clicked.connect(
            self.refresh_page
        )

        filter_layout.addWidget(
            refresh_button
        )

        main_layout.addLayout(
            filter_layout
        )

        # ====================================================
        # HISTORY LABEL
        # ====================================================

        history_label = QLabel(
            "Payroll History"
        )

        history_label.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Weight.Bold
            )
        )

        history_label.setStyleSheet(
            """
            QLabel {
                color: #0F2747;
                margin-top: 4px;
            }
            """
        )

        main_layout.addWidget(
            history_label
        )

        # ====================================================
        # TABLE
        # ====================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            12
        )

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Employee ID",
                "Employee Name",
                "Month",
                "Basic Salary",
                "Allowances",
                "Deductions",
                "Net Salary",
                "Status",
                "Edit",
                "Payslip",
                "Action",
            ]
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setStyleSheet(
            """
            QTableWidget {
                background: white;
                alternate-background-color: #F8FAFC;
                border: 1px solid #D9E2EF;
                border-radius: 10px;
                gridline-color: #E5EAF1;
                color: #0F2747;
                font-size: 13px;
            }

            QHeaderView::section {
                background: #F1F5F9;
                color: #0F2747;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #D9E2EF;
                font-weight: 700;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QTableWidget::item:selected {
                background: #DBEAFE;
                color: #0F2747;
            }
            """
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        main_layout.addWidget(
            self.table
        )

    # ========================================================
    # FILTER COMBO STYLE
    # ========================================================

    def filter_combo_style(self):

        return """
        QComboBox {
            background: white;
            color: #0F2747;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
        }

        QComboBox:hover {
            border: 1px solid #7AA7E8;
        }

        QComboBox:focus {
            border: 1px solid #2563EB;
        }

        QComboBox::drop-down {
            border: none;
            width: 30px;
        }

        QComboBox QAbstractItemView {
            background: white;
            color: #0F2747;
            border: 1px solid #CBD5E1;
            selection-background-color: #2563EB;
            selection-color: white;
        }
        """

    # ========================================================
    # SUMMARY CARD
    # ========================================================

    def create_summary_card(
        self,
        title,
        value
    ):

        card = QFrame()

        card.setMinimumHeight(
            105
        )

        card.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #D9E2EF;
                border-radius: 12px;
            }
            """
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            """
            QLabel {
                color: #718096;
                font-size: 13px;
                background: transparent;
                border: none;
            }
            """
        )

        value_label = QLabel(
            value
        )

        value_label.setFont(
            QFont(
                "Segoe UI",
                21,
                QFont.Weight.Bold
            )
        )

        value_label.setStyleSheet(
            """
            QLabel {
                color: #2563EB;
                background: transparent;
                border: none;
            }
            """
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        card.value_label = value_label

        return card

    # ========================================================
    # LOAD SUMMARY
    # ========================================================

    def load_summary(self):

        try:

            summary = get_payroll_summary()

            self.total_card.value_label.setText(
                str(
                    summary["total_payroll"]
                )
            )

            self.processed_card.value_label.setText(
                str(
                    summary["processed"]
                )
            )

            self.locked_card.value_label.setText(
                str(
                    summary["locked"]
                )
            )

            self.net_card.value_label.setText(
                f"₹ {summary['total_net']:,.2f}"
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "Error",
                f"Unable to load payroll summary.\n\n{error}"
            )

    # ========================================================
    # LOAD PAYROLL HISTORY
    # ========================================================

    def load_payroll(self):

        search_text = (
            self.search_input.text().strip()
        )

        payroll_month = (
            self.month_filter.currentText()
        )

        status = (
            self.status_filter.currentText()
        )

        try:

            records = search_payroll(
                search_text=search_text,
                payroll_month=payroll_month,
                status=status
            )

            self.table.setRowCount(
                len(records)
            )

            for row, record in enumerate(
                records
            ):

                payroll = record[0]

                employee = record[1]

                # ------------------------------------------------
                # ID
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        str(payroll.id)
                    )
                )

                # ------------------------------------------------
                # Employee ID
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        employee.employee_id
                    )
                )

                # ------------------------------------------------
                # Employee Name
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        employee.full_name
                    )
                )

                # ------------------------------------------------
                # Month
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        payroll.payroll_month
                    )
                )

                # ------------------------------------------------
                # Basic Salary
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        f"₹ {float(payroll.basic_salary or 0):,.2f}"
                    )
                )

                # ------------------------------------------------
                # Allowances
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    5,
                    QTableWidgetItem(
                        f"₹ {float(payroll.allowances or 0):,.2f}"
                    )
                )

                # ------------------------------------------------
                # Deductions
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    6,
                    QTableWidgetItem(
                        f"₹ {float(payroll.deductions or 0):,.2f}"
                    )
                )

                # ------------------------------------------------
                # Net Salary
                # ------------------------------------------------

                self.table.setItem(
                    row,
                    7,
                    QTableWidgetItem(
                        f"₹ {float(payroll.net_salary or 0):,.2f}"
                    )
                )

                # ------------------------------------------------
                # Status
                # ------------------------------------------------

                status_item = QTableWidgetItem(
                    payroll.status
                )

                status_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    8,
                    status_item
                )

                # =================================================
                # EDIT BUTTON
                # =================================================

                edit_button = QPushButton(
                    "Edit"
                )

                edit_button.setStyleSheet(
                    """
                    QPushButton {
                        background: #E0ECFF;
                        color: #1D4ED8;
                        border: none;
                        border-radius: 6px;
                        padding: 7px 10px;
                        font-weight: 600;
                    }

                    QPushButton:hover {
                        background: #C7DBFF;
                    }
                    """
                )

                edit_button.clicked.connect(
                    lambda checked=False,
                    payroll_id=payroll.id:
                    self.edit_payroll(
                        payroll_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    9,
                    edit_button
                )

                # =================================================
                # PDF PAYSLIP BUTTON
                # =================================================

                payslip_button = QPushButton(
                    "PDF"
                )

                payslip_button.setStyleSheet(
                    """
                    QPushButton {
                        background: #E8F5E9;
                        color: #166534;
                        border: none;
                        border-radius: 6px;
                        padding: 7px 10px;
                        font-weight: 600;
                    }

                    QPushButton:hover {
                        background: #DCFCE7;
                    }
                    """
                )

                payslip_button.clicked.connect(
                    lambda checked=False,
                    payroll_id=payroll.id:
                    self.generate_payslip(
                        payroll_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    10,
                    payslip_button
                )

                # =================================================
                # ACTION BUTTON
                # =================================================

                if payroll.status == "Locked":

                    action_button = QPushButton(
                        "Locked"
                    )

                    action_button.setEnabled(
                        False
                    )

                    action_button.setStyleSheet(
                        """
                        QPushButton {
                            background: #E5E7EB;
                            color: #6B7280;
                            border: none;
                            border-radius: 6px;
                            padding: 7px 10px;
                        }
                        """
                    )

                else:

                    action_button = QPushButton(
                        "Lock"
                    )

                    action_button.setStyleSheet(
                        """
                        QPushButton {
                            background: #FEF3C7;
                            color: #92400E;
                            border: none;
                            border-radius: 6px;
                            padding: 7px 10px;
                            font-weight: 600;
                        }

                        QPushButton:hover {
                            background: #FDE68A;
                        }
                        """
                    )

                    action_button.clicked.connect(
                        lambda checked=False,
                        payroll_id=payroll.id:
                        self.lock_payroll_record(
                            payroll_id
                        )
                    )

                self.table.setCellWidget(
                    row,
                    11,
                    action_button
                )

            self.table.resizeRowsToContents()

        except Exception as error:

            QMessageBox.warning(
                self,
                "Error",
                f"Unable to load payroll records.\n\n{error}"
            )

    # ========================================================
    # EXPORT FILTERED PAYROLL TO EXCEL
    # ========================================================

    def export_excel(self):

        search_text = (
            self.search_input.text().strip()
        )

        payroll_month = (
            self.month_filter.currentText()
        )

        status = (
            self.status_filter.currentText()
        )

        try:

            records = search_payroll(
                search_text=search_text,
                payroll_month=payroll_month,
                status=status
            )

            if not records:

                QMessageBox.information(
                    self,
                    "No Payroll Data",
                    "There are no payroll records available "
                    "for the selected filters."
                )

                return

            file_path = export_payroll_to_excel(
                records
            )

            QMessageBox.information(
                self,
                "Excel Export Successful",
                "Payroll history exported successfully.\n\n"
                f"Saved at:\n{file_path}"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Excel Export Error",
                "Unable to export payroll history.\n\n"
                f"{error}"
            )

    # ========================================================
    # ADD PAYROLL
    # ========================================================

    def open_add_payroll(self):

        dialog = PayrollFormDialog(
            parent=self
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):

            self.refresh_page()

    # ========================================================
    # EDIT PAYROLL
    # ========================================================

    def edit_payroll(
        self,
        payroll_id
    ):

        payroll_records = get_all_payroll()

        payroll = None

        for record in payroll_records:

            if record.id == payroll_id:

                payroll = record

                break

        if payroll is None:

            QMessageBox.warning(
                self,
                "Error",
                "Payroll record not found."
            )

            return

        if payroll.status == "Locked":

            QMessageBox.warning(
                self,
                "Locked Payroll",
                "This payroll is locked and cannot be modified."
            )

            return

        dialog = PayrollFormDialog(
            payroll=payroll,
            parent=self
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):

            self.refresh_page()

    # ========================================================
    # GENERATE PDF PAYSLIP
    # ========================================================

    def generate_payslip(
        self,
        payroll_id
    ):

        payroll_records = get_all_payroll()

        payroll = None

        for record in payroll_records:

            if record.id == payroll_id:

                payroll = record

                break

        if payroll is None:

            QMessageBox.warning(
                self,
                "Error",
                "Payroll record not found."
            )

            return

        try:

            employees = get_payroll_employees()

            employee = None

            for item in employees:

                if item.id == payroll.employee_id:

                    employee = item

                    break

            if employee is None:

                QMessageBox.warning(
                    self,
                    "Employee Not Found",
                    "The employee associated with this payroll "
                    "record could not be found."
                )

                return

            file_path = generate_payslip_pdf(
                payroll=payroll,
                employee=employee
            )

            QMessageBox.information(
                self,
                "Payslip Generated",
                "Payslip generated successfully.\n\n"
                f"Saved at:\n{file_path}"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "PDF Error",
                "Unable to generate payslip.\n\n"
                f"{error}"
            )

    # ========================================================
    # LOCK PAYROLL
    # ========================================================

    def lock_payroll_record(
        self,
        payroll_id
    ):

        answer = QMessageBox.question(
            self,
            "Lock Payroll",
            "Are you sure you want to lock this payroll?\n\n"
            "A locked payroll cannot be modified or deleted.",
            QMessageBox.StandardButton.Yes
            |
            QMessageBox.StandardButton.No
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):

            return

        success, message = lock_payroll(
            payroll_id
        )

        if success:

            QMessageBox.information(
                self,
                "Success",
                message
            )

            self.refresh_page()

        else:

            QMessageBox.warning(
                self,
                "Error",
                message
            )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_page(self):

        self.load_summary()

        self.load_payroll()