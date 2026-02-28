"""Content selector — picks the best next item for a teacher."""

from __future__ import annotations

import logging
from typing import Optional

from app.db.contracts.content import AbstractContentRepository
from app.db.contracts.settings import AbstractSettingsRepository
from app.db.contracts.tracking import AbstractTrackingRepository
from app.domain.models import Category, ContentItem

logger = logging.getLogger(__name__)


class ContentSelector:
    """Selects content items respecting anti-repeat rules.

    Priority order:
      1. Not hidden by teacher
      2. Not recently exported (group-based window)
      3. Not recently seen
      4. Fallback: any non-hidden item
    """

    def __init__(
        self,
        content_repo: AbstractContentRepository,
        tracking_repo: AbstractTrackingRepository,
        settings_repo: AbstractSettingsRepository,
    ) -> None:
        self._content = content_repo
        self._tracking = tracking_repo
        self._settings = settings_repo

    async def next_item(
        self,
        teacher_id: int,
        category: Category,
        offset: int = 0,
    ) -> Optional[ContentItem]:
        """Return the best item at the given stable offset in the visible list.

        ``offset`` is an index into the full non-hidden item list (ordered by
        ID), giving stable Prev/Next navigation even as items become "seen".
        Starting from that offset, we scan forward for the highest-priority
        eligible item, then fall back to the item at the exact offset position.
        """
        settings = await self._settings.get_teacher_settings(teacher_id)
        rules = await self._settings.get_rules()
        group_id = settings.current_group

        hidden = await self._tracking.hidden_ids(teacher_id)
        seen_items = await self._tracking.recent_seen(teacher_id, rules.seen_window)
        exported_items = await self._tracking.recent_exported(
            teacher_id, group_id, rules.exported_window
        )
        seen_ids = {s.content_item_id for s in seen_items}
        exported_ids = {e.content_item_id for e in exported_items}

        all_items = await self._content.list_all(category=category, limit=500)
        visible = [i for i in all_items if i.id not in hidden]

        if not visible or offset >= len(visible):
            return None

        return _pick_from_offset(visible, seen_ids, exported_ids, offset)


def _pick_from_offset(
    visible: list[ContentItem],
    seen_ids: set[int],
    exported_ids: set[int],
    offset: int,
) -> ContentItem:
    """Return the best item starting from *offset* in the stable visible list.

    Scans forward from ``offset`` looking for the highest-priority item:
      1. Not recently exported and not recently seen
      2. Not recently exported (but seen)
      3. Fallback: the item at the exact offset position
    """
    # Priority 1: clean (not exported, not seen)
    for i in range(offset, len(visible)):
        item = visible[i]
        if item.id not in exported_ids and item.id not in seen_ids:
            return item

    # Priority 2: not exported even if seen
    for i in range(offset, len(visible)):
        item = visible[i]
        if item.id not in exported_ids:
            return item

    # Fallback: stable position (item may be seen/exported)
    return visible[offset]
