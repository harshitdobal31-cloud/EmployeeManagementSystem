from datetime import date

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QCalendarWidget,
    QFrame,
)

from services.calendar_service import (
    add_event,
    get_all_events,
    get_events_by_date,
    search_events,
    update_event,
    delete_event,
    get_event_statistics,
    normalize_date,
    format_date,
)

from utils.session import Session


# ============================================================
# COLORS
# ============================================================

BG = "#0F172A"
CARD = "#111827"
CARD_2 = "#1E293B"
BORDER = "#334155"

TEXT = "#F8FAFC"
TEXT_MUTED = "#94A3B8"

BLUE = "#3B82F6"
BLUE_HOVER = "#2563EB"

GREEN = "#22C55E"
RED = "#EF4444"
YELLOW = "#FACC15"
PURPLE = "#8B5CF6"
CYAN = "#06B6D4"


# ============================================================
# EVENT TYPES
# ============================================================

EVENT_TYPES = [
    "Meeting",
    "Holiday",
    "Training",
    "Birthday",
    "Company Event",
    "Interview",
    "Other",
]


# ============================================================
# HELPERS
# ============================================================

def create_label(
    text,
    size=12,
    bold=False,
    color=TEXT
):

    label = QLabel(text)

    font = QFont("Segoe UI")

    font.setPointSize(size)
    font.setBold(bold)

    label.setFont(font)

    label.setStyleSheet(
        f"color: {color};"
    )

    return label


def style_input(widget):

    widget.setMinimumHeight(40)

    widget.setStyleSheet(
        f"""
        QLineEdit,
        QComboBox,
        QDateEdit,
        QTextEdit {{
            background-color: {CARD_2};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 8px 10px;
            color: {TEXT};
            selection-background-color: {BLUE};
        }}

        QLineEdit:focus,
        QComboBox:focus,
        QDateEdit:focus,
        QTextEdit:focus {{
            border: 1px solid {BLUE};
        }}

        QComboBox QAbstractItemView {{
            background-color: {CARD_2};
            color: {TEXT};
            selection-background-color: {BLUE};
            border: 1px solid {BORDER};
        }}
        """
    )


def create_stat_card(
    title,
    value,
    color
):

    frame = QFrame()

    frame.setObjectName(
        "statCard"
    )

    frame.setStyleSheet(
        f"""
        QFrame#statCard {{
            background-color: {CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
        }}
        """
    )

    layout = QVBoxLayout(frame)

    layout.setContentsMargins(
        18,
        14,
        18,
        14
    )

    layout.setSpacing(4)

    title_label = create_label(
        title,
        size=10,
        color=TEXT_MUTED
    )

    value_label = create_label(
        str(value),
        size=22,
        bold=True,
        color=color
    )

    layout.addWidget(
        title_label
    )

    layout.addWidget(
        value_label
    )

    return frame


# ============================================================
# EVENT DIALOG
# ============================================================

class EventDialog(QDialog):

    def __init__(
        self,
        parent=None,
        event_data=None
    ):

        super().__init__(parent)

        # IMPORTANT:
        # Do NOT use self.event here.
        # QDialog already has a built-in event()
        # method. Using self.event would overwrite it.

        self.event_data = event_data

        self.is_edit_mode = (
            self.event_data is not None
        )

        if self.is_edit_mode:

            self.setWindowTitle(
                "Edit Calendar Event"
            )

        else:

            self.setWindowTitle(
                "Add Calendar Event"
            )

        self.setMinimumWidth(560)

        self.setModal(True)

        self.setup_ui()

        if self.is_edit_mode:
            self.load_event_data()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {BG};
            }}

            QLabel {{
                color: {TEXT};
            }}

            QPushButton {{
                background-color: {BLUE};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: {BLUE_HOVER};
            }}
            """
        )

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        main_layout.setSpacing(15)

        title = create_label(
            (
                "Edit Event"
                if self.is_edit_mode
                else "Create New Event"
            ),
            size=21,
            bold=True
        )

        subtitle = create_label(
            (
                "Update existing calendar event."
                if self.is_edit_mode
                else "Add a new event to the company calendar."
            ),
            size=10,
            color=TEXT_MUTED
        )

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            subtitle
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title_label = create_label(
            "Event Title *",
            size=11,
            bold=True
        )

        self.title_input = QLineEdit()

        self.title_input.setPlaceholderText(
            "Enter event title"
        )

        style_input(
            self.title_input
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        date_label = create_label(
            "Event Date *",
            size=11,
            bold=True
        )

        self.date_input = QDateEdit()

        self.date_input.setCalendarPopup(
            True
        )

        self.date_input.setDate(
            QDate.currentDate()
        )

        self.date_input.setDisplayFormat(
            "dd-MM-yyyy"
        )

        style_input(
            self.date_input
        )

        # ----------------------------------------------------
        # TYPE
        # ----------------------------------------------------

        type_label = create_label(
            "Event Type *",
            size=11,
            bold=True
        )

        self.type_input = QComboBox()

        self.type_input.addItems(
            EVENT_TYPES
        )

        style_input(
            self.type_input
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        description_label = create_label(
            "Description",
            size=11,
            bold=True
        )

        self.description_input = QTextEdit()

        self.description_input.setPlaceholderText(
            "Enter event description..."
        )

        self.description_input.setMinimumHeight(
            120
        )

        style_input(
            self.description_input
        )

        # ----------------------------------------------------
        # FORM
        # ----------------------------------------------------

        form = QGridLayout()

        form.setHorizontalSpacing(15)

        form.setVerticalSpacing(12)

        form.addWidget(
            title_label,
            0,
            0
        )

        form.addWidget(
            self.title_input,
            0,
            1
        )

        form.addWidget(
            date_label,
            1,
            0
        )

        form.addWidget(
            self.date_input,
            1,
            1
        )

        form.addWidget(
            type_label,
            2,
            0
        )

        form.addWidget(
            self.type_input,
            2,
            1
        )

        form.addWidget(
            description_label,
            3,
            0,
            Qt.AlignTop
        )

        form.addWidget(
            self.description_input,
            3,
            1
        )

        main_layout.addLayout(
            form
        )

        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        self.buttons.accepted.connect(
            self.save_event
        )

        self.buttons.rejected.connect(
            self.reject
        )

        main_layout.addWidget(
            self.buttons
        )

    # ========================================================
    # LOAD EVENT
    # ========================================================

    def load_event_data(self):

        event_data = self.event_data

        if event_data is None:
            return

        self.title_input.setText(
            event_data.title or ""
        )

        event_date = normalize_date(
            event_data.event_date
        )

        if event_date:

            self.date_input.setDate(
                QDate(
                    event_date.year,
                    event_date.month,
                    event_date.day
                )
            )

        event_type = (
            event_data.event_type
            or "Other"
        )

        index = (
            self.type_input.findText(
                event_type
            )
        )

        if index >= 0:

            self.type_input.setCurrentIndex(
                index
            )

        self.description_input.setPlainText(
            event_data.description or ""
        )

    # ========================================================
    # SAVE EVENT
    # ========================================================

    def save_event(self):

        title = (
            self.title_input
            .text()
            .strip()
        )

        if not title:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter event title."
            )

            self.title_input.setFocus()

            return

        event_date = (
            self.date_input
            .date()
            .toPython()
        )

        event_type = (
            self.type_input
            .currentText()
        )

        description = (
            self.description_input
            .toPlainText()
            .strip()
        )

        current_user = Session.get_user()

        created_by = None

        if current_user:

            created_by = (
                current_user.id
            )

        try:

            # ------------------------------------------------
            # EDIT
            # ------------------------------------------------

            if self.is_edit_mode:

                update_event(
                    event_id=self.event_data.id,
                    title=title,
                    description=description,
                    event_date=event_date,
                    event_type=event_type
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Calendar event updated successfully."
                )

            # ------------------------------------------------
            # ADD
            # ------------------------------------------------

            else:

                add_event(
                    title=title,
                    description=description,
                    event_date=event_date,
                    event_type=event_type,
                    created_by=created_by
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Calendar event added successfully."
                )

            self.accept()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Save Error",
                f"Unable to save event.\n\n{error}"
            )


# ============================================================
# CALENDAR WINDOW
# ============================================================

class CalendarWindow(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Employee Management System | Calendar"
        )

        self.setMinimumSize(
            1250,
            820
        )

        self.events = []

        self.setup_ui()

        self.load_statistics()

        self.load_events()

        self.show_selected_date_events()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {BG};
                color: {TEXT};
                font-family: "Segoe UI";
            }}

            QLineEdit {{
                background-color: {CARD_2};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 9px;
                color: {TEXT};
            }}

            QLineEdit:focus {{
                border: 1px solid {BLUE};
            }}

            QPushButton {{
                background-color: {CARD_2};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 9px 15px;
                color: {TEXT};
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: {BLUE};
                border-color: {BLUE};
            }}

            QTableWidget {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                gridline-color: {BORDER};
                color: {TEXT};
                selection-background-color: #1D4ED8;
                selection-color: white;
            }}

            QTableWidget::item {{
                padding: 8px;
            }}

            QHeaderView::section {{
                background-color: {CARD_2};
                color: {TEXT};
                padding: 10px;
                border: none;
                border-bottom: 1px solid {BORDER};
                font-weight: 600;
            }}

            QCalendarWidget {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}

            QCalendarWidget QToolButton {{
                color: {TEXT};
                background-color: {CARD_2};
                border: none;
                padding: 7px;
                border-radius: 5px;
            }}

            QCalendarWidget QToolButton:hover {{
                background-color: {BLUE};
            }}

            QCalendarWidget QMenu {{
                background-color: {CARD_2};
                color: {TEXT};
            }}

            QCalendarWidget QSpinBox {{
                background-color: {CARD_2};
                color: {TEXT};
                border: none;
            }}

            QCalendarWidget QWidget {{
                alternate-background-color: {CARD};
            }}

            QCalendarWidget QAbstractItemView {{
                background-color: {CARD};
                color: {TEXT};
                selection-background-color: {BLUE};
                selection-color: white;
            }}
            """
        )

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        main_layout.setSpacing(18)

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        heading_layout = QVBoxLayout()

        heading_layout.setSpacing(3)

        heading = create_label(
            "Calendar & Events",
            size=25,
            bold=True
        )

        subtitle = create_label(
            "Manage meetings, holidays, training and company events.",
            size=11,
            color=TEXT_MUTED
        )

        heading_layout.addWidget(
            heading
        )

        heading_layout.addWidget(
            subtitle
        )

        header.addLayout(
            heading_layout
        )

        header.addStretch()

        self.add_button = QPushButton(
            "+  Add Event"
        )

        self.add_button.setMinimumHeight(
            42
        )

        self.add_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BLUE};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background-color: {BLUE_HOVER};
            }}
            """
        )

        self.add_button.clicked.connect(
            self.open_add_event
        )

        header.addWidget(
            self.add_button
        )

        main_layout.addLayout(
            header
        )

        # ====================================================
        # STATISTICS
        # ====================================================

        stats_layout = QHBoxLayout()

        stats_layout.setSpacing(12)

        self.total_card = create_stat_card(
            "TOTAL EVENTS",
            0,
            BLUE
        )

        self.today_card = create_stat_card(
            "TODAY",
            0,
            GREEN
        )

        self.upcoming_card = create_stat_card(
            "UPCOMING",
            0,
            PURPLE
        )

        self.meeting_card = create_stat_card(
            "MEETINGS",
            0,
            CYAN
        )

        stats_layout.addWidget(
            self.total_card
        )

        stats_layout.addWidget(
            self.today_card
        )

        stats_layout.addWidget(
            self.upcoming_card
        )

        stats_layout.addWidget(
            self.meeting_card
        )

        main_layout.addLayout(
            stats_layout
        )

        # ====================================================
        # SEARCH
        # ====================================================

        search_layout = QHBoxLayout()

        search_label = create_label(
            "Search:",
            size=11,
            bold=True
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search title, type, description or date..."
        )

        self.search_input.setMinimumHeight(
            40
        )

        self.search_input.textChanged.connect(
            self.search_events
        )

        refresh_button = QPushButton(
            "⟳  Refresh"
        )

        refresh_button.setMinimumHeight(
            40
        )

        refresh_button.clicked.connect(
            self.refresh_calendar
        )

        search_layout.addWidget(
            search_label
        )

        search_layout.addWidget(
            self.search_input,
            1
        )

        search_layout.addWidget(
            refresh_button
        )

        main_layout.addLayout(
            search_layout
        )

        # ====================================================
        # CALENDAR AREA
        # ====================================================

        middle_layout = QHBoxLayout()

        middle_layout.setSpacing(15)

        # ----------------------------------------------------
        # Calendar
        # ----------------------------------------------------

        calendar_frame = QFrame()

        calendar_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """
        )

        calendar_layout = QVBoxLayout(
            calendar_frame
        )

        calendar_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        calendar_title = create_label(
            "Company Calendar",
            size=14,
            bold=True
        )

        calendar_layout.addWidget(
            calendar_title
        )

        self.calendar = QCalendarWidget()

        self.calendar.setGridVisible(
            True
        )

        self.calendar.setSelectedDate(
            QDate.currentDate()
        )

        self.calendar.selectionChanged.connect(
            self.show_selected_date_events
        )

        middle_layout.addWidget(
            calendar_frame,
            1
        )

        calendar_layout.addWidget(
            self.calendar
        )

        # ----------------------------------------------------
        # Selected Day
        # ----------------------------------------------------

        events_frame = QFrame()

        events_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """
        )

        events_layout = QVBoxLayout(
            events_frame
        )

        events_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        self.selected_date_label = create_label(
            "Events",
            size=15,
            bold=True
        )

        events_layout.addWidget(
            self.selected_date_label
        )

        self.selected_events_table = QTableWidget()

        self.selected_events_table.setColumnCount(
            3
        )

        self.selected_events_table.setHorizontalHeaderLabels(
            [
                "Title",
                "Type",
                "Description"
            ]
        )

        self.selected_events_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.selected_events_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        selected_header = (
            self.selected_events_table
            .horizontalHeader()
        )

        selected_header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        selected_header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        selected_header.setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        events_layout.addWidget(
            self.selected_events_table
        )

        middle_layout.addWidget(
            events_frame,
            1
        )

        main_layout.addLayout(
            middle_layout,
            1
        )

        # ====================================================
        # ALL EVENTS
        # ====================================================

        all_events_title = create_label(
            "All Calendar Events",
            size=15,
            bold=True
        )

        main_layout.addWidget(
            all_events_title
        )

        self.events_table = QTableWidget()

        self.events_table.setColumnCount(
            7
        )

        self.events_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Title",
                "Date",
                "Type",
                "Description",
                "Created By",
                "Actions"
            ]
        )

        self.events_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.events_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.events_table.verticalHeader().setVisible(
            False
        )

        table_header = (
            self.events_table
            .horizontalHeader()
        )

        table_header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        table_header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        table_header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        table_header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        table_header.setSectionResizeMode(
            4,
            QHeaderView.Stretch
        )

        table_header.setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents
        )

        table_header.setSectionResizeMode(
            6,
            QHeaderView.ResizeToContents
        )

        main_layout.addWidget(
            self.events_table,
            1
        )

    # ========================================================
    # STATISTICS
    # ========================================================

    def load_statistics(self):

        try:

            stats = (
                get_event_statistics()
            )

            self.set_card_value(
                self.total_card,
                stats.get(
                    "total_events",
                    0
                )
            )

            self.set_card_value(
                self.today_card,
                stats.get(
                    "today_events",
                    0
                )
            )

            self.set_card_value(
                self.upcoming_card,
                stats.get(
                    "upcoming_events",
                    0
                )
            )

            self.set_card_value(
                self.meeting_card,
                stats.get(
                    "meeting_events",
                    0
                )
            )

        except Exception as error:

            print(
                "Statistics error:",
                error
            )

    def set_card_value(
        self,
        card,
        value
    ):

        layout = card.layout()

        if layout is None:
            return

        if layout.count() < 2:
            return

        value_widget = (
            layout
            .itemAt(1)
            .widget()
        )

        if value_widget:

            value_widget.setText(
                str(value)
            )

    # ========================================================
    # LOAD EVENTS
    # ========================================================

    def load_events(self):

        try:

            self.events = (
                get_all_events()
            )

            self.populate_events_table(
                self.events
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Calendar Error",
                (
                    "Unable to load Calendar.\n\n"
                    f"{error}"
                )
            )

    # ========================================================
    # POPULATE EVENTS TABLE
    # ========================================================

    def populate_events_table(
        self,
        events
    ):

        self.events_table.setRowCount(
            0
        )

        for event_data in events:

            row = (
                self.events_table
                .rowCount()
            )

            self.events_table.insertRow(
                row
            )

            # ------------------------------------------------
            # ID
            # ------------------------------------------------

            id_item = QTableWidgetItem(
                str(event_data.id)
            )

            id_item.setForeground(
                QBrush(
                    QColor(TEXT_MUTED)
                )
            )

            self.events_table.setItem(
                row,
                0,
                id_item
            )

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title_item = QTableWidgetItem(
                event_data.title or ""
            )

            title_item.setForeground(
                QBrush(
                    QColor(TEXT)
                )
            )

            title_item.setFont(
                QFont(
                    "Segoe UI",
                    10,
                    QFont.Bold
                )
            )

            self.events_table.setItem(
                row,
                1,
                title_item
            )

            # ------------------------------------------------
            # DATE
            # ------------------------------------------------

            date_item = QTableWidgetItem(
                format_date(
                    event_data.event_date
                )
            )

            date_item.setForeground(
                QBrush(
                    QColor(TEXT)
                )
            )

            self.events_table.setItem(
                row,
                2,
                date_item
            )

            # ------------------------------------------------
            # TYPE
            # ------------------------------------------------

            event_type = (
                event_data.event_type
                or "Other"
            )

            type_item = QTableWidgetItem(
                event_type
            )

            type_item.setForeground(
                QBrush(
                    QColor(
                        self.get_event_color(
                            event_type
                        )
                    )
                )
            )

            type_item.setFont(
                QFont(
                    "Segoe UI",
                    10,
                    QFont.Bold
                )
            )

            self.events_table.setItem(
                row,
                3,
                type_item
            )

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            description_item = QTableWidgetItem(
                event_data.description
                or "-"
            )

            description_item.setForeground(
                QBrush(
                    QColor(TEXT_MUTED)
                )
            )

            self.events_table.setItem(
                row,
                4,
                description_item
            )

            # ------------------------------------------------
            # CREATED BY
            # ------------------------------------------------

            created_by = (
                str(event_data.created_by)
                if event_data.created_by
                else "-"
            )

            created_item = QTableWidgetItem(
                created_by
            )

            created_item.setForeground(
                QBrush(
                    QColor(TEXT_MUTED)
                )
            )

            self.events_table.setItem(
                row,
                5,
                created_item
            )

            # ------------------------------------------------
            # ACTIONS
            # ------------------------------------------------

            action_widget = QWidget()

            action_layout = QHBoxLayout(
                action_widget
            )

            action_layout.setContentsMargins(
                4,
                2,
                4,
                2
            )

            action_layout.setSpacing(
                5
            )

            edit_button = QPushButton(
                "Edit"
            )

            edit_button.setFixedHeight(
                30
            )

            edit_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {BLUE};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 4px 10px;
                }}

                QPushButton:hover {{
                    background-color: {BLUE_HOVER};
                }}
                """
            )

            delete_button = QPushButton(
                "Delete"
            )

            delete_button.setFixedHeight(
                30
            )

            delete_button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {RED};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 4px 10px;
                }}

                QPushButton:hover {{
                    background-color: #DC2626;
                }}
                """
            )

            edit_button.clicked.connect(
                lambda checked=False,
                current_event=event_data:
                self.edit_event(
                    current_event
                )
            )

            delete_button.clicked.connect(
                lambda checked=False,
                current_event=event_data:
                self.delete_event_confirm(
                    current_event
                )
            )

            action_layout.addWidget(
                edit_button
            )

            action_layout.addWidget(
                delete_button
            )

            self.events_table.setCellWidget(
                row,
                6,
                action_widget
            )

            self.events_table.setRowHeight(
                row,
                45
            )

    # ========================================================
    # SELECTED DATE
    # ========================================================

    def show_selected_date_events(
        self
    ):

        selected_date = (
            self.calendar
            .selectedDate()
        )

        python_date = (
            selected_date.toPython()
        )

        self.selected_date_label.setText(
            "Events on "
            + selected_date.toString(
                "dd MMMM yyyy"
            )
        )

        try:

            events = (
                get_events_by_date(
                    python_date
                )
            )

        except Exception as error:

            print(
                "Selected date error:",
                error
            )

            events = []

        self.selected_events_table.setRowCount(
            0
        )

        for event_data in events:

            row = (
                self.selected_events_table
                .rowCount()
            )

            self.selected_events_table.insertRow(
                row
            )

            # Title
            title_item = QTableWidgetItem(
                event_data.title or ""
            )

            title_item.setForeground(
                QBrush(
                    QColor(TEXT)
                )
            )

            self.selected_events_table.setItem(
                row,
                0,
                title_item
            )

            # Type
            event_type = (
                event_data.event_type
                or "Other"
            )

            type_item = QTableWidgetItem(
                event_type
            )

            type_item.setForeground(
                QBrush(
                    QColor(
                        self.get_event_color(
                            event_type
                        )
                    )
                )
            )

            type_item.setFont(
                QFont(
                    "Segoe UI",
                    10,
                    QFont.Bold
                )
            )

            self.selected_events_table.setItem(
                row,
                1,
                type_item
            )

            # Description
            description_item = QTableWidgetItem(
                event_data.description
                or "-"
            )

            description_item.setForeground(
                QBrush(
                    QColor(TEXT_MUTED)
                )
            )

            self.selected_events_table.setItem(
                row,
                2,
                description_item
            )

    # ========================================================
    # EVENT COLORS
    # ========================================================

    def get_event_color(
        self,
        event_type
    ):

        colors = {

            "Meeting": BLUE,

            "Holiday": GREEN,

            "Training": PURPLE,

            "Birthday": CYAN,

            "Company Event": YELLOW,

            "Interview": RED,

            "Other": TEXT_MUTED,
        }

        return colors.get(
            event_type,
            TEXT_MUTED
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search_events(
        self,
        text
    ):

        text = (
            text or ""
        ).strip()

        if not text:

            self.populate_events_table(
                self.events
            )

            return

        try:

            results = (
                search_events(
                    text
                )
            )

            self.populate_events_table(
                results
            )

        except Exception as error:

            print(
                "Search error:",
                error
            )

    # ========================================================
    # ADD
    # ========================================================

    def open_add_event(self):

        dialog = EventDialog(
            self
        )

        if (
            dialog.exec()
            == QDialog.Accepted
        ):

            self.refresh_calendar()

    # ========================================================
    # EDIT
    # ========================================================

    def edit_event(
        self,
        event_data
    ):

        dialog = EventDialog(
            self,
            event_data=event_data
        )

        if (
            dialog.exec()
            == QDialog.Accepted
        ):

            self.refresh_calendar()

    # ========================================================
    # DELETE
    # ========================================================

    def delete_event_confirm(
        self,
        event_data
    ):

        reply = QMessageBox.question(
            self,
            "Delete Event",
            (
                "Are you sure you want to delete:\n\n"
                f"{event_data.title}?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:

            delete_event(
                event_data.id
            )

            QMessageBox.information(
                self,
                "Deleted",
                "Calendar event deleted successfully."
            )

            self.refresh_calendar()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Delete Error",
                (
                    "Unable to delete event.\n\n"
                    f"{error}"
                )
            )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_calendar(self):

        self.load_statistics()

        self.load_events()

        self.show_selected_date_events()

    # ========================================================
    # CALENDAR PAGE
    # ========================================================

    def on_calendar_page_changed(
        self,
        year,
        month
    ):

        selected = (
            self.calendar
            .selectedDate()
        )

        if (
            selected.year() != year
            or selected.month() != month
        ):

            self.calendar.setSelectedDate(
                QDate(
                    year,
                    month,
                    1
                )
            )

        self.show_selected_date_events()


# ============================================================
# STANDALONE RUN
# ============================================================

def run_calendar_window():

    import sys

    app = QApplication.instance()

    created_app = False

    if app is None:

        app = QApplication(
            sys.argv
        )

        created_app = True

    window = CalendarWindow()

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

    run_calendar_window()