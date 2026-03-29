"""Add source_filename column to activities table.

This allows filtering already-imported Garmin FIT files by their original
filename, avoiding redundant downloads and re-parsing on subsequent imports.
"""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def migrate(engine: Engine) -> None:
    """Add source_filename column to activities table."""
    inspector = inspect(engine)

    with engine.connect() as conn:
        if "activities" in inspector.get_table_names():
            existing_columns = {c["name"] for c in inspector.get_columns("activities")}

            if "source_filename" not in existing_columns:
                conn.execute(
                    text("ALTER TABLE activities ADD COLUMN source_filename VARCHAR")
                )

        conn.commit()
