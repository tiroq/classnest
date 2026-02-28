"""Inline keyboard builders for the Telegram UI."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.domain.models import Category, Layout


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📚 Browse", callback_data="browse_menu"))
    builder.row(InlineKeyboardButton(text="🗂 My Pack", callback_data="pack_menu"))
    builder.row(InlineKeyboardButton(text="⚙️ Settings", callback_data="settings_menu"))
    return builder.as_markup()


def browse_category_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎯 Activities", callback_data="browse:activity:0"),
        InlineKeyboardButton(text="✂️ Crafts", callback_data="browse:craft:0"),
    )
    builder.row(
        InlineKeyboardButton(text="🧩 Logic", callback_data="browse:logic:0"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Home", callback_data="main_menu"))
    return builder.as_markup()


def browse_item_actions(
    category: str, offset: int, item_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Add to Pack", callback_data=f"add_item:{item_id}"
        ),
        InlineKeyboardButton(
            text="🙈 Hide", callback_data=f"hide_item:{item_id}"
        ),
    )
    prev_offset = max(0, offset - 1)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Prev", callback_data=f"browse:{category}:{prev_offset}"
        ),
        InlineKeyboardButton(
            text="➡️ Next", callback_data=f"browse:{category}:{offset + 1}"
        ),
    )
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="browse_menu"))
    return builder.as_markup()


def pack_menu(has_items: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_items:
        builder.row(
            InlineKeyboardButton(text="📄 Export PDF", callback_data="export_pack")
        )
        builder.row(
            InlineKeyboardButton(text="🗑 Clear Pack", callback_data="clear_pack")
        )
    builder.row(InlineKeyboardButton(text="🏠 Home", callback_data="main_menu"))
    return builder.as_markup()


def settings_menu(group: str, layout: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"👥 Group: {group}", callback_data="cycle_group"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"📐 Layout: {layout}", callback_data="cycle_layout"
        )
    )
    builder.row(InlineKeyboardButton(text="🏠 Home", callback_data="main_menu"))
    return builder.as_markup()
