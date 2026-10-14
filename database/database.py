from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Project folder
BASE_DIR = Path(__file__).resolve().parent.parent


# Data folder
DATA_DIR = BASE_DIR / "data"

# Create data folder if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)


# Database file
DATABASE_PATH = DATA_DIR / "employee_management.db"


# SQLite database connection URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False
)


# Database session
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Base class for database models
class Base(DeclarativeBase):
    pass


# Create database tables
def create_tables():
    Base.metadata.create_all(bind=engine)