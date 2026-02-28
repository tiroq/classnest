"""Browse / content discovery handler."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from app.domain.models import Category
from app.ui.dependencies import make_selector, make_tracking_service
from app.ui.keyboards import browse_category_menu, browse_item_actions

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "browse_menu")
async def cb_browse_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        "📚 *Browse Content*\n\nChoose a category:",
        parse_mode="Markdown",
        reply_markup=browse_category_menu(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("browse:"))
async def cb_browse_item(callback: CallbackQuery) -> None:
    """Display the next content item for the selected category and offset."""
    parts = callback.data.split(":")  # type: ignore[union-attr]
    if len(parts) != 3:
        await callback.answer("Invalid action.")
        return

    _, raw_category, raw_offset = parts
    try:
        category = Category(raw_category)
        offset = int(raw_offset)
    except (ValueError, KeyError):
        await callback.answer("Unknown category.")
        return

    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    selector = make_selector()
    tracking = make_tracking_service()

    item = await selector.next_item(teacher_id, category, offset)

    if item is None:
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"No more items in *{category.value}*.",
            parse_mode="Markdown",
            reply_markup=browse_category_menu(),
        )
        await callback.answer()
        return

    await tracking.mark_seen(teacher_id, item.id)

    text = (
        f"*{item.title}*\n"
        f"Category: {item.category.value}\n"
    )
    if item.source_url:
        text += f"[Source]({item.source_url})"

    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        parse_mode="Markdown",
        reply_markup=browse_item_actions(category.value, offset, item.id),
        disable_web_page_preview=False,
    )
    await callback.answer()
