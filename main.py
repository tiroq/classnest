"""Application entry point — starts both the Telegram bot and the admin panel."""

from __future__ import annotations

import asyncio
import logging
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config.settings import get_settings
from app.db.sqlite.connection import close_db, init_db
from app.admin.app import create_admin_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _run_admin(host: str, port: int, db_path: str) -> None:
    """Run the FastAPI admin panel in a background thread with its own event loop."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db(db_path)
        yield
        await close_db()

    admin_app = create_admin_app()
    admin_app.router.lifespan_context = lifespan
    uvicorn.run(admin_app, host=host, port=port, log_level="info")


async def run_bot() -> None:
    from app.ui.bot import main as bot_main
    await bot_main()


def main() -> None:
    cfg = get_settings()
    cfg.ensure_dirs()

    # Start the admin panel in a daemon thread (own event loop + own DB connection)
    admin_thread = threading.Thread(
        target=_run_admin,
        args=(cfg.admin_host, cfg.admin_port, cfg.db_sqlite_path),
        daemon=True,
    )
    admin_thread.start()
    logger.info("Admin panel starting on http://%s:%d", cfg.admin_host, cfg.admin_port)

    # Run the bot in the main asyncio loop (initialises its own DB connection)
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
