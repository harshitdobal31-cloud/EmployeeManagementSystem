# Employee Management System (EMS)

A desktop-based Employee Management System developed using **Python, PySide6, SQLAlchemy, and SQLite**. The application is designed to simplify employee-related administrative tasks through a graphical user interface, database management, reporting, attendance tracking, and payroll operations.

## 📌 Project Overview

The Employee Management System (EMS) is a Python desktop application that helps organizations manage employee information and related HR activities from a centralized system.

The project follows a modular structure that separates the user interface, database models, business logic, and utility functions, making the application easier to maintain and extend.

## ✨ Features

### 👥 Employee Management
- Add and manage employee information.
- Organize employee records in a centralized database.
- Use a dedicated employee form and management interface.

### 🔐 Authentication
- Login and signup interfaces.
- Password security utilities using bcrypt.
- User authentication and session management.

### 📅 Attendance Management
- Attendance-related operations.
- Attendance data export support.

### 💰 Payroll Management
- Payroll processing and related calculations.
- Payroll reporting and Excel export support.
- Payslip generation in PDF format.

### 📊 Performance Management
- Manage employee performance-related information.
- Generate performance reports.

### 🏖️ Leave Management
- Leave-related workflows and service functions.
- Leave request database migration support.

### 📈 Reports and Exports
- Generate PDF reports.
- Export data to Excel and CSV formats.
- Support for employee, attendance, payroll, performance, quality, and audit-related reports where implemented.

### 🗓️ Calendar and Notifications
- Calendar-related functionality.
- Notification data and workflows supported by the application.

### ⚙️ Additional Modules
- Quality management.
- Application settings.
- Dashboard interfaces.
- Database migration and seed scripts.

> Note: The availability of individual features may depend on the current implementation and database configuration.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| PySide6 | Desktop graphical user interface |
| SQLAlchemy | Database ORM and data access |
| SQLite | Local database storage |
| pandas | Data processing and exports |
| Matplotlib | Data visualization |
| openpyxl | Excel file handling |
| ReportLab | PDF report generation |
| bcrypt | Password hashing |
| pytest | Automated testing |

## 📁 Project Structure

```text
EmployeeManagementSystem/
│
├── assets/                  # Application assets
├── database/
│   ├── database.py          # Database connection and sessions
│   ├── models.py            # Database models
│   ├── seed.py              # Seed data utility
│   ├── migrate_employee.py  # Employee database migration
│   └── migrate_leave_requests.py
│
├── services/
│   ├── auth_service.py
│   ├── employee_service.py
│   ├── attendance_service.py
│   ├── leave_service.py
│   ├── payroll_service.py
│   ├── performance_service.py
│   ├── quality_service.py
│   ├── calendar_service.py
│   ├── report_service.py
│   └── settings_service.py
│
├── ui/
│   ├── login.py
│   ├── signup.py
│   ├── dashboard.py
│   ├── employee_dashboard.py
│   ├── employees.py
│   ├── employee_form.py
│   ├── attendance.py
│   ├── payroll.py
│   ├── performance.py
│   ├── quality.py
│   ├── calendar.py
│   ├── reports.py
│   └── settings.py
│
├── utils/                   # Security, sessions, themes and exports
├── reports/                 # Report generation modules
├── tests/                   # Automated tests
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

## 💻 System Requirements

- Windows, Linux, or macOS
- Python 3.10 or newer recommended
- pip package manager
- Git (for cloning the repository)

The application has been developed and tested in a Windows environment. Compatibility with other operating systems may require additional configuration.

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/harshitdobal31-cloud/EmployeeManagementSystem.git
```

### 2. Open the Project Directory

```bash
cd EmployeeManagementSystem
```

### 3. Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv venv
```

### 4. Activate the Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt instead:

```cmd
venv\Scripts\activate.bat
```

### 5. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Run the Application

```bash
python main.py
```

## 🗄️ Database

The project uses SQLAlchemy for database operations and SQLite for local data storage.

The database configuration is located in:

```text
database/database.py
```

Database models are defined in:

```text
database/models.py
```

The project also contains database seed and migration scripts. Review their contents before executing them, especially when working with an existing database.

**Important:** Keep personal employee information, passwords, private database files, and production records out of public repositories.

## 🧪 Testing

The project includes a `tests/` directory and uses pytest for automated testing.

Run the available tests from the project root:

```bash
python -m pytest -v
```

Some tests may require a correctly configured database and environment.

## 🔒 Security Considerations

- Password hashing utilities use bcrypt.
- Local database files and environment secrets should not be committed.
- Configure production credentials securely.
- Use appropriate access controls when handling employee and payroll information.
- Review authentication and authorization before deploying the application in a real organization.

## 🔮 Future Enhancements

Potential improvements include:

- More comprehensive role-based access control.
- Enhanced dashboards and analytics.
- Expanded notification workflows.
- Improved automated test coverage.
- Additional database and deployment options.
- More comprehensive validation and error handling.

These are potential enhancements and should not be considered implemented unless they are available in the current codebase.

## 👨‍💻 Author

**Harshit Dobal**

GitHub: [@harshitdobal31-cloud](https://github.com/harshitdobal31-cloud)

## 📄 License

No license has been specified yet. Unless a license is added to this repository, reuse and redistribution are subject to the applicable copyright rules.

---

⭐ If you find this project useful, consider starring the repository.

**Project:** Employee Management System  
**Language:** Python  
**Application Type:** Desktop Application  
**Repository:** [EmployeeManagementSystem](https://github.com/harshitdobal31-cloud/EmployeeManagementSystem)
