"""Pack management service."""

from __future__ import annotations

import logging
from typing import Optional

from app.db.contracts.content import AbstractContentRepository
from app.db.contracts.pack import AbstractPackRepository
from app.db.contracts.settings import AbstractSettingsRepository
from app.domain.models import ContentItem, Pack, PackItem

logger = logging.getLogger(__name__)


class PackService:
    """Manages creation, modification, and retrieval of packs."""

    def __init__(
        self,
        pack_repo: AbstractPackRepository,
        content_repo: AbstractContentRepository,
        settings_repo: AbstractSettingsRepository,
    ) -> None:
        self._packs = pack_repo
        self._content = content_repo
        self._settings = settings_repo

    async def ensure_active_pack(self, teacher_id: int) -> Pack:
        """Return active pack, creating one if none exists."""
        settings = await self._settings.get_teacher_settings(teacher_id)
        if settings.active_pack_id is not None:
            pack = await self._packs.get_pack(settings.active_pack_id)
            if pack is not None:
                return pack
        return await self.create_pack(teacher_id, "My Pack")

    async def create_pack(self, teacher_id: int, name: str) -> Pack:
        """Create a new pack and set it as the active pack."""
        pack = await self._packs.create_pack(teacher_id, name)
        settings = await self._settings.get_teacher_settings(teacher_id)
        settings.active_pack_id = pack.id
        await self._settings.save_teacher_settings(settings)
        logger.info("Created pack %d for teacher %d", pack.id, teacher_id)
        return pack

    async def add_item(
        self, teacher_id: int, content_item_id: int
    ) -> Optional[PackItem]:
        """Add an item to the active pack, respecting max size."""
        pack = await self.ensure_active_pack(teacher_id)
        rules = await self._settings.get_rules()
        items = await self._packs.list_items(pack.id)
        if len(items) >= rules.max_pack_size:
            logger.warning(
                "Pack %d is full (max %d items)", pack.id, rules.max_pack_size
            )
            return None
        return await self._packs.add_item(pack.id, content_item_id)

    async def remove(self, pack_item_id: int) -> bool:
        return await self._packs.remove_item(pack_item_id)

    async def reorder(self, pack_item_id: int, new_position: int) -> bool:
        return await self._packs.reorder_item(pack_item_id, new_position)

    async def clear(self, teacher_id: int) -> None:
        pack = await self.ensure_active_pack(teacher_id)
        await self._packs.clear_pack(pack.id)

    async def list_items(self, teacher_id: int) -> list[tuple[PackItem, ContentItem]]:
        """Return ordered pack items paired with their content objects (single batch fetch)."""
        pack = await self.ensure_active_pack(teacher_id)
        pack_items = await self._packs.list_items(pack.id)
        if not pack_items:
            return []
        item_ids = [pi.content_item_id for pi in pack_items]
        content_map = {
            c.id: c for c in await self._content.get_by_ids(item_ids)
        }
        return [
            (pi, content_map[pi.content_item_id])
            for pi in pack_items
            if pi.content_item_id in content_map
        ]
