# ============================================================
# EMPLOYEE MANAGEMENT SYSTEM
# PROFESSIONAL SETTINGS
# ============================================================

import sys
import platform
import os

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtGui import (
    QFont,
    QColor,
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QFrame,
    QMessageBox,
    QFileDialog,
    QColorDialog,
    QTabWidget,
    QSpinBox,
)

from services.settings_service import (
    initialize_default_settings,
    get_setting,
    set_setting,
    get_bool_setting,
    set_bool_setting,
    create_database_backup,
    restore_database,
    get_system_paths,
    check_database,
)

from utils.theme_manager import (
    get_theme_names,
    get_current_theme,
    get_theme_data,
    save_theme,
    save_accent_color,
    get_accent_color,
    apply_theme,
)




# ============================================================
# SETTINGS WINDOW
# ============================================================

class SettingsWindow(QWidget):

    theme_changed = Signal(str)

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)

        self.warning_label_style = ""

        initialize_default_settings()

        self.setWindowTitle(
            "Employee Management System | Settings"
        )

        self.setMinimumSize(
            1100,
            750
        )

        self.resize(
            1200,
            820
        )

        self.setup_ui()

        self.load_settings()

    # ========================================================
    # SETUP UI
    # ========================================================

    def setup_ui(self):
        # The application-wide theme is controlled by
        # utils.theme_manager. We intentionally do not install a
        # second full stylesheet here because it would override
        # the selected global theme.
        main = QVBoxLayout(
            self
        )

        main.setContentsMargins(
            28,
            24,
            28,
            24
        )

        main.setSpacing(
            18
        )

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "Settings & Preferences"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                26,
                QFont.Bold
            )
        )

        subtitle = QLabel(
            "Manage appearance, notifications, security, backup and system preferences."
        )

        subtitle.setObjectName("settingsSubtitle")

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        header.addLayout(
            title_layout
        )

        header.addStretch()

        self.status_label = QLabel(
            "â— Ready"
        )

        self.status_label.setObjectName("settingsStatus")
        self.status_label.setMinimumWidth(150)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setStyleSheet(
            "color: #22C55E; font-weight: 600; padding: 6px 10px;"
        )

        header.addWidget(
            self.status_label
        )

        main.addLayout(
            header
        )

        # ====================================================
        # TABS
        # ====================================================

        self.tabs = QTabWidget()

        self.tabs.addTab(
            self.create_appearance_tab(),
            'Appearance'
        )

        self.tabs.addTab(
            self.create_notification_tab(),
            'Notifications'
        )

        self.tabs.addTab(
            self.create_application_tab(),
            'Application'
        )

        self.tabs.addTab(
            self.create_backup_tab(),
            'Backup & Restore'
        )

        self.tabs.addTab(
            self.create_security_tab(),
            'Security'
        )

        self.tabs.addTab(
            self.create_regional_tab(),
            'Regional'
        )

        self.tabs.addTab(
            self.create_system_tab(),
            'System'
        )

        main.addWidget(
            self.tabs,
            1
        )

        # ====================================================
        # BOTTOM
        # ====================================================

        bottom = QHBoxLayout()

        reset = QPushButton(
            "Reset Defaults"
        )

        reset.clicked.connect(
            self.reset_settings
        )

        bottom.addWidget(
            reset
        )

        bottom.addStretch()

        close_button = QPushButton(
            "Close"
        )

        close_button.clicked.connect(
            self.close
        )

        save_button = QPushButton(
            "Save All Settings"
        )

        save_button.setObjectName(
            "save"
        )

        save_button.clicked.connect(
            self.save_settings
        )

        bottom.addWidget(
            close_button
        )

        bottom.addWidget(
            save_button
        )

        main.addLayout(
            bottom
        )

    # ========================================================
    # APPEARANCE TAB
    # ========================================================

    def create_appearance_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        appearance = QGroupBox(
            "Theme & Appearance"
        )

        grid = QGridLayout(
            appearance
        )

        grid.setVerticalSpacing(
            15
        )

        grid.addWidget(
            QLabel("Application Theme"),
            0,
            0
        )

        self.theme_combo = QComboBox()

        self.theme_combo.addItems(
            get_theme_names()
        )

        self.theme_combo.currentTextChanged.connect(
            self.update_theme_preview
        )

        grid.addWidget(
            self.theme_combo,
            0,
            1
        )

        grid.addWidget(
            QLabel("Interface Density"),
            1,
            0
        )

        self.density_combo = QComboBox()

        self.density_combo.addItems(
            [
                "Comfortable",
                "Compact"
            ]
        )

        self.density_combo.currentTextChanged.connect(
            lambda _value: self.update_theme_preview(
                self.theme_combo.currentText()
            )
        )

        grid.addWidget(
            self.density_combo,
            1,
            1
        )

        grid.addWidget(
            QLabel("Custom Accent"),
            2,
            0
        )

        self.accent_button = QPushButton(
            "Choose Accent Color"
        )

        self.accent_button.clicked.connect(
            self.choose_accent
        )

        grid.addWidget(
            self.accent_button,
            2,
            1
        )

        self.animation_checkbox = QCheckBox(
            "Enable dashboard animations"
        )

        grid.addWidget(
            self.animation_checkbox,
            3,
            0,
            1,
            2
        )

        layout.addWidget(
            appearance
        )

        # Preview

        preview = QGroupBox(
            "Live Theme Preview"
        )

        preview_layout = QVBoxLayout(
            preview
        )

        self.preview_frame = QFrame()

        self.preview_frame.setMinimumHeight(
            220
        )

        preview_inner = QVBoxLayout(
            self.preview_frame
        )

        self.preview_title = QLabel(
            "Employee Management System"
        )

        self.preview_title.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Bold
            )
        )

        self.preview_text = QLabel(
            "Professional HR management workspace"
        )

        self.preview_button = QPushButton(
            "Sample Action"
        )

        preview_inner.addWidget(
            self.preview_title
        )

        preview_inner.addWidget(
            self.preview_text
        )

        preview_inner.addStretch()

        preview_inner.addWidget(
            self.preview_button
        )

        preview_layout.addWidget(
            self.preview_frame
        )

        layout.addWidget(
            preview
        )

        layout.addStretch()

        return page

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    def create_notification_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        group = QGroupBox(
            "Notification Preferences"
        )

        box = QVBoxLayout(
            group
        )

        self.notifications_checkbox = QCheckBox(
            "Enable application notifications"
        )

        self.payroll_notification_checkbox = QCheckBox(
            "Payroll processing and payroll reminders"
        )

        self.performance_notification_checkbox = QCheckBox(
            "Performance review reminders"
        )

        self.calendar_notification_checkbox = QCheckBox(
            "Calendar and event reminders"
        )

        self.notification_sound_checkbox = QCheckBox(
            "Enable notification sound"
        )

        box.addWidget(
            self.notifications_checkbox
        )

        box.addWidget(
            self.payroll_notification_checkbox
        )

        box.addWidget(
            self.performance_notification_checkbox
        )

        box.addWidget(
            self.calendar_notification_checkbox
        )

        box.addWidget(
            self.notification_sound_checkbox
        )

        layout.addWidget(
            group
        )

        info = QLabel(
            "These preferences are stored in the application database and can be used by the Notifications module."
        )

        info.setWordWrap(
            True
        )

        info.setObjectName("settingsInfo")

        layout.addWidget(
            info
        )

        layout.addStretch()

        return page

    # ========================================================
    # APPLICATION
    # ========================================================

    def create_application_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        group = QGroupBox(
            "Application Behavior"
        )

        box = QVBoxLayout(
            group
        )

        self.auto_refresh_checkbox = QCheckBox(
            "Automatically refresh application data"
        )

        self.confirm_delete_checkbox = QCheckBox(
            "Ask for confirmation before deleting records"
        )

        self.auto_save_checkbox = QCheckBox(
            "Enable automatic save behavior"
        )

        self.startup_dashboard_checkbox = QCheckBox(
            "Open dashboard automatically after login"
        )

        box.addWidget(
            self.auto_refresh_checkbox
        )

        box.addWidget(
            self.confirm_delete_checkbox
        )

        box.addWidget(
            self.auto_save_checkbox
        )

        box.addWidget(
            self.startup_dashboard_checkbox
        )

        layout.addWidget(
            group
        )

        layout.addStretch()

        return page

    # ========================================================
    # BACKUP TAB
    # ========================================================

    def create_backup_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        group = QGroupBox(
            "Database Backup & Restore"
        )

        box = QVBoxLayout(
            group
        )

        self.auto_backup_checkbox = QCheckBox(
            "Enable automatic database backup"
        )

        box.addWidget(
            self.auto_backup_checkbox
        )

        frequency_layout = QHBoxLayout()

        frequency_layout.addWidget(
            QLabel("Backup Frequency")
        )

        self.backup_frequency_combo = QComboBox()

        self.backup_frequency_combo.addItems(
            [
                "Daily",
                "Weekly",
                "Monthly"
            ]
        )

        frequency_layout.addWidget(
            self.backup_frequency_combo
        )

        frequency_layout.addStretch()

        box.addLayout(
            frequency_layout
        )

        buttons = QHBoxLayout()

        backup_button = QPushButton(
            "ðŸ’¾ Backup Database Now"
        )

        backup_button.setObjectName(
            "backup"
        )

        backup_button.clicked.connect(
            self.backup_database
        )

        restore_button = QPushButton(
            "â†© Restore Database"
        )

        restore_button.setObjectName(
            "restore"
        )

        restore_button.clicked.connect(
            self.restore_database
        )

        open_backup_button = QPushButton(
            "ðŸ“ Open Backup Folder"
        )

        open_backup_button.clicked.connect(
            self.open_backup_folder
        )

        buttons.addWidget(
            backup_button
        )

        buttons.addWidget(
            restore_button
        )

        buttons.addWidget(
            open_backup_button
        )

        box.addLayout(
            buttons
        )

        layout.addWidget(
            group
        )

        warning = QLabel(
            "Important: A safety backup is created before database restoration."
        )

        warning.setObjectName("settingsWarning")

        layout.addWidget(
            warning
        )

        layout.addStretch()

        return page

    # ========================================================
    # SECURITY
    # ========================================================

    def create_security_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        group = QGroupBox(
            "Session & Security"
        )

        grid = QGridLayout(
            group
        )

        grid.addWidget(
            QLabel("Session Timeout"),
            0,
            0
        )

        self.session_timeout_spin = QSpinBox()

        self.session_timeout_spin.setRange(
            30,
            28800
        )

        self.session_timeout_spin.setSuffix(
            " seconds"
        )

        grid.addWidget(
            self.session_timeout_spin,
            0,
            1
        )

        self.auto_lock_checkbox = QCheckBox(
            "Automatically lock application after timeout"
        )

        grid.addWidget(
            self.auto_lock_checkbox,
            1,
            0,
            1,
            2
        )

        password_info = QLabel(
            "Passwords are protected using the application's password hashing system."
        )

        password_info.setObjectName("settingsInfo")

        grid.addWidget(
            password_info,
            2,
            0,
            1,
            2
        )

        layout.addWidget(
            group
        )

        layout.addStretch()

        return page

    # ========================================================
    # REGIONAL
    # ========================================================

    def create_regional_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        group = QGroupBox(
            "Regional Preferences"
        )

        grid = QGridLayout(
            group
        )

        grid.addWidget(
            QLabel("Currency"),
            0,
            0
        )

        self.currency_combo = QComboBox()

        self.currency_combo.addItems(
            [
                "INR (â‚¹)",
                "USD ($)",
                "EUR (â‚¬)",
                "GBP (Â£)"
            ]
        )

        grid.addWidget(
            self.currency_combo,
            0,
            1
        )

        grid.addWidget(
            QLabel("Date Format"),
            1,
            0
        )

        self.date_format_combo = QComboBox()

        self.date_format_combo.addItems(
            [
                "DD-MM-YYYY",
                "DD/MM/YYYY",
                "YYYY-MM-DD",
                "MM-DD-YYYY"
            ]
        )

        grid.addWidget(
            self.date_format_combo,
            1,
            1
        )

        grid.addWidget(
            QLabel("Week Starts"),
            2,
            0
        )

        self.week_start_combo = QComboBox()

        self.week_start_combo.addItems(
            [
                "Monday",
                "Sunday"
            ]
        )

        grid.addWidget(
            self.week_start_combo,
            2,
            1
        )

        layout.addWidget(
            group
        )

        layout.addStretch()

        return page

    # ========================================================
    # SYSTEM
    # ========================================================

    def create_system_tab(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        group = QGroupBox(
            "System Information"
        )

        grid = QGridLayout(
            group
        )

        paths = get_system_paths()

        information = [

            (
                "Application",
                "Employee Management System"
            ),

            (
                "Version",
                "1.0"
            ),

            (
                "Python",
                platform.python_version()
            ),

            (
                "Operating System",
                platform.system()
                + " "
                + platform.release()
            ),

            (
                "Database",
                "SQLite"
            ),

            (
                "Database Status",
                "Connected"
                if check_database()
                else "Not Connected"
            ),

            (
                "Database Path",
                paths["database"]
            ),

            (
                "Reports Folder",
                paths["reports"]
            ),

            (
                "Backup Folder",
                paths["backups"]
            ),

            (
                "Logs Folder",
                paths["logs"]
            ),
        ]

        for row, (name, value) in enumerate(
            information
        ):

            label = QLabel(
                name
            )

            label.setStyleSheet(
                "font-weight: 600;"
            )

            value_label = QLabel(
                value
            )

            value_label.setWordWrap(
                True
            )

            value_label.setObjectName("settingsInfo")

            grid.addWidget(
                label,
                row,
                0
            )

            grid.addWidget(
                value_label,
                row,
                1
            )

        layout.addWidget(
            group
        )

        layout.addStretch()

        return page

    # ========================================================
    # LOAD SETTINGS
    # ========================================================

    def load_settings(self):

        # Appearance
        self.theme_combo.setCurrentText(
            get_current_theme()
        )

        self.density_combo.setCurrentText(
            get_setting(
                "ui_density",
                "Comfortable"
            )
        )

        self.animation_checkbox.setChecked(
            get_bool_setting(
                "dashboard_animation",
                True
            )
        )

        # Notifications
        self.notifications_checkbox.setChecked(
            get_bool_setting(
                "notifications_enabled",
                True
            )
        )

        self.payroll_notification_checkbox.setChecked(
            get_bool_setting(
                "payroll_notifications",
                True
            )
        )

        self.performance_notification_checkbox.setChecked(
            get_bool_setting(
                "performance_notifications",
                True
            )
        )

        self.calendar_notification_checkbox.setChecked(
            get_bool_setting(
                "calendar_notifications",
                True
            )
        )

        self.notification_sound_checkbox.setChecked(
            get_bool_setting(
                "notification_sound",
                False
            )
        )

        # Application
        self.auto_refresh_checkbox.setChecked(
            get_bool_setting(
                "auto_refresh",
                True
            )
        )

        self.confirm_delete_checkbox.setChecked(
            get_bool_setting(
                "confirm_delete",
                True
            )
        )

        self.auto_save_checkbox.setChecked(
            get_bool_setting(
                "auto_save",
                True
            )
        )

        self.startup_dashboard_checkbox.setChecked(
            get_bool_setting(
                "startup_dashboard",
                True
            )
        )

        # Backup
        self.auto_backup_checkbox.setChecked(
            get_bool_setting(
                "auto_backup",
                False
            )
        )

        self.backup_frequency_combo.setCurrentText(
            get_setting(
                "backup_frequency",
                "Daily"
            )
        )

        # Security
        self.session_timeout_spin.setValue(
            int(
                get_setting(
                    "session_timeout",
                    "30"
                )
            )
        )

        self.auto_lock_checkbox.setChecked(
            get_bool_setting(
                "auto_lock",
                False
            )
        )

        # Regional
        self.currency_combo.setCurrentText(
            get_setting(
                "currency",
                "INR (â‚¹)"
            )
        )

        self.date_format_combo.setCurrentText(
            get_setting(
                "date_format",
                "DD-MM-YYYY"
            )
        )

        self.week_start_combo.setCurrentText(
            get_setting(
                "week_start",
                "Monday"
            )
        )

        self.update_theme_preview(
            self.theme_combo.currentText()
        )

    # ========================================================
    # THEME PREVIEW
    # ========================================================

    def update_theme_preview(
        self,
        theme_name
    ):
        """
        Update the preview and apply the selected theme immediately.

        The database preference is saved only by Save All Settings.
        """

        if not theme_name:
            return

        try:
            theme = get_theme_data(theme_name)

            accent = (
                get_accent_color()
                or theme["accent"]
            )

            app = QApplication.instance()

            if app is not None:
                apply_theme(
                    app,
                    theme_name,
                    self.density_combo.currentText()
                    if hasattr(self, "density_combo")
                    else get_setting(
                        "ui_density",
                        "Comfortable"
                    )
                )

            self.preview_frame.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {theme["card"]};
                    border: 1px solid {theme["border"]};
                    border-radius: 12px;
                }}
                """
            )

            self.preview_title.setStyleSheet(
                f"""
                color: {theme["text"]};
                background: transparent;
                """
            )

            self.preview_text.setStyleSheet(
                f"""
                color: {theme["muted"]};
                background: transparent;
                """
            )

            self.preview_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {accent};
                    color: white;
                    border: none;
                    border-radius: 7px;
                    padding: 9px 16px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {theme.get("accent_hover", accent)};
                }}
                """
            )

            self._apply_settings_dynamic_styles(theme)

        except Exception as error:
            print(f"Theme preview error: {error}")

    def _apply_settings_dynamic_styles(self, theme):
        """Apply only small Settings-specific styles dynamically."""

        success = theme.get("success", theme["accent"])
        warning = theme.get("warning", theme["accent"])
        muted = theme["muted"]

        self.status_label.setStyleSheet(
            f"""
            color: {success};
            font-weight: 600;
            """
        )

        for widget in self.findChildren(QLabel):
            if widget.objectName() == "settingsWarning":
                widget.setStyleSheet(
                    f"""
                    color: {warning};
                    padding: 10px;
                    font-weight: 600;
                    """
                )

            elif widget.objectName() == "settingsSubtitle":
                widget.setStyleSheet(
                    f"""
                    color: {muted};
                    font-size: 11px;
                    """
                )

            elif widget.objectName() == "settingsInfo":
                widget.setStyleSheet(
                    f"""
                    color: {muted};
                    """
                )

    # ========================================================
    # CUSTOM ACCENT
    # ========================================================

    def choose_accent(self):

        color = QColorDialog.getColor(
            QColor(
                get_accent_color()
                or "#3B82F6"
            ),
            self,
            "Choose Accent Color"
        )

        if color.isValid():

            save_accent_color(
                color.name()
            )

            self.accent_button.setText(
                f"Accent: {color.name()}"
            )

            self.update_theme_preview(
                self.theme_combo.currentText()
            )

    # ========================================================
    # SAVE
    # ========================================================

    def save_settings(self):

        try:

            # Appearance
            save_theme(
                self.theme_combo.currentText()
            )

            set_setting(
                "ui_density",
                self.density_combo.currentText()
            )

            set_bool_setting(
                "dashboard_animation",
                self.animation_checkbox.isChecked()
            )

            # Notifications
            set_bool_setting(
                "notifications_enabled",
                self.notifications_checkbox.isChecked()
            )

            set_bool_setting(
                "payroll_notifications",
                self.payroll_notification_checkbox.isChecked()
            )

            set_bool_setting(
                "performance_notifications",
                self.performance_notification_checkbox.isChecked()
            )

            set_bool_setting(
                "calendar_notifications",
                self.calendar_notification_checkbox.isChecked()
            )

            set_bool_setting(
                "notification_sound",
                self.notification_sound_checkbox.isChecked()
            )

            # Application
            set_bool_setting(
                "auto_refresh",
                self.auto_refresh_checkbox.isChecked()
            )

            set_bool_setting(
                "confirm_delete",
                self.confirm_delete_checkbox.isChecked()
            )

            set_bool_setting(
                "auto_save",
                self.auto_save_checkbox.isChecked()
            )

            set_bool_setting(
                "startup_dashboard",
                self.startup_dashboard_checkbox.isChecked()
            )

            # Backup
            set_bool_setting(
                "auto_backup",
                self.auto_backup_checkbox.isChecked()
            )

            set_setting(
                "backup_frequency",
                self.backup_frequency_combo.currentText()
            )

            # Security
            set_setting(
                "session_timeout",
                self.session_timeout_spin.value()
            )

            set_bool_setting(
                "auto_lock",
                self.auto_lock_checkbox.isChecked()
            )

            # Regional
            set_setting(
                "currency",
                self.currency_combo.currentText()
            )

            set_setting(
                "date_format",
                self.date_format_combo.currentText()
            )

            set_setting(
                "week_start",
                self.week_start_combo.currentText()
            )

            # Apply
            app = QApplication.instance()

            apply_theme(
                app,
                self.theme_combo.currentText(),
                self.density_combo.currentText()
            )

            self.status_label.setText(
                "â— All settings saved"
            )

            current_theme = get_theme_data(self.theme_combo.currentText())
            self.status_label.setStyleSheet(
                f"""
                color: {current_theme["success"]};
                font-weight: 600;
                """
            )

            self.theme_changed.emit(
                self.theme_combo.currentText()
            )

            QMessageBox.information(
                self,
                "Settings Saved",
                "All application settings have been saved successfully."
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Settings Error",
                f"Unable to save settings.\n\n{error}"
            )

    # ========================================================
    # BACKUP
    # ========================================================

    def backup_database(self):

        try:

            path = create_database_backup()

            QMessageBox.information(
                self,
                "Backup Successful",
                (
                    "Database backup created successfully.\n\n"
                    f"Backup File:\n{path}"
                )
            )

            self.status_label.setText(
                "â— Database backup created"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Backup Error",
                f"Unable to create backup.\n\n{error}"
            )

    # ========================================================
    # RESTORE
    # ========================================================

    def restore_database(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database Backup",
            str(
                Path(
                    get_system_paths()["backups"]
                )
            ),
            "SQLite Database (*.db)"
        )

        if not file_path:

            return

        answer = QMessageBox.warning(
            self,
            "Confirm Database Restore",
            (
                "Restoring a database will replace the current "
                "database with the selected backup.\n\n"
                "A safety backup will be created first.\n\n"
                "Continue?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:

            return

        try:

            safety_backup = restore_database(
                file_path
            )

            QMessageBox.information(
                self,
                "Restore Successful",
                (
                    "Database restored successfully.\n\n"
                    f"Safety backup:\n{safety_backup}\n\n"
                    "Please restart the application."
                )
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Restore Error",
                f"Unable to restore database.\n\n{error}"
            )

    # ========================================================
    # OPEN BACKUP FOLDER
    # ========================================================

    def open_backup_folder(self):

        folder = get_system_paths()[
            "backups"
        ]

        try:

            os.startfile(
                folder
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "Folder Error",
                f"Unable to open folder.\n\n{error}"
            )

    # ========================================================
    # RESET
    # ========================================================

    def reset_settings(self):

        answer = QMessageBox.question(
            self,
            "Reset Settings",
            (
                "Reset all settings to their "
                "default values?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:

            return

        try:

            from services.settings_service import (
                DEFAULT_SETTINGS
            )

            for key, value in DEFAULT_SETTINGS.items():

                set_setting(
                    key,
                    value
                )

            self.load_settings()

            app = QApplication.instance()

            apply_theme(
                app,
                "Dark",
                "Comfortable"
            )

            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been restored to defaults."
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Reset Error",
                f"Unable to reset settings.\n\n{error}"
            )


# ============================================================
# STANDALONE TEST
# ============================================================

def run_settings_window():

    app = QApplication.instance()

    created_app = False

    if app is None:

        app = QApplication(
            sys.argv
        )

        created_app = True

    initialize_default_settings()

    apply_theme(
        app,
        get_current_theme(),
        get_setting(
            "ui_density",
            "Comfortable"
        )
    )

    window = SettingsWindow()

    window.show()

    if created_app:

        sys.exit(
            app.exec()
        )

    return window


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_settings_window()

