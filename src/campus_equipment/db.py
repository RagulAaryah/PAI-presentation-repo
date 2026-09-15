"""Connection helpers shared by tests, the seed script, the benchmark
script and the CLI entry point.

Kept deliberately thin: this module's only job is producing a correctly
configured sqlite3.Connection (schema applied, foreign keys enforced,
rows addressable by column name). All business logic and SQL statements
beyond DDL live in the repository classes under campus_equipment.data.
"""

from __future__ import annotations

import sqlite3
from importlib import resources

_SCHEMA_SQL = resources.files("campus_equipment").joinpath("schema.sql").read_text()

_REPORTING_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment (status);
CREATE INDEX IF NOT EXISTS idx_loan_due_date ON loan (due_date);
"""


def connect(database: str = ":memory:") -> sqlite3.Connection:
    """Open a connection with foreign-key enforcement on and dict-like rows.

    SQLite enforces foreign keys per-connection and defaults it OFF, so
    every connection this application opens must set the pragma explicitly
    -- otherwise the ON DELETE RESTRICT constraints in schema.sql would
    silently do nothing.
    """
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables/constraints defined in schema.sql (idempotent)."""
    conn.executescript(_SCHEMA_SQL)
    conn.commit()


def add_reporting_indexes(conn: sqlite3.Connection) -> None:
    """Add the two reporting indexes benchmarked in scripts/benchmark.py.

    Deliberately separate from init_schema so the benchmark script can
    create an indexed and an unindexed copy of the same seeded database.
    """
    conn.executescript(_REPORTING_INDEXES_SQL)
    conn.commit()
