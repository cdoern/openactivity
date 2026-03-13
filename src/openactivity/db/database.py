"""Database initialization and session management."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from openactivity.db.models import Base

DEFAULT_DB_DIR = Path.home() / ".local" / "share" / "openactivity"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "openactivity.db"

_engine = None
_session_factory = None


def _set_wal_mode(dbapi_connection, connection_record):
    """Enable WAL mode for concurrent read performance."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.close()


def get_engine(db_path: Path | None = None):
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        path = db_path or DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{path}", echo=False)
        event.listen(_engine, "connect", _set_wal_mode)
    return _engine


def init_db(db_path: Path | None = None) -> None:
    """Initialize database: create all tables if they don't exist."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def get_session(db_path: Path | None = None) -> Session:
    """Create a new database session."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(db_path)
        _session_factory = sessionmaker(bind=engine)
    return _session_factory()
