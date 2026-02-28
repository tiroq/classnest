"""SQLite connection management with WAL mode enabled.

Each asyncio Task (and therefore each thread's event loop) receives its own
aiosqlite connection via a ContextVar.  This prevents the bot and the admin
panel – which run in separate threads with separate event loops – from ever
sharing the same connection object.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

# Module-level path set once by init_db(); safe to read from any thread.
_db_path: Optional[str] = None

# Per-asyncio-task connection; each task gets its own isolated connection.
_connection_var: ContextVar[Optional[aiosqlite.Connection]] = ContextVar(
    "_connection_var", default=None
)


async def get_connection() -> aiosqlite.Connection:
    """Return the task-local aiosqlite connection, creating it if necessary."""
    if _db_path is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    conn = _connection_var.get()
    if conn is None:
        conn = await aiosqlite.connect(_db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        _connection_var.set(conn)
    return conn


async def init_db(path: str) -> None:
    """Set the DB path, create directories, and apply schema migrations."""
    global _db_path
    _db_path = path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # Schema migration runs via a short-lived temporary connection so that
    # the per-task connection pool starts clean.
    async with aiosqlite.connect(path) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await _apply_schema(conn)
        await conn.commit()
    logger.info("Database initialised at %s", path)


async def close_db() -> None:
    """Close the task-local connection, if one exists."""
    conn = _connection_var.get()
    if conn is not None:
        await conn.close()
        _connection_var.set(None)


async def _apply_schema(conn: aiosqlite.Connection) -> None:
    """Create all tables if they do not exist."""
    await conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS content_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            image_url   TEXT,
            source_url  TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_content_category ON content_items(category);

        CREATE TABLE IF NOT EXISTS teacher_settings (
            teacher_id       INTEGER PRIMARY KEY,
            active_pack_id   INTEGER,
            current_group    TEXT    NOT NULL DEFAULT 'group_a',
            preferred_layout TEXT    NOT NULL DEFAULT 'a4_2x2'
        );

        CREATE TABLE IF NOT EXISTS packs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id  INTEGER NOT NULL,
            name        TEXT    NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pack_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id         INTEGER NOT NULL REFERENCES packs(id) ON DELETE CASCADE,
            content_item_id INTEGER NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
            position        INTEGER NOT NULL,
            UNIQUE (pack_id, position)
        );

        CREATE TABLE IF NOT EXISTS seen_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id      INTEGER NOT NULL,
            content_item_id INTEGER NOT NULL,
            seen_at         TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_seen_teacher ON seen_items(teacher_id);

        CREATE TABLE IF NOT EXISTS hidden_items (
            teacher_id      INTEGER NOT NULL,
            content_item_id INTEGER NOT NULL,
            hidden_at       TEXT    NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (teacher_id, content_item_id)
        );

        CREATE TABLE IF NOT EXISTS exported_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id      INTEGER NOT NULL,
            group_id        TEXT    NOT NULL,
            content_item_id INTEGER NOT NULL,
            exported_at     TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_exported_teacher_group
            ON exported_items(teacher_id, group_id);

        CREATE TABLE IF NOT EXISTS rules (
            id               INTEGER PRIMARY KEY CHECK (id = 1),
            seen_window      INTEGER NOT NULL DEFAULT 20,
            exported_window  INTEGER NOT NULL DEFAULT 10,
            max_pack_size    INTEGER NOT NULL DEFAULT 12
        );
        INSERT OR IGNORE INTO rules (id, seen_window, exported_window, max_pack_size)
            VALUES (1, 20, 10, 12);
        """
    )
