"""Kuzu database connection management."""

import os
from pathlib import Path

import kuzu

# Default database path
DEFAULT_DB_PATH = Path.home() / ".talos" / "telemetry" / "kuzu"

# Module-level connection cache
_db: kuzu.Database | None = None
_conn: kuzu.Connection | None = None


def get_db_path() -> Path:
    """Get database path from environment or default."""
    env_path = os.environ.get("TALOS_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def init_database(path: Path | None = None) -> kuzu.Database:
    """Initialize or get existing database.

    Args:
        path: Optional path to database directory. Uses default if not provided.

    Returns:
        Kuzu Database instance.
    """
    global _db

    if _db is not None:
        return _db

    db_path = path or get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _db = kuzu.Database(str(db_path))
    return _db


def get_connection(path: Path | None = None) -> kuzu.Connection:
    """Get database connection.

    Args:
        path: Optional path to database directory.

    Returns:
        Kuzu Connection instance.
    """
    global _conn

    if _conn is not None:
        return _conn

    db = init_database(path)
    _conn = kuzu.Connection(db)
    return _conn


def close_connection() -> None:
    """Close database connection."""
    global _db, _conn
    _conn = None
    _db = None


def execute_query(query: str, parameters: dict | None = None) -> kuzu.QueryResult:
    """Execute a Cypher query.

    Args:
        query: Cypher query string.
        parameters: Optional query parameters.

    Returns:
        Query result.
    """
    conn = get_connection()
    if parameters:
        return conn.execute(query, parameters)
    return conn.execute(query)
