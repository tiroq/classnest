"""Seed script — populates the database with sample content items."""

from __future__ import annotations

import asyncio
import logging

from app.config.settings import get_settings
from app.db.sqlite.connection import close_db, init_db
from app.db.sqlite.content_repo import SQLiteContentRepository
from app.domain.models import Category

logger = logging.getLogger(__name__)

SEED_ITEMS = [
    ("Color Sorting", Category.ACTIVITY, None, None),
    ("Shape Matching", Category.ACTIVITY, None, None),
    ("Number Tracing 1-10", Category.ACTIVITY, None, None),
    ("Letter Recognition A-M", Category.ACTIVITY, None, None),
    ("Paper Plate Sun", Category.CRAFT, None, None),
    ("Toilet Roll Animals", Category.CRAFT, None, None),
    ("Handprint Butterfly", Category.CRAFT, None, None),
    ("Cotton Ball Snowman", Category.CRAFT, None, None),
    ("Simple Maze", Category.LOGIC, None, None),
    ("Spot the Difference", Category.LOGIC, None, None),
    ("Pattern Completion", Category.LOGIC, None, None),
    ("Odd One Out", Category.LOGIC, None, None),
]


async def seed() -> None:
    cfg = get_settings()
    cfg.ensure_dirs()
    await init_db(cfg.db_sqlite_path)
    repo = SQLiteContentRepository()
    existing = await repo.count()
    if existing > 0:
        logger.info("Database already has %d items — skipping seed.", existing)
        await close_db()
        return
    for title, category, image_url, source_url in SEED_ITEMS:
        await repo.create(title=title, category=category, image_url=image_url, source_url=source_url)
        logger.info("Created: %s (%s)", title, category.value)
    logger.info("Seed complete — %d items inserted.", len(SEED_ITEMS))
    await close_db()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
