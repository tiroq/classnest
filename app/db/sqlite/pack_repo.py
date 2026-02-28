"""SQLite implementation of the pack repository."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from app.db.contracts.pack import AbstractPackRepository
from app.db.sqlite.connection import get_connection
from app.domain.models import Pack, PackItem

logger = logging.getLogger(__name__)


class SQLitePackRepository(AbstractPackRepository):

    async def get_pack(self, pack_id: int) -> Optional[Pack]:
        conn = await get_connection()
        async with conn.execute(
            "SELECT * FROM packs WHERE id = ?", (pack_id,)
        ) as cur:
            row = await cur.fetchone()
        return _row_to_pack(row) if row else None

    async def get_active_pack(self, teacher_id: int) -> Optional[Pack]:
        conn = await get_connection()
        async with conn.execute(
            "SELECT p.* FROM packs p"
            " JOIN teacher_settings ts ON ts.active_pack_id = p.id"
            " WHERE ts.teacher_id = ?",
            (teacher_id,),
        ) as cur:
            row = await cur.fetchone()
        return _row_to_pack(row) if row else None

    async def create_pack(self, teacher_id: int, name: str) -> Pack:
        conn = await get_connection()
        now = datetime.now(timezone.utc).isoformat()
        async with conn.execute(
            "INSERT INTO packs (teacher_id, name, created_at) VALUES (?, ?, ?)",
            (teacher_id, name, now),
        ) as cur:
            pack_id = cur.lastrowid
        await conn.commit()
        pack = await self.get_pack(pack_id)
        assert pack is not None
        return pack

    async def delete_pack(self, pack_id: int) -> bool:
        conn = await get_connection()
        async with conn.execute(
            "DELETE FROM packs WHERE id = ?", (pack_id,)
        ) as cur:
            deleted = cur.rowcount > 0
        await conn.commit()
        return deleted

    async def list_items(self, pack_id: int) -> list[PackItem]:
        conn = await get_connection()
        async with conn.execute(
            "SELECT * FROM pack_items WHERE pack_id = ? ORDER BY position",
            (pack_id,),
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_pack_item(r) for r in rows]

    async def add_item(self, pack_id: int, content_item_id: int) -> PackItem:
        conn = await get_connection()
        async with conn.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 FROM pack_items WHERE pack_id = ?",
            (pack_id,),
        ) as cur:
            row = await cur.fetchone()
        next_pos = row[0]
        async with conn.execute(
            "INSERT INTO pack_items (pack_id, content_item_id, position) VALUES (?, ?, ?)",
            (pack_id, content_item_id, next_pos),
        ) as cur:
            item_id = cur.lastrowid
        await conn.commit()
        async with conn.execute(
            "SELECT * FROM pack_items WHERE id = ?", (item_id,)
        ) as cur2:
            pi_row = await cur2.fetchone()
        return _row_to_pack_item(pi_row)

    async def remove_item(self, pack_item_id: int) -> bool:
        conn = await get_connection()
        async with conn.execute(
            "DELETE FROM pack_items WHERE id = ?", (pack_item_id,)
        ) as cur:
            deleted = cur.rowcount > 0
        await conn.commit()
        return deleted

    async def reorder_item(self, pack_item_id: int, new_position: int) -> bool:
        """Move an item to new_position, shifting other items to maintain contiguous order.

        Processing items in the correct sequential order (descending when moving
        up, ascending when moving down) ensures each row's target position is
        always unoccupied, satisfying UNIQUE(pack_id, position) at every step.
        A negative sentinel parks the target item out of the way during shifts.
        """
        conn = await get_connection()

        async with conn.execute(
            "SELECT pack_id, position FROM pack_items WHERE id = ?",
            (pack_item_id,),
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            return False

        pack_id = row["pack_id"]
        current_position = row["position"]

        async with conn.execute(
            "SELECT COALESCE(MAX(position), 0) FROM pack_items WHERE pack_id = ?",
            (pack_id,),
        ) as cur:
            max_row = await cur.fetchone()

        max_position = max_row[0]
        if max_position == 0:
            return False

        # Clamp to valid range
        new_position = max(1, min(new_position, max_position))
        if new_position == current_position:
            return True

        # Park target at a unique negative sentinel to free its current slot
        sentinel = -pack_item_id
        await conn.execute(
            "UPDATE pack_items SET position = ? WHERE id = ?",
            (sentinel, pack_item_id),
        )

        if new_position < current_position:
            # Moving up: process items in DESC position order so each item
            # moves into the slot just vacated by the one processed before it.
            async with conn.execute(
                "SELECT id FROM pack_items"
                " WHERE pack_id = ? AND position >= ? AND position < ?"
                " ORDER BY position DESC",
                (pack_id, new_position, current_position),
            ) as cur:
                to_shift = await cur.fetchall()
            for r in to_shift:
                await conn.execute(
                    "UPDATE pack_items SET position = position + 1 WHERE id = ?",
                    (r["id"],),
                )
        else:
            # Moving down: process items in ASC position order.
            async with conn.execute(
                "SELECT id FROM pack_items"
                " WHERE pack_id = ? AND position > ? AND position <= ?"
                " ORDER BY position ASC",
                (pack_id, current_position, new_position),
            ) as cur:
                to_shift = await cur.fetchall()
            for r in to_shift:
                await conn.execute(
                    "UPDATE pack_items SET position = position - 1 WHERE id = ?",
                    (r["id"],),
                )

        # Place target at final position (now unoccupied)
        async with conn.execute(
            "UPDATE pack_items SET position = ? WHERE id = ?",
            (new_position, pack_item_id),
        ) as cur:
            updated = cur.rowcount > 0

        await conn.commit()
        return updated

    async def clear_pack(self, pack_id: int) -> None:
        conn = await get_connection()
        await conn.execute("DELETE FROM pack_items WHERE pack_id = ?", (pack_id,))
        await conn.commit()


def _row_to_pack(row: aiosqlite.Row) -> Pack:
    return Pack(
        id=row["id"],
        teacher_id=row["teacher_id"],
        name=row["name"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_pack_item(row: aiosqlite.Row) -> PackItem:
    return PackItem(
        id=row["id"],
        pack_id=row["pack_id"],
        content_item_id=row["content_item_id"],
        position=row["position"],
    )
