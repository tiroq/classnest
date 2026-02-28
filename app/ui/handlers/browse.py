"""Browse / content discovery handler."""

from __future__ import annotations

import html
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
        "📚 <b>Browse Content</b>\n\nChoose a category:",
        parse_mode="HTML",
        reply_markup=browse_category_menu(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("browse:"))
async def cb_browse_item(callback: CallbackQuery) -> None:
    """Display the content item at the given stable offset for the category."""
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
            f"No more items in <b>{html.escape(category.value)}</b>.",
            parse_mode="HTML",
            reply_markup=browse_category_menu(),
        )
        await callback.answer()
        return

    await tracking.mark_seen(teacher_id, item.id)

    text = f"<b>{html.escape(item.title)}</b>\nCategory: {html.escape(item.category.value)}"
    if item.source_url:
        text += f'\n<a href="{html.escape(item.source_url)}">Source</a>'

    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        parse_mode="HTML",
        reply_markup=browse_item_actions(category.value, offset, item.id),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("hide_item:"))
async def cb_hide_item(callback: CallbackQuery) -> None:
    """Hide the item so it no longer appears in browse results."""
    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    item_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    tracking = make_tracking_service()
    await tracking.mark_hidden(teacher_id, item_id)
    await callback.answer("🙈 Item hidden.")
