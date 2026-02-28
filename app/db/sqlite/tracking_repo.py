"""SQLite implementation of the tracking repository."""

from __future__ import annotations

import logging
from datetime import datetime

from app.db.contracts.tracking import AbstractTrackingRepository
from app.db.sqlite.connection import get_connection
from app.domain.models import ExportedItem, HiddenItem, SeenItem

logger = logging.getLogger(__name__)


class SQLiteTrackingRepository(AbstractTrackingRepository):

    async def mark_seen(self, teacher_id: int, content_item_id: int) -> None:
        conn = await get_connection()
        now = datetime.utcnow().isoformat()
        await conn.execute(
            "INSERT INTO seen_items (teacher_id, content_item_id, seen_at) VALUES (?, ?, ?)",
            (teacher_id, content_item_id, now),
        )
        await conn.commit()

    async def mark_hidden(self, teacher_id: int, content_item_id: int) -> None:
        conn = await get_connection()
        now = datetime.utcnow().isoformat()
        await conn.execute(
            "INSERT OR IGNORE INTO hidden_items (teacher_id, content_item_id, hidden_at)"
            " VALUES (?, ?, ?)",
            (teacher_id, content_item_id, now),
        )
        await conn.commit()

    async def unmark_hidden(self, teacher_id: int, content_item_id: int) -> None:
        conn = await get_connection()
        await conn.execute(
            "DELETE FROM hidden_items WHERE teacher_id = ? AND content_item_id = ?",
            (teacher_id, content_item_id),
        )
        await conn.commit()

    async def mark_exported(
        self, teacher_id: int, group_id: str, content_item_id: int
    ) -> None:
        conn = await get_connection()
        now = datetime.utcnow().isoformat()
        await conn.execute(
            "INSERT INTO exported_items (teacher_id, group_id, content_item_id, exported_at)"
            " VALUES (?, ?, ?, ?)",
            (teacher_id, group_id, content_item_id, now),
        )
        await conn.commit()

    async def recent_seen(self, teacher_id: int, limit: int) -> list[SeenItem]:
        conn = await get_connection()
        async with conn.execute(
            "SELECT * FROM seen_items WHERE teacher_id = ?"
            " ORDER BY seen_at DESC LIMIT ?",
            (teacher_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [
            SeenItem(
                teacher_id=r["teacher_id"],
                content_item_id=r["content_item_id"],
                seen_at=datetime.fromisoformat(r["seen_at"]),
            )
            for r in rows
        ]

    async def recent_exported(
        self, teacher_id: int, group_id: str, limit: int
    ) -> list[ExportedItem]:
        conn = await get_connection()
        async with conn.execute(
            "SELECT * FROM exported_items WHERE teacher_id = ? AND group_id = ?"
            " ORDER BY exported_at DESC LIMIT ?",
            (teacher_id, group_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [
            ExportedItem(
                teacher_id=r["teacher_id"],
                group_id=r["group_id"],
                content_item_id=r["content_item_id"],
                exported_at=datetime.fromisoformat(r["exported_at"]),
            )
            for r in rows
        ]

    async def is_hidden(self, teacher_id: int, content_item_id: int) -> bool:
        conn = await get_connection()
        async with conn.execute(
            "SELECT 1 FROM hidden_items WHERE teacher_id = ? AND content_item_id = ?",
            (teacher_id, content_item_id),
        ) as cur:
            row = await cur.fetchone()
        return row is not None

    async def hidden_ids(self, teacher_id: int) -> set[int]:
        conn = await get_connection()
        async with conn.execute(
            "SELECT content_item_id FROM hidden_items WHERE teacher_id = ?",
            (teacher_id,),
        ) as cur:
            rows = await cur.fetchall()
        return {r["content_item_id"] for r in rows}
