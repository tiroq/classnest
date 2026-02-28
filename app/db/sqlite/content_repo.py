"""SQLite implementation of the content repository."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from app.db.contracts.content import AbstractContentRepository
from app.db.sqlite.connection import get_connection
from app.domain.models import Category, ContentItem

logger = logging.getLogger(__name__)


class SQLiteContentRepository(AbstractContentRepository):
    """Stores and retrieves content items from SQLite."""

    async def get_by_id(self, item_id: int) -> Optional[ContentItem]:
        conn = await get_connection()
        async with conn.execute(
            "SELECT * FROM content_items WHERE id = ?", (item_id,)
        ) as cur:
            row = await cur.fetchone()
        return _row_to_item(row) if row else None

    async def list_all(
        self,
        category: Optional[Category] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ContentItem]:
        conn = await get_connection()
        if category:
            sql = "SELECT * FROM content_items WHERE category = ? ORDER BY id LIMIT ? OFFSET ?"
            params = (category.value, limit, offset)
        else:
            sql = "SELECT * FROM content_items ORDER BY id LIMIT ? OFFSET ?"
            params = (limit, offset)
        async with conn.execute(sql, params) as cur:
            rows = await cur.fetchall()
        return [_row_to_item(r) for r in rows]

    async def create(
        self,
        title: str,
        category: Category,
        image_url: Optional[str],
        source_url: Optional[str],
        description: Optional[str] = None,
        source: str = "local",
        tags_json: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        difficulty: Optional[str] = None,
    ) -> ContentItem:
        conn = await get_connection()
        now = datetime.now(timezone.utc).isoformat()
        async with conn.execute(
            "INSERT INTO content_items (title, category, image_url, source_url, description, source, tags_json, age_min, age_max, difficulty, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, category.value, image_url, source_url, description, source, tags_json, age_min, age_max, difficulty, now),
        ) as cur:
            row_id = cur.lastrowid
        await conn.commit()
        item = await self.get_by_id(row_id)
        assert item is not None
        return item

    async def update(
        self,
        item_id: int,
        title: Optional[str] = None,
        category: Optional[Category] = None,
        image_url: Optional[str] = None,
        source_url: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        tags_json: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        difficulty: Optional[str] = None,
    ) -> Optional[ContentItem]:
        existing = await self.get_by_id(item_id)
        if existing is None:
            return None
        new_title = title if title is not None else existing.title
        new_category = category if category is not None else existing.category
        new_image = image_url if image_url is not None else existing.image_url
        new_source_url = source_url if source_url is not None else existing.source_url
        new_description = description if description is not None else existing.description
        new_source = source if source is not None else existing.source
        new_tags_json = tags_json if tags_json is not None else existing.tags_json
        new_age_min = age_min if age_min is not None else existing.age_min
        new_age_max = age_max if age_max is not None else existing.age_max
        new_difficulty = difficulty if difficulty is not None else existing.difficulty
        conn = await get_connection()
        await conn.execute(
            "UPDATE content_items SET title=?, category=?, image_url=?, source_url=?,"
            " description=?, source=?, tags_json=?, age_min=?, age_max=?, difficulty=? WHERE id=?",
            (new_title, new_category.value, new_image, new_source_url, new_description, new_source, new_tags_json, new_age_min, new_age_max, new_difficulty, item_id),
        )
        await conn.commit()
        return await self.get_by_id(item_id)

    async def delete(self, item_id: int) -> bool:
        conn = await get_connection()
        async with conn.execute(
            "DELETE FROM content_items WHERE id = ?", (item_id,)
        ) as cur:
            deleted = cur.rowcount > 0
        await conn.commit()
        return deleted

    async def get_by_ids(self, item_ids: list[int]) -> list[ContentItem]:
        """Fetch multiple items by ID in a single query (batch to avoid N+1).

        The f-string only interpolates ``?`` placeholder characters — no user
        data is embedded in the SQL string — so there is no injection risk.
        """
        if not item_ids:
            return []
        conn = await get_connection()
        # Build a parameterised IN clause: "?,?,?" with len(item_ids) slots
        placeholders = ",".join("?" * len(item_ids))
        async with conn.execute(
            f"SELECT * FROM content_items WHERE id IN ({placeholders})",
            item_ids,
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_item(r) for r in rows]

    async def count(self, category: Optional[Category] = None) -> int:
        conn = await get_connection()
        if category:
            sql = "SELECT COUNT(*) FROM content_items WHERE category = ?"
            params = (category.value,)
        else:
            sql = "SELECT COUNT(*) FROM content_items"
            params = ()
        async with conn.execute(sql, params) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0


def _row_to_item(row: aiosqlite.Row) -> ContentItem:
    return ContentItem(
        id=row["id"],
        title=row["title"],
        category=Category(row["category"]),
        image_url=row["image_url"],
        source_url=row["source_url"],
        description=row["description"],
        source=row["source"] if row["source"] else "local",
        tags_json=row["tags_json"],
        age_min=row["age_min"],
        age_max=row["age_max"],
        difficulty=row["difficulty"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
