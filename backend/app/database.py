"""Database connection and session handling using SQLAlchemy 2.0.

Provides standard SQLite connection, sessionmaker, and dependency injection.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# For SQLite, check_same_thread=False is needed when accessed across worker threads
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session for each request.

    Closes the session cleanly upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
