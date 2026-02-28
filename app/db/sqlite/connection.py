"""SQLite connection management with WAL mode enabled."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

_db_path: Optional[str] = None
_connection: Optional[aiosqlite.Connection] = None


async def get_connection() -> aiosqlite.Connection:
    """Return the shared aiosqlite connection, creating it if necessary."""
    global _connection, _db_path
    if _connection is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _connection


async def init_db(path: str) -> None:
    """Initialise the SQLite database, enable WAL mode, and create schema."""
    global _connection, _db_path
    _db_path = path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    _connection = await aiosqlite.connect(path)
    _connection.row_factory = aiosqlite.Row
    await _connection.execute("PRAGMA journal_mode=WAL")
    await _connection.execute("PRAGMA foreign_keys=ON")
    await _apply_schema(_connection)
    await _connection.commit()
    logger.info("Database initialised at %s", path)


async def close_db() -> None:
    """Close the database connection."""
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None


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
            position        INTEGER NOT NULL
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
