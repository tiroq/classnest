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
        """Return the best next item for the given teacher and category."""
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

        candidate = _pick(visible, seen_ids, exported_ids, offset)
        if candidate is not None:
            return candidate

        # Fallback: ignore seen/exported constraints
        if offset < len(visible):
            return visible[offset]
        return None


def _pick(
    visible: list[ContentItem],
    seen_ids: set[int],
    exported_ids: set[int],
    offset: int,
) -> Optional[ContentItem]:
    """Walk through visible items applying priority filter."""
    clean: list[ContentItem] = []
    partially_clean: list[ContentItem] = []

    for item in visible:
        not_exported = item.id not in exported_ids
        not_seen = item.id not in seen_ids
        if not_exported and not_seen:
            clean.append(item)
        elif not_exported:
            partially_clean.append(item)

    preferred = clean if clean else partially_clean
    if offset < len(preferred):
        return preferred[offset]
    return None
