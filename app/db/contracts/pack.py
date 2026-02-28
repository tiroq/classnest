"""Abstract repository contract for packs and pack items."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models import Pack, PackItem


class AbstractPackRepository(ABC):

    @abstractmethod
    async def get_pack(self, pack_id: int) -> Optional[Pack]:
        ...

    @abstractmethod
    async def get_active_pack(self, teacher_id: int) -> Optional[Pack]:
        ...

    @abstractmethod
    async def create_pack(self, teacher_id: int, name: str) -> Pack:
        ...

    @abstractmethod
    async def delete_pack(self, pack_id: int) -> bool:
        ...

    @abstractmethod
    async def list_items(self, pack_id: int) -> list[PackItem]:
        ...

    @abstractmethod
    async def add_item(self, pack_id: int, content_item_id: int) -> PackItem:
        ...

    @abstractmethod
    async def remove_item(self, pack_item_id: int) -> bool:
        ...

    @abstractmethod
    async def reorder_item(self, pack_item_id: int, new_position: int) -> bool:
        ...

    @abstractmethod
    async def clear_pack(self, pack_id: int) -> None:
        ...
