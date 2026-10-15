from PySide6.QtCore import (
    Qt,
    QObject,
    QEvent,
    QEasingCurve,
    QPropertyAnimation,
    QVariantAnimation,
    QTimer,
    QEventLoop,
)
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QApplication,
    QGraphicsDropShadowEffect,
)

from services.auth_service import register_user


# =============================================================
# GLOW ANIMATOR
# =============================================================
class GlowAnimator(QObject):
    """
    Animates a soft colored glow around a LEAF widget (input, combo box, button).

    IMPORTANT: Never apply this to a container (frame, card, window) that has
    child widgets with their own effects. Qt cannot paint nested graphics
    effects correctly, which causes the "Painter not active" warnings.

    - hover=True: glow on mouse enter/leave (buttons)
    - always:     glow on keyboard focus in/out (inputs)
    """

    def __init__(self, widget, color, hover=True, base_blur=0, peak_blur=22):
        super().__init__(widget)
        self._widget = widget
        self._hover = hover
        self._base = base_blur
        self._peak = peak_blur

        self._effect = QGraphicsDropShadowEffect(widget)
        self._effect.setOffset(0, 0)
        self._effect.setColor(QColor(color))
        self._effect.setBlurRadius(base_blur)
        widget.setGraphicsEffect(self._effect)

        self._anim = QPropertyAnimation(self._effect, b"blurRadius", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self._widget:
            event_type = event.type()
            if event_type == QEvent.Type.FocusIn:
                self._play(self._peak)
            elif event_type == QEvent.Type.FocusOut:
                self._play(self._base)
            elif self._hover and event_type == QEvent.Type.Enter:
                self._play(self._peak)
            elif self._hover and event_type == QEvent.Type.Leave:
                self._play(self._base)
        return False  # never swallow events; clicks work normally

    def _play(self, target):
        self._anim.stop()
        self._anim.setStartValue(self._effect.blurRadius())
        self._anim.setEndValue(target)
        self._anim.start()


class SignupWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Employee Management System | Create Account")
        self.setMinimumSize(650, 750)
        self.resize(700, 800)

        self._busy = False          # True while registration is running
        self._animations = []       # keeps animation objects alive
        self._glows = []            # keeps glow helpers alive
        self._entrance_played = False

        # Start invisible; the entrance animation fades the window in
        self.setWindowOpacity(0.0)

        self.setup_ui()

    # =========================================================
    # SHOW EVENT (entrance animation runs once, when visible)
    # =========================================================
    def showEvent(self, event):
        super().showEvent(event)
        if not self._entrance_played:
            self._entrance_played = True
            self.play_entrance_animation()

    # =========================================================
    # UI BUILD
    # =========================================================
    def setup_ui(self):
        # Root frame carries the gradient background.
        # It has NO graphics effect of its own.
        root = QFrame()
        root.setObjectName("root")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(40, 28, 40, 20)
        root_layout.setSpacing(16)

        # -----------------------------------------------------
        # BRAND BADGE + HEADER
        # -----------------------------------------------------
        badge = QLabel("EMS")
        badge.setObjectName("badge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(64, 64)

        badge_row = QHBoxLayout()
        badge_row.addStretch(1)
        badge_row.addWidget(badge)
        badge_row.addStretch(1)

        title = QLabel("Create Your Account")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Join the Employee Management System")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root_layout.addLayout(badge_row)
        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addSpacing(8)

        # -----------------------------------------------------
        # FORM CARD (plain frame, no graphics effect)
        # -----------------------------------------------------
        card = QFrame()
        card.setObjectName("signupCard")
        card.setMaximumWidth(560)
        self.card = card

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        # Inputs (attribute names are unchanged from the original)
        self.full_name_input = self.create_input("Enter your full name")
        self.email_input = self.create_input("Enter your email address")

        self.role_input = QComboBox()
        self.role_input.addItems(["Employee", "HR Manager"])
        self.role_input.setMinimumHeight(46)
        self._glows.append(
            GlowAnimator(self.role_input, "#3b82f6", hover=False, peak_blur=16)
        )

        self.password_input = self.create_input("Enter password", password=True)
        self.password_toggle = self.create_toggle_button(self.toggle_password)

        self.confirm_password_input = self.create_input(
            "Confirm your password", password=True
        )
        self.confirm_password_toggle = self.create_toggle_button(
            self.toggle_confirm_password
        )

        password_row = QHBoxLayout()
        password_row.setSpacing(8)
        password_row.addWidget(self.password_input)
        password_row.addWidget(self.password_toggle)

        confirm_password_row = QHBoxLayout()
        confirm_password_row.setSpacing(8)
        confirm_password_row.addWidget(self.confirm_password_input)
        confirm_password_row.addWidget(self.confirm_password_toggle)

        card_layout.addLayout(self.build_field("Full Name", self.full_name_input))
        card_layout.addLayout(self.build_field("Email", self.email_input))
        card_layout.addLayout(self.build_field("Account Type", self.role_input))
        card_layout.addLayout(self.build_field("Password", password_row))
        card_layout.addLayout(
            self.build_field("Confirm Password", confirm_password_row)
        )

        info_label = QLabel(
            "Note: Admin accounts can only be created by the system administrator."
        )
        info_label.setObjectName("note")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(info_label)

        # Primary button
        self.create_account_button = QPushButton("Create Account")
        self.create_account_button.setObjectName("primaryButton")
        self.create_account_button.setMinimumHeight(50)
        self.create_account_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_account_button.clicked.connect(self.create_account)
        self._glows.append(
            GlowAnimator(self.create_account_button, "#8b5cf6", hover=True, peak_blur=26)
        )
        card_layout.addWidget(self.create_account_button)

        # Enter in the confirm field submits the form
        self.confirm_password_input.returnPressed.connect(self.create_account)

        # Center the card horizontally.
        # card_row is kept as an attribute so the entrance animation can
        # shift the card by changing its margin (no graphics effect needed).
        self.card_row = QHBoxLayout()
        self.card_row.setContentsMargins(0, 0, 0, 0)
        self.card_row.addStretch(1)
        self.card_row.addWidget(card, 10)
        self.card_row.addStretch(1)
        root_layout.addLayout(self.card_row)

        # Back to login
        self.back_button = QPushButton("← Back to Sign In")
        self.back_button.setObjectName("ghostButton")
        self.back_button.setMinimumHeight(44)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.back_to_login)
        root_layout.addWidget(self.back_button)

        root_layout.addStretch(1)

        footer = QLabel("Employee Management System · Authorized personnel only")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(footer)

        self.apply_styles()

    # =========================================================
    # WIDGET FACTORY HELPERS
    # =========================================================
    def create_input(self, placeholder, password=False):
        line = QLineEdit()
        line.setPlaceholderText(placeholder)
        line.setMinimumHeight(46)

        if password:
            line.setEchoMode(QLineEdit.EchoMode.Password)

        palette = line.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#64748b"))
        line.setPalette(palette)

        # Glow on focus only
        self._glows.append(GlowAnimator(line, "#3b82f6", hover=False, peak_blur=16))
        return line

    def create_toggle_button(self, handler):
        button = QPushButton("Show")
        button.setObjectName("toggleButton")
        button.setFixedSize(72, 46)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)
        return button

    def build_field(self, label_text, field):
        """Label stacked above a widget or a layout."""
        box = QVBoxLayout()
        box.setSpacing(6)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        box.addWidget(label)

        if isinstance(field, QWidget):
            box.addWidget(field)
        else:
            box.addLayout(field)

        return box

    # =========================================================
    # ANIMATIONS (no QGraphicsEffect on containers)
    # =========================================================
    def play_entrance_animation(self):
        # 1) Window fade-in: animates the top-level window opacity.
        #    This avoids nested offscreen rendering entirely.
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(500)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade.start()
        self._animations.append(fade)

        # 2) Card slide-up: animates the top margin of the card's row.
        #    Layout margin changes are cheap and need no graphics effect.
        slide = QVariantAnimation(self)
        slide.setDuration(550)
        slide.setStartValue(40)
        slide.setEndValue(0)
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        slide.valueChanged.connect(
            lambda v: self.card_row.setContentsMargins(0, int(v), 0, 0)
        )
        slide.finished.connect(
            lambda: self.card_row.setContentsMargins(0, 0, 0, 0)
        )
        slide.start()
        self._animations.append(slide)

        # Delay the slide slightly so the card appears after the fade begins
        QTimer.singleShot(120, slide.start)

    # =========================================================
    # PASSWORD TOGGLES (behavior unchanged)
    # =========================================================
    def toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_toggle.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_toggle.setText("Show")

    def toggle_confirm_password(self):
        if self.confirm_password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.confirm_password_toggle.setText("Hide")
        else:
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password_toggle.setText("Show")

    # =========================================================
    # BUSY STATE (loading UI)
    # =========================================================
    def set_busy(self, busy):
        self._busy = busy

        for widget in (
            self.full_name_input,
            self.email_input,
            self.role_input,
            self.password_input,
            self.password_toggle,
            self.confirm_password_input,
            self.confirm_password_toggle,
            self.back_button,
            self.create_account_button,
        ):
            widget.setEnabled(not busy)

        self.create_account_button.setText(
            "Creating Account..." if busy else "Create Account"
        )

        if busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            # Repaint the loading state before the blocking database call.
            # Excluding user input prevents clicks from re-entering this method.
            QApplication.processEvents(
                QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
            )
        else:
            QApplication.restoreOverrideCursor()

    # =========================================================
    # VALIDATION HELPER
    # =========================================================
    def _warn(self, title, message, focus_widget=None):
        QMessageBox.warning(self, title, message)
        if focus_widget is not None:
            focus_widget.setFocus()

    # =========================================================
    # CREATE ACCOUNT
    # =========================================================
    def create_account(self):
        # Guard against duplicate submissions (double-click, Enter key, etc.)
        if self._busy:
            return

        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_input.currentText()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        checks = [
            (not full_name, "Validation Error",
             "Please enter your full name.", self.full_name_input),
            (len(full_name) < 3, "Validation Error",
             "Full name must contain at least 3 characters.", self.full_name_input),
            (not email, "Validation Error",
             "Please enter your email address.", self.email_input),
            ("@" not in email or "." not in email.split("@")[-1],
             "Validation Error",
             "Please enter a valid email address.", self.email_input),
            (not password, "Validation Error",
             "Please enter a password.", self.password_input),
            (len(password) < 6, "Validation Error",
             "Password must contain at least 6 characters.", self.password_input),
            (password != confirm_password, "Password Error",
             "Password and Confirm Password do not match.", self.confirm_password_input),
        ]

        for failed, title, message, widget in checks:
            if failed:
                self._warn(title, message, widget)
                return

        # Existing service call, unchanged
        self.set_busy(True)
        success, message = None, ""

        try:
            success, message = register_user(
                full_name=full_name,
                email=email,
                password=password,
                role=role,
            )
        except Exception as error:
            success, message = None, str(error)
        finally:
            self.set_busy(False)

        if success is None:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"Unable to create account.\n\nError:\n{message}"
            )
        elif success:
            QMessageBox.information(
                self,
                "Account Created Successfully",
                message
                + "\n\nYou can now sign in using your generated username or email."
            )
            self.clear_form()
            self.back_to_login()
        else:
            QMessageBox.warning(self, "Registration Failed", message)

    # =========================================================
    # CLEAR FORM
    # =========================================================
    def clear_form(self):
        self.full_name_input.clear()
        self.email_input.clear()
        self.role_input.setCurrentIndex(0)
        self.password_input.clear()
        self.confirm_password_input.clear()

        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.password_toggle.setText("Show")
        self.confirm_password_toggle.setText("Show")

    # =========================================================
    # BACK TO LOGIN (unchanged navigation)
    # =========================================================
    def back_to_login(self):
        from ui.login import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()

        self.close()

    # =========================================================
    # STYLESHEET
    # =========================================================
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: "Segoe UI";
                color: #f1f5f9;
                font-size: 13px;
            }

            QFrame#root {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0b1224, stop:0.5 #0f1a3a, stop:1 #1a1040);
            }

            QLabel {
                background: transparent;
            }

            QLabel#badge {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2563eb, stop:1 #7c3aed);
                color: #ffffff;
                border-radius: 18px;
                font-size: 20px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#title {
                color: #ffffff;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#subtitle {
                color: #94a3b8;
                font-size: 13px;
            }

            QFrame#signupCard {
                background-color: rgba(30, 41, 59, 0.85);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 18px;
            }

            QLabel#fieldLabel {
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 600;
            }

            QLabel#note {
                color: #94a3b8;
                font-size: 11px;
            }

            QLabel#footer {
                color: #64748b;
                font-size: 11px;
            }

            QLineEdit, QComboBox {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 0px 14px;
                selection-background-color: #3b82f6;
            }

            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #3b82f6;
            }

            QLineEdit:disabled, QComboBox:disabled {
                color: #64748b;
            }

            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #2563eb;
                border: 1px solid #334155;
            }

            QPushButton#toggleButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 10px;
                font-weight: 600;
            }

            QPushButton#toggleButton:hover {
                color: #e2e8f0;
                border-color: #3b82f6;
            }

            QPushButton#primaryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #7c3aed);
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
                padding: 10px 14px;
            }

            QPushButton#primaryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #8b5cf6);
            }

            QPushButton#primaryButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1d4ed8, stop:1 #6d28d9);
            }

            QPushButton#primaryButton:disabled {
                background: #334155;
                color: #94a3b8;
            }

            QPushButton#ghostButton {
                background-color: transparent;
                color: #93c5fd;
                border: none;
                font-weight: 600;
            }

            QPushButton#ghostButton:hover {
                color: #bfdbfe;
            }

            QPushButton#ghostButton:disabled {
                color: #475569;
            }

            /* Message boxes inherit this window's stylesheet */
            QMessageBox {
                background-color: #0f172a;
            }

            QMessageBox QLabel {
                color: #f8fafc;
            }

            QMessageBox QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                min-width: 80px;
                font-weight: 600;
            }

            QMessageBox QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = SignupWindow()
    window.show()

    sys.exit(app.exec())