"""
Database configuration and SQLite connection helper.
"""

import sqlite3
from pathlib import Path


# ---------------------------------------------------------------------
# DATABASE PATH
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "data" / "nifty100.db"


# ---------------------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------------------

def get_db_connection():
    """Create and return a SQLite database connection."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection