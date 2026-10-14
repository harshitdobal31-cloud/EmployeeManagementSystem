# ============================================================
# EMPLOYEE MANAGEMENT SYSTEM
# SETTINGS SERVICE
# ============================================================

from datetime import datetime
from pathlib import Path
import shutil
import sqlite3

from sqlalchemy import text

from database.database import (
    SessionLocal,
    DATABASE_PATH,
)

from database.models import AppSetting


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

BACKUP_DIR = BASE_DIR / "backups"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"


BACKUP_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS = {

    # Appearance
    "theme": "Dark",
    "accent_color": "",
    "ui_density": "Comfortable",
    "dashboard_animation": "True",

    # Notifications
    "notifications_enabled": "True",
    "payroll_notifications": "True",
    "performance_notifications": "True",
    "calendar_notifications": "True",
    "notification_sound": "False",

    # Application
    "auto_refresh": "True",
    "confirm_delete": "True",
    "auto_save": "True",
    "startup_dashboard": "True",

    # Backup
    "auto_backup": "False",
    "backup_frequency": "Daily",

    # Security
    "session_timeout": "30",
    "auto_lock": "False",

    # Regional
    "currency": "INR (₹)",
    "date_format": "DD-MM-YYYY",
    "week_start": "Monday",
}


# ============================================================
# SETTING DESCRIPTIONS
# ============================================================

SETTING_DESCRIPTIONS = {

    "theme":
        "Application visual theme",

    "accent_color":
        "Application accent color",

    "ui_density":
        "Application interface density",

    "dashboard_animation":
        "Dashboard animation preference",

    "notifications_enabled":
        "Enable application notifications",

    "payroll_notifications":
        "Enable payroll notifications",

    "performance_notifications":
        "Enable performance notifications",

    "calendar_notifications":
        "Enable calendar notifications",

    "notification_sound":
        "Notification sound preference",

    "auto_refresh":
        "Automatically refresh application data",

    "confirm_delete":
        "Confirm before deleting records",

    "auto_save":
        "Automatic save preference",

    "startup_dashboard":
        "Open dashboard after login",

    "auto_backup":
        "Automatic database backup",

    "backup_frequency":
        "Automatic backup frequency",

    "session_timeout":
        "Session timeout in minutes",

    "auto_lock":
        "Automatically lock application",

    "currency":
        "Application currency",

    "date_format":
        "Application date format",

    "week_start":
        "First day of the week",
}


# ============================================================
# GET SETTING
# ============================================================

def get_setting(
    key,
    default=None
):

    db = SessionLocal()

    try:

        setting = (
            db.query(AppSetting)
            .filter(
                AppSetting.setting_key == key
            )
            .first()
        )

        if setting is None:
            return default

        return setting.setting_value

    finally:

        db.close()


# ============================================================
# SET SETTING
# ============================================================

def set_setting(
    key,
    value,
    description=None
):

    db = SessionLocal()

    try:

        setting = (
            db.query(AppSetting)
            .filter(
                AppSetting.setting_key == key
            )
            .first()
        )

        if setting is None:

            setting = AppSetting(
                setting_key=key,
                setting_value=str(value),
                description=(
                    description
                    if description is not None
                    else SETTING_DESCRIPTIONS.get(
                        key,
                        ""
                    )
                ),
                updated_at=datetime.now()
            )

            db.add(setting)

        else:

            setting.setting_value = str(value)

            if description is not None:
                setting.description = description

            setting.updated_at = datetime.now()

        db.commit()

        db.refresh(setting)

        return setting

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# GET ALL SETTINGS
# ============================================================

def get_all_settings():

    db = SessionLocal()

    try:

        settings = (
            db.query(AppSetting)
            .order_by(
                AppSetting.setting_key.asc()
            )
            .all()
        )

        return {
            item.setting_key: item.setting_value
            for item in settings
        }

    finally:

        db.close()


# ============================================================
# INITIALIZE DEFAULT SETTINGS
# ============================================================

def initialize_default_settings():

    db = SessionLocal()

    try:

        for key, value in DEFAULT_SETTINGS.items():

            setting = (
                db.query(AppSetting)
                .filter(
                    AppSetting.setting_key == key
                )
                .first()
            )

            if setting is None:

                setting = AppSetting(
                    setting_key=key,
                    setting_value=str(value),
                    description=SETTING_DESCRIPTIONS.get(
                        key,
                        ""
                    ),
                    updated_at=datetime.now()
                )

                db.add(setting)

        db.commit()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# BOOLEAN SETTING
# ============================================================

def get_bool_setting(
    key,
    default=True
):

    value = get_setting(
        key,
        None
    )

    if value is None:
        return default

    return str(value).lower() in {
        "true",
        "1",
        "yes",
        "on"
    }


def set_bool_setting(
    key,
    value,
    description=None
):

    return set_setting(
        key,
        "True" if value else "False",
        description
    )


# ============================================================
# DATABASE CONNECTION TEST
# ============================================================

def check_database():

    db = None

    try:

        db = SessionLocal()

        db.execute(
            text("SELECT 1")
        )

        return True

    except Exception:

        return False

    finally:

        if db is not None:
            db.close()


# ============================================================
# DATABASE BACKUP
# ============================================================

def create_database_backup():

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / f"employee_management_backup_{timestamp}.db"
    )

    source = None
    destination = None

    try:

        source = sqlite3.connect(
            str(DATABASE_PATH)
        )

        destination = sqlite3.connect(
            str(backup_path)
        )

        source.backup(
            destination
        )

        destination.commit()

    finally:

        if destination is not None:
            destination.close()

        if source is not None:
            source.close()

    return backup_path


# ============================================================
# RESTORE DATABASE
# ============================================================

def restore_database(
    backup_file
):

    backup_file = Path(
        backup_file
    )

    if not backup_file.exists():

        raise FileNotFoundError(
            "Selected backup file does not exist."
        )

    if backup_file.suffix.lower() != ".db":

        raise ValueError(
            "Please select a valid SQLite database backup."
        )

    # --------------------------------------------------------
    # Validate backup
    # --------------------------------------------------------

    connection = sqlite3.connect(
        str(backup_file)
    )

    try:

        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        ).fetchall()

        if not result:

            raise ValueError(
                "Selected file does not contain a valid database."
            )

    finally:

        connection.close()

    # --------------------------------------------------------
    # Safety backup
    # --------------------------------------------------------

    safety_backup = create_database_backup()

    # --------------------------------------------------------
    # Restore
    # --------------------------------------------------------

    shutil.copy2(
        backup_file,
        DATABASE_PATH
    )

    return safety_backup


# ============================================================
# SYSTEM PATHS
# ============================================================

def get_system_paths():

    return {

        "database":
            str(DATABASE_PATH),

        "backups":
            str(BACKUP_DIR),

        "reports":
            str(REPORT_DIR),

        "logs":
            str(LOG_DIR),
    }