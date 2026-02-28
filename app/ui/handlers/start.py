"""Start / main menu handler."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.ui.keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Display the main menu."""
    await message.answer(
        "👋 Welcome to *ClassNest*\n\nBuild printable activity packs for your group.",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )


@router.callback_query(lambda c: c.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        "🏠 *ClassNest — Main Menu*",
        parse_mode="Markdown",
        reply_markup=main_menu(),
    )
    await callback.answer()
