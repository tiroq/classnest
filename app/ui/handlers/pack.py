"""Pack management handler."""

from __future__ import annotations

import html
import logging
import os
import uuid

from aiogram import Router
from aiogram.types import CallbackQuery, FSInputFile

from app.config.settings import get_settings
from app.ui.dependencies import (
    make_pack_service,
    make_settings_repo,
    make_tracking_service,
)
from app.ui.keyboards import pack_menu

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data == "pack_menu")
async def cb_pack_menu(callback: CallbackQuery) -> None:
    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    pack_svc = make_pack_service()
    items = await pack_svc.list_items(teacher_id)

    if not items:
        text = "🗂 <b>Your Pack</b>\n\nPack is empty. Browse content to add items."
    else:
        lines = [f"🗂 <b>Your Pack</b> ({len(items)} items)\n"]
        for pi, content in items:
            lines.append(f"{pi.position}. {html.escape(content.title)}")
        text = "\n".join(lines)

    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        parse_mode="HTML",
        reply_markup=pack_menu(bool(items)),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("add_item:"))
async def cb_add_item(callback: CallbackQuery) -> None:
    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    item_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    pack_svc = make_pack_service()
    result = await pack_svc.add_item(teacher_id, item_id)
    if result is None:
        await callback.answer("Pack is full!", show_alert=True)
    else:
        await callback.answer("✅ Added to pack!")


@router.callback_query(lambda c: c.data == "clear_pack")
async def cb_clear_pack(callback: CallbackQuery) -> None:
    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    pack_svc = make_pack_service()
    await pack_svc.clear(teacher_id)
    await callback.message.edit_text(  # type: ignore[union-attr]
        "🗑 Pack cleared.",
        reply_markup=pack_menu(False),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "export_pack")
async def cb_export_pack(callback: CallbackQuery) -> None:
    """Generate and send the PDF for the active pack."""
    from app.export.pdf_engine import export_pack

    teacher_id = callback.from_user.id  # type: ignore[union-attr]
    settings_obj = get_settings()
    settings_repo = make_settings_repo()
    pack_svc = make_pack_service()
    tracking_svc = make_tracking_service()

    teacher_settings = await settings_repo.get_teacher_settings(teacher_id)
    rules = await settings_repo.get_rules()
    layout = teacher_settings.preferred_layout

    items_with_pi = await pack_svc.list_items(teacher_id)
    if not items_with_pi:
        await callback.answer("Pack is empty!", show_alert=True)
        return

    await callback.answer("⏳ Generating PDF…")
    content_items = [ci for _, ci in items_with_pi]

    filename = f"pack_{uuid.uuid4().hex}.pdf"
    out_path = await export_pack(
        items=content_items,
        layout=layout,
        export_dir=settings_obj.export_dir,
        cache_dir=settings_obj.cache_dir,
        filename=filename,
        show_source_footer=rules.pdf_footer_show_source,
    )

    group_id = teacher_settings.current_group
    for ci in content_items:
        await tracking_svc.mark_exported(teacher_id, group_id, ci.id)

    if os.path.exists(out_path):
        doc = FSInputFile(out_path)
        try:
            await callback.message.answer_document(  # type: ignore[union-attr]
                doc, caption="📄 Your activity pack"
            )
        finally:
            # Clean up export file to avoid unbounded disk accumulation
            try:
                os.remove(out_path)
            except OSError:
                logger.warning("Could not remove export file: %s", out_path)
    else:
        await callback.message.answer("⚠️ Export failed.")  # type: ignore[union-attr]
