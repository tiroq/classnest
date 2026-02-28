"""SQLite implementation of the settings repository."""

from __future__ import annotations

import logging

import aiosqlite

from app.db.contracts.settings import AbstractSettingsRepository
from app.db.sqlite.connection import get_connection
from app.domain.models import Layout, Rules, TeacherSettings

logger = logging.getLogger(__name__)


class SQLiteSettingsRepository(AbstractSettingsRepository):

    async def get_teacher_settings(self, teacher_id: int) -> TeacherSettings:
        conn = await get_connection()
        async with conn.execute(
            "SELECT * FROM teacher_settings WHERE teacher_id = ?", (teacher_id,)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            settings = TeacherSettings(teacher_id=teacher_id)
            await self.save_teacher_settings(settings)
            return settings
        return _row_to_settings(row)

    async def save_teacher_settings(self, settings: TeacherSettings) -> None:
        conn = await get_connection()
        await conn.execute(
            "INSERT INTO teacher_settings (teacher_id, active_pack_id, current_group,"
            " preferred_layout) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(teacher_id) DO UPDATE SET"
            "   active_pack_id   = excluded.active_pack_id,"
            "   current_group    = excluded.current_group,"
            "   preferred_layout = excluded.preferred_layout",
            (
                settings.teacher_id,
                settings.active_pack_id,
                settings.current_group,
                settings.preferred_layout.value,
            ),
        )
        await conn.commit()

    async def get_rules(self) -> Rules:
        conn = await get_connection()
        async with conn.execute("SELECT * FROM rules WHERE id = 1") as cur:
            row = await cur.fetchone()
        if row is None:
            return Rules()
        return Rules(
            seen_window=row["seen_window"],
            exported_window=row["exported_window"],
            max_pack_size=row["max_pack_size"],
        )

    async def save_rules(self, rules: Rules) -> None:
        conn = await get_connection()
        await conn.execute(
            "INSERT INTO rules (id, seen_window, exported_window, max_pack_size)"
            " VALUES (1, ?, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET"
            "   seen_window     = excluded.seen_window,"
            "   exported_window = excluded.exported_window,"
            "   max_pack_size   = excluded.max_pack_size",
            (rules.seen_window, rules.exported_window, rules.max_pack_size),
        )
        await conn.commit()


def _row_to_settings(row: aiosqlite.Row) -> TeacherSettings:
    return TeacherSettings(
        teacher_id=row["teacher_id"],
        active_pack_id=row["active_pack_id"],
        current_group=row["current_group"],
        preferred_layout=Layout(row["preferred_layout"]),
    )
