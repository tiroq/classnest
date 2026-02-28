"""Telegram bot entry point — sets up dispatcher and starts polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config.settings import get_settings
from app.db.sqlite.connection import close_db, init_db
from app.ui.handlers import browse, pack, settings, start

logger = logging.getLogger(__name__)


async def main() -> None:
    cfg = get_settings()
    cfg.ensure_dirs()

    await init_db(cfg.db_sqlite_path)

    bot = Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(browse.router)
    dp.include_router(pack.router)
    dp.include_router(settings.router)

    logger.info("Starting ClassNest bot…")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
