# Employee Management System

A desktop-based Employee Management System built with Python and PySide6. The project is designed to help manage employee information and common HR operations through a graphical user interface.

## Features

- **Employee Management:** Add and manage employee records.
- **Authentication:** Login with role-based access.
- **Attendance Management:** Organize employee attendance records.
- **Payroll Management:** Maintain payroll-related information.
- **Performance Management:** Track employee performance.
- **Notifications:** Display notifications to relevant users.
- **Departments:** Organize employees by department.
- **Audit Logs:** Maintain records of selected system activities.
- **Database Integration:** Store and manage application data.

> Note: Features listed here describe the project's intended modules. Availability may depend on the current implementation.

## Technology Stack

- **Language:** Python
- **Desktop GUI:** PySide6
- **Data Processing:** Pandas and NumPy
- **Charts and Visualization:** Matplotlib
- **Database Layer:** SQLAlchemy / project database configuration
- **Development Environment:** Visual Studio Code

## Project Structure

```text
EmployeeManagementSystem/
├── database/
│   ├── seed.py
│   └── ...
├── services/
├── tests/
├── requirements.txt
├── database.py
├── models.py
├── .gitignore
└── README.md
```

The actual folder structure may differ as the project develops.

## Prerequisites

- Python installed on your computer
- Git installed
- Visual Studio Code (recommended)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/Employee-Management-System.git
cd Employee-Management-System
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If the project contains a `requirements.txt` file:

```bash
python -m pip install -r requirements.txt
```

If it does not, install the project's required packages according to the imports and database configuration before running the application.

### 4. Configure the database

Check the project's database configuration and follow its setup or migration instructions. Use your own local credentials and keep passwords and private database files out of GitHub.

### 5. Run the application

Use the entry-point Python file configured by the project. For example, if the main file is `main.py`:

```bash
python main.py
```

If your entry point has a different name, replace `main.py` with the correct filename.


python -m pytest
```

Resolve any missing dependencies or database setup requirements before running the tests.

## Security Notes

- Do not commit passwords, API keys, or `.env` files.
- Do not upload private employee information or production database backups.
- Use demo data for screenshots and demonstrations.
- Configure database credentials locally.

## Future Improvements

- Improve reporting and dashboard visualizations.
- Expand automated testing.
- Improve notification workflows.
- Add additional reporting and export options.

## Author

**Harshit Dobal**

## License

No license has been selected yet. All rights remain with the author unless a license is added to this repository.
## Testing

Run the automated tests from the project root directory:

```powershell
python -m pytest -v
```

If a test fails, review the error message and verify that the required dependencies and database configuration are available.

## Project Structure

- `database/` — Database models, connection, migrations, and seed scripts
- `services/` — Application business logic
- `ui/` — PySide6 desktop interface
- `reports/` — Report generation and export utilities
- `tests/` — Automated tests
- `utils/` — Shared utilities and helper functions

## Technologies Used

- Python
- PySide6
- SQLAlchemy
- SQLite
- Pandas
- Matplotlib
- Pytest