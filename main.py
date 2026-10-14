# ============================================================
# EMPLOYEE MANAGEMENT SYSTEM
# MAIN APPLICATION
# ============================================================

import sys

from PySide6.QtWidgets import QApplication

from database.database import create_tables
from database import models

from services.settings_service import (
    initialize_default_settings,
)

from utils.theme_manager import (
    get_current_theme,
    apply_theme,
)

from ui.login import LoginWindow


# ============================================================
# MAIN
# ============================================================

def main():

    print("Starting Employee Management System...")

    # --------------------------------------------------------
    # 1. Initialize database
    # --------------------------------------------------------

    try:

        create_tables()

        print(
            "Database initialized successfully!"
        )

    except Exception as error:

        print(
            f"Database initialization failed: {error}"
        )

        return

    # --------------------------------------------------------
    # 2. Initialize default application settings
    # --------------------------------------------------------

    try:

        initialize_default_settings()

        print(
            "Application settings initialized!"
        )

    except Exception as error:

        print(
            f"Settings initialization failed: {error}"
        )

    # --------------------------------------------------------
    # 3. Create Qt application
    # --------------------------------------------------------

    app = QApplication(
        sys.argv
    )

    # --------------------------------------------------------
    # 4. Load saved theme
    # --------------------------------------------------------

    try:

        current_theme = get_current_theme()

        apply_theme(
            app,
            current_theme
        )

        print(
            f"Application theme: {current_theme}"
        )

    except Exception as error:

        print(
            f"Theme loading failed: {error}"
        )

        # Safe fallback
        apply_theme(
            app,
            "Dark"
        )

    # --------------------------------------------------------
    # 5. Open Login
    # --------------------------------------------------------

    window = LoginWindow()

    window.show()

    print(
        "Login window opened successfully!"
    )

    # --------------------------------------------------------
    # 6. Start application
    # --------------------------------------------------------

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()