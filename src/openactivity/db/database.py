"""Database initialization and session management."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
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


def _migrate_db(engine) -> None:
    """Apply schema migrations for new columns on existing tables."""
    inspector = inspect(engine)
    migrations = [
        ("activities", "pr_scanned", "BOOLEAN DEFAULT 0"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            if table in inspector.get_table_names():
                existing = {c["name"] for c in inspector.get_columns(table)}
                if column not in existing:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                    )
        conn.commit()


def init_db(db_path: Path | None = None) -> None:
    """Initialize database: create all tables if they don't exist."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    _migrate_db(engine)


def get_session(db_path: Path | None = None) -> Session:
    """Create a new database session."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(db_path)
        _session_factory = sessionmaker(bind=engine)
    return _session_factory()
