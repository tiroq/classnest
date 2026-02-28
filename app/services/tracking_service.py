"""Anti-repeat tracking service."""

from __future__ import annotations

import logging

from app.db.contracts.tracking import AbstractTrackingRepository
from app.domain.models import ExportedItem, SeenItem

logger = logging.getLogger(__name__)


class TrackingService:
    """Records and queries teacher interaction history for anti-repeat logic."""

    def __init__(self, tracking_repo: AbstractTrackingRepository) -> None:
        self._repo = tracking_repo

    async def mark_seen(self, teacher_id: int, content_item_id: int) -> None:
        await self._repo.mark_seen(teacher_id, content_item_id)

    async def mark_hidden(self, teacher_id: int, content_item_id: int) -> None:
        await self._repo.mark_hidden(teacher_id, content_item_id)

    async def mark_exported(
        self, teacher_id: int, group_id: str, content_item_id: int
    ) -> None:
        await self._repo.mark_exported(teacher_id, group_id, content_item_id)

    async def recent_seen(self, teacher_id: int, limit: int = 20) -> list[SeenItem]:
        return await self._repo.recent_seen(teacher_id, limit)

    async def recent_exported(
        self, teacher_id: int, group_id: str, limit: int = 10
    ) -> list[ExportedItem]:
        return await self._repo.recent_exported(teacher_id, group_id, limit)
