# ============================================================
# PERFORMANCE MANAGEMENT MODULE
# ============================================================

from PySide6.QtCore import (
    Qt,
    QDate,
    QPropertyAnimation,
    QEasingCurve,
)

from PySide6.QtGui import QFont

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from services.performance_service import (
    PERFORMANCE_CATEGORIES,
    get_performance_employees,
    add_performance,
    update_performance,
    get_all_performance,
    search_performance,
    delete_performance,
    get_performance_summary,
)


# ============================================================
# PERFORMANCE FORM DIALOG
# ============================================================

class PerformanceFormDialog(QDialog):

    def __init__(
        self,
        performance=None,
        parent=None
    ):

        super().__init__(parent)

        self.performance = performance
        self.fade_animation = None

        self.setWindowTitle(
            "Edit Performance Review"
            if performance
            else "Add Performance Review"
        )

        self.setMinimumSize(
            680,
            750
        )

        self.setModal(True)

        self.setup_ui()

        self.load_employees()

        self.load_categories()

        if self.performance:

            self.load_performance_data()

        self.update_preview()

        self.start_fade_animation()

    # ========================================================
    # FADE ANIMATION
    # ========================================================

    def start_fade_animation(self):

        effect = QGraphicsOpacityEffect(
            self
        )

        self.setGraphicsEffect(
            effect
        )

        self.fade_animation = QPropertyAnimation(
            effect,
            b"opacity",
            self
        )

        self.fade_animation.setDuration(
            350
        )

        self.fade_animation.setStartValue(
            0.0
        )

        self.fade_animation.setEndValue(
            1.0
        )

        self.fade_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.fade_animation.start()

    # ========================================================
    # UI SETUP
    # ========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        main_layout.setSpacing(
            16
        )

        # ====================================================
        # HEADER
        # ====================================================

        title = QLabel(
            "Edit Performance Review"
            if self.performance
            else "Add Performance Review"
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
            "Update employee performance information"
            if self.performance
            else "Evaluate employee performance using a 1–10 score"
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color: #64748B;
                font-size: 14px;
                background: transparent;
            }
            """
        )

        main_layout.addWidget(
            subtitle
        )

        # ====================================================
        # FORM CARD
        # ====================================================

        form_card = QFrame()

        form_card.setStyleSheet(
            """
            QFrame {
                background: #FFFFFF;
                border: 1px solid #D9E2EF;
                border-radius: 16px;
            }
            """
        )

        form_layout = QGridLayout(
            form_card
        )

        form_layout.setContentsMargins(
            25,
            24,
            25,
            24
        )

        form_layout.setHorizontalSpacing(
            18
        )

        form_layout.setVerticalSpacing(
            17
        )

        # ====================================================
        # EMPLOYEE
        # ====================================================

        employee_label = QLabel(
            "Employee"
        )

        employee_label.setStyleSheet(
            self.label_style()
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
        # REVIEW DATE
        # ====================================================

        date_label = QLabel(
            "Review Date"
        )

        date_label.setStyleSheet(
            self.label_style()
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

        self.date_input.setMinimumHeight(
            44
        )

        self.date_input.setStyleSheet(
            self.date_style()
        )

        calendar = QCalendarWidget()

        calendar.setGridVisible(
            False
        )

        calendar.setMinimumSize(
            330,
            250
        )

        calendar.setStyleSheet(
            """
            QCalendarWidget {
                background: #FFFFFF;
                color: #0F2747;
                border: 1px solid #CBD5E1;
                border-radius: 12px;
            }

            QCalendarWidget QToolButton {
                color: #0F2747;
                background: #F1F5F9;
                border: none;
                border-radius: 6px;
                padding: 7px;
                font-size: 14px;
                font-weight: 600;
            }

            QCalendarWidget QToolButton:hover {
                background: #DBEAFE;
                color: #1D4ED8;
            }

            QCalendarWidget QAbstractItemView {
                background: #FFFFFF;
                color: #0F2747;
                selection-background-color: #2563EB;
                selection-color: #FFFFFF;
                outline: none;
                font-size: 13px;
            }
            """
        )

        self.date_input.setCalendarWidget(
            calendar
        )

        form_layout.addWidget(
            date_label,
            1,
            0
        )

        form_layout.addWidget(
            self.date_input,
            1,
            1
        )

        # ====================================================
        # CATEGORY
        # ====================================================

        category_label = QLabel(
            "Performance Category"
        )

        category_label.setStyleSheet(
            self.label_style()
        )

        self.category_input = QComboBox()

        self.category_input.setMinimumHeight(
            44
        )

        self.category_input.setStyleSheet(
            self.combo_style()
        )

        form_layout.addWidget(
            category_label,
            2,
            0
        )

        form_layout.addWidget(
            self.category_input,
            2,
            1
        )

        # ====================================================
        # SCORE
        # ====================================================

        score_label = QLabel(
            "Performance Score"
        )

        score_label.setStyleSheet(
            self.label_style()
        )

        self.score_input = QDoubleSpinBox()

        self.score_input.setRange(
            1,
            10
        )

        self.score_input.setDecimals(
            1
        )

        self.score_input.setSingleStep(
            0.5
        )

        self.score_input.setValue(
            5
        )

        self.score_input.setSuffix(
            " / 10"
        )

        self.score_input.setMinimumHeight(
            44
        )

        self.score_input.setStyleSheet(
            self.spinbox_style()
        )

        form_layout.addWidget(
            score_label,
            3,
            0
        )

        form_layout.addWidget(
            self.score_input,
            3,
            1
        )

        # ====================================================
        # COMMENTS
        # ====================================================

        comments_label = QLabel(
            "Performance Comments"
        )

        comments_label.setStyleSheet(
            self.label_style()
        )

        self.comments_input = QTextEdit()

        self.comments_input.setPlaceholderText(
            "Enter performance comments, achievements, "
            "areas of improvement..."
        )

        self.comments_input.setMinimumHeight(
            105
        )

        self.comments_input.setStyleSheet(
            """
            QTextEdit {
                background: #FFFFFF;
                color: #0F2747;
                border: 1px solid #C9D5E5;
                border-radius: 9px;
                padding: 10px;
                font-size: 14px;
            }

            QTextEdit:hover {
                border: 1px solid #93B4E8;
            }

            QTextEdit:focus {
                border: 2px solid #2563EB;
            }
            """
        )

        form_layout.addWidget(
            comments_label,
            4,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        form_layout.addWidget(
            self.comments_input,
            4,
            1
        )

        main_layout.addWidget(
            form_card
        )

        # ====================================================
        # PREVIEW
        # ====================================================

        preview_card = QFrame()

        preview_card.setStyleSheet(
            """
            QFrame {
                background: #F5F9FF;
                border: 1px solid #C8DDFF;
                border-radius: 16px;
            }
            """
        )

        preview_layout = QGridLayout(
            preview_card
        )

        preview_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        # Average

        average_title = QLabel(
            "Average Score"
        )

        average_title.setStyleSheet(
            self.preview_title_style()
        )

        self.average_label = QLabel(
            "5.00 / 10"
        )

        self.average_label.setStyleSheet(
            self.preview_value_style()
        )

        preview_layout.addWidget(
            average_title,
            0,
            0
        )

        preview_layout.addWidget(
            self.average_label,
            1,
            0
        )

        # Percentage

        percentage_title = QLabel(
            "Percentage"
        )

        percentage_title.setStyleSheet(
            self.preview_title_style()
        )

        self.percentage_label = QLabel(
            "50.00%"
        )

        self.percentage_label.setStyleSheet(
            self.preview_value_style()
        )

        preview_layout.addWidget(
            percentage_title,
            0,
            1
        )

        preview_layout.addWidget(
            self.percentage_label,
            1,
            1
        )

        # Grade

        grade_title = QLabel(
            "Performance Grade"
        )

        grade_title.setStyleSheet(
            self.preview_title_style()
        )

        self.grade_label = QLabel(
            "Needs Improvement"
        )

        preview_layout.addWidget(
            grade_title,
            0,
            2
        )

        preview_layout.addWidget(
            self.grade_label,
            1,
            2
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
            115,
            45
        )

        cancel_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        cancel_button.setStyleSheet(
            self.cancel_button_style()
        )

        cancel_button.clicked.connect(
            self.reject
        )

        save_button = QPushButton(
            "Update Performance"
            if self.performance
            else "Save Performance"
        )

        save_button.setMinimumSize(
            180,
            45
        )

        save_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        save_button.setStyleSheet(
            self.save_button_style()
        )

        save_button.clicked.connect(
            self.save_performance
        )

        button_layout.addWidget(
            cancel_button
        )

        button_layout.addWidget(
            save_button
        )

        main_layout.addLayout(
            button_layout
        )

        self.score_input.valueChanged.connect(
            self.update_preview
        )

    # ========================================================
    # STYLES
    # ========================================================

    def label_style(self):

        return """
        QLabel {
            color: #0F2747;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        }
        """

    def combo_style(self):

        return """
        QComboBox {
            background: #FFFFFF;
            color: #0F2747;
            border: 1px solid #C9D5E5;
            border-radius: 9px;
            padding: 8px 12px;
            font-size: 14px;
        }

        QComboBox:hover {
            border: 1px solid #7AA7E8;
        }

        QComboBox:focus {
            border: 2px solid #2563EB;
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

    def date_style(self):

        return """
        QDateEdit {
            background: #FFFFFF;
            color: #0F2747;
            border: 1px solid #C9D5E5;
            border-radius: 9px;
            padding: 8px 12px;
            font-size: 14px;
        }

        QDateEdit:hover {
            border: 1px solid #7AA7E8;
        }

        QDateEdit:focus {
            border: 2px solid #2563EB;
        }

        QDateEdit::drop-down {
            width: 38px;
            border: none;
            border-left: 1px solid #E2E8F0;
            background: #F8FAFC;
        }
        """

    def spinbox_style(self):

        return """
        QDoubleSpinBox {
            background: #FFFFFF;
            color: #0F2747;
            border: 1px solid #C9D5E5;
            border-radius: 9px;
            padding: 8px 12px;
            font-size: 14px;
        }

        QDoubleSpinBox:focus {
            border: 2px solid #2563EB;
        }
        """

    def preview_title_style(self):

        return """
        QLabel {
            color: #64748B;
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
        }
        """

    def preview_value_style(self):

        return """
        QLabel {
            color: #2563EB;
            font-size: 21px;
            font-weight: 700;
            background: transparent;
            border: none;
        }
        """

    def cancel_button_style(self):

        return """
        QPushButton {
            background: #E8EEF7;
            color: #334155;
            border: none;
            border-radius: 9px;
            font-size: 14px;
            font-weight: 600;
            padding: 8px 18px;
        }

        QPushButton:hover {
            background: #D9E3F0;
        }
        """

    def save_button_style(self):

        return """
        QPushButton {
            background: #2563EB;
            color: white;
            border: none;
            border-radius: 9px;
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

            employees = (
                get_performance_employees()
            )

            for employee in employees:

                self.employee_input.addItem(
                    f"{employee.employee_id} - "
                    f"{employee.full_name}",
                    employee.id
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                f"Unable to load employees.\n\n{error}"
            )

    # ========================================================
    # LOAD CATEGORIES
    # ========================================================

    def load_categories(self):

        self.category_input.clear()

        self.category_input.addItem(
            "Select Category",
            None
        )

        for category in PERFORMANCE_CATEGORIES:

            self.category_input.addItem(
                category,
                category
            )

    # ========================================================
    # LOAD EXISTING PERFORMANCE
    # ========================================================

    def load_performance_data(self):

        if not self.performance:
            return

        # ----------------------------------------------------
        # EMPLOYEE
        # ----------------------------------------------------

        employee_index = (
            self.employee_input.findData(
                self.performance.employee_id
            )
        )

        if employee_index >= 0:

            self.employee_input.setCurrentIndex(
                employee_index
            )

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        saved_category = (
            str(
                self.performance.category
                or ""
            ).strip()
        )

        category_index = (
            self.category_input.findData(
                saved_category
            )
        )

        if category_index < 0:

            category_index = (
                self.category_input.findText(
                    saved_category,
                    Qt.MatchFlag.MatchFixedString
                )
            )

        if category_index >= 0:

            self.category_input.setCurrentIndex(
                category_index
            )

        # IMPORTANT:
        # Category must remain ENABLED during edit.
        self.category_input.setEnabled(
            True
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        review_date = QDate.fromString(
            str(
                self.performance.review_date
            ),
            "yyyy-MM-dd"
        )

        if review_date.isValid():

            self.date_input.setDate(
                review_date
            )

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        self.score_input.setValue(
            float(
                self.performance.score or 0
            )
        )

        # ----------------------------------------------------
        # COMMENTS
        # ----------------------------------------------------

        self.comments_input.setPlainText(
            self.performance.comments or ""
        )

        # ----------------------------------------------------
        # LOCK ONLY EMPLOYEE + DATE
        # ----------------------------------------------------

        self.employee_input.setEnabled(
            False
        )

        self.date_input.setEnabled(
            False
        )

    # ========================================================
    # UPDATE PREVIEW
    # ========================================================

    def update_preview(self):

        score = self.score_input.value()

        percentage = score * 10

        if percentage >= 90:

            grade = "Excellent"

            color = "#15803D"

        elif percentage >= 75:

            grade = "Very Good"

            color = "#2563EB"

        elif percentage >= 60:

            grade = "Good"

            color = "#CA8A04"

        else:

            grade = "Needs Improvement"

            color = "#DC2626"

        self.average_label.setText(
            f"{score:.2f} / 10"
        )

        self.percentage_label.setText(
            f"{percentage:.2f}%"
        )

        self.grade_label.setText(
            grade
        )

        self.grade_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 17px;
                font-weight: 700;
                background: transparent;
                border: none;
            }}
            """
        )

    # ========================================================
    # SAVE / UPDATE PERFORMANCE
    # ========================================================

    def save_performance(self):

        employee_id = (
            self.employee_input.currentData()
        )

        category = (
            self.category_input.currentData()
        )

        review_date = (
            self.date_input
            .date()
            .toString(
                "yyyy-MM-dd"
            )
        )

        score = (
            self.score_input.value()
        )

        comments = (
            self.comments_input
            .toPlainText()
            .strip()
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if employee_id is None:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select an employee."
            )

            return

        if category is None:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select a performance category."
            )

            return

        if score < 1 or score > 10:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Performance score must be between 1 and 10."
            )

            return

        # ----------------------------------------------------
        # EDIT
        # ----------------------------------------------------

        if self.performance:

            success, message = (
                update_performance(
                    performance_id=
                    self.performance.id,

                    score=score,

                    comments=comments,

                    category=category
                )
            )

        # ----------------------------------------------------
        # ADD
        # ----------------------------------------------------

        else:

            success, message = (
                add_performance(
                    employee_id=employee_id,
                    review_date=review_date,
                    category=category,
                    score=score,
                    comments=comments
                )
            )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

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
                "Performance Error",
                message
            )


# ============================================================
# PERFORMANCE MANAGEMENT WINDOW
# ============================================================

class PerformanceWindow(QWidget):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "Performance Management"
        )

        self.setMinimumSize(
            1250,
            760
        )

        self.setup_ui()

        self.load_summary()

        self.load_performance()

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout(
            self
        )

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
            "Performance Management"
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
                background: transparent;
            }
            """
        )

        subtitle = QLabel(
            "Evaluate, monitor and track employee performance"
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

        add_button = QPushButton(
            "+ Add Performance"
        )

        add_button.setMinimumSize(
            180,
            46
        )

        add_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        add_button.setStyleSheet(
            """
            QPushButton {
                background: #2563EB;
                color: white;
                border: none;
                border-radius: 9px;
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

        add_button.clicked.connect(
            self.open_add_performance
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

        cards_layout.setSpacing(
            15
        )

        self.total_card = (
            self.create_summary_card(
                "TOTAL REVIEWS",
                "0"
            )
        )

        self.average_card = (
            self.create_summary_card(
                "AVERAGE SCORE",
                "0.00 / 10"
            )
        )

        self.percentage_card = (
            self.create_summary_card(
                "AVERAGE PERCENTAGE",
                "0%"
            )
        )

        self.excellent_card = (
            self.create_summary_card(
                "EXCELLENT REVIEWS",
                "0"
            )
        )

        cards_layout.addWidget(
            self.total_card
        )

        cards_layout.addWidget(
            self.average_card
        )

        cards_layout.addWidget(
            self.percentage_card
        )

        cards_layout.addWidget(
            self.excellent_card
        )

        main_layout.addLayout(
            cards_layout
        )

        # ====================================================
        # SEARCH
        # ====================================================

        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search employee, category or review date..."
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
            self.load_performance
        )

        search_layout.addWidget(
            self.search_input
        )

        refresh_button = QPushButton(
            "↻  Refresh"
        )

        refresh_button.setMinimumSize(
            110,
            44
        )

        refresh_button.clicked.connect(
            self.refresh_page
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
                color: #1D4ED8;
            }
            """
        )

        search_layout.addWidget(
            refresh_button
        )

        main_layout.addLayout(
            search_layout
        )

        # ====================================================
        # TABLE
        # ====================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            11
        )

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Employee ID",
                "Employee Name",
                "Review Date",
                "Category",
                "Score",
                "Percentage",
                "Grade",
                "Comments",
                "Edit",
                "Delete",
            ]
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
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
                border-radius: 12px;
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

        header = (
            self.table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        main_layout.addWidget(
            self.table
        )

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
                border-radius: 14px;
            }

            QFrame:hover {
                border: 1px solid #93B4E8;
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
                font-size: 12px;
                font-weight: 700;
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

        card.value_label = (
            value_label
        )

        return card

    # ========================================================
    # LOAD SUMMARY
    # ========================================================

    def load_summary(self):

        try:

            summary = (
                get_performance_summary()
            )

            self.total_card.value_label.setText(
                str(
                    summary["total_records"]
                )
            )

            self.average_card.value_label.setText(
                f"{summary['average_score']:.2f} / 10"
            )

            self.percentage_card.value_label.setText(
                f"{summary['average_percentage']:.2f}%"
            )

            self.excellent_card.value_label.setText(
                str(
                    summary["excellent"]
                )
            )

        except Exception as error:

            QMessageBox.warning(
                self,
                "Error",
                f"Unable to load performance summary.\n\n{error}"
            )

    # ========================================================
    # LOAD PERFORMANCE
    # ========================================================

    def load_performance(self):

        search_text = (
            self.search_input
            .text()
            .strip()
        )

        try:

            records = search_performance(
                search_text
            )

            self.table.setRowCount(
                0
            )

            self.table.setRowCount(
                len(records)
            )

            for row, record in enumerate(
                records
            ):

                performance = record[0]

                employee = record[1]

                self.table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        str(
                            performance.id
                        )
                    )
                )

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        employee.employee_id
                    )
                )

                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        employee.full_name
                    )
                )

                self.table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        str(
                            performance.review_date
                        )
                    )
                )

                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        performance.category
                    )
                )

                score_item = QTableWidgetItem(
                    f"{float(performance.score or 0):.1f} / 10"
                )

                score_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    5,
                    score_item
                )

                percentage = float(
                    performance.percentage or 0
                )

                percentage_item = QTableWidgetItem(
                    f"{percentage:.1f}%"
                )

                percentage_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    6,
                    percentage_item
                )

                if percentage >= 90:

                    grade = "Excellent"

                elif percentage >= 75:

                    grade = "Very Good"

                elif percentage >= 60:

                    grade = "Good"

                else:

                    grade = "Needs Improvement"

                grade_item = QTableWidgetItem(
                    grade
                )

                grade_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    7,
                    grade_item
                )

                comments = (
                    performance.comments
                    or "-"
                )

                self.table.setItem(
                    row,
                    8,
                    QTableWidgetItem(
                        comments
                    )
                )

                # ------------------------------------------------
                # EDIT
                # ------------------------------------------------

                edit_button = QPushButton(
                    "Edit"
                )

                edit_button.setCursor(
                    Qt.CursorShape.PointingHandCursor
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
                    performance_id=performance.id:
                    self.edit_performance(
                        performance_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    9,
                    edit_button
                )

                # ------------------------------------------------
                # DELETE
                # ------------------------------------------------

                delete_button = QPushButton(
                    "Delete"
                )

                delete_button.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )

                delete_button.setStyleSheet(
                    """
                    QPushButton {
                        background: #FEE2E2;
                        color: #B91C1C;
                        border: none;
                        border-radius: 6px;
                        padding: 7px 10px;
                        font-weight: 600;
                    }

                    QPushButton:hover {
                        background: #FECACA;
                    }
                    """
                )

                delete_button.clicked.connect(
                    lambda checked=False,
                    performance_id=performance.id:
                    self.delete_performance_record(
                        performance_id
                    )
                )

                self.table.setCellWidget(
                    row,
                    10,
                    delete_button
                )

            self.table.resizeRowsToContents()

        except Exception as error:

            QMessageBox.warning(
                self,
                "Error",
                f"Unable to load performance records.\n\n{error}"
            )

    # ========================================================
    # ADD
    # ========================================================

    def open_add_performance(self):

        dialog = PerformanceFormDialog(
            parent=self
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):

            self.refresh_page()

    # ========================================================
    # EDIT
    # ========================================================

    def edit_performance(
        self,
        performance_id
    ):

        records = (
            get_all_performance()
        )

        performance = None

        for record in records:

            if record[0].id == performance_id:

                performance = record[0]

                break

        if performance is None:

            QMessageBox.warning(
                self,
                "Error",
                "Performance record not found."
            )

            return

        dialog = PerformanceFormDialog(
            performance=performance,
            parent=self
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):

            self.refresh_page()

    # ========================================================
    # DELETE
    # ========================================================

    def delete_performance_record(
        self,
        performance_id
    ):

        answer = QMessageBox.question(
            self,
            "Delete Performance",
            "Are you sure you want to delete this "
            "performance record?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes
            |
            QMessageBox.StandardButton.No
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):

            return

        success, message = (
            delete_performance(
                performance_id
            )
        )

        if success:

            QMessageBox.information(
                self,
                "Deleted",
                message
            )

            self.refresh_page()

        else:

            QMessageBox.warning(
                self,
                "Delete Error",
                message
            )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_page(self):

        self.load_summary()

        self.load_performance()