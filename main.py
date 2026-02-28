"""Application entry point — starts both the Telegram bot and the admin panel."""

from __future__ import annotations

import asyncio
import logging
import threading

import uvicorn

from app.config.settings import get_settings
from app.db.sqlite.connection import init_db
from app.admin.app import create_admin_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _run_admin(host: str, port: int, db_path: str) -> None:
    """Run the FastAPI admin panel in a dedicated thread with its own event loop.

    Calling ``init_db`` here sets ``_db_path`` for this thread's event loop.
    With the ContextVar-based connection pool, the admin and bot never share a
    connection object.
    """

    async def run() -> None:
        await init_db(db_path)
        config = uvicorn.Config(
            create_admin_app(), host=host, port=port, log_level="info"
        )
        await uvicorn.Server(config).serve()

    asyncio.run(run())


async def run_bot() -> None:
    from app.ui.bot import main as bot_main
    await bot_main()


def main() -> None:
    cfg = get_settings()
    cfg.ensure_dirs()

    # Start the admin panel in a daemon thread (own event loop + own DB connections)
    admin_thread = threading.Thread(
        target=_run_admin,
        args=(cfg.admin_host, cfg.admin_port, cfg.db_sqlite_path),
        daemon=True,
    )
    admin_thread.start()
    logger.info("Admin panel starting on http://%s:%d", cfg.admin_host, cfg.admin_port)

    # Run the bot in the main asyncio loop (its own DB connections via ContextVar)
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
