import sys

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QTimer,
    QSettings,
)

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.auth_service import login_user
from utils.session import Session

from ui.dashboard import DashboardWindow
from ui.hr_dashboard import HRDashboardWindow
from ui.employee_dashboard import EmployeeDashboardWindow


class LoginWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------
        # Window settings
        # ------------------------------------------------------

        self.setWindowTitle(
            "Employee Management System"
        )

        self.setFixedSize(
            1200,
            720
        )

        # ------------------------------------------------------
        # Application settings
        # ------------------------------------------------------

        self.settings = QSettings(
            "EmployeeManagementSystem",
            "EmployeeManagementSystem"
        )

        self.dark_mode = self.settings.value(
            "login_dark_mode",
            False,
            type=bool
        )

        self.dashboard_window = None
        self.signup_window = None

        # ------------------------------------------------------
        # Build UI
        # ------------------------------------------------------

        self.setup_ui()

        self.load_remembered_username()

        self.apply_theme()

        # ------------------------------------------------------
        # Start entrance animation
        # ------------------------------------------------------

        QTimer.singleShot(
            100,
            self.start_entrance_animation
        )

    # ==========================================================
    # UI
    # ==========================================================

    def setup_ui(self):

        self.central_widget = QWidget()

        self.central_widget.setObjectName(
            "centralWidget"
        )

        self.setCentralWidget(
            self.central_widget
        )

        main_layout = QHBoxLayout(
            self.central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)

        # ======================================================
        # LEFT SIDE
        # ======================================================

        self.left_panel = QFrame()

        self.left_panel.setObjectName(
            "leftPanel"
        )

        left_layout = QVBoxLayout(
            self.left_panel
        )

        left_layout.setContentsMargins(
            65,
            55,
            65,
            50
        )

        # ------------------------------------------------------
        # Brand
        # ------------------------------------------------------

        brand_layout = QHBoxLayout()

        logo = QLabel("E")

        logo.setObjectName(
            "logo"
        )

        logo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo.setFixedSize(
            52,
            52
        )

        brand_name = QLabel(
            "Employee Management"
        )

        brand_name.setObjectName(
            "brandName"
        )

        brand_layout.addWidget(
            logo
        )

        brand_layout.addSpacing(
            14
        )

        brand_layout.addWidget(
            brand_name
        )

        brand_layout.addStretch()

        left_layout.addLayout(
            brand_layout
        )

        left_layout.addStretch()

        # ------------------------------------------------------
        # Main left content
        # ------------------------------------------------------

        welcome_small = QLabel(
            "WELCOME BACK"
        )

        welcome_small.setObjectName(
            "welcomeSmall"
        )

        left_layout.addWidget(
            welcome_small
        )

        left_layout.addSpacing(
            12
        )

        main_heading = QLabel(
            "Manage your\nworkforce smarter."
        )

        main_heading.setObjectName(
            "mainHeading"
        )

        main_heading.setWordWrap(
            True
        )

        left_layout.addWidget(
            main_heading
        )

        left_layout.addSpacing(
            20
        )

        description = QLabel(
            "A simple and powerful workspace for managing "
            "employees, attendance, payroll and performance "
            "from one place."
        )

        description.setObjectName(
            "description"
        )

        description.setWordWrap(
            True
        )

        description.setMaximumWidth(
            430
        )

        left_layout.addWidget(
            description
        )

        left_layout.addSpacing(
            35
        )

        # ------------------------------------------------------
        # Feature cards
        # ------------------------------------------------------

        self.create_feature(
            left_layout,
            "01",
            "Employee Management",
            "Keep employee records organized."
        )

        self.create_feature(
            left_layout,
            "02",
            "Automated Payroll",
            "Make salary processing faster."
        )

        self.create_feature(
            left_layout,
            "03",
            "Performance Tracking",
            "Monitor employee performance easily."
        )

        left_layout.addStretch()

        # ------------------------------------------------------
        # Bottom
        # ------------------------------------------------------

        copyright_label = QLabel(
            "Employee Management System  •  Secure Workspace"
        )

        copyright_label.setObjectName(
            "copyrightLabel"
        )

        left_layout.addWidget(
            copyright_label
        )

        # ======================================================
        # RIGHT SIDE
        # ======================================================

        self.right_panel = QFrame()

        self.right_panel.setObjectName(
            "rightPanel"
        )

        right_layout = QVBoxLayout(
            self.right_panel
        )

        right_layout.setContentsMargins(
            55,
            30,
            55,
            30
        )

        # ------------------------------------------------------
        # Top bar
        # ------------------------------------------------------

        top_bar = QHBoxLayout()

        top_bar.addStretch()

        self.theme_button = QPushButton()

        self.theme_button.setObjectName(
            "themeButton"
        )

        self.theme_button.setFixedSize(
            42,
            42
        )

        self.theme_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.theme_button.clicked.connect(
            self.toggle_theme
        )

        top_bar.addWidget(
            self.theme_button
        )

        right_layout.addLayout(
            top_bar
        )

        right_layout.addStretch()

        # ======================================================
        # LOGIN CARD
        # ======================================================

        self.login_card = QFrame()

        self.login_card.setObjectName(
            "loginCard"
        )

        self.login_card.setMaximumWidth(
            430
        )

        card_layout = QVBoxLayout(
            self.login_card
        )

        card_layout.setContentsMargins(
            42,
            40,
            42,
            35
        )

        # ------------------------------------------------------
        # Header
        # ------------------------------------------------------

        login_title = QLabel(
            "Sign in"
        )

        login_title.setObjectName(
            "loginTitle"
        )

        card_layout.addWidget(
            login_title
        )

        card_layout.addSpacing(
            7
        )

        login_subtitle = QLabel(
            "Enter your credentials to continue"
        )

        login_subtitle.setObjectName(
            "loginSubtitle"
        )

        card_layout.addWidget(
            login_subtitle
        )

        card_layout.addSpacing(
            30
        )

        # ------------------------------------------------------
        # Username
        # ------------------------------------------------------

        username_label = QLabel(
            "Username or Email"
        )

        username_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            username_label
        )

        card_layout.addSpacing(
            8
        )

        self.username_input = QLineEdit()

        self.username_input.setObjectName(
            "inputField"
        )

        self.username_input.setPlaceholderText(
            "Enter your username or email"
        )

        self.username_input.setMinimumHeight(
            50
        )

        card_layout.addWidget(
            self.username_input
        )

        card_layout.addSpacing(
            20
        )

        # ------------------------------------------------------
        # Password
        # ------------------------------------------------------

        password_label = QLabel(
            "Password"
        )

        password_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            password_label
        )

        card_layout.addSpacing(
            8
        )

        password_container = QFrame()

        password_container.setObjectName(
            "passwordContainer"
        )

        password_layout = QHBoxLayout(
            password_container
        )

        password_layout.setContentsMargins(
            0,
            0,
            8,
            0
        )

        password_layout.setSpacing(
            0
        )

        self.password_input = QLineEdit()

        self.password_input.setObjectName(
            "passwordInput"
        )

        self.password_input.setPlaceholderText(
            "Enter your password"
        )

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password_input.setMinimumHeight(
            50
        )

        password_layout.addWidget(
            self.password_input
        )

        self.show_password_button = QPushButton(
            "Show"
        )

        self.show_password_button.setObjectName(
            "showPasswordButton"
        )

        self.show_password_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.show_password_button.clicked.connect(
            self.toggle_password
        )

        password_layout.addWidget(
            self.show_password_button
        )

        card_layout.addWidget(
            password_container
        )

        card_layout.addSpacing(
            15
        )

        # ------------------------------------------------------
        # Remember
        # ------------------------------------------------------

        options_layout = QHBoxLayout()

        self.remember_checkbox = QCheckBox(
            "Remember me"
        )

        self.remember_checkbox.setObjectName(
            "rememberCheckbox"
        )

        options_layout.addWidget(
            self.remember_checkbox
        )

        options_layout.addStretch()

        secure_label = QLabel(
            "● Secure"
        )

        secure_label.setObjectName(
            "secureLabel"
        )

        options_layout.addWidget(
            secure_label
        )

        card_layout.addLayout(
            options_layout
        )

        card_layout.addSpacing(
            25
        )

        # ------------------------------------------------------
        # Login button
        # ------------------------------------------------------

        self.login_button = QPushButton(
            "Sign In  →"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setMinimumHeight(
            52
        )

        self.login_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.login_button.clicked.connect(
            self.handle_login
        )

        card_layout.addWidget(
            self.login_button
        )

        card_layout.addSpacing(
            12
        )

        # ------------------------------------------------------
        # Create account
        # ------------------------------------------------------

        self.create_account_button = QPushButton(
            "Create Account"
        )

        self.create_account_button.setObjectName(
            "createAccountButton"
        )

        self.create_account_button.setMinimumHeight(
            45
        )

        self.create_account_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.create_account_button.clicked.connect(
            self.open_signup
        )

        card_layout.addWidget(
            self.create_account_button
        )

        card_layout.addSpacing(
            15
        )

        # ------------------------------------------------------
        # Status
        # ------------------------------------------------------

        self.status_label = QLabel(
            ""
        )

        self.status_label.setObjectName(
            "statusLabel"
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setWordWrap(
            True
        )

        card_layout.addWidget(
            self.status_label
        )

        # ------------------------------------------------------
        # Security text
        # ------------------------------------------------------

        security_text = QLabel(
            "Your account is protected with secure "
            "password verification."
        )

        security_text.setObjectName(
            "securityText"
        )

        security_text.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        security_text.setWordWrap(
            True
        )

        card_layout.addSpacing(
            8
        )

        card_layout.addWidget(
            security_text
        )

        # ------------------------------------------------------
        # Add card
        # ------------------------------------------------------

        card_container = QHBoxLayout()

        card_container.addStretch()

        card_container.addWidget(
            self.login_card
        )

        card_container.addStretch()

        right_layout.addLayout(
            card_container
        )

        right_layout.addStretch()

        # ------------------------------------------------------
        # Main panels
        # ------------------------------------------------------

        main_layout.addWidget(
            self.left_panel,
            55
        )

        main_layout.addWidget(
            self.right_panel,
            45
        )

        # ------------------------------------------------------
        # Enter key
        # ------------------------------------------------------

        self.username_input.returnPressed.connect(
            self.handle_login
        )

        self.password_input.returnPressed.connect(
            self.handle_login
        )

    # ==========================================================
    # FEATURE
    # ==========================================================

    def create_feature(
        self,
        parent_layout,
        number,
        title,
        description
    ):

        feature = QFrame()

        feature.setObjectName(
            "featureCard"
        )

        feature_layout = QHBoxLayout(
            feature
        )

        feature_layout.setContentsMargins(
            15,
            12,
            15,
            12
        )

        feature_layout.setSpacing(
            14
        )

        number_label = QLabel(
            number
        )

        number_label.setObjectName(
            "featureNumber"
        )

        number_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        number_label.setFixedSize(
            42,
            42
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            3
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "featureTitle"
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "featureDescription"
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            description_label
        )

        feature_layout.addWidget(
            number_label
        )

        feature_layout.addLayout(
            text_layout
        )

        parent_layout.addWidget(
            feature
        )

        parent_layout.addSpacing(
            10
        )

    # ==========================================================
    # OPEN SIGNUP
    # ==========================================================

    def open_signup(self):

        try:

            from ui.signup import SignupWindow

            self.signup_window = SignupWindow()

            self.signup_window.show()

            # Hide login instead of closing it.
            # This allows SignupWindow to return here.
            self.hide()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Signup Error",
                f"Unable to open Create Account window.\n\n"
                f"Error:\n{error}"
            )

    # ==========================================================
    # THEME
    # ==========================================================

    def toggle_theme(self):

        self.dark_mode = not self.dark_mode

        self.settings.setValue(
            "login_dark_mode",
            self.dark_mode
        )

        self.apply_theme()

    def apply_theme(self):

        if self.dark_mode:

            self.theme_button.setText(
                "☀"
            )

            self.setStyleSheet("""

                #centralWidget {
                    background: #111827;
                }

                #leftPanel {
                    background: #020617;
                }

                #rightPanel {
                    background: #111827;
                }

                #logo {
                    background: #2563EB;
                    color: white;
                    border-radius: 14px;
                    font-size: 25px;
                    font-weight: 800;
                }

                #brandName {
                    color: #F8FAFC;
                    font-size: 16px;
                    font-weight: 700;
                }

                #welcomeSmall {
                    color: #60A5FA;
                    font-size: 12px;
                    font-weight: 800;
                    letter-spacing: 2px;
                }

                #mainHeading {
                    color: #F8FAFC;
                    font-size: 42px;
                    font-weight: 800;
                }

                #description {
                    color: #94A3B8;
                    font-size: 14px;
                }

                #featureCard {
                    background: #0F172A;
                    border: 1px solid #1E293B;
                    border-radius: 12px;
                }

                #featureNumber {
                    background: #1D4ED8;
                    color: white;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 800;
                }

                #featureTitle {
                    color: #F8FAFC;
                    font-size: 13px;
                    font-weight: 700;
                }

                #featureDescription {
                    color: #64748B;
                    font-size: 11px;
                }

                #copyrightLabel {
                    color: #475569;
                    font-size: 10px;
                }

                #themeButton {
                    background: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #334155;
                    border-radius: 21px;
                    font-size: 19px;
                }

                #themeButton:hover {
                    background: #334155;
                }

                #loginCard {
                    background: #1E293B;
                    border: 1px solid #334155;
                    border-radius: 18px;
                }

                #loginTitle {
                    color: #F8FAFC;
                    font-size: 30px;
                    font-weight: 800;
                }

                #loginSubtitle {
                    color: #94A3B8;
                    font-size: 13px;
                }

                #fieldLabel {
                    color: #E2E8F0;
                    font-size: 12px;
                    font-weight: 700;
                }

                #inputField {
                    background: #0F172A;
                    color: #F8FAFC;
                    border: 1px solid #475569;
                    border-radius: 9px;
                    padding-left: 14px;
                    font-size: 13px;
                }

                #inputField:focus {
                    border: 2px solid #3B82F6;
                }

                #passwordContainer {
                    background: #0F172A;
                    border: 1px solid #475569;
                    border-radius: 9px;
                }

                #passwordInput {
                    background: transparent;
                    color: #F8FAFC;
                    border: none;
                    padding-left: 14px;
                    font-size: 13px;
                }

                #showPasswordButton {
                    background: transparent;
                    color: #60A5FA;
                    border: none;
                    font-size: 11px;
                    font-weight: 700;
                }

                #rememberCheckbox {
                    color: #CBD5E1;
                    font-size: 11px;
                }

                #secureLabel {
                    color: #4ADE80;
                    font-size: 10px;
                    font-weight: 700;
                }

                #loginButton {
                    background: #2563EB;
                    color: white;
                    border: none;
                    border-radius: 9px;
                    font-size: 14px;
                    font-weight: 800;
                }

                #loginButton:hover {
                    background: #3B82F6;
                }

                #loginButton:pressed {
                    background: #1D4ED8;
                }

                #loginButton:disabled {
                    background: #475569;
                    color: #94A3B8;
                }

                #createAccountButton {
                    background: transparent;
                    color: #60A5FA;
                    border: 1px solid #475569;
                    border-radius: 9px;
                    font-size: 13px;
                    font-weight: 700;
                }

                #createAccountButton:hover {
                    background: #0F172A;
                    border: 1px solid #60A5FA;
                }

                #statusLabel {
                    color: #F87171;
                    font-size: 11px;
                    font-weight: 600;
                }

                #securityText {
                    color: #64748B;
                    font-size: 9px;
                }

            """)

        else:

            self.theme_button.setText(
                "☾"
            )

            self.setStyleSheet("""

                #centralWidget {
                    background: #F1F5F9;
                }

                #leftPanel {
                    background: #0F172A;
                }

                #rightPanel {
                    background: #F8FAFC;
                }

                #logo {
                    background: #2563EB;
                    color: white;
                    border-radius: 14px;
                    font-size: 25px;
                    font-weight: 800;
                }

                #brandName {
                    color: white;
                    font-size: 16px;
                    font-weight: 700;
                }

                #welcomeSmall {
                    color: #60A5FA;
                    font-size: 12px;
                    font-weight: 800;
                    letter-spacing: 2px;
                }

                #mainHeading {
                    color: white;
                    font-size: 42px;
                    font-weight: 800;
                }

                #description {
                    color: #94A3B8;
                    font-size: 14px;
                }

                #featureCard {
                    background: #172033;
                    border: 1px solid #243047;
                    border-radius: 12px;
                }

                #featureNumber {
                    background: #2563EB;
                    color: white;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 800;
                }

                #featureTitle {
                    color: white;
                    font-size: 13px;
                    font-weight: 700;
                }

                #featureDescription {
                    color: #94A3B8;
                    font-size: 11px;
                }

                #copyrightLabel {
                    color: #64748B;
                    font-size: 10px;
                }

                #themeButton {
                    background: white;
                    color: #334155;
                    border: 1px solid #CBD5E1;
                    border-radius: 21px;
                    font-size: 19px;
                }

                #themeButton:hover {
                    background: #F1F5F9;
                }

                #loginCard {
                    background: white;
                    border: 1px solid #E2E8F0;
                    border-radius: 18px;
                }

                #loginTitle {
                    color: #0F172A;
                    font-size: 30px;
                    font-weight: 800;
                }

                #loginSubtitle {
                    color: #64748B;
                    font-size: 13px;
                }

                #fieldLabel {
                    color: #1E293B;
                    font-size: 12px;
                    font-weight: 700;
                }

                #inputField {
                    background: #F8FAFC;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 9px;
                    padding-left: 14px;
                    font-size: 13px;
                }

                #inputField:focus {
                    background: white;
                    border: 2px solid #2563EB;
                }

                #passwordContainer {
                    background: #F8FAFC;
                    border: 1px solid #CBD5E1;
                    border-radius: 9px;
                }

                #passwordInput {
                    background: transparent;
                    color: #0F172A;
                    border: none;
                    padding-left: 14px;
                    font-size: 13px;
                }

                #showPasswordButton {
                    background: transparent;
                    color: #2563EB;
                    border: none;
                    font-size: 11px;
                    font-weight: 700;
                }

                #rememberCheckbox {
                    color: #475569;
                    font-size: 11px;
                }

                #secureLabel {
                    color: #16A34A;
                    font-size: 10px;
                    font-weight: 700;
                }

                #loginButton {
                    background: #2563EB;
                    color: white;
                    border: none;
                    border-radius: 9px;
                    font-size: 14px;
                    font-weight: 800;
                }

                #loginButton:hover {
                    background: #1D4ED8;
                }

                #loginButton:pressed {
                    background: #1E40AF;
                }

                #loginButton:disabled {
                    background: #93C5FD;
                    color: white;
                }

                #createAccountButton {
                    background: white;
                    color: #2563EB;
                    border: 1px solid #CBD5E1;
                    border-radius: 9px;
                    font-size: 13px;
                    font-weight: 700;
                }

                #createAccountButton:hover {
                    background: #EFF6FF;
                    border: 1px solid #2563EB;
                }

                #statusLabel {
                    color: #DC2626;
                    font-size: 11px;
                    font-weight: 600;
                }

                #securityText {
                    color: #94A3B8;
                    font-size: 9px;
                }

            """)

    # ==========================================================
    # ENTRANCE ANIMATION
    # ==========================================================

    def start_entrance_animation(self):

        # ------------------------------------------------------
        # Left panel
        # ------------------------------------------------------

        left_start = self.left_panel.pos()

        left_start.setX(
            left_start.x() - 120
        )

        left_end = self.left_panel.pos()

        self.left_animation = QPropertyAnimation(
            self.left_panel,
            b"pos"
        )

        self.left_animation.setDuration(
            750
        )

        self.left_animation.setStartValue(
            left_start
        )

        self.left_animation.setEndValue(
            left_end
        )

        self.left_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        # ------------------------------------------------------
        # Login card
        # ------------------------------------------------------

        card_start = self.login_card.pos()

        card_start.setX(
            card_start.x() + 100
        )

        card_end = self.login_card.pos()

        self.card_animation = QPropertyAnimation(
            self.login_card,
            b"pos"
        )

        self.card_animation.setDuration(
            800
        )

        self.card_animation.setStartValue(
            card_start
        )

        self.card_animation.setEndValue(
            card_end
        )

        self.card_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        # ------------------------------------------------------
        # Run animations
        # ------------------------------------------------------

        self.animation_group = QParallelAnimationGroup()

        self.animation_group.addAnimation(
            self.left_animation
        )

        self.animation_group.addAnimation(
            self.card_animation
        )

        self.animation_group.start()

    # ==========================================================
    # PASSWORD
    # ==========================================================

    def toggle_password(self):

        if (
            self.password_input.echoMode()
            == QLineEdit.EchoMode.Password
        ):

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Normal
            )

            self.show_password_button.setText(
                "Hide"
            )

        else:

            self.password_input.setEchoMode(
                QLineEdit.EchoMode.Password
            )

            self.show_password_button.setText(
                "Show"
            )

    # ==========================================================
    # REMEMBER ME
    # ==========================================================

    def load_remembered_username(self):

        username = self.settings.value(
            "remembered_username",
            ""
        )

        if username:

            self.username_input.setText(
                username
            )

            self.remember_checkbox.setChecked(
                True
            )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def validate_form(self):

        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        if not username:

            self.show_error(
                "Please enter your username or email."
            )

            self.username_input.setFocus()

            return False

        if not password:

            self.show_error(
                "Please enter your password."
            )

            self.password_input.setFocus()

            return False

        if len(password) < 6:

            self.show_error(
                "Password must contain at least 6 characters."
            )

            self.password_input.setFocus()

            return False

        return True

    # ==========================================================
    # LOGIN
    # ==========================================================

    def handle_login(self):

        if not self.validate_form():
            return

        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        self.login_button.setEnabled(
            False
        )

        self.login_button.setText(
            "Signing in..."
        )

        self.status_label.setStyleSheet(
            "color: #2563EB;"
        )

        self.status_label.setText(
            "Verifying your account..."
        )

        QTimer.singleShot(
            400,
            lambda: self.perform_login(
                username,
                password
            )
        )

    # ==========================================================
    # ACTUAL LOGIN
    # ==========================================================

    def perform_login(
        self,
        username,
        password
    ):

        try:

            user = login_user(
                username,
                password
            )

            if user is None:

                self.login_button.setEnabled(
                    True
                )

                self.login_button.setText(
                    "Sign In  →"
                )

                self.show_error(
                    "Invalid username/email or password."
                )

                self.password_input.clear()

                self.password_input.setFocus()

                return

            # --------------------------------------------------
            # Save session
            # --------------------------------------------------

            Session.login(
                user
            )

            # --------------------------------------------------
            # Remember username
            # --------------------------------------------------

            if self.remember_checkbox.isChecked():

                self.settings.setValue(
                    "remembered_username",
                    username
                )

            else:

                self.settings.remove(
                    "remembered_username"
                )

            # --------------------------------------------------
            # Success
            # --------------------------------------------------

            self.status_label.setStyleSheet(
                "color: #16A34A;"
            )

            self.status_label.setText(
                f"Welcome back, {user.username}"
            )

            self.login_button.setText(
                "Success ✓"
            )

            QTimer.singleShot(
                600,
                self.open_dashboard
            )

        except Exception as error:

            import traceback

            print("\n" + "=" * 70)
            print("LOGIN ERROR")
            print("=" * 70)
            print(str(error))
            traceback.print_exc()
            print("=" * 70 + "\n")

            self.login_button.setEnabled(
                True
            )

            self.login_button.setText(
                "Sign In  →"
            )

            self.show_error(
                f"Login error: {error}"
            )

    # ==========================================================
    # OPEN DASHBOARD
    # ==========================================================

    def open_dashboard(self):

        # ------------------------------------------------------
        # Get logged-in user
        # ------------------------------------------------------

        user = Session.get_user()

        if user is None:

            self.show_error(
                "Unable to identify logged-in user."
            )

            self.login_button.setEnabled(
                True
            )

            self.login_button.setText(
                "Sign In  →"
            )

            return

        # ------------------------------------------------------
        # Get role
        # ------------------------------------------------------

        role = str(
            user.role
        ).strip().lower()

        # ------------------------------------------------------
        # ADMIN
        # ------------------------------------------------------

        if role == "admin":

            self.dashboard_window = DashboardWindow()

        # ------------------------------------------------------
        # HR MANAGER
        # ------------------------------------------------------

        elif role in (
            "hr manager",
            "hr_manager",
            "hrmanager",
            "hr"
        ):

            self.dashboard_window = HRDashboardWindow()

        # ------------------------------------------------------
        # EMPLOYEE
        # ------------------------------------------------------

        elif role == "employee":

            self.dashboard_window = (
                EmployeeDashboardWindow()
            )

        # ------------------------------------------------------
        # UNKNOWN ROLE
        # ------------------------------------------------------

        else:

            QMessageBox.critical(
                self,
                "Access Error",
                f"Unknown user role: {user.role}"
            )

            Session.logout()

            self.login_button.setEnabled(
                True
            )

            self.login_button.setText(
                "Sign In  →"
            )

            return

        # ------------------------------------------------------
        # Open dashboard
        # ------------------------------------------------------

        self.dashboard_window.show()

        # ------------------------------------------------------
        # Close login window
        # ------------------------------------------------------

        self.close()

    # ==========================================================
    # ERROR
    # ==========================================================

    def show_error(
        self,
        message
    ):

        self.status_label.setStyleSheet(
            "color: #DC2626;"
        )

        self.status_label.setText(
            message
        )


# ==============================================================
# RUN DIRECTLY
# ==============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = LoginWindow()

    window.show()

    sys.exit(
        app.exec()
    )