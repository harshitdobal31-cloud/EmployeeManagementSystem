from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QMessageBox,
    QFrame,
)

from services.auth_service import register_user


class SignupWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Employee Management System | Create Account")
        self.setMinimumSize(650, 750)
        self.resize(700, 800)

        self.setup_ui()

    def setup_ui(self):
        # =========================================================
        # MAIN LAYOUT
        # =========================================================
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 35, 50, 35)
        main_layout.setSpacing(20)

        # =========================================================
        # HEADER
        # =========================================================
        title = QLabel("Create Your Account")
        title.setAlignment(Qt.AlignCenter)

        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "Join the Employee Management System"
        )
        subtitle.setAlignment(Qt.AlignCenter)

        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle.setFont(subtitle_font)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # =========================================================
        # FORM CARD
        # =========================================================
        card = QFrame()
        card.setObjectName("signupCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(18)

        # ---------------------------------------------------------
        # FULL NAME
        # ---------------------------------------------------------
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Enter your full name")
        self.full_name_input.setMinimumHeight(45)

        # ---------------------------------------------------------
        # EMAIL
        # ---------------------------------------------------------
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setMinimumHeight(45)

        # ---------------------------------------------------------
        # ROLE
        # ---------------------------------------------------------
        self.role_input = QComboBox()
        self.role_input.addItems([
            "Employee",
            "HR Manager",
        ])
        self.role_input.setMinimumHeight(45)

        # ---------------------------------------------------------
        # PASSWORD
        # ---------------------------------------------------------
        password_layout = QHBoxLayout()
        password_layout.setSpacing(8)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)

        self.password_toggle = QPushButton("Show")
        self.password_toggle.setFixedWidth(70)
        self.password_toggle.setMinimumHeight(45)
        self.password_toggle.clicked.connect(
            self.toggle_password
        )

        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.password_toggle)

        # ---------------------------------------------------------
        # CONFIRM PASSWORD
        # ---------------------------------------------------------
        confirm_password_layout = QHBoxLayout()
        confirm_password_layout.setSpacing(8)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText(
            "Confirm your password"
        )
        self.confirm_password_input.setEchoMode(
            QLineEdit.Password
        )
        self.confirm_password_input.setMinimumHeight(45)

        self.confirm_password_toggle = QPushButton("Show")
        self.confirm_password_toggle.setFixedWidth(70)
        self.confirm_password_toggle.setMinimumHeight(45)
        self.confirm_password_toggle.clicked.connect(
            self.toggle_confirm_password
        )

        confirm_password_layout.addWidget(
            self.confirm_password_input
        )
        confirm_password_layout.addWidget(
            self.confirm_password_toggle
        )

        # =========================================================
        # FORM LAYOUT
        # =========================================================
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(18)
        form_layout.setHorizontalSpacing(20)

        form_layout.addRow(
            self.create_label("Full Name"),
            self.full_name_input
        )

        form_layout.addRow(
            self.create_label("Email"),
            self.email_input
        )

        form_layout.addRow(
            self.create_label("Account Type"),
            self.role_input
        )

        form_layout.addRow(
            self.create_label("Password"),
            password_layout
        )

        form_layout.addRow(
            self.create_label("Confirm Password"),
            confirm_password_layout
        )

        card_layout.addLayout(form_layout)

        # =========================================================
        # INFORMATION LABEL
        # =========================================================
        info_label = QLabel(
            "Note: Admin accounts can only be created by the system administrator."
        )

        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(info_label)

        # =========================================================
        # CREATE ACCOUNT BUTTON
        # =========================================================
        self.create_account_button = QPushButton(
            "Create Account"
        )

        self.create_account_button.setMinimumHeight(50)
        self.create_account_button.setCursor(
            Qt.PointingHandCursor
        )

        self.create_account_button.clicked.connect(
            self.create_account
        )

        card_layout.addWidget(
            self.create_account_button
        )

        main_layout.addWidget(card)

        # =========================================================
        # BACK TO LOGIN
        # =========================================================
        self.back_button = QPushButton(
            "← Back to Sign In"
        )

        self.back_button.setMinimumHeight(45)
        self.back_button.setCursor(
            Qt.PointingHandCursor
        )

        self.back_button.clicked.connect(
            self.back_to_login
        )

        main_layout.addWidget(self.back_button)

        main_layout.addStretch()

        # Apply stylesheet
        self.apply_styles()

    # =============================================================
    # CREATE LABEL
    # =============================================================
    def create_label(self, text):
        label = QLabel(text)

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)

        label.setFont(font)

        return label

    # =============================================================
    # TOGGLE PASSWORD
    # =============================================================
    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(
                QLineEdit.Normal
            )
            self.password_toggle.setText("Hide")
        else:
            self.password_input.setEchoMode(
                QLineEdit.Password
            )
            self.password_toggle.setText("Show")

    # =============================================================
    # TOGGLE CONFIRM PASSWORD
    # =============================================================
    def toggle_confirm_password(self):
        if (
            self.confirm_password_input.echoMode()
            == QLineEdit.Password
        ):
            self.confirm_password_input.setEchoMode(
                QLineEdit.Normal
            )
            self.confirm_password_toggle.setText("Hide")
        else:
            self.confirm_password_input.setEchoMode(
                QLineEdit.Password
            )
            self.confirm_password_toggle.setText("Show")

    # =============================================================
    # CREATE ACCOUNT
    # =============================================================
    def create_account(self):
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_input.currentText()
        password = self.password_input.text()
        confirm_password = (
            self.confirm_password_input.text()
        )

        # ---------------------------------------------------------
        # BASIC VALIDATION
        # ---------------------------------------------------------
        if not full_name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter your full name."
            )
            self.full_name_input.setFocus()
            return

        if len(full_name) < 3:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Full name must contain at least 3 characters."
            )
            self.full_name_input.setFocus()
            return

        if not email:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter your email address."
            )
            self.email_input.setFocus()
            return

        if "@" not in email or "." not in email.split("@")[-1]:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a valid email address."
            )
            self.email_input.setFocus()
            return

        if not password:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter a password."
            )
            self.password_input.setFocus()
            return

        if len(password) < 6:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Password must contain at least 6 characters."
            )
            self.password_input.setFocus()
            return

        if password != confirm_password:
            QMessageBox.warning(
                self,
                "Password Error",
                "Password and Confirm Password do not match."
            )
            self.confirm_password_input.setFocus()
            return

        # ---------------------------------------------------------
        # DISABLE BUTTON WHILE PROCESSING
        # ---------------------------------------------------------
        self.create_account_button.setEnabled(False)
        self.create_account_button.setText(
            "Creating Account..."
        )

        try:
            success, message = register_user(
                full_name=full_name,
                email=email,
                password=password,
                role=role,
            )

            if success:
                QMessageBox.information(
                    self,
                    "Account Created Successfully",
                    message
                    + "\n\nYou can now sign in using your generated username or email."
                )

                self.clear_form()

                self.back_to_login()

            else:
                QMessageBox.warning(
                    self,
                    "Registration Failed",
                    message
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"Unable to create account.\n\nError:\n{error}"
            )

        finally:
            self.create_account_button.setEnabled(True)
            self.create_account_button.setText(
                "Create Account"
            )

    # =============================================================
    # CLEAR FORM
    # =============================================================
    def clear_form(self):
        self.full_name_input.clear()
        self.email_input.clear()

        self.role_input.setCurrentIndex(0)

        self.password_input.clear()
        self.confirm_password_input.clear()

        self.password_input.setEchoMode(
            QLineEdit.Password
        )
        self.confirm_password_input.setEchoMode(
            QLineEdit.Password
        )

        self.password_toggle.setText("Show")
        self.confirm_password_toggle.setText("Show")

    # =============================================================
    # BACK TO LOGIN
    # =============================================================
    def back_to_login(self):
        from ui.login import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()

        self.close()

    # =============================================================
    # STYLESHEET
    # =============================================================
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: "Segoe UI";
            }

            #signupCard {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
            }

            QLineEdit,
            QComboBox {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }

            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #2563eb;
            }

            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #475569;
            }

            QPushButton:pressed {
                background-color: #1e40af;
            }

            QPushButton:disabled {
                background-color: #475569;
                color: #94a3b8;
            }

            #signupCard QPushButton {
                background-color: #2563eb;
            }

            #signupCard QPushButton:hover {
                background-color: #1d4ed8;
            }

            #signupCard QPushButton:pressed {
                background-color: #1e40af;
            }
        """)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = SignupWindow()
    window.show()

    sys.exit(app.exec())