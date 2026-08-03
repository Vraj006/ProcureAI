"""
Database connection and session management module.

Configures the SQLAlchemy engine and provides session factory utilities.
Table creation is intentionally deferred — models will define schema later.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """
    Declarative base class for all SQLAlchemy ORM models.

    All database models will inherit from this class to share
    metadata and enable Alembic migrations in the future.
    """

    pass


# SQLAlchemy engine — connection pool configured for production workloads
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,  # Log SQL statements in debug mode
)

# Session factory — creates isolated database sessions per request
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Ensures the session is always closed after the request completes,
    preventing connection leaks.

    Yields:
        SQLAlchemy Session bound to the configured engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> None:
    """
    Verify that the database is reachable.

    Used during application startup to fail fast on misconfiguration.
    Raises RuntimeError when the connection cannot be established.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection verified: %s", settings.database_url.split("@")[-1])
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        raise RuntimeError(
            "Failed to connect to PostgreSQL. Verify DATABASE_URL in backend/.env "
            "matches docker-compose credentials and port (default host port: 5433)."
        ) from exc
