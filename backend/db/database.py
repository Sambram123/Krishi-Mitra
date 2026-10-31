"""
Krishi Mitra — Database Connection and Session Management
SQLAlchemy 2.0 configuration with SQLite default and PostgreSQL readiness.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Default to local SQLite database; supports postgresql:// or postgresql+psycopg2://
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./krishi_mitra.db")

# Normalize Postgres driver URL for SQLAlchemy 2.0 if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates all defined tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
