"""PDF export engine producing A4 printable activity packs."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from app.domain.models import ContentItem, Layout

logger = logging.getLogger(__name__)

# ─── Layout constants ───────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4           # 595.28 x 841.89 pt
MARGIN = 15 * mm              # page margin
TITLE_H = 18 * mm             # height reserved for the title below the image
FOOTER_H = 8 * mm             # height for optional source URL
CELL_PAD = 4 * mm             # inner cell padding

_GRID: dict[Layout, tuple[int, int]] = {
    Layout.A4_2X2: (2, 2),
    Layout.A4_2X3: (2, 3),
    Layout.A4_1COL: (1, 3),
}


def _cell_dimensions(cols: int, rows: int) -> tuple[float, float]:
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN
    cell_w = usable_w / cols
    cell_h = usable_h / rows
    return cell_w, cell_h


async def export_pack(
    items: list[ContentItem],
    layout: Layout,
    export_dir: str,
    cache_dir: str,
    filename: str,
    show_source_footer: bool = True,
) -> str:
    """Render items to a PDF file and return the absolute file path.

    Never raises — logs errors and renders placeholders on failure.
    """
    from app.export.image_cache import fetch_image  # local import to avoid circular

    out_path = str(Path(export_dir) / filename)
    cols, rows = _GRID[layout]
    per_page = cols * rows
    cell_w, cell_h = _cell_dimensions(cols, rows)

    canvas = Canvas(out_path, pagesize=A4)

    if not items:
        _draw_empty_page(canvas)
        canvas.save()
        logger.info("Exported empty pack to %s", out_path)
        return out_path

    for page_start in range(0, len(items), per_page):
        page_items = items[page_start : page_start + per_page]
        for idx, item in enumerate(page_items):
            col = idx % cols
            row_idx = idx // cols
            x = MARGIN + col * cell_w
            y = PAGE_H - MARGIN - (row_idx + 1) * cell_h

            img_path: Optional[str] = None
            if item.image_url:
                img_path = await fetch_image(item.image_url, cache_dir)

            _draw_cell(canvas, item, x, y, cell_w, cell_h, img_path, show_source=show_source_footer)

        canvas.showPage()

    canvas.save()
    logger.info("Exported %d items to %s", len(items), out_path)
    return out_path


def _draw_cell(
    canvas: Canvas,
    item: ContentItem,
    x: float,
    y: float,
    w: float,
    h: float,
    img_path: Optional[str],
    show_source: bool = True,
) -> None:
    """Draw a single item cell with image, title, and optional source."""
    # Cell border
    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.5)
    canvas.rect(x, y, w, h)

    inner_x = x + CELL_PAD
    inner_w = w - 2 * CELL_PAD

    footer_reserve = FOOTER_H if (show_source and item.source_url) else 0
    title_y = y + footer_reserve
    img_h = h - TITLE_H - footer_reserve - 2 * CELL_PAD
    img_y = title_y + TITLE_H

    # Image or placeholder
    if img_path and os.path.exists(img_path):
        try:
            canvas.drawImage(
                img_path,
                inner_x,
                img_y,
                width=inner_w,
                height=img_h,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
        except Exception as exc:
            logger.warning("Could not render image %s: %s", img_path, exc)
            _draw_placeholder(canvas, inner_x, img_y, inner_w, img_h)
    else:
        _draw_placeholder(canvas, inner_x, img_y, inner_w, img_h)

    # Title
    title_text = _truncate(item.title, 48)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.black)
    canvas.drawString(inner_x, title_y + 4 * mm, title_text)

    # Source footer
    if show_source and item.source_url and footer_reserve > 0:
        source_text = _truncate(item.source_url, 60)
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(colors.grey)
        canvas.drawString(inner_x, y + 1 * mm, source_text)


def _draw_placeholder(
    canvas: Canvas, x: float, y: float, w: float, h: float
) -> None:
    canvas.setFillColor(colors.Color(0.93, 0.93, 0.93))
    canvas.setStrokeColor(colors.lightgrey)
    canvas.rect(x, y, w, h, fill=1)
    canvas.setFillColor(colors.grey)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(x + w / 2, y + h / 2, "No image")


def _draw_empty_page(canvas: Canvas) -> None:
    canvas.setFont("Helvetica", 14)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H / 2, "Pack is empty")


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
