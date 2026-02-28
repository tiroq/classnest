"""Settings handler — cycle group and layout."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from app.domain.models import Layout
from app.ui.dependencies import make_settings_repo
from app.ui.keyboards import settings_menu

logger = logging.getLogger(__name__)
router = Router()

_GROUPS = ["group_a", "group_b", "group_c", "group_d"]
_LAYOUTS = [l.value for l in Layout]


@router.callback_query(lambda c: c.data == "settings_menu")
async def cb_settings_menu(callback: CallbackQuery) -> None:
    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    settings_repo = make_settings_repo()
    ts = await settings_repo.get_teacher_settings(teacher_id)
    await callback.message.edit_text(  # type: ignore[union-attr]
        "⚙️ *Settings*",
        parse_mode="Markdown",
        reply_markup=settings_menu(ts.current_group, ts.preferred_layout.value),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "cycle_group")
async def cb_cycle_group(callback: CallbackQuery) -> None:
    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    settings_repo = make_settings_repo()
    ts = await settings_repo.get_teacher_settings(teacher_id)
    current_idx = _GROUPS.index(ts.current_group) if ts.current_group in _GROUPS else 0
    ts.current_group = _GROUPS[(current_idx + 1) % len(_GROUPS)]
    await settings_repo.save_teacher_settings(ts)
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=settings_menu(ts.current_group, ts.preferred_layout.value)
    )
    await callback.answer(f"Group: {ts.current_group}")


@router.callback_query(lambda c: c.data == "cycle_layout")
async def cb_cycle_layout(callback: CallbackQuery) -> None:
    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    settings_repo = make_settings_repo()
    ts = await settings_repo.get_teacher_settings(teacher_id)
    current_idx = (
        _LAYOUTS.index(ts.preferred_layout.value)
        if ts.preferred_layout.value in _LAYOUTS
        else 0
    )
    ts.preferred_layout = Layout(_LAYOUTS[(current_idx + 1) % len(_LAYOUTS)])
    await settings_repo.save_teacher_settings(ts)
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=settings_menu(ts.current_group, ts.preferred_layout.value)
    )
    await callback.answer(f"Layout: {ts.preferred_layout.value}")
