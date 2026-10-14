import re

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QPushButton,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QFrame,
)

from services.employee_service import (
    add_employee,
    update_employee,
)


class EmployeeFormWindow(QWidget):

    def __init__(self, employee=None):

        super().__init__()

        self.employee = employee
        self.is_edit_mode = employee is not None
        self.profile_photo_path = None

        if self.is_edit_mode:

            self.setWindowTitle(
                "Employee Management System | Edit Employee"
            )

        else:

            self.setWindowTitle(
                "Employee Management System | Add Employee"
            )

        self.setMinimumSize(
            1150,
            800
        )

        self.setup_ui()

        if self.is_edit_mode:
            self.load_employee_data()

    # ========================================================
    # MAIN UI
    # ========================================================

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

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "Edit Employee"
            if self.is_edit_mode
            else "Add New Employee"
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            "Update employee information and maintain the profile."
            if self.is_edit_mode
            else "Create and maintain a complete employee profile."
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addLayout(
            title_layout
        )

        header_layout.addStretch()

        close_button = QPushButton(
            "✕  Close"
        )

        close_button.setObjectName(
            "secondaryButton"
        )

        close_button.setFixedSize(
            110,
            40
        )

        close_button.clicked.connect(
            self.close
        )

        header_layout.addWidget(
            close_button
        )

        main_layout.addLayout(
            header_layout
        )

        # ----------------------------------------------------
        # LINE
        # ----------------------------------------------------

        line = QFrame()

        line.setFrameShape(
            QFrame.Shape.HLine
        )

        line.setObjectName(
            "separator"
        )

        main_layout.addWidget(
            line
        )

        # ----------------------------------------------------
        # SCROLL AREA
        # ----------------------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        content = QWidget()

        content_layout = QVBoxLayout()

        content_layout.setSpacing(
            18
        )

        # ----------------------------------------------------
        # PROFILE + BASIC INFORMATION
        # ----------------------------------------------------

        top_layout = QHBoxLayout()

        top_layout.setSpacing(
            18
        )

        profile_card = (
            self.create_profile_card()
        )

        basic_card = (
            self.create_basic_card()
        )

        top_layout.addWidget(
            profile_card
        )

        top_layout.addWidget(
            basic_card,
            1
        )

        content_layout.addLayout(
            top_layout
        )

        # ----------------------------------------------------
        # EMPLOYMENT
        # ----------------------------------------------------

        employment_card = (
            self.create_employment_card()
        )

        content_layout.addWidget(
            employment_card
        )

        # ----------------------------------------------------
        # LOGIN ACCOUNT
        # ----------------------------------------------------

        login_card = (
            self.create_login_card()
        )

        content_layout.addWidget(
            login_card
        )

        # ----------------------------------------------------
        # CONTACT
        # ----------------------------------------------------

        contact_card = (
            self.create_contact_card()
        )

        content_layout.addWidget(
            contact_card
        )

        # ----------------------------------------------------
        # EMERGENCY + BANK
        # ----------------------------------------------------

        bottom_layout = QHBoxLayout()

        bottom_layout.setSpacing(
            18
        )

        emergency_card = (
            self.create_emergency_card()
        )

        bank_card = (
            self.create_bank_card()
        )

        bottom_layout.addWidget(
            emergency_card
        )

        bottom_layout.addWidget(
            bank_card
        )

        content_layout.addLayout(
            bottom_layout
        )

        content.setLayout(
            content_layout
        )

        scroll.setWidget(
            content
        )

        main_layout.addWidget(
            scroll
        )

        # ----------------------------------------------------
        # ACTION BUTTONS
        # ----------------------------------------------------

        buttons = QHBoxLayout()

        buttons.addStretch()

        cancel_button = QPushButton(
            "Cancel"
        )

        cancel_button.setObjectName(
            "secondaryButton"
        )

        cancel_button.setFixedSize(
            130,
            45
        )

        cancel_button.clicked.connect(
            self.close
        )

        save_button = QPushButton(
            "✓  Update Employee"
            if self.is_edit_mode
            else "✓  Save Employee"
        )

        save_button.setObjectName(
            "primaryButton"
        )

        save_button.setFixedSize(
            180,
            45
        )

        save_button.clicked.connect(
            self.save_employee
        )

        buttons.addWidget(
            cancel_button
        )

        buttons.addWidget(
            save_button
        )

        main_layout.addLayout(
            buttons
        )

        self.setLayout(
            main_layout
        )

        self.apply_styles()

    # ========================================================
    # PROFILE CARD
    # ========================================================

    def create_profile_card(self):

        card = QGroupBox(
            "Employee Profile"
        )

        card.setMinimumWidth(
            280
        )

        layout = QVBoxLayout()

        layout.setSpacing(
            12
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        self.photo_label = QLabel(
            "No Photo"
        )

        self.photo_label.setObjectName(
            "photoPreview"
        )

        self.photo_label.setFixedSize(
            150,
            150
        )

        self.photo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.photo_label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        upload_button = QPushButton(
            "Upload Profile Photo"
        )

        upload_button.setObjectName(
            "outlineButton"
        )

        upload_button.clicked.connect(
            self.upload_photo
        )

        layout.addWidget(
            upload_button
        )

        note = QLabel(
            "JPG or PNG • Maximum 5 MB"
        )

        note.setObjectName(
            "helperText"
        )

        note.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            note
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.create_label(
                "Employee Status"
            )
        )

        self.status_input = QComboBox()

        self.status_input.addItems([
            "Active",
            "Inactive"
        ])

        layout.addWidget(
            self.status_input
        )

        card.setLayout(
            layout
        )

        return card

    # ========================================================
    # BASIC INFORMATION
    # ========================================================

    def create_basic_card(self):

        card = QGroupBox(
            "Basic Information"
        )

        form = QFormLayout()

        form.setSpacing(
            14
        )

        self.employee_id_input = (
            self.create_line_edit(
                "Example: EMP002"
            )
        )

        self.full_name_input = (
            self.create_line_edit(
                "Enter full name"
            )
        )

        self.email_input = (
            self.create_line_edit(
                "employee@example.com"
            )
        )

        self.phone_input = (
            self.create_line_edit(
                "10-digit mobile number"
            )
        )

        self.gender_input = QComboBox()

        self.gender_input.addItems([
            "Select Gender",
            "Male",
            "Female",
            "Other"
        ])

        self.date_of_birth_input = QDateEdit()

        self.date_of_birth_input.setCalendarPopup(
            True
        )

        self.date_of_birth_input.setDisplayFormat(
            "dd-MM-yyyy"
        )

        self.date_of_birth_input.setDate(
            QDate(
                2000,
                1,
                1
            )
        )

        form.addRow(
            self.create_label(
                "Employee ID *"
            ),
            self.employee_id_input
        )

        form.addRow(
            self.create_label(
                "Full Name *"
            ),
            self.full_name_input
        )

        form.addRow(
            self.create_label(
                "Email *"
            ),
            self.email_input
        )

        form.addRow(
            self.create_label(
                "Phone"
            ),
            self.phone_input
        )

        form.addRow(
            self.create_label(
                "Gender"
            ),
            self.gender_input
        )

        form.addRow(
            self.create_label(
                "Date of Birth"
            ),
            self.date_of_birth_input
        )

        card.setLayout(
            form
        )

        return card

    # ========================================================
    # EMPLOYMENT CARD
    # ========================================================

    def create_employment_card(self):

        card = QGroupBox(
            "Employment Information"
        )

        layout = QGridLayout()

        layout.setHorizontalSpacing(
            20
        )

        layout.setVerticalSpacing(
            14
        )

        self.department_input = QComboBox()

        self.department_input.addItems([
            "Select Department",
            "Human Resources",
            "Information Technology",
            "Finance",
            "Administration"
        ])

        self.designation_input = (
            self.create_line_edit(
                "Example: Software Developer"
            )
        )

        self.employment_type_input = QComboBox()

        self.employment_type_input.addItems([
            "Select Employment Type",
            "Full Time",
            "Part Time",
            "Contract",
            "Intern"
        ])

        self.joining_date_input = QDateEdit()

        self.joining_date_input.setCalendarPopup(
            True
        )

        self.joining_date_input.setDisplayFormat(
            "dd-MM-yyyy"
        )

        self.joining_date_input.setDate(
            QDate.currentDate()
        )

        self.salary_input = QDoubleSpinBox()

        self.salary_input.setMinimum(
            0
        )

        self.salary_input.setMaximum(
            100000000
        )

        self.salary_input.setDecimals(
            2
        )

        self.salary_input.setPrefix(
            "₹ "
        )

        layout.addWidget(
            self.create_label(
                "Department"
            ),
            0,
            0
        )

        layout.addWidget(
            self.department_input,
            0,
            1
        )

        layout.addWidget(
            self.create_label(
                "Designation"
            ),
            0,
            2
        )

        layout.addWidget(
            self.designation_input,
            0,
            3
        )

        layout.addWidget(
            self.create_label(
                "Employment Type"
            ),
            1,
            0
        )

        layout.addWidget(
            self.employment_type_input,
            1,
            1
        )

        layout.addWidget(
            self.create_label(
                "Joining Date"
            ),
            1,
            2
        )

        layout.addWidget(
            self.joining_date_input,
            1,
            3
        )

        layout.addWidget(
            self.create_label(
                "Monthly Salary"
            ),
            2,
            0
        )

        layout.addWidget(
            self.salary_input,
            2,
            1
        )

        card.setLayout(
            layout
        )

        return card

    # ========================================================
    # LOGIN ACCOUNT CARD
    # ========================================================

    def create_login_card(self):

        card = QGroupBox(
            "🔐 Employee Login Account"
        )

        layout = QGridLayout()

        layout.setHorizontalSpacing(
            20
        )

        layout.setVerticalSpacing(
            14
        )

        # ----------------------------------------------------
        # USERNAME
        # ----------------------------------------------------

        self.login_username_input = (
            self.create_line_edit(
                "Employee ID"
            )
        )

        self.login_username_input.setReadOnly(
            True
        )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        self.login_password_input = (
            self.create_password_edit(
                "Enter login password"
            )
        )

        # ----------------------------------------------------
        # CONFIRM PASSWORD
        # ----------------------------------------------------

        self.confirm_password_input = (
            self.create_password_edit(
                "Confirm login password"
            )
        )

        # ----------------------------------------------------
        # INFO
        # ----------------------------------------------------

        self.login_info_label = QLabel()

        if self.is_edit_mode:

            self.login_info_label.setText(
                "Leave password fields empty to keep the existing password."
            )

        else:

            self.login_info_label.setText(
                "Employee will use Employee ID and this password to login."
            )

        self.login_info_label.setObjectName(
            "helperText"
        )

        # ----------------------------------------------------
        # ADD ROWS
        # ----------------------------------------------------

        layout.addWidget(
            self.create_label(
                "Login Username"
            ),
            0,
            0
        )

        layout.addWidget(
            self.login_username_input,
            0,
            1
        )

        layout.addWidget(
            self.create_label(
                "Login Password"
            ),
            1,
            0
        )

        layout.addWidget(
            self.login_password_input,
            1,
            1
        )

        layout.addWidget(
            self.create_label(
                "Confirm Password"
            ),
            2,
            0
        )

        layout.addWidget(
            self.confirm_password_input,
            2,
            1
        )

        layout.addWidget(
            self.login_info_label,
            3,
            0,
            1,
            2
        )

        card.setLayout(
            layout
        )

        return card

    # ========================================================
    # PASSWORD FIELD
    # ========================================================

    def create_password_edit(
        self,
        placeholder=""
    ):

        field = QLineEdit()

        field.setPlaceholderText(
            placeholder
        )

        field.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        field.setMinimumHeight(
            38
        )

        return field

    # ========================================================
    # CONTACT CARD
    # ========================================================

    def create_contact_card(self):

        card = QGroupBox(
            "Contact & Address"
        )

        layout = QVBoxLayout()

        layout.addWidget(
            self.create_label(
                "Residential Address"
            )
        )

        self.address_input = QTextEdit()

        self.address_input.setPlaceholderText(
            "Enter complete residential address..."
        )

        self.address_input.setMinimumHeight(
            90
        )

        layout.addWidget(
            self.address_input
        )

        card.setLayout(
            layout
        )

        return card

    # ========================================================
    # EMERGENCY CARD
    # ========================================================

    def create_emergency_card(self):

        card = QGroupBox(
            "Emergency Contact"
        )

        form = QFormLayout()

        form.setSpacing(
            14
        )

        self.emergency_name_input = (
            self.create_line_edit(
                "Contact person's name"
            )
        )

        self.emergency_phone_input = (
            self.create_line_edit(
                "10-digit phone number"
            )
        )

        form.addRow(
            self.create_label(
                "Contact Name"
            ),
            self.emergency_name_input
        )

        form.addRow(
            self.create_label(
                "Phone"
            ),
            self.emergency_phone_input
        )

        card.setLayout(
            form
        )

        return card

    # ========================================================
    # BANK CARD
    # ========================================================

    def create_bank_card(self):

        card = QGroupBox(
            "Bank Information"
        )

        form = QFormLayout()

        form.setSpacing(
            14
        )

        self.bank_account_input = (
            self.create_line_edit(
                "Enter bank account number"
            )
        )

        form.addRow(
            self.create_label(
                "Bank Account"
            ),
            self.bank_account_input
        )

        note = QLabel(
            "Used for payroll processing."
        )

        note.setObjectName(
            "helperText"
        )

        form.addRow(
            "",
            note
        )

        card.setLayout(
            form
        )

        return card

    # ========================================================
    # LOAD EMPLOYEE FOR EDIT
    # ========================================================

    def load_employee_data(self):

        employee = self.employee

        self.employee_id_input.setText(
            employee.employee_id or ""
        )

        # Employee ID should not be changed
        self.employee_id_input.setReadOnly(
            True
        )

        self.login_username_input.setText(
            employee.employee_id or ""
        )

        self.full_name_input.setText(
            employee.full_name or ""
        )

        self.email_input.setText(
            employee.email or ""
        )

        self.phone_input.setText(
            employee.phone or ""
        )

        # Gender

        gender_index = (
            self.gender_input.findText(
                employee.gender or ""
            )
        )

        if gender_index >= 0:

            self.gender_input.setCurrentIndex(
                gender_index
            )

        # Date of Birth

        if employee.date_of_birth:

            dob = self.parse_date(
                employee.date_of_birth
            )

            if dob.isValid():

                self.date_of_birth_input.setDate(
                    dob
                )

        # Department

        department_index = (
            self.department_input.findText(
                employee.department or ""
            )
        )

        if department_index >= 0:

            self.department_input.setCurrentIndex(
                department_index
            )

        # Designation

        self.designation_input.setText(
            employee.designation or ""
        )

        # Employment Type

        employment_index = (
            self.employment_type_input.findText(
                employee.employment_type or ""
            )
        )

        if employment_index >= 0:

            self.employment_type_input.setCurrentIndex(
                employment_index
            )

        # Joining Date

        if employee.joining_date:

            joining_date = self.parse_date(
                employee.joining_date
            )

            if joining_date.isValid():

                self.joining_date_input.setDate(
                    joining_date
                )

        # Salary

        if employee.salary is not None:

            self.salary_input.setValue(
                float(employee.salary)
            )

        # Address

        self.address_input.setPlainText(
            employee.address or ""
        )

        # Emergency

        self.emergency_name_input.setText(
            employee.emergency_contact_name or ""
        )

        self.emergency_phone_input.setText(
            employee.emergency_contact_phone or ""
        )

        # Bank

        self.bank_account_input.setText(
            employee.bank_account or ""
        )

        # Status

        status_index = (
            self.status_input.findText(
                employee.status or "Active"
            )
        )

        if status_index >= 0:

            self.status_input.setCurrentIndex(
                status_index
            )

        # Photo

        if employee.profile_photo:

            self.profile_photo_path = (
                employee.profile_photo
            )

            pixmap = QPixmap(
                employee.profile_photo
            )

            if not pixmap.isNull():

                scaled = pixmap.scaled(
                    140,
                    140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                self.photo_label.setPixmap(
                    scaled
                )

                self.photo_label.setText(
                    ""
                )

    # ========================================================
    # DATE PARSER
    # ========================================================

    def parse_date(self, value):

        value = str(value)

        date_value = QDate.fromString(
            value,
            "dd-MM-yyyy"
        )

        if date_value.isValid():

            return date_value

        return QDate.fromString(
            value,
            "yyyy-MM-dd"
        )

    # ========================================================
    # HELPERS
    # ========================================================

    def create_line_edit(
        self,
        placeholder=""
    ):

        field = QLineEdit()

        field.setPlaceholderText(
            placeholder
        )

        field.setMinimumHeight(
            38
        )

        return field

    def create_label(
        self,
        text
    ):

        label = QLabel(
            text
        )

        label.setObjectName(
            "fieldLabel"
        )

        return label

    # ========================================================
    # PHOTO
    # ========================================================

    def upload_photo(self):

        file_path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Select Profile Photo",
                "",
                "Images (*.png *.jpg *.jpeg)"
            )
        )

        if not file_path:

            return

        pixmap = QPixmap(
            file_path
        )

        if pixmap.isNull():

            QMessageBox.warning(
                self,
                "Invalid Image",
                "Unable to load the selected image."
            )

            return

        self.profile_photo_path = (
            file_path
        )

        scaled = pixmap.scaled(
            140,
            140,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.photo_label.setPixmap(
            scaled
        )

        self.photo_label.setText(
            ""
        )

    # ========================================================
    # SAVE / UPDATE EMPLOYEE
    # ========================================================

    def save_employee(self):

        employee_id = (
            self.employee_id_input
            .text()
            .strip()
            .upper()
        )

        full_name = (
            self.full_name_input
            .text()
            .strip()
        )

        email = (
            self.email_input
            .text()
            .strip()
            .lower()
        )

        phone = (
            self.phone_input
            .text()
            .strip()
        )

        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        if not employee_id:

            QMessageBox.warning(
                self,
                "Required Field",
                "Please enter Employee ID."
            )

            self.employee_id_input.setFocus()

            return

        if not full_name:

            QMessageBox.warning(
                self,
                "Required Field",
                "Please enter employee full name."
            )

            self.full_name_input.setFocus()

            return

        if not email:

            QMessageBox.warning(
                self,
                "Required Field",
                "Please enter employee email."
            )

            self.email_input.setFocus()

            return

        # ----------------------------------------------------
        # EMAIL VALIDATION
        # ----------------------------------------------------

        email_pattern = (
            r"^[A-Za-z0-9._%+-]+@"
            r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )

        if not re.match(
            email_pattern,
            email
        ):

            QMessageBox.warning(
                self,
                "Invalid Email",
                "Please enter a valid email address."
            )

            self.email_input.setFocus()

            return

        # ----------------------------------------------------
        # PHONE VALIDATION
        # ----------------------------------------------------

        if phone:

            if (
                not phone.isdigit()
                or len(phone) != 10
            ):

                QMessageBox.warning(
                    self,
                    "Invalid Phone",
                    "Phone number must contain exactly 10 digits."
                )

                self.phone_input.setFocus()

                return

        # ----------------------------------------------------
        # EMERGENCY PHONE
        # ----------------------------------------------------

        emergency_phone = (
            self.emergency_phone_input
            .text()
            .strip()
        )

        if emergency_phone:

            if (
                not emergency_phone.isdigit()
                or len(emergency_phone) != 10
            ):

                QMessageBox.warning(
                    self,
                    "Invalid Emergency Phone",
                    "Emergency phone must contain exactly 10 digits."
                )

                self.emergency_phone_input.setFocus()

                return

        # ----------------------------------------------------
        # LOGIN PASSWORD
        # ----------------------------------------------------

        login_password = (
            self.login_password_input
            .text()
            .strip()
        )

        confirm_password = (
            self.confirm_password_input
            .text()
            .strip()
        )

        # New employee must have password

        if not self.is_edit_mode:

            if not login_password:

                QMessageBox.warning(
                    self,
                    "Login Password Required",
                    "Please create a login password for this employee."
                )

                self.login_password_input.setFocus()

                return

            if len(login_password) < 6:

                QMessageBox.warning(
                    self,
                    "Weak Password",
                    "Password must contain at least 6 characters."
                )

                self.login_password_input.setFocus()

                return

            if login_password != confirm_password:

                QMessageBox.warning(
                    self,
                    "Password Mismatch",
                    "Login password and confirm password do not match."
                )

                self.confirm_password_input.setFocus()

                return

        # Edit mode:
        # If password is entered, both fields must match

        else:

            if login_password or confirm_password:

                if len(login_password) < 6:

                    QMessageBox.warning(
                        self,
                        "Weak Password",
                        "Password must contain at least 6 characters."
                    )

                    self.login_password_input.setFocus()

                    return

                if login_password != confirm_password:

                    QMessageBox.warning(
                        self,
                        "Password Mismatch",
                        "Login password and confirm password do not match."
                    )

                    self.confirm_password_input.setFocus()

                    return

        # ----------------------------------------------------
        # GENDER
        # ----------------------------------------------------

        gender = (
            self.gender_input.currentText()
        )

        if gender == "Select Gender":

            gender = None

        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        department = (
            self.department_input.currentText()
        )

        if department == "Select Department":

            department = None

        # ----------------------------------------------------
        # EMPLOYMENT TYPE
        # ----------------------------------------------------

        employment_type = (
            self.employment_type_input.currentText()
        )

        if employment_type == "Select Employment Type":

            employment_type = None

        # ----------------------------------------------------
        # DATES
        # ----------------------------------------------------

        date_of_birth = (
            self.date_of_birth_input
            .date()
            .toString("dd-MM-yyyy")
        )

        joining_date = (
            self.joining_date_input
            .date()
            .toString("dd-MM-yyyy")
        )

        # ----------------------------------------------------
        # OTHER VALUES
        # ----------------------------------------------------

        designation = (
            self.designation_input
            .text()
            .strip()
        )

        address = (
            self.address_input
            .toPlainText()
            .strip()
        )

        bank_account = (
            self.bank_account_input
            .text()
            .strip()
        )

        emergency_name = (
            self.emergency_name_input
            .text()
            .strip()
        )

        # ----------------------------------------------------
        # DATA
        # ----------------------------------------------------

        employee_data = {

            "employee_id":
                employee_id,

            "full_name":
                full_name,

            "email":
                email,

            "phone":
                phone or None,

            "gender":
                gender,

            "date_of_birth":
                date_of_birth,

            "address":
                address or None,

            "department":
                department,

            "designation":
                designation or None,

            "employment_type":
                employment_type,

            "joining_date":
                joining_date,

            "salary":
                self.salary_input.value(),

            "bank_account":
                bank_account or None,

            "emergency_contact_name":
                emergency_name or None,

            "emergency_contact_phone":
                emergency_phone or None,

            "profile_photo":
                self.profile_photo_path,

            "status":
                self.status_input.currentText(),

            # NEW LOGIN PASSWORD
            "login_password":
                login_password,
        }

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        if self.is_edit_mode:

            success, result = update_employee(
                self.employee.id,
                employee_data
            )

            success_title = (
                "Employee Updated"
            )

            success_message = (
                f"Employee '{full_name}' "
                "has been updated successfully."
            )

        else:

            success, result = add_employee(
                employee_data
            )

            success_title = (
                "Employee Added"
            )

            success_message = (
                f"Employee '{full_name}' "
                "has been added successfully.\n\n"
                f"Login Username: {employee_id}\n"
                "The employee can now login using the password you created."
            )

        # ----------------------------------------------------
        # DATABASE ERROR
        # ----------------------------------------------------

        if not success:

            QMessageBox.warning(
                self,
                "Unable to Save",
                str(result)
            )

            return

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        QMessageBox.information(
            self,
            success_title,
            success_message
        )

        self.close()

    # ========================================================
    # STYLES
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
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #64748B;
                font-size: 13px;
            }

            QLabel#fieldLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 600;
            }

            QLabel#helperText {
                color: #64748B;
                font-size: 11px;
            }

            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                margin-top: 15px;
                padding: 20px;
                font-size: 15px;
                font-weight: 700;
                color: #1E293B;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: #FFFFFF;
                color: #1E3A8A;
            }

            QLineEdit,
            QComboBox,
            QDateEdit,
            QDoubleSpinBox,
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                padding: 8px 10px;
                color: #0F172A;
                selection-background-color: #2563EB;
                min-height: 22px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QDoubleSpinBox:focus,
            QTextEdit:focus {
                border: 2px solid #2563EB;
                background-color: #FFFFFF;
            }

            QLineEdit:read-only {
                background-color: #F1F5F9;
                color: #475569;
            }

            QComboBox {
                padding-right: 25px;
            }

            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                selection-background-color: #2563EB;
                selection-color: #FFFFFF;
            }

            QLabel#photoPreview {
                background-color: #F1F5F9;
                border: 2px dashed #CBD5E1;
                border-radius: 75px;
                color: #94A3B8;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton#primaryButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 7px;
                font-size: 14px;
                font-weight: 700;
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
                border-radius: 7px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#secondaryButton:hover {
                background-color: #F1F5F9;
                border-color: #94A3B8;
            }

            QPushButton#outlineButton {
                background-color: #EFF6FF;
                color: #2563EB;
                border: 1px solid #BFDBFE;
                border-radius: 7px;
                padding: 9px;
                font-weight: 600;
            }

            QPushButton#outlineButton:hover {
                background-color: #DBEAFE;
                border-color: #2563EB;
            }

            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QFrame#separator {
                background-color: #E2E8F0;
                max-height: 1px;
            }
        """)