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
        conn = await get_connection()
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
